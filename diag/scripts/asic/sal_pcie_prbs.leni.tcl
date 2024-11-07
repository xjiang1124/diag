# !/usr/bin/tclsh

set slot        [lindex $argv 0]
set card_type   [lindex $argv 1]
set vmarg       [lindex $argv 2]
set dura        [lindex $argv 3]
set mtp_clk     [lindex $argv 4]

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

set ::env(MTP_PCIE_USE_REFCLK_0) $mtp_clk

#csr_write sal0.txs.txs\[0].base 0xaabbcc
#rds sal0.txs.txs\[0].base
set err_cnt_init [ plog_get_err_count ]

set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "snake_slot${slot}_${cur_time}.log"
plog_start $fn

#set card_type [sal_get_card_type]
#set cpld_id [ ssi_cpld_read 0x80 ]
plog_msg "card_type = $card_type"
#plog_msg "cpld_id = $cpld_id"
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

pcie_mtp_prbs_test 1100 $card_type 4 $dura 6

plog_msg "PRBS TEST DONE"

set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "PRBS test FAILED"
} else {
    plog_msg "PRBS test PASSED"
}

exit 0
