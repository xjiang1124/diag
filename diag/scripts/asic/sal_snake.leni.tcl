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

proc die_temp_fan_control_1 { cur_temp {tgt_temp 105} } {
    set fan_max 100
    set fan_min 30
    set margin 3
    set kp 0.6
    set ki 0.4

    if {$cur_temp < 10} {
        set cur_temp [expr {128+$cur_temp}]
    }
    set diff [expr {$tgt_temp - $cur_temp}]

    set fan_change [expr {-1.0*$diff}]
    set fan_change [expr {max($fan_change, -5)}]
    set fan_change [expr {min($fan_change,  5)}]

    set ::FAN_SPD [expr {int(round($::FAN_SPD+$fan_change))}]

    plog_msg "$diff, $::FAN_SPD"

    set ::FAN_SPD [expr {max($::FAN_SPD, $fan_min)}]
    set ::FAN_SPD [expr {min($::FAN_SPD, $fan_max)}]

    plog_msg "cur_temp: $cur_temp; tgt_temp: $tgt_temp; tgt_fan_spd: $::FAN_SPD"
    if {[catch {exec $::DEVMGR fanctrl --pct=$::FAN_SPD}]} {
        plog_err "Fail to control fan speed!"
    } else {
        plog_msg "Fan speed set to $::FAN_SPD"
    }
    if {[catch {set output [exec fpgautil show fan]}]} {
        plog_err "Fail to control fan speed!"
    } else {
        plog_msg $output
    }
}

proc parse_number_string {input_string} {
    set result_list {}
    foreach element [split $input_string ","] {
        if {[string match "*-*" $element]} {
            # It's a range, so split it and generate the sequence
            set range [split $element "-"]
            set start [lindex $range 0]
            set end [lindex $range 1]
            for {set i $start} {$i <= $end} {incr i} {
                lappend result_list $i
            }
        } else {
            # It's a single number, just append to list
            lappend result_list $element
        }
    }
    return $result_list
}


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
        #sal_pb_dump_cntrs 0 0
        get_sal_offload_cnt 0
        get_sal_offload_cnt 1
        if { $test_type == "esam_pktgen_ddr_burst_400G" } {
            find_avg_rate 5 3840
        } elseif { $test_type == "esam_pktgen_pcie_mtp_sor" || $test_type == "esam_pktgen_ddr_arm_sor.400g" || $test_type == "esam_pktgen_ddr_arm_sor" || $test_type == "esam_pktgen_max_power_pcie_sor"} {
            find_avg_rate 5 8000
        } else {
            find_avg_rate 5 4000
        }


        if {[string first "FF" $vmarg] == 0} {
            set fn "$asic_src/ip/cosim/salina/sal_FF_thermal_calibration.csv"
        } elseif {[string first "SS" $vmarg] == 0} {
            set fn "$asic_src/ip/cosim/salina/sal_SS_thermal_calibration.csv"
        } else {
            set fn "$asic_src/ip/cosim/salina/sal_TT_thermal_calibration.csv"
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

	    #===============================
	    # Debug info dump
	    plog_msg "=== Debug info dump ==="
        sal_top_get_cntr 0
        get_sal_offload_cnt 0
        get_sal_offload_cnt 1
        sal_xd_ptd_cnt_chk
        sal_pb_dump_cntrs 0 0

        sal_mes_dump_stats 0 0
        sal_pf_dump_ebuf_cnt 0 0
        sal_pf_dump_ibuf_cnt 0 0

	#die_temp_fan_control_1 $cali_ret

        plog_msg "Done Pulling"
    }
}

proc get_vmarg_by_index_vdd {corner_idx} {
    #---------------------------------
    set volt_VDD_Dict [dict create]

    #---------------------------------
    dict set volt_VDD_Dict UU_0   675
    dict set volt_VDD_Dict UU_1   709
    dict set volt_VDD_Dict UU_2   709
    dict set volt_VDD_Dict UU_3   780
    dict set volt_VDD_Dict UU_4   709
    dict set volt_VDD_Dict UU_5   709
    dict set volt_VDD_Dict UU_6   780
    dict set volt_VDD_Dict UU_7   709
    dict set volt_VDD_Dict UU_8   756
    dict set volt_VDD_Dict UU_9   832
    dict set volt_VDD_Dict UU_10  709
    dict set volt_VDD_Dict UU_11  732
    dict set volt_VDD_Dict UU_12  806
    dict set volt_VDD_Dict UU_13  709
    dict set volt_VDD_Dict UU_14  732
    dict set volt_VDD_Dict UU_15  806
    dict set volt_VDD_Dict UU_16  709
    dict set volt_VDD_Dict UU_17  781
    dict set volt_VDD_Dict UU_18  859

    if {[dict exists $volt_VDD_Dict $corner_idx]} {
        return [dict get $volt_VDD_Dict $corner_idx]
    } else {
        return -1
    }
}

proc get_vmarg_by_index_arm {corner_idx} {
    #---------------------------------
    set volt_ARM_Dict [dict create]

    #-------------ARM-----------------
    dict set volt_ARM_Dict UU_0   900
    dict set volt_ARM_Dict UU_1   803
    dict set volt_ARM_Dict UU_2   893
    dict set volt_ARM_Dict UU_3   982
    dict set volt_ARM_Dict UU_4   851
    dict set volt_ARM_Dict UU_5   945
    dict set volt_ARM_Dict UU_6   1040
    dict set volt_ARM_Dict UU_7   907
    dict set volt_ARM_Dict UU_8   1008
    dict set volt_ARM_Dict UU_9   1109
    dict set volt_ARM_Dict UU_10  830
    dict set volt_ARM_Dict UU_11  922
    dict set volt_ARM_Dict UU_12  1014
    dict set volt_ARM_Dict UU_13  879
    dict set volt_ARM_Dict UU_14  977
    dict set volt_ARM_Dict UU_15  1074
    dict set volt_ARM_Dict UU_16  937
    dict set volt_ARM_Dict UU_17  1042
    dict set volt_ARM_Dict UU_18  1146

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

plog_msg "test_type: $test_type"
#plog_msg "SNAKE TEST DONE"
#exit 0

set ::FAN_SPD 40
set ::DEVMGR devmgr_v2

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
set j2c_secure 1
#sal_ow

set val [_msrd]
if { $val != 0x1 } {
    plog_msg "OW sanity test failed!"
    exit 0
}

#csr_write sal0.txs.txs\[0].base 0xaabbcc
#rds sal0.txs.txs\[0].base
set err_cnt_init [ plog_get_err_count ]

set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "snake_slot${slot}_${cur_time}.log"
plog_start $fn

set card_type [sal_get_card_type]
set cpld_id [ ssi_cpld_read 0x80 ]
plog_msg "card_type = $card_type"
plog_msg "cpld_id = $cpld_id"
sal_print_die_id

if { $vmarg == "high" || $vmarg == "low" || $vmarg == "normal" } {
    set new_vmarg $vmarg
} else {
    # Convert everything to UU_x
    set new_vmarg [string range $vmarg 2 end]
    set new_vmarg "UU${new_vmarg}"
}
    plog_msg "new_vmarg: $new_vmarg"
    
    set_vmarg $new_vmarg $card_type

#plog_msg "Change fan speed to $::FAN_SPD"
#exec $::DEVMGR fanctrl --pct=$::FAN_SPD

#return

# put arm in reset
#sal_pcc
# start test snake test
cd ../$test_type
#set cpld_id 0x62

#===========================
if { $test_type == "esam_pktgen_pcie_mtp_sor"       || 
     $test_type == "esam_pktgen_ddr_arm_sor"        || 
     $test_type == "esam_pktgen_ddr_arm_sor.400g"   || 
     $test_type == "esam_pktgen_max_power_pcie_sor"      ||
     1 } {
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
	    plog_msg "pcie done"
        after 10000
        plog_msg "SNAKE TEST DONE"
        exit 0
    }
}
plog_msg "pcie done"
#after 10000
after 1000
if { $test_type == "esam_pktgen_ddr_no_mac_sor" ||
     $test_type == "esam_pktgen_ddr_sor"        ||
     $test_type == "esam_pktgen_ddr_burst_400G" } {
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

if { $test_type == "esam_pktgen_llc_sor"            || 
     $test_type == "esam_pktgen_ddr_sor"            || 
     $test_type == "esam_pktgen_pcie_mtp_sor"       || 
     $test_type == "esam_pktgen_ddr_arm_sor"        || 
     $test_type == "esam_pktgen_ddr_arm_sor.400g"   || 
     $test_type == "esam_pktgen_max_power_pcie_sor"      ||
     1 } {
    set in_err_ecc [plog_get_err_count]
    sal_aw_srds_powerup_init
    #sal_front_panel_port_up 0 "Fiber" 1
    sal_front_panel_port_up 0 "CU" 1 "2x400" 0
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
    if {$err_cnt != 0} {
        plog_msg "MX linkup failed"
        plog_msg "SNAKE TEST DONE"
        exit 0
    }
}
plog_msg "mx done"
sal_aw_dump_pmon

# check for lback, should all be 0
set ret [sal_mx_gmii_lpbk_get 0 0 0]
if {$ret != 0} {
    plog_msg "sal_mx_gmii_lpbk_get 0 0 0 check failed"
    #plog_msg "SNAKE TEST DONE"
    #exit 0
}
set ret [sal_mx_gmii_lpbk_get 0 1 0]
if {$ret != 0} {
    plog_msg "sal_mx_gmii_lpbk_get 0 1 0 check failed"
    #plog_msg "SNAKE TEST DONE"
    #exit 0
}
set ret [sal_mx_pcs_lpbk_get 0 0 0]
if {$ret != 0} {
    plog_msg "sal_mx_pcs_lpbk_get 0 0 0 check failed"
    #plog_msg "SNAKE TEST DONE"
    #exit 0
}
set ret [sal_mx_pcs_lpbk_get 0 1 0]
if {$ret != 0} {
    plog_msg "sal_mx_pcs_lpbk_get 0 1 0 check failed"
    #plog_msg "SNAKE TEST DONE"
    #exit 0
}
# before test start
sal_mx_get_mac_chsts 0 0 0 1
sal_mx_get_mac_chsts 0 1 0 1
# start test
sal_asic_init 2
# before snake starts
sal_top_eos 0

if {$test_type == "esam_pktgen_max_power_pcie_sor"} {
    set stream_list_all "61,62,30-37,40-47,50-57,4-15,0-3,16-21"
    #set stream_list_all "0-21,30-37,40-47,50-57"
} elseif {$test_type == "esam_pktgen_ddr_arm_sor.400g" || $test_type == "esam_pktgen_ddr_arm_sor"} {
    set stream_list_all "10,20"
} elseif {$test_type == "esam_pktgen_pcie_mtp_sor"} {
    set stream_list_all "10,21"
} else {
    set stream_list_all "10"
}

set stream_list [parse_number_string $stream_list_all]

plog_msg "stream_list: ${stream_list}"

foreach stream $stream_list {
    #set stream [expr {$stream_str}]
    sal_top_stream_load_snake_traffic 0 $stream
}

foreach stream $stream_list {
    #set stream [expr {$stream_str}]
    sal_top_stream_start_snake_traffic 0 $stream
}

# check if pkt is running
sal_top_get_cntr 0
get_sal_offload_cnt 0
get_sal_offload_cnt 1
mtp_sts_pull $ASIC_SRC $cpld_id $test_type $dura 30 $vmarg
#sal_noc_nis_bwmon_setup 0 0
#sal_noc_nis_bwmon_dump  0 0

# Gen 4
#rds sal0.pp.pxc\[0\].port_p.sat_p_port_cnt_ltssm_state_changed

sal_top_stream_stop_snake_traffic 0
# after test completes
sal_top_eos 0
plog_msg "Counters after stop snake"
# check counters
sal_top_get_cntr 0
sal_mx_dump_mibs 0 0
sal_mx_dump_mibs 0 1
sal_mx_get_mac_chsts 0 0 0 1
sal_mx_get_mac_chsts 0 1 0 1
#sal_pf_cntrs
#sal_pb_dump_cntrs 0 0
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
    plog_msg $cur_time
    exec tar cf ${slot}_dump_${cur_time}.tar ${slot}_dump/
}

plog_stop
set err_cnt_fnl [ plog_get_err_count ]
diag_close_ow_if $port $slot
plog_msg "SNAKE TEST DONE"
exit 0
