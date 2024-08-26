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

proc mtp_sts_pull { {cpld_id} {test_type} {duration 60} {intv 30} } {
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
        } elseif { $test_type == "esam_pktgen_pcie_mtp_sor" } {
            find_avg_rate 5 8000
        } else {
            find_avg_rate 5 4000
        }
        sal_print_voltage_temp_from_j2c
        sal_mc_irq_show -1 -1 1
        sal_mc_check_ecc -1 -1 1 $cpld_id
        check_ecc_intr
        plog_msg "Done Pulling"
    }
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



# put arm in reset
#sal_pcc
# start test snake test
cd ../$test_type
set cpld_id 0x62
if {$test_type == "esam_pktgen_pcie_mtp_sor"} {
    if { $card_type == "MALFA" } {
        pcie_mtp_bringup_ports 1100 MALFA 4
    } elseif { $card_type == "LENI" || $card_type == "LENI48G" } {
        pcie_mtp_bringup_ports 1100 LENI 4
    }
    puts "pcie done"
}
if {$test_type == "esam_pktgen_ddr_no_mac_sor" || $test_type == "esam_pktgen_ddr_sor" || $test_type == "esam_pktgen_ddr_burst_400G" || $test_type == "esam_pktgen_pcie_mtp_sor"} {
    if { $card_type == "MALFA" } {
        cdn_ddr5_init 3200
        set cpld_id 0x62
    } elseif { $card_type == "LENI" } {
        cdn_ddr5_init 6400 0x64 0
        set cpld_id 0x64
    } elseif { $card_type == "LENI48G" } {
        cdn_ddr5_init 6400 0x66 0
        set cpld_id 0x66
    }
    sal_mc_irq_show -1 -1 1
    sal_mc_check_ecc -1 -1 1 $cpld_id
    check_ecc_intr
}
# do vmarg
if {$vmarg == "normal"} {
    plog_msg "Vmarg: $vmarg"
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
} else {
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

if {$test_type == "esam_pktgen_llc_sor" || $test_type == "esam_pktgen_ddr_sor" || $test_type == "esam_pktgen_pcie_mtp_sor" } {
    sal_aw_srds_powerup_init
    sal_front_panel_port_up
}
# check for lback, should all be 0
sal_mx_gmii_lpbk_get 0 0 0
sal_mx_gmii_lpbk_get 0 1 0
sal_mx_pcs_lpbk_get 0 0 0
sal_mx_pcs_lpbk_get 0 1 0

sal_asic_init 2
sal_top_stream_load_snake_traffic 0 10
sal_top_stream_start_snake_traffic 0 10
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


# check if pkt is running
sal_top_get_cntr 0
mtp_sts_pull $cpld_id $test_type $dura
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
sal_top_eos 0
plog_stop
after 1000
cd ../tclsh
# check counters
if {[catch {exec grep {ptd\[1\]_CNT:ud0} $fn | tail -n1 | awk {{ print $6,$7 }}} result]} {
    puts "No matches found for 'ptd\[1\]_CNT:ud0'"
} else {
    set ptd_sop_cnt [lindex [split $result] 0]
    set ptd_eop_cnt [lindex [split $result] 1]
    set ptd_sop_cnt [format 0x%x [scan $ptd_sop_cnt %x]]
    set ptd_eop_cnt [format 0x%x [scan $ptd_eop_cnt %x]]
    puts $ptd_sop_cnt
    puts $ptd_eop_cnt
}
exec grep {prd\[1\]_CNT:ud1} $fn | tail -n1
if {[catch {exec grep {prd\[0\]_CNT:ud0} $fn | tail -n1 | awk {{ print $6,$7 }}} result]} {
    puts "No matches found for 'prd\[0\]_CNT:ud0'"
} else {
    set prd_sop_cnt [lindex [split $result] 0]
    set prd_eop_cnt [lindex [split $result] 1]
    set prd_sop_cnt [format 0x%x [scan $prd_sop_cnt %x]]
    set prd_eop_cnt [format 0x%x [scan $prd_eop_cnt %x]]
    puts $prd_sop_cnt
    puts $prd_eop_cnt
}
set queue0_drop 0
if {[catch {exec grep {sal0\.pf\.pf\[0\]\.cnt_ibuf_port0\.queue0_drop} $fn | tail -n1 | awk {{ print $6 }}} result]} {
    puts "No matches found for 'sal0\.pf\.pf\[0\]\.cnt_ibuf_port0\.queue0_drop'"
} else {
    set queue0_drop $result
    puts $queue0_drop
}
if {$ptd_sop_cnt != [expr $prd_sop_cnt + $queue0_drop] || $ptd_eop_cnt != [expr $prd_eop_cnt + $queue0_drop]} {
    puts "SNAKE TEST FAILED"
}

set err_cnt_fnl [ plog_get_err_count ]
diag_close_ow_if $port $slot
puts "SNAKE TEST DONE"
exit 0