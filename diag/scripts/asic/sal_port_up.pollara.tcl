#! /usr/bin/tclsh

set slot [lindex $argv 0]
# test types:
# esam_pktgen_llc_no_mac_sor : no ddr + no mac
# esam_pktgen_llc_sor        :  no ddr + mac
# esam_pktgen_ddr_no_mac_sor : ddr + no mac
# esam_pktgen_ddr_sor        : ddr + mac  <-- stress both ddr and mac
# esam_pktgen_ddr_burst_400G : ddr burst
# esam_pktgen_pcie_mtp_sor   : pcie + ddr + mac

set card_type [lindex $argv 1]
set vmarg [lindex $argv 2]
set inf [lindex $argv 3]

proc get_vmarg_by_index_vdd {corner_idx} {
    dict set volt_VDD_Dict UU_1   650
    dict set volt_VDD_Dict UU_2   665
    dict set volt_VDD_Dict UU_3   680
    dict set volt_VDD_Dict UU_4   695
    dict set volt_VDD_Dict UU_5   710
    dict set volt_VDD_Dict UU_6   725
    dict set volt_VDD_Dict UU_7   740
    dict set volt_VDD_Dict UU_8   755
    dict set volt_VDD_Dict UU_9   770
    dict set volt_VDD_Dict UU_10  785
    dict set volt_VDD_Dict UU_11  800

    dict set volt_VDD_Dict UU_30  710
    dict set volt_VDD_Dict UU_31  710
    dict set volt_VDD_Dict UU_32  750

    if {[dict exists $volt_VDD_Dict $corner_idx]} {
        return [dict get $volt_VDD_Dict $corner_idx]
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
        return
    } elseif {$vmarg  == "low"} {
        plog_msg "Vmarg: $vmarg"
        sal_set_margin_by_value vdd 760
        return
    }

    plog_msg "Vmargin with index"
    set key "${vmarg}"
    set tgt_vdd_volt [get_vmarg_by_index_vdd $key]
    plog_msg "key: $key; tgt_vdd_volt: $tgt_vdd_volt"
    sal_set_margin_by_value VDD $tgt_vdd_volt

    set vdd_volt [sal_get_vout VDD]
    plog_msg "Set vmarg: vdd_volt: $vdd_volt"
    sal_print_voltage_temp_from_j2c
}

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set ::FAN_SPD 80
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
    set new_vmarg [string range $vmarg 2 end]
    set new_vmarg "UU${new_vmarg}"
}
plog_msg "new_vmarg: $new_vmarg"
set_vmarg $new_vmarg $card_type

#set cpld_id 0x62

#===========================
# Disable PCIe for now
if { $inf == "pcie" || 
     $inf == "all" } {
    plog_msg "pcie bring-up"
    set in_err_ecc [plog_get_err_count]
    # temporarily use LENI before POLLARA ready
    plog_msg "pcie_mtp_bringup_ports 1100 LENI 4\n"
    pcie_mtp_bringup_ports 1100 LENI 4
    
    plog_msg "rds sal0.pp.pxc\[0\].port_p.sta_p_port_mac\n"
    rds sal0.pp.pxc\[0\].port_p.sta_p_port_mac
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
    if {$err_cnt != 0} {
        plog_msg "pcie linkup failed"
    }
    plog_msg "pcie done"
}
after 1000

if { $inf == "eth" || 
     $inf == "all" } {
    set in_err_ecc [plog_get_err_count]
    sal_aw_srds_powerup_init
    after 3000
    #sal_front_panel_port_up 0 "Fiber" 1
    sal_front_panel_port_up 0 "CU" 0 "2x400" 0
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err_ecc ) ]
    if {$err_cnt != 0} {
        plog_err "MX linkup failed"
    }

    #set ret [sal_srds_vco_cdr_chk 0 0 0]
    #if { $ret == 0 } {
    #    plog_msg "sal_srds_vco_cdr_chk: PASS"
    #} else {
    #    plog_msg "sal_srds_vco_cdr_chk: FAIL"
    #}
    plog_msg "mx done"
}
set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_msg "Port up test FAILED"
} else {
    plog_msg "Port up test PASSED"
}

plog_msg "SNAKE TEST DONE"
exit 0
