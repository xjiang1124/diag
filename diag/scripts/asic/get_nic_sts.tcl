# !/usr/bin/tclsh
puts "argv: $argv"

proc test_proc {input} {
    return $input
}

set sn      [lindex $argv 0]
set slot    [lindex $argv 1]
set check_vrm    [lindex $argv 2]

set port 10

set err_cnt 0

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

set MTP_TYPE $::env(MTP_TYPE)
set ASIC_TYPE $::env(ASIC_TYPE)
set UUT_NUM "UUT_$slot"
set BOARD_TYPE $::env($UUT_NUM)
set ddr5 0
set cpld_id 0x60
if { $BOARD_TYPE == "GINESTRA_D5" } {
    set ddr5 1
    set cpld_id 0x61
}
puts "Getting ASIC status - sn: $sn; slot: $slot; check_vrm: $check_vrm; board_type: $BOARD_TYPE"
source /home/diag/diag/scripts/asic/asic_tests.tcl

cd $ASIC_SRC/ip/cosim/tclsh
if {($MTP_TYPE == "MTP_ELBA") || ($MTP_TYPE == "MTP_TURBO_ELBA")} {
    puts $MTP_TYPE
    if {$ASIC_TYPE == "GIGLIO"} {
        source .tclrc.diag.gig
    } else {
        source .tclrc.diag.elb.new
    }

    if { $MTP_TYPE == "MTP_TURBO_ELBA" } {
        set port [get_port_turbo $slot]
        set slot 1
    }
} elseif {$MTP_TYPE == "MTP_TOR"} {
    puts "TOR MTP"
    catch {
        set ELBA0_ID $::env(ELBA0_J2C_ID)
	set ELBA1_ID $::env(ELBA1_J2C_ID)
    }
    if { $slot == 1 } {
        set port $ELBA0_ID
        if { [file exists /sys/bus/pci/devices/0000:0b:00.0/remove] == 1} {
            exec echo 1 > /sys/bus/pci/devices/0000:0b:00.0/remove
        }
        set val [exec /fs/nos/home_diag/diag/util/fpgautil r32 1 0x414]
        puts "ELB_PWR_STAT_REG=$val \n"
        return
    } else {
        if { [file exists /sys/bus/pci/devices/0000:05:00.0/remove] == 1} {
            set port $ELBA1_ID
            exec echo 1 > /sys/bus/pci/devices/0000:05:00.0/remove
        }
        set val [exec /fs/nos/home_diag/diag/util/fpgautil r32 1 0x41C]
        puts "ELB_PWR_STAT_REG=$val \n"
        return
    }
    set slot 10
    source .tclrc.diag.elb.new

} else {
    puts "Capri MTP"
    source .tclrc.diag.new
}

diag_open_j2c_if $port $slot

set val [_msrd]
if { $val != 0x00000001 } {
    plog_msg "J2C sanity test failed!"
    exit 0
}

set in_err [plog_get_err_count]

plog_msg "=================="
plog_msg "MC intr"
plog_msg "=================="
if {$ASIC_TYPE == "GIGLIO"} {
    #gig_platform 1
    gig_mc_irq_show -1 -1 $ddr5
} else {
    mc_int
}

set val [_msrd]
if { $val != 0x00000001 } {
    plog_msg "J2C sanity test failed!"
    exit 0
}
plog_msg "\n\n\n"
plog_msg "=================="
plog_msg "ECC intr"
plog_msg "=================="
if {$ASIC_TYPE == "GIGLIO"} {
    gig_mc_check_ecc -1 -1 $ddr5 $cpld_id
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt != 0} {
        plog_msg "ECC happaned. Dumping DDR configuration"
        exec rm -rf ${sn}_dump 
        exec mkdir ${sn}_dump 
        cd ${sn}_dump
        ddr5_dump_all
        cd ..
        set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
        exec tar cf ${sn}_dump_${cur_time}.tar ${sn}_dump/
    } else {
        plog_msg "ECC is clean"
    }
    gig_mc_clear_ecc_irq  -1  -1  -1  $ddr5
    gig_mc_clear_ecc_counter  -1  -1  $ddr5

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]

    if {$err_cnt != 0} {
        plog_msg "ECC happaned. Dumping DDR configuration"
        exec rm -rf ${sn}_dump 
        exec mkdir ${sn}_dump 
        cd ${sn}_dump
        ddr5_dump_all
        cd ..
        set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
        exec tar cf ${sn}_dump_${cur_time}.tar ${sn}_dump/
    } else {
        plog_msg "ECC is clean"
    }
} else {
    set output [check_ecc_intr]
    set substring "ECC_EN:0x33 ECC_INTERRUPT:0x0"
    if {[string first $substring $output] == -1} {
        plog_msg "ECC happened! Dumping training config"
        exec rm -rf ${sn}_dump 
        exec mkdir ${sn}_dump 
        cd ${sn}_dump
        dump_all
        cd ..
        exec tar cf ${sn}_dump.tar ${sn}_dump/
    }
    elb_ddr_rst_ecc_intr_counter
}

set val [_msrd]
if { $val != 0x00000001 } {
    plog_msg "J2C sanity test failed!"
    exit 0
}

if {$ASIC_TYPE == "GIGLIO"} {
    plog_msg "\n\n\n"
    plog_msg "=================="
    plog_msg "GIG health check"
    plog_msg "=================="
    gig_health_check
}

plog_msg "\n\n\n"
plog_msg "=================="
plog_msg "ARM status"
plog_msg "=================="
arm_hang_dbg_display

set val [_msrd]
if { $val != 0x00000001 } {
    plog_msg "J2C sanity test failed!"
    exit 0
}

if { $check_vrm != 0 } {
        plog_msg "\n\n\n"
        plog_msg "=================="
        plog_msg "Get volt info via J2C"
        plog_msg "=================="

    if {$ASIC_TYPE == "GIGLIO"} {
        gig_assert_arm_rst 0 0xf
        ssi_cpld_write 0x20 0x0
        gig_print_voltage_temp
    } else {
        elb_assert_arm_rst 0 0xf
        ssi_cpld_write 0x20 0x0
        elb_print_voltage_temp
    }
}
plog_msg "Getting ASIC status - Done"

