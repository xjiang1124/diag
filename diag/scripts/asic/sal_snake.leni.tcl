# !/usr/bin/tclsh

set slot        [lindex $argv 0]
set test_type   [lindex $argv 1]
set dura        [lindex $argv 2]
set card_type   [lindex $argv 3]
set vmarg       [lindex $argv 4]
set int_lpbk    [lindex $argv 5]
set mtp_clk     [lindex $argv 6]

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
        if { $test_type == "esam_pktgen_ddr_burst_400G_no_mac" || $test_type == "esam_pktgen_ddr_burst"} {
            find_avg_rate 5 3840
        } elseif { $test_type == "esam_pktgen_ddr_arm_sor"          || 
                   $test_type == "esam_pktgen_max_power_pcie_sor"   ||
                   $test_type == "esam_pktgen_max_power_sor" } {
            find_avg_rate 5 714
        } else {
            find_avg_rate 5 4000
        }

        set cali_ret_mx0 [sal_aw_adc_temp_read_ref_fuse 0 3 100]
        plog_msg "sal_aw_adc_temp_read_ref_fuse: MX0: $cali_ret_mx0"
        set cali_ret_mx1 [sal_aw_adc_temp_read_ref_fuse 1 3 100]
        plog_msg "sal_aw_adc_temp_read_ref_fuse: MX1: $cali_ret_mx1"
        set cali_ret [expr ($cali_ret_mx0 + $cali_ret_mx1) / 2]
        plog_msg "sal_aw_adc_temp_read_ref_fuse: AVG: $cali_ret"

        #set ret [sal_port_sync]
        #plog_msg "sal_port_sync: $ret"

        plog_msg "pcie width and mac status:"
        pcie_check_link_width_and_mac_status 1100 LENI 4 0

        sal_print_voltage_temp_from_j2c
        sal_mc_irq_show -1 -1 1
        sal_mc_check_ecc -1 -1 1 0x61 1
        check_ecc_intr

	    #===============================
	    # Debug info dump

        sal_eos_intr_chk  none none
        sal_eos_intr_clr  none none

	    plog_msg "=== Debug info dump ==="
        sal_top_get_cntr 0
        if { $test_type != "esam_pktgen_llc_sor" &&
             $test_type != "esam_pktgen_ddr_burst_400G_no_mac" &&
             $test_type != "esam_pktgen_ddr_burst" } {
            get_sal_offload_cnt 0
            get_sal_offload_cnt 1
            get_sal_offload_cnt_chk 0
            get_sal_offload_cnt_chk 1
            sal_xd_ptd_cnt_chk
        }
        sal_pb_dump_cntrs 0 0

        sal_mes_dump_stats 0 0
        sal_pf_dump_ebuf_cnt 0 0
        sal_pf_dump_ibuf_cnt 0 0

        show_pbus_stats pipe

        # Check crypto counters
        read_sal_mc_crypto_counters 0 0; set_sal_mc_crypto_counters 0 0
        read_sal_mc_crypto_counters 0 1; set_sal_mc_crypto_counters 0 1
        read_sal_mc_crypto_counters 0 2; set_sal_mc_crypto_counters 0 2
        read_sal_mc_crypto_counters 0 3; set_sal_mc_crypto_counters 0 3
        # IS counters
        sal_inline_crypto
        sal_inline_crypto_chk
        # BX
        sal_bx_mac_stat 0 2 0
        sal_bx_mac_stat 0 3 0
        sal_ix_mac_stat 0 0 0
        sal_bx_check_bad_crc_counter 0 2
        sal_bx_check_bad_crc_counter 0 3

        #die_temp_fan_control_1 $cali_ret

        plog_msg "Done Pulling"
    }
}

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl

plog_msg "test_type: $test_type"

set ::FAN_SPD 40
set ::DEVMGR devmgr_v2

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port
exec jtag_accpcie_salina clr $slot
exec fpgautil spimode $slot off
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

set ::env(MTP_PCIE_USE_REFCLK_0) $mtp_clk

set err_cnt_init [ plog_get_err_count ]

if { $test_type == "esam_pktgen_llc_sor" ||
     $test_type == "esam_pktgen_ddr_burst_400G_no_mac" ||
     $test_type == "esam_pktgen_ddr_burst" } {
    #sal_pcc
    #sal_arm_reset
    plog_msg "calling reset_to_proto_mode no_proto"
    reset_to_proto_mode no_proto
    # disable WDT
    set i2c_bus [expr $slot + 2]
    exec i2cset -y $i2c_bus 0x4f 1 0
    set reg1 [exec i2cget -y $i2c_bus 0x4f 0x1]
    plog_msg "CPLD reg1: $reg1"
}

set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "snake_slot${slot}_${cur_time}.log"
plog_start $fn

set card_type [sal_get_card_type]
set cpld_id [ ssi_cpld_read 0x80 ]
plog_msg "card_type = $card_type"
plog_msg "cpld_id = $cpld_id"
sal_print_die_id

sal_set_vmarg $vmarg

#plog_msg "Change fan speed to $::FAN_SPD"
#exec $::DEVMGR fanctrl --pct=$::FAN_SPD

# start test snake test
cd ../$test_type

#===========================
if { $test_type == "esam_pktgen_ddr_arm_sor"        || 
     $test_type == "esam_pktgen_max_power_pcie_sor" ||
     0 } {
    set in_err_ecc [plog_get_err_count]
    if { $card_type == "MALFA" } {
        pcie_mtp_bringup_ports 1100 MALFA 4
    } elseif { $card_type == "LENI" || $card_type == "LENI48G" } {
        pcie_mtp_bringup_ports 1100 LENI 4
    }
    rds sal0.pp.pxc\[0\].port_p.sta_p_port_mac
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
    if {$err_cnt != 0} {
        plog_err "pcie linkup failed"
	    plog_msg "pcie done"
        after 1000
        plog_err "SNAKE TEST FAILED"
        plog_msg "SNAKE TEST DONE"
        exit 0
    }
}
plog_msg "pcie done"
after 1000
if { $test_type == "esam_pktgen_ddr_sor"        ||
     $test_type == "esam_pktgen_ddr_burst_400G_no_mac" ||
     $test_type == "esam_pktgen_ddr_burst" } {
    if { $card_type == "MALFA" } {
        cdn_ddr5_init 3200
    } elseif { $card_type == "LENI" } {
        cdn_ddr5_init 6400 0x64 0
    } elseif { $card_type == "LENI48G" } {
        cdn_ddr5_init 6400 0x66 0
    }
    sal_mc_irq_show -1 -1 1
    sal_mc_check_ecc -1 -1 1 0x61 1
    check_ecc_intr
}

if { $test_type == "esam_pktgen_llc_sor"            || 
     $test_type == "esam_pktgen_ddr_sor"            || 
     $test_type == "esam_pktgen_ddr_arm_sor"        || 
     $test_type == "esam_pktgen_max_power_pcie_sor" ||
     $test_type == "esam_pktgen_max_power_sor"      ||
     $test_type == "esam_pktgen_ddr_burst"          ||
     0 } {
    set in_err_ecc [plog_get_err_count]
    sal_aw_srds_powerup_init
    after 3000
    if {$test_type == "esam_pktgen_llc_sor" || $test_type == "esam_pktgen_ddr_burst"} {
        sal_front_panel_port_up 1 "CU" 1 "2x400" 0
    } else {
        sal_front_panel_port_up $int_lpbk "CU" 1 "2x400" 0
    }
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
    if {$err_cnt != 0} {
        plog_err "MX linkup failed"
        plog_err "SNAKE TEST FAILED"
        plog_msg "SNAKE TEST DONE"
        exit 0
    }
}
plog_msg "mx done"

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

sknobs_set_string  is/phv_crypto_skip_ok  1

if { $test_type == "esam_pktgen_ddr_sor"        ||
     $test_type == "esam_pktgen_ddr_burst_400G_no_mac" ||
     $test_type == "esam_pktgen_ddr_burst" } {
    sknobs_set_string sal0/ms/ms/int_prp5/intreg/read_interrupt/int_exclude_field 1
}

if { $test_type == "esam_pktgen_ddr_burst_400G_no_mac"} {
    sknobs_load_file mx_1x400g.out
    sknobs_set_string "sal0/top/mac_cfg/mx0/mode" "mode_1x400gr4kp"
    sknobs_set_string "sal0/top/mac_cfg/mx1/mode" "mode_1x400gr4kp"
}
# start test
sal_asic_init 2

plog_msg "sal_aw_dump_pmon"
if { $test_type == "esam_pktgen_max_power_pcie_sor" } {
    # if pcie is enabled, check all macro
    sal_aw_dump_pmon
} elseif { $test_type != "esam_pktgen_ddr_burst_400G_no_mac" &&
           $test_type != "esam_pktgen_ddr_arm_sor"} {
    # only check MX0 and MX1
    sal_aw_dump_pmon 0x3
}

# before snake starts
sal_top_eos 0

if { $test_type == "esam_pktgen_max_power_pcie_sor" ||
     $test_type == "esam_pktgen_max_power_sor" } {
    #set stream_list_all "61,62,30-37,40-47,50-57,4-15,0-3,16-21"
    set stream_list_all "61,62,30-33,40-43,50-53,4-15,0-3,16-21"
} elseif {$test_type == "esam_pktgen_ddr_arm_sor" || $test_type == "esam_pktgen_llc_sor" } {
    set stream_list_all "10,20"
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
sal_mc_check_ecc -1 -1 1 0x61 1
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
set err_cnt  [ expr ( $err_cnt_fnl - $err_cnt_init ) ]
if {$err_cnt != 0} {
    sal_aw_port_status
    plog_err "SNAKE TEST FAILED"
    set ret -1
} else {
    plog_msg "SNAKE TEST PASSED"
    set ret 0
}
plog_msg "SNAKE TEST DONE"
diag_close_ow_if $port $slot
exit $ret
