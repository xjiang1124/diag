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
        sal_set_margin_by_value DDR_VDD 1167
        sal_set_margin_by_value DDR_VDDQ 1167
    }
    #sal_set_margin_by_pct DDR_VDD 2
    #sal_set_margin_by_pct DDR_VDDQ 2
    #sal_set_margin_by_pct DDR_VPP 2
} else {
    plog_msg "Vmarg: $vmarg"
    sal_set_margin_by_value vdd 760
    sal_set_margin_by_value arm 975

    if {$cpld_id == 0x62} {
        sal_set_margin_by_value DDR_VDD_0 1067
        sal_set_margin_by_value DDR_VDDQ_0 1067
        sal_set_margin_by_value DDR_VDD_1 1067
        sal_set_margin_by_value DDR_VDDQ_1 1067
    } else {
        sal_set_margin_by_value DDR_VDD 1067
        sal_set_margin_by_value DDR_VDDQ 1067
    }

    #sal_set_margin_by_pct DDR_VDD -2
    #sal_set_margin_by_pct DDR_VDDQ -2
    #sal_set_margin_by_pct DDR_VPP -2
} 

#set vdd_vout [sal_get_vout vdd]
#set arm_vout [sal_get_vout arm]
#set ddr_vdd_vout [sal_get_vout DDR_VDD]
#set ddr_vddq_vout [sal_get_vout DDR_VDDQ]
#set ddr_vpp_vout [sal_get_vout DDR_VPP]
#
#plog_msg "vdd_vout: $vdd_vout; arm_vout: $arm_vout; ddr_vdd_vout: $ddr_vdd_vout; ddr_vddq_vout: $ddr_vddq_vout; ddr_vpp_vout: $ddr_vpp_vout"


set err_cnt_fnl [ plog_get_err_count ]

set err_cnt [expr $err_cnt_fnl - $err_cnt_init]


# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    plog_msg "SET AVS PASSED"
    plog_msg "SET AVS PASSED"
} else {
    plog_err "SET AVS FAILED"
    plog_err "SET AVS FAILED"
}

