#! /usr/bin/tclsh
puts "argv: $argv"

proc test_proc {input} {
    return $input
}

proc print_pmic_events {} {
    plog_msg "=================="
    plog_msg "PMIC fault events:"
    plog_msg "=================="

    set val [gig_smbus_read_byte_data 2 0x4F 0x08]
    set vin_bulk_sts [expr ($val >> 0) & 0x1]
    plog_msg "\tVIN_BULK_INPUT_OVER_VOLTAGE_STATUS     : $vin_bulk_sts"
    set temp_shutdown_sts [expr ($val >> 6) & 0x1]
    plog_msg "\tCRITICAL_TEMPERATURE_SHUTDOWN_STATUS   : $temp_shutdown_sts"

    set val [gig_smbus_read_byte_data 2 0x4F 0x0A]
    set swa_over_vol_sts [expr ($val >> 7) & 0x1]
    plog_msg "\tSWA_OUTPUT_OVER_VOLTAGE_STATUS         : $swa_over_vol_sts"
    set swb_over_vol_sts [expr ($val >> 6) & 0x1]
    plog_msg "\tSWB_OUTPUT_OVER_VOLTAGE_STATUS         : $swb_over_vol_sts"
    set swc_over_vol_sts [expr ($val >> 5) & 0x1]
    plog_msg "\tSWC_OUTPUT_OVER_VOLTAGE_STATUS         : $swc_over_vol_sts"
    set swd_over_vol_sts [expr ($val >> 4) & 0x1]
    plog_msg "\tSWD_OUTPUT_OVER_VOLTAGE_STATUS         : $swd_over_vol_sts"

    set val [gig_smbus_read_byte_data 2 0x4F 0x0B]
    set swa_under_volt_sts [expr ($val >> 3) & 0x1]
    plog_msg "\tSWA_OUTPUT_UNDER_VOLTAGE_LOCKOUT_STATUS: $swa_under_volt_sts"
    set swb_under_volt_sts [expr ($val >> 2) & 0x1]
    plog_msg "\tSWB_OUTPUT_UNDER_VOLTAGE_LOCKOUT_STATUS: $swb_under_volt_sts"
    set swc_under_volt_sts [expr ($val >> 1) & 0x1]
    plog_msg "\tSWC_OUTPUT_UNDER_VOLTAGE_LOCKOUT_STATUS: $swc_under_volt_sts"
    set swd_under_volt_sts [expr ($val >> 0) & 0x1]
    plog_msg "\tSWD_OUTPUT_UNDER_VOLTAGE_LOCKOUT_STATUS: $swd_under_volt_sts"

    set val [gig_smbus_read_byte_data 2 0x4F 0x33]
    set vbias_under_volt_stat [expr ($val >> 3) & 0x1]
    plog_msg "\tVBIAS_UNDER_VOLTAGE_LOCKOUT_STATUS     : $vbias_under_volt_stat"
}

proc sal_get_ddr_read_write_eye {} {
    # Dump DRAM mode register by MRR command
    plog_msg "MC0: DRAM mode register dump"
    for {set i 0} {$i < 255} {incr i} {
        ddr_mrr 0 0 $i
    }
    plog_msg "MC1: DRAM mode register dump"
    for {set i 0} {$i < 255} {incr i} {
        ddr_mrr 1 0 $i
    }

    # Check any MC got CE, do read/write eye for only first CE
    for {set eye_mc 0} {$eye_mc < 4} {incr eye_mc} {
        set eye_inst_id [expr {$eye_mc / 2}]
        set eye_core_id [expr {$eye_mc % 2}]
        set eye_err_ce [mc_dhs_read ECC_C_SYND $eye_inst_id $eye_core_id]

        # Ignore if this MC doesn't get any CE
        if { $eye_err_ce == 0 } {
            continue
        }

        # Otherwise, check CE on which slice (not care per bit this time). Note: CPLD_ID is not matter here
        set eye_ori_dq [tcl_sal_mc_interpret_ecc_syndrome $eye_err_ce]
        set eye_soc_dq [tcl_sal_mc_decode_dq $eye_core_id $eye_ori_dq 0x64)]
        set eye_slice [expr {$eye_soc_dq / 8}]

        # Reduce test size to run faster, along with dlystep = 4
        set ::pi_bist_default_end_bank 2
        set ::pi_bist_default_end_row 0xFF

        # Run write eye
        set eye_channel 0; set eye_rank 0; set eye_run 0; set eye_dlystep 4
        plog_msg [format "Write eye of Slice%d" $eye_slice]
        set pi_bist_default_slice_dis_mask [expr {~(1 << $eye_slice)}]
        pi_bist_find_eye $eye_channel $eye_rank $eye_run -0x30 0x30 0x4 -0x40 0x40 $eye_dlystep

        # Run read eye
        set eye_channel 0; set eye_rank 0; set eye_run 5; set eye_dlystep 4
        plog_msg [format "Read eye of Slice%d" $eye_slice]
        set pi_bist_default_slice_dis_mask [expr {~(1 << $eye_slice)}]
        pi_bist_find_eye $eye_channel $eye_rank $eye_run -0x60 0x60 0x8 -0x40 0x40 $eye_dlystep
        break
    }
}

set sn      [lindex $argv 0]
set slot    [lindex $argv 1]
if {[llength $argv] >= 3} {
    set check_vrm    [lindex $argv 2]
} else {
    set check_vrm 0
}
if {[llength $argv] >= 4} {
    set check_ecc_only [lindex $argv 3]
} else {
    set check_ecc_only 0
}
set check_prp 1

set port 10

set err_cnt 0
set slot_num $slot

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
puts "Getting ASIC status - sn: $sn; slot: $slot; check_vrm: $check_vrm; check_ecc_only: $check_ecc_only; board_type: $BOARD_TYPE"
source /home/diag/diag/scripts/asic/asic_tests.tcl

cd $ASIC_SRC/ip/cosim/tclsh
if {($MTP_TYPE == "MTP_ELBA") || ($MTP_TYPE == "MTP_TURBO_ELBA") || ($MTP_TYPE == "MTP_MATERA")} {
    puts $MTP_TYPE
    if {$ASIC_TYPE == "GIGLIO"} {
        source .tclrc.diag.gig
    } elseif {$ASIC_TYPE == "SALINA"} {
        source .tclrc.diag.sal
    } else {
        source .tclrc.diag.elb.new
    }

    if { $MTP_TYPE == "MTP_TURBO_ELBA" } {
        set port [get_port_turbo $slot]
        set slot 1
    } elseif { $MTP_TYPE == "MTP_MATERA" } {
        if {$ASIC_TYPE == "SALINA"} {
            set slot $slot
            set port $slot

            set ::slot $slot
            set ::port $port

            exec jtag_accpcie_salina clr $slot
            exec fpgautil spimode $slot off

            diag_close_j2c_if $port $slot
            diag_open_j2c_if $port $slot
            diag_close_j2c_if $port $slot

            after 1000
            diag_close_ow_if $port $slot
            after 1000
            diag_open_ow_if $port $slot
            after 1000
            sal_ow_axi

            csr_write sal0.ms.ms.cfg_ow 3
            after 500
            rd sal0.ms.ms.cfg_ow

            sal_j2c
            set j2c_secure 1
        } else {
            set port $slot
        }
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

if {$ASIC_TYPE != "SALINA"} {
    diag_open_j2c_if $port $slot
}
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
} elseif {$ASIC_TYPE == "SALINA"} {
    sal_mc_irq_show -1 -1 1
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
if {$ASIC_TYPE == "GIGLIO" || $ASIC_TYPE == "SALINA"} {
    if {$ASIC_TYPE == "GIGLIO"} {
        gig_mc_check_ecc -1 -1 $ddr5 $cpld_id
    } else {
        sal_mc_check_ecc -1 -1 1 0x61 1
    }
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt != 0} {
        plog_msg "GET_NIC_STS_DBG_INFO: ECC happened. Dumping DDR configuration"
        exec rm -rf ${sn}_dump 
        exec mkdir ${sn}_dump 
        cd ${sn}_dump
        ddr5_dump_all
        cd ..
        set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
        exec tar cf ${sn}_dump_${cur_time}.tar ${sn}_dump/
        if {$ASIC_TYPE == "SALINA"} {
            source $::env(ASIC_SRC)/ip/cosim/salina/ddr/salina_ddr_eye.tcl
            plog_msg "GET_NIC_STS_DBG_INFO: ECC happened. Do read/write eye"
            sal_get_ddr_read_write_eye
        }
    } else {
        plog_msg "ECC is clean"
    }
    if {$ASIC_TYPE == "GIGLIO"} {
        gig_mc_clear_ecc_irq  -1  -1  -1  $ddr5
        gig_mc_clear_ecc_counter  -1  -1  $ddr5
    } else {
        sal_mc_clear_ecc_irq  -1  -1  -1  1
        sal_mc_clear_ecc_counter  -1  -1  1
    }

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]

    if {$err_cnt != 0} {
        plog_msg "GET_NIC_STS_DBG_INFO: ECC happened. Dumping DDR configuration"
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

if { $check_ecc_only != 0 } {
    plog_msg "Getting ASIC ECC status - Done"
    exit 0
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

if {$ASIC_TYPE == "GIGLIO"} {
    set pmic_gsi [exec inventory -pw -slot=$slot_num | grep gilo_ddr_pmic_gsi | rev | cut -d " " -f 1]
    if { $pmic_gsi == 1 } {
        gig_assert_arm_rst 0 0xf
        ssi_cpld_write 0x20 0x0
        print_pmic_events
    }
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
    } elseif {$ASIC_TYPE == "SALINA"} {
        sal_print_voltage_temp_from_j2c
        if {[ssi_cpld_read 0x32] == "0x08"} {
            plog_msg "VDD_CORE status registers:"; sal_tps53688_explain_status 2 0x60 0
            plog_msg "VDD_ARM  status registers:"; sal_tps53688_explain_status 2 0x60 1
        }
        plog_msg "Measuring frequencies:"; sal_get_freq
        plog_msg "Measuring ARM frequency:"; sal_PLL_SYSPLL_T_ARM_PLL_DFX_CLK_OBS
    } else {
        elb_assert_arm_rst 0 0xf
        ssi_cpld_write 0x20 0x0
        elb_print_voltage_temp
    }
}

if { $check_prp != 0 && \
     $ASIC_TYPE == "SALINA" } {
    plog_msg "\n\n\n"
    plog_msg "=================="
    plog_msg " PRP test "
    plog_msg "=================="
    if {[llength [info procs sal_ms_ring_full_test]] == 1} {
        sal_ms_ring_full_test
    } else {
        sal_ms_ring_test
    }
}
plog_msg "Getting ASIC status - Done"

