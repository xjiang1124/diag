#! /usr/bin/tclsh
#
#package require cmdline
source /home/diag/diag/scripts/asic/cmdline.tcl
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl
set parameters {
    {slot.arg       ""                      "Slot number"}
    {vboot_core.arg "none"                  "Set CORE Vboot value"}
    {vboot_arm.arg  "none"                  "Set ARM Vboot value"}
    {tcl_path.arg   "/home/diag/diag/asic/" "ASIC nic.tar path"}
}

array set arg [cmdline::getoptions argv $parameters]
set slot        $arg(slot)
set vboot_core  $arg(vboot_core)
set vboot_arm   $arg(vboot_arm)
set tcl_path    $arg(tcl_path)
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }
set ASIC_SRC $::env(ASIC_SRC)
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
set ::slot  $slot
set ::port  $slot
sal_j2c
set ret [_msrd]
plog_msg "_msrd: $ret"
reset_to_proto_mode 
if {$vboot_core != "none"} {
    sal_update_vboot VDD $vboot_core
    set new_volt [sal_get_vboot VDD]
    plog_msg "New VDD vboot: $new_volt"
}
if {$vboot_arm != "none"} {
    sal_update_vboot ARM $vboot_arm
    set new_volt [sal_get_vboot ARM]
    plog_msg "New ARM vboot: $new_volt"
}
diag_close_j2c_if $::port $::slot
exit 0
