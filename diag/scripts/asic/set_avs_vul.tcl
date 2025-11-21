#! /usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl
#source /home/diag/diag/scripts/asic/vul_diag_utils.tcl
source /home/diag/diag/scripts/asic/asic_tests.tcl
set usage {
    {slot.arg       ""                      "Slot number"}
    {sn.arg         ""                      "Serial Number"}
    {tcl_path.arg   "/home/diag/diag/asic/" "ASIC lib location"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }
if { $sn   == "" } { set sn "Slot${slot}" }

set ASIC_LIB_BUNDLE "$tcl_path"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$tcl_path/diag/scripts/asic/"
set ::VEL_SHELL 0
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.vul
set ::slot  $slot
set ::port  $slot

# start logfile
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set log_file $ASIC_SRC/ip/cosim/tclsh/set_avs_${sn}_${cur_time}.log
plog_stop
plog_start $log_file 1000000000

# run test
exec jtag_accpcie_vulcano clr $slot
set err_cnt_set [vul_get_myerr_cnt "vul_set_voltage_vboot avs"]
set err_cnt_set 0
exec turn_on_slot.sh off $slot
exec turn_on_slot.sh on $slot
set err_cnt_verify [vul_get_myerr_cnt "vul_verify_voltage_vboot"]
diag_close_j2c_if $::slot $::port

plog_stop
# Print twice for DSP to capture signature
if {$err_cnt_set == 0 && $err_cnt_verify == 0} {
    plog_msg "SET AVS PASSED"
    plog_msg "SET AVS PASSED"
    exit 0
} else {
    plog_err "SET AVS FAILED"
    plog_err "SET AVS FAILED"
    exit -1
}