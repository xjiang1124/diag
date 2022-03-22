# !/usr/bin/tclsh
puts "argv: $argv"

proc test_proc {input} {
    return $input
}

set slot     [lindex $argv 0]
set port 10

set err_cnt 0

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

set MTP_TYPE $::env(MTP_TYPE)

puts "Getting ASIC status - slot: $slot"
source /home/diag/diag/scripts/asic/asic_tests.tcl

cd $ASIC_SRC/ip/cosim/tclsh
if {($MTP_TYPE == "MTP_ELBA") || ($MTP_TYPE == "MTP_TURBO_ELBA")} {
    puts $MTP_TYPE
    source .tclrc.diag.elb.new

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

mc_int
check_ecc_intr
elb_ddr_rst_ecc_intr_counter

#rst_arm0_set 0
elb_assert_arm_rst 0 0xf
ssi_cpld_write 0x20 0x0
elb_print_voltage_temp

puts "Getting ASIC status - Done"

