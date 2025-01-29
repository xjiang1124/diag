# !/usr/bin/tclsh
#
#package require cmdline
source /home/diag/diag/scripts/asic/cmdline.tcl
set parameters {
    {slot.arg       ""                      "Slot number"}
    {vmarg.arg      "0"                     "Voltage margin: normal/high/low"}
    {vmarg_core.arg "0"                     "Set CORE VOUT value"}
    {vmarg_arm.arg  "0"                     "Set ARM VOUT value"}
    {vmarg_ddr.arg  "0"                     "DDR vmargin percentage"} ;# need to add support
    {tcl_path.arg   "/home/diag/diag/asic/" "ASIC nic.tar path"}
}

array set arg [cmdline::getoptions argv $parameters]
set slot        $arg(slot)
set vmarg       $arg(vmarg)
set vmarg_core  $arg(vmarg_core)
set vmarg_arm   $arg(vmarg_arm)
set vmarg_ddr   $arg(vmarg_ddr)
set tcl_path    $arg(tcl_path)

set ASIC_SRC $::env(ASIC_SRC)
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
set ::slot  $slot
set ::port  $slot
sal_j2c
set ret [_msrd]
plog_msg "_msrd: $ret"
if {$vmarg != "0"} {
    plog_msg "set vmarg: $vmarg"
    sal_set_vmarg $vmarg
}
if {$vmarg_core != "0"} {
    plog_msg "set vmarg VDD: $vmarg_core"
    sal_set_margin_by_value VDD $vmarg_core
    set new_volt [sal_get_vout VDD]
    plog_msg "New VDD vout: $new_volt"
}
if {$vmarg_arm != "0"} {
    plog_msg "set vmarg ARM: $vmarg_arm"
    sal_set_margin_by_value ARM $vmarg_arm
    set new_volt [sal_get_vout ARM]
    plog_msg "New ARM vout: $new_volt"
}
diag_close_j2c_if $::port $::slot
plog_msg "vmarg set"
exit 0
