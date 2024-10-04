# !/usr/bin/tclsh

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

    dict set volt_VDD_Dict UU_30  710
    dict set volt_VDD_Dict UU_31  710
    dict set volt_VDD_Dict UU_32  750

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

    dict set volt_ARM_Dict UU_30  920
    dict set volt_ARM_Dict UU_31  940
    dict set volt_ARM_Dict UU_32  980

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
    puts "OW sanity test failed!"
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
plog_msg "new_vmarg: $new_vmarg; vmarg: $vmarg"
 
#plog_msg "SNAKE TEST DONE"
#exit 0   
set_vmarg $new_vmarg $card_type

#plog_msg "Change fan speed to $::FAN_SPD"
#exec $::DEVMGR fanctrl --pct=$::FAN_SPD

#===========================
# Disable PCIe for now
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
}
plog_msg "pcie done"
#after 10000
after 1000

plog_msg "SNAKE TEST DONE"
exit 0

set ret [sal_srds_vco_cdr_chk 0 0 0]
if { $ret == 0 } {
    plog_msg "sal_srds_vco_cdr_chk: PASS"
} else {
    plog_msg "sal_srds_vco_cdr_chk: FAIL"
}

plog_msg "SNAKE TEST DONE"
exit 0
