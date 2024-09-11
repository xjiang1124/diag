# !/usr/bin/tclsh

set slot [lindex $argv 0]
# test types:
# esam_pktgen_llc_no_mac_sor : no ddr + no mac
# esam_pktgen_llc_sor        :  no ddr + mac
# esam_pktgen_ddr_no_mac_sor : ddr + no mac
# esam_pktgen_ddr_sor        : ddr + mac  <-- stress both ddr and mac
# esam_pktgen_ddr_burst_400G : ddr burst
# esam_pktgen_pcie_mtp_sor   : pcie + ddr + mac

set test_type [lindex $argv 1]
set dura [lindex $argv 2]
set card_type [lindex $argv 3]
set vmarg [lindex $argv 4]

proc mtp_sts_pull { {asic_src} {cpld_id} {test_type} {duration 60} {intv 30} {vmarg "TT"}} {
    set time_left $duration
    set time_passed 0

    plog_msg "\n-----------------------------------------------------------------"
    plog_msg "Running snake for $time_left seconds"
    while {$time_left > 0} {
        if {$time_left < $intv} {
           set intv $time_left
        }
        set ss [ expr $intv*1000 ]
        plog_msg "sal_snake_test_mtp_sts_pull:: Sleeping $intv Seconds"
        after $ss
        set time_left [expr $time_left - $intv]
        set time_passed [expr $time_passed + $intv]
        plog_msg "\n-----------------------------------------------------------------"
        plog_msg "$time_passed second passed; $time_left remains"

        plog_msg " BW_voltage_temp report "
        sal_top_get_cntr 0
        sal_pb_dump_cntrs 0 0
        if { $test_type == "esam_pktgen_ddr_burst_400G" } {
            find_avg_rate 5 3840
        } elseif { $test_type == "esam_pktgen_pcie_mtp_sor" || $test_type == "esam_pktgen_ddr_arm_sor.400g" || $test_type == "esam_pktgen_ddr_arm_sor" || $test_type == "esam_pktgen_max_power_sor"} {
            find_avg_rate 5 8000
        } else {
            find_avg_rate 5 4000
        }

        if {[string first "FF" $vmarg] == 0} {
            set fn "$asic_src/ip/cosim/salina/sal_FF_thermal_calibration.csv"
        } elseif {[string first "TT" $vmarg] == 0} {
            set fn "$asic_src/ip/cosim/salina/sal_TT_thermal_calibration.csv"
        } else {
            set fn "$asic_src/ip/cosim/salina/sal_SS_thermal_calibration.csv"
        }
        plog_msg "AW Cal file: $fn"
        set cali_ret [sal_aw_adc_temp_read 0 50 100 0 3 100 $fn]
        plog_msg "sal_aw_adc_temp_read: $cali_ret"

        #set ret [sal_port_sync]
        #plog_msg "sal_port_sync: $ret"

        sal_print_voltage_temp_from_j2c
        sal_mc_irq_show -1 -1 1
        sal_mc_check_ecc -1 -1 1 $cpld_id
        check_ecc_intr
        plog_msg "Done Pulling"
    }
}

proc get_vmarg_by_index_vdd {corner_idx} {
    #---------------------------------
    set volt_VDD_Dict [dict create]
    dict set volt_VDD_Dict FF_0  675

    dict set volt_VDD_Dict FF_1  659
    dict set volt_VDD_Dict FF_2  696
    dict set volt_VDD_Dict FF_3  732
    dict set volt_VDD_Dict FF_4  769
    dict set volt_VDD_Dict FF_5  806
    dict set volt_VDD_Dict FF_6  659
    dict set volt_VDD_Dict FF_7  806

    dict set volt_VDD_Dict FF_8  638
    dict set volt_VDD_Dict FF_9  673
    dict set volt_VDD_Dict FF_10 709
    dict set volt_VDD_Dict FF_11 744
    dict set volt_VDD_Dict FF_12 780
    dict set volt_VDD_Dict FF_13 638
    dict set volt_VDD_Dict FF_14 780

    dict set volt_VDD_Dict FF_15 703

    #---------------------------------
    dict set volt_VDD_Dict TT_0  675

    dict set volt_VDD_Dict TT_1  659
    dict set volt_VDD_Dict TT_2  696
    dict set volt_VDD_Dict TT_3  732
    dict set volt_VDD_Dict TT_4  769
    dict set volt_VDD_Dict TT_5  806
    dict set volt_VDD_Dict TT_6  659
    dict set volt_VDD_Dict TT_7  806

    dict set volt_VDD_Dict TT_8  638
    dict set volt_VDD_Dict TT_9  673
    dict set volt_VDD_Dict TT_10 709
    dict set volt_VDD_Dict TT_11 744
    dict set volt_VDD_Dict TT_12 780
    dict set volt_VDD_Dict TT_13 638
    dict set volt_VDD_Dict TT_14 780

    #---------------------------------
    dict set volt_VDD_Dict SS_0  720

    dict set volt_VDD_Dict SS_1  703
    dict set volt_VDD_Dict SS_2  742
    dict set volt_VDD_Dict SS_3  781
    dict set volt_VDD_Dict SS_4  820
    dict set volt_VDD_Dict SS_5  859
    dict set volt_VDD_Dict SS_6  703
    dict set volt_VDD_Dict SS_7  859

    dict set volt_VDD_Dict SS_8  680
    dict set volt_VDD_Dict SS_9  718
    dict set volt_VDD_Dict SS_10 756
    dict set volt_VDD_Dict SS_11 794
    dict set volt_VDD_Dict SS_12 832
    dict set volt_VDD_Dict SS_13 680
    dict set volt_VDD_Dict SS_14 832

    if {[dict exists $volt_VDD_Dict $corner_idx]} {
        return [dict get $volt_VDD_Dict $corner_idx]
    } else {
        return -1
    }
}

proc get_vmarg_by_index_arm {corner_idx} {
    #---------------------------------
    set volt_ARM_Dict [dict create]
    dict set volt_ARM_Dict FF_0  850

    dict set volt_ARM_Dict FF_1  830
    dict set volt_ARM_Dict FF_2  876
    dict set volt_ARM_Dict FF_3  922
    dict set volt_ARM_Dict FF_4  968
    dict set volt_ARM_Dict FF_5  1014
    dict set volt_ARM_Dict FF_6  1014
    dict set volt_ARM_Dict FF_7  830

    dict set volt_ARM_Dict FF_8  803
    dict set volt_ARM_Dict FF_9  848
    dict set volt_ARM_Dict FF_10 893
    dict set volt_ARM_Dict FF_11 937
    dict set volt_ARM_Dict FF_12 982
    dict set volt_ARM_Dict FF_13 982
    dict set volt_ARM_Dict FF_14 803
    dict set volt_ARM_Dict FF_15 937

    #-------------ARM-----------------
    dict set volt_ARM_Dict TT_0  900

    dict set volt_ARM_Dict TT_1  879
    dict set volt_ARM_Dict TT_2  928
    dict set volt_ARM_Dict TT_3  977
    dict set volt_ARM_Dict TT_4  1025
    dict set volt_ARM_Dict TT_5  1074
    dict set volt_ARM_Dict TT_6  1074
    dict set volt_ARM_Dict TT_7  879

    dict set volt_ARM_Dict TT_8  851
    dict set volt_ARM_Dict TT_9  898
    dict set volt_ARM_Dict TT_10 945
    dict set volt_ARM_Dict TT_11 992
    dict set volt_ARM_Dict TT_12 1040
    dict set volt_ARM_Dict TT_13 1040
    dict set volt_ARM_Dict TT_14 851

    #-------------ARM-----------------
    dict set volt_ARM_Dict SS_0  960

    dict set volt_ARM_Dict SS_1  937
    dict set volt_ARM_Dict SS_2  990
    dict set volt_ARM_Dict SS_3  1042
    dict set volt_ARM_Dict SS_4  1094
    dict set volt_ARM_Dict SS_5  1146
    dict set volt_ARM_Dict SS_6  1146
    dict set volt_ARM_Dict SS_7  937

    dict set volt_ARM_Dict SS_8  907
    dict set volt_ARM_Dict SS_9  958
    dict set volt_ARM_Dict SS_10 1008
    dict set volt_ARM_Dict SS_11 1058
    dict set volt_ARM_Dict SS_12 1109
    dict set volt_ARM_Dict SS_13 1109
    dict set volt_ARM_Dict SS_14 907

    if {[dict exists $volt_ARM_Dict $corner_idx]} {
        return [dict get $volt_ARM_Dict $corner_idx]
    } else {
        return -1
    }
}

proc set_vmarg { vmarg card_type } {
    # do vmarg
    if {$vmarg == "normal"} {
        plog_msg "Vmarg: $vmarg"
        return
    } elseif {$vmarg == "high"} {
        plog_msg "Vmarg: $vmarg"
        sal_set_margin_by_value vdd 840
        sal_set_margin_by_value arm 1100
        if { $card_type == "MALFA" } {
            sal_set_margin_by_value DDR_VDD_0 1167
            sal_set_margin_by_value DDR_VDDQ_0 1167
            sal_set_margin_by_value DDR_VDD_1 1167
            sal_set_margin_by_value DDR_VDDQ_1 1167
        } else {
            sal_set_margin_by_value DDR_VDD 1167
            sal_set_margin_by_value DDR_VDDQ 1167
        }
        return
    } elseif {$vmarg  == "low"} {
        plog_msg "Vmarg: $vmarg"
        sal_set_margin_by_value vdd 760
        sal_set_margin_by_value arm 975
        if { $card_type == "MALFA" } {
            sal_set_margin_by_value DDR_VDD_0 1067
            sal_set_margin_by_value DDR_VDDQ_0 1067
            sal_set_margin_by_value DDR_VDD_1 1067
            sal_set_margin_by_value DDR_VDDQ_1 1067
        } else {
            sal_set_margin_by_value DDR_VDD 1067
            sal_set_margin_by_value DDR_VDDQ 1067
        }
        return
    }

    plog_msg "Vmargin with index"
    set key "${vmarg}"
    set tgt_vdd_volt [get_vmarg_by_index_vdd $key]
    set tgt_arm_volt [get_vmarg_by_index_arm $key]
    plog_msg "key: $key; tgt_vdd_volt: $tgt_vdd_volt; tgt_arm_volt: $tgt_arm_volt"
    sal_set_margin_by_value VDD $tgt_vdd_volt
    sal_set_margin_by_value ARM $tgt_arm_volt

    set vdd_volt [sal_get_vout VDD]
    set arm_volt [sal_get_vout ARM]
    plog_msg "Set vmarg: vdd_volt: $vdd_volt; arm_volt: $arm_volt"
    sal_print_voltage_temp_from_j2c
}

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port
diag_close_j2c_if $port $slot
diag_open_j2c_if $port $slot
diag_close_j2c_if $port $slot

after 500
diag_close_ow_if $port $slot
after 500
diag_open_ow_if $port $slot
after 2000
sal_ow_axi

set dd 0
set cnt 0
while { ($dd==0) && ($cnt<10) } {
    csr_write sal0.ms.ms.cfg_ow 3
    after 500
    set dd [ rd sal0.ms.ms.cfg_ow ]
    incr cnt
}
set ret 1
if { $cnt  >= 10 } {
    plog_err "\n\n==== J2C / OW is not working.... Ping HW team\n\n"
    return
}
sal_j2c
#sal_ow

set val [_msrd]
if { $val != 0x1 } {
    puts "OW sanity test failed!"
    exit 0
}

#csr_write sal0.txs.txs\[0].base 0xaabbcc
#rds sal0.txs.txs\[0].base
#set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "snake_slot${slot}_${cur_time}.log"
plog_start $fn

set card_type [sal_get_card_type]
set cpld_id [ ssi_cpld_read 0x80 ]
plog_msg "card_type = $card_type"
plog_msg "cpld_id = $cpld_id"
sal_print_die_id

set_vmarg $vmarg $card_type
#return

# put arm in reset
#sal_pcc
# start test snake test
cd ../$test_type
#set cpld_id 0x62
if {$test_type == "esam_pktgen_pcie_mtp_sor" || $test_type == "esam_pktgen_ddr_arm_sor" || $test_type == "esam_pktgen_ddr_arm_sor.400g" || $test_type == "esam_pktgen_max_power_sor"} {
    set in_err_ecc [plog_get_err_count]
    if { $card_type == "MALFA" } {
        pcie_mtp_bringup_ports 1100 MALFA 4
    } elseif { $card_type == "LENI" || $card_type == "LENI48G" } {
        pcie_mtp_bringup_ports 1100 LENI 4
    }
    rds sal0.pp.pxc\[0\].port_p.sta_p_port_mac
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
    if {$err_cnt != 0} {
        plog_msg "pcie linkup failed"
        puts "SNAKE TEST DONE"
        exit 0
    }
}
puts "pcie done"
after 10000
if {$test_type == "esam_pktgen_ddr_no_mac_sor" || $test_type == "esam_pktgen_ddr_sor" || $test_type == "esam_pktgen_ddr_burst_400G"} {
    if { $card_type == "MALFA" } {
        cdn_ddr5_init 3200
        #set cpld_id 0x62
    } elseif { $card_type == "LENI" } {
        cdn_ddr5_init 6400 0x64 0
        #set cpld_id 0x64
    } elseif { $card_type == "LENI48G" } {
        cdn_ddr5_init 6400 0x66 0
        #set cpld_id 0x66
    }
    sal_mc_irq_show -1 -1 1
    sal_mc_check_ecc -1 -1 1 $cpld_id
    check_ecc_intr
}


set vdd_vout [sal_get_vout vdd]
set arm_vout [sal_get_vout arm]
if { $card_type == "MALFA" } {
    set ddr_vdd_0_vout [sal_get_vout DDR_VDD_0]
    set ddr_vddq_0_vout [sal_get_vout DDR_VDDQ_0]
    set ddr_vpp_0_vout [sal_get_vout DDR_VPP_0]
    set ddr_vdd_1_vout [sal_get_vout DDR_VDD_1]
    set ddr_vddq_1_vout [sal_get_vout DDR_VDDQ_1]
    set ddr_vpp_1_vout [sal_get_vout DDR_VPP_1]
} else {
    set ddr_vdd_vout [sal_get_vout DDR_VDD]
    set ddr_vddq_vout [sal_get_vout DDR_VDDQ]
    set ddr_vpp_vout [sal_get_vout DDR_VPP]
}
if { $card_type == "MALFA" } {
    plog_msg "vdd_vout: $vdd_vout; arm_vout: $arm_vout; ddr_vdd_0_vout: $ddr_vdd_0_vout; ddr_vddq_0_vout: $ddr_vddq_0_vout; ddr_vpp_0_vout: $ddr_vpp_0_vout; ddr_vdd_1_vout: $ddr_vdd_1_vout; ddr_vddq_1_vout: $ddr_vddq_1_vout; ddr_vpp_1_vout: $ddr_vpp_1_vout"
} else {
    plog_msg "vdd_vout: $vdd_vout; arm_vout: $arm_vout; ddr_vdd_vout: $ddr_vdd_vout; ddr_vddq_vout: $ddr_vddq_vout; ddr_vpp_vout: $ddr_vpp_vout"
}

if {$test_type == "esam_pktgen_llc_sor" || $test_type == "esam_pktgen_ddr_sor" || $test_type == "esam_pktgen_pcie_mtp_sor" || $test_type == "esam_pktgen_ddr_arm_sor" || $test_type == "esam_pktgen_ddr_arm_sor.400g" || $test_type == "esam_pktgen_max_power_sor"} {
    set in_err_ecc [plog_get_err_count]
    sal_aw_srds_powerup_init
    sal_front_panel_port_up
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
    if {$err_cnt != 0} {
        plog_msg "MX linkup failed"
        #puts "SNAKE TEST DONE"
        #exit 0
    }
}
# check for lback, should all be 0
set ret [sal_mx_gmii_lpbk_get 0 0 0]
if {$ret != 0} {
    plog_msg "sal_mx_gmii_lpbk_get 0 0 0 check failed"
    #puts "SNAKE TEST DONE"
    #exit 0
}
set ret [sal_mx_gmii_lpbk_get 0 1 0]
if {$ret != 0} {
    plog_msg "sal_mx_gmii_lpbk_get 0 1 0 check failed"
    #puts "SNAKE TEST DONE"
    #exit 0
}
set ret [sal_mx_pcs_lpbk_get 0 0 0]
if {$ret != 0} {
    plog_msg "sal_mx_pcs_lpbk_get 0 0 0 check failed"
    #puts "SNAKE TEST DONE"
    #exit 0
}
set ret [sal_mx_pcs_lpbk_get 0 1 0]
if {$ret != 0} {
    plog_msg "sal_mx_pcs_lpbk_get 0 1 0 check failed"
    #puts "SNAKE TEST DONE"
    #exit 0
}

sal_asic_init 2
if {$test_type == "esam_pktgen_max_power_sor"} {
    for {set num 30} {$num < 48} {incr num} {
        if {$num == 38 || $num == 39} {
            continue
        }
        plog_msg "starting stream $num"
        sal_top_stream_load_snake_traffic 0 $num
        sal_top_stream_start_snake_traffic 0 $num
    }
} else {
sal_top_stream_load_snake_traffic 0 10
sal_top_stream_start_snake_traffic 0 10
if {$test_type == "esam_pktgen_ddr_arm_sor.400g" || $test_type == "esam_pktgen_ddr_arm_sor"} {
    sal_top_stream_load_snake_traffic 0 20
    sal_top_stream_start_snake_traffic 0 20
}
if {$test_type == "esam_pktgen_pcie_mtp_sor"} {
    sal_top_stream_load_snake_traffic 0 21
    sal_top_stream_start_snake_traffic 0 21
}
#sal_top_stream_load_snake_traffic 0 11
#sal_top_stream_start_snake_traffic 0 11
#if { $test_type != "esam_pktgen_ddr_burst_400G" } {
#    sal_top_stream_load_snake_traffic 0 20
#    sal_top_stream_start_snake_traffic 0 20
#}
}


# check if pkt is running
sal_top_get_cntr 0
after 5000
sal_top_get_cntr 0
after 5000
if {[catch {exec grep {prd\[0\]_CNT:ud0} ../tclsh/$fn | tail -n1 | awk {{ print $6,$7 }}} result]} {
    puts "No matches found for 'prd\[0\]_CNT:ud0'"
} else {
    set prd0_sop_cnt [lindex [split $result] 0]
    set prd0_sop_cnt [format 0x%x [scan $prd0_sop_cnt %x]]
    puts $prd0_sop_cnt
    if {$prd0_sop_cnt == 0} {
        plog_msg "counter is 0"
        puts "SNAKE TEST DONE"
        exit 0
    }
}
mtp_sts_pull $ASIC_SRC $cpld_id $test_type $dura 30 $vmarg
#sal_noc_nis_bwmon_setup 0 0
#sal_noc_nis_bwmon_dump  0 0

# Gen 4
rds sal0.pp.pxc\[0\].port_p.sat_p_port_cnt_ltssm_state_changed

sal_top_stream_stop_snake_traffic 0
plog_msg "Counters after stop snake"
# check counters
sal_top_get_cntr 0
sal_pf_cntrs
sal_pb_dump_cntrs 0 0
# check ecc
set in_err_ecc [plog_get_err_count]
sal_mc_irq_show -1 -1 1
sal_mc_check_ecc -1 -1 1 $cpld_id
check_ecc_intr
set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
if {$err_cnt != 0} {
    plog_msg "ECC happaned. Dumping DDR configuration"
    exec rm -rf ${slot}_dump
    exec mkdir ${slot}_dump
    cd ${slot}_dump
    ddr5_dump_all
    cd ..
    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    puts $cur_time
    exec tar cf ${slot}_dump_${cur_time}.tar ${slot}_dump/
}
sal_mx_dump_mibs 0 0
sal_mx_dump_mibs 0 1
sal_top_eos 0
plog_stop
after 1000
cd ../tclsh
# check counters
if {[catch {exec grep {prd\[0\]_CNT:ud0} $fn | tail -n1 | awk {{ print $6,$7 }}} result]} {
    puts "No matches found for 'prd\[0\]_CNT:ud0'"
} else {
    set prd0_sop_cnt [lindex [split $result] 0]
    set prd0_eop_cnt [lindex [split $result] 1]
    set prd0_sop_cnt [format 0x%x [scan $prd0_sop_cnt %x]]
    set prd0_eop_cnt [format 0x%x [scan $prd0_eop_cnt %x]]
    set prd0_sop_cnt [expr $prd0_sop_cnt & 0xFFFFFFFF]
    puts $prd0_sop_cnt
    puts $prd0_eop_cnt
}
if {[catch {exec grep {ptd\[1\]_CNT:ud0} $fn | tail -n1 | awk {{ print $6,$7 }}} result]} {
    puts "No matches found for 'ptd\[1\]_CNT:ud0'"
} else {
    set ptd1_sop_cnt [lindex [split $result] 0]
    set ptd1_eop_cnt [lindex [split $result] 1]
    set ptd1_sop_cnt [format 0x%x [scan $ptd1_sop_cnt %x]]
    set ptd1_eop_cnt [format 0x%x [scan $ptd1_eop_cnt %x]]
    set ptd1_sop_cnt [expr $ptd1_sop_cnt & 0xFFFFFFFF]
    puts $ptd1_sop_cnt
    puts $ptd1_eop_cnt
}
if {[catch {exec grep {prd\[1\]_CNT:ud1} $fn | tail -n1 | awk {{ print $6,$7 }}} result]} {
    puts "No matches found for 'prd\[1\]_CNT:ud1'"
} else {
    set prd1_sop_cnt [lindex [split $result] 0]
    set prd1_eop_cnt [lindex [split $result] 1]
    set prd1_sop_cnt [format 0x%x [scan $prd1_sop_cnt %x]]
    set prd1_eop_cnt [format 0x%x [scan $prd1_eop_cnt %x]]
    set prd1_sop_cnt [expr $prd1_sop_cnt & 0xFFFFFFFF]
    puts $prd1_sop_cnt
    puts $prd1_eop_cnt
}
if {[catch {exec grep {ptd\[2\]_CNT:ud1} $fn | tail -n1 | awk {{ print $6,$7 }}} result]} {
    puts "No matches found for 'ptd\[2\]_CNT:ud1'"
} else {
    set ptd2_sop_cnt [lindex [split $result] 0]
    set ptd2_eop_cnt [lindex [split $result] 1]
    set ptd2_sop_cnt [format 0x%x [scan $ptd2_sop_cnt %x]]
    set ptd2_eop_cnt [format 0x%x [scan $ptd2_eop_cnt %x]]
    set ptd2_sop_cnt [expr $ptd2_sop_cnt & 0xFFFFFFFF]
    puts $ptd2_sop_cnt
    puts $ptd2_eop_cnt
}
#set queue0_drop 0
#if {[catch {exec grep {sal0\.pf\.pf\[0\]\.cnt_ibuf_port0\.queue0_drop} $fn | tail -n1 | awk {{ print $6 }}} result]} {
#    puts "No matches found for 'sal0\.pf\.pf\[0\]\.cnt_ibuf_port0\.queue0_drop'"
#} else {
#    set queue0_drop $result
#    puts $queue0_drop
#}
#if {$ptd_sop_cnt != [expr $prd_sop_cnt + $queue0_drop] || $ptd_eop_cnt != [expr $prd_eop_cnt + $queue0_drop]} {
#    puts "SNAKE TEST FAILED"
#}
if {$prd0_sop_cnt == $prd0_eop_cnt &&
    $prd0_sop_cnt == $ptd1_sop_cnt &&
    $ptd1_sop_cnt == $ptd1_eop_cnt &&
    $prd1_sop_cnt == $prd1_eop_cnt &&
    $prd1_sop_cnt == $ptd2_sop_cnt &&
    $ptd2_sop_cnt == $ptd2_eop_cnt} {
    puts "Counters check passed"
} else {
    puts "Counters check failed"
}
set err_cnt_fnl [ plog_get_err_count ]
diag_close_ow_if $port $slot
puts "SNAKE TEST DONE"
exit 0
