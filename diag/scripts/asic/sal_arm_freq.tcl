source /home/diag/diag/scripts/asic/cmdline.tcl
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl
set usage {
    {slot.arg       ""          "Slot number"}
    {arm_freq.arg   "1500"      "Change ARM frequency"}
    {protomode.arg  "no"        "Set back proto mode after changing. For snake use 'no'; for L1/MBIST use 'yes'"}
    {logEn.arg      "yes"       "Save to logfile"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }

set ASIC_SRC $::env(ASIC_SRC)
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
set ::slot  $slot
set ::port  $slot
if { $logEn == "yes" } {
    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    if { $sn == "" } { set sn SLOT$slot }
    set log_file $ASIC_SRC/ip/cosim/tclsh/sal_jtag_mbist_${sn}_${cur_time}.log
    plog_stop
    plog_start $log_file 1000000000
}
exec fpgautil spimode $slot off
exec jtag_accpcie_salina clr $slot
set_pollara_frequency $arm_freq $protomode
plog_msg "Measuring frequencies:"
sal_get_freq
diag_close_j2c_if $::slot $::port
if { $logEn == "yes" } { plog_stop }
exit 0