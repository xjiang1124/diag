# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {sn.arg         ""                      "Serial number"}
    {slot.arg       ""                      "Slot number"}
    {vmarg.arg      "normal"                "Voltage margin: normal/high/low"}
    {vmarg_core.arg "0"                     "Core vmargin percentage"}
    {vmarg_arm.arg "0"                      "arm vmargin percentage"}
    {vmarg_ddr.arg "0"                      "DDR vmargin percentage"}
    {diag_dir.arg   "/home/diag/diag/asic/" "Diag ASIC home directory"}
}

array set arg [cmdline::getoptions argv $parameters]
set sn          $arg(sn)
set slot        $arg(slot)
set vmarg       $arg(vmarg)
set vmarg_core  $arg(vmarg_core)
set vmarg_arm   $arg(vmarg_core)
set vmarg_ddr   $arg(vmarg_core)
set DIAG_DIR    $arg(diag_dir)

source asic_tests.tcl

puts "sn: $sn; slot: $slot; vmarg: $vmarg; vmarg_core: $vmarg_core; vmarg_arm: $vmarg_arm; vmarg_ddr; $vmarg_ddr"

set ASIC_LIB_BUNDLE "$DIAG_DIR"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

#source /home/diag/diag/scripts/asic/sal_init.tcl
set err_cnt_init [ plog_get_err_count ]

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
sal_j2c_stress

set err_cnt_fnl [ plog_get_err_count ]
set err_cnt [expr $err_cnt_fnl - $err_cnt_init]
if {$err_cnt != 0} {
    plog_err "SET AVS FAILED"
    plog_err "SET AVS FAILED"
    return 0
} 

set cpld_id [ssi_cpld_read 0x80]
plog_msg "cpld_id: $cpld_id"

if {$vmarg == "normal"} {
    plog_msg "Vmarg: $vmarg"
} elseif {$vmarg == "high"} {
    plog_msg "Vmarg: $vmarg"
    sal_set_margin_by_value vdd 840
    sal_set_margin_by_value arm 1100

    if {$cpld_id == 0x62} {
        sal_set_margin_by_value DDR_VDD_0 1167
        sal_set_margin_by_value DDR_VDDQ_0 1167
        sal_set_margin_by_value DDR_VDD_1 1167
        sal_set_margin_by_value DDR_VDDQ_1 1167
    } else {
        return -1
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

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    plog_msg "SET AVS PASSED"
    plog_msg "SET AVS PASSED"
} else {
    plog_err "SET AVS FAILED"
    plog_err "SET AVS FAILED"
}
