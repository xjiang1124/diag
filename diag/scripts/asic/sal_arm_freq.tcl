source /home/diag/diag/scripts/asic/cmdline.tcl
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl
set usage {
    {slot.arg       ""          "Slot number"}
    {arm_freq.arg   "1500"      "Change ARM frequency"}
    {ddr_freq.arg   "3200"      "Change DDR frequency"}
    {nxc_freq.arg   "800"       "Change NXC frequency"}
    {protomode.arg  "no"        "Set back proto mode after changing. For snake use 'no'; for L1/MBIST use 'yes'"}
    {verify.arg     "yes"       "Parse to verify"}
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

# start logfile
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set log_file $ASIC_SRC/ip/cosim/tclsh/sal_arm_freq_SLOT${slot}_${cur_time}.log
plog_stop
plog_start $log_file 1000000000

# run test
exec fpgautil spimode $slot off
exec jtag_accpcie_salina clr $slot
set_pollara_frequency $arm_freq $protomode
plog_msg "Measuring frequencies:"
sal_get_freq
diag_close_j2c_if $::slot $::port

# close
plog_stop

# verify
if { $verify == "yes" } {
    set got_arm_freq [scan [exec grep arm_counter_bits $log_file | tail -n1 | awk "{print \$NF}"] %x ]
    set got_ddr_freq [scan [exec grep ddr_counter_bits $log_file | tail -n1 | awk "{print \$NF}"] %x ]
    set got_nxc_freq [scan [exec grep nxc_counter_bits $log_file | tail -n1 | awk "{print \$NF}"] %x ]
    plog_msg "Verifying arm frequency: got $got_arm_freq MHz"
    plog_msg "Verifying ddr frequency: got $got_ddr_freq MHz"
    plog_msg "Verifying nxc frequency: got $got_nxc_freq MHz"
    if { [expr $got_arm_freq - $arm_freq] > 50 } { plog_err "Not able to set correct ARM frequency, expecting '$arm_freq' got '$got_arm_freq'" }
    if { [expr $got_ddr_freq - $ddr_freq] > 50 } { plog_err "Not able to set correct DDR frequency, expecting '$ddr_freq' got '$got_ddr_freq'" }
    if { [expr $got_nxc_freq - $nxc_freq] > 50 } { plog_err "Not able to set correct NXC frequency, expecting '$nxc_freq' got '$got_nxc_freq'" }
}
exit 0