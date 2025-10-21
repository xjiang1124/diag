#! /usr/bin/tclsh
set diag_path [file normalize [file join [info script] ../../..]]
source $diag_path/scripts/asic/cmdline.tcl
source $diag_path/scripts/asic/sal_diag_utils.tcl

set usage {
    {sn.arg                     ""                      "Serial number"}
    {slot.arg                   ""                      "Slot number"}
    {vmarg.arg                  "none"                  "Voltage margin"}
    {test_type.arg              "FULL"                  "Test type (FULL/SHORT)"}
    {logEn.arg                  "yes"                   "Save to logfile"}
    {tcl_path.arg               ""                      "ASIC lib location"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit }
parray arg
### initialize asic lib
if { $tcl_path != "" } {
    set ASIC_LIB_BUNDLE "$tcl_path"
} elseif { $::env(ASIC_LIB_BUNDLE) != "" } {
    set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
} else {
    set ASIC_LIB_BUNDLE "/home/diag/diag/asic"
}
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set env(ASIC_LIB_BUNDLE) "$ASIC_LIB_BUNDLE"
set env(ASIC_LIB) "$ASIC_LIB_BUNDLE/asic_lib"
set env(ASIC_SRC) "$ASIC_LIB_BUNDLE/asic_src"
set env(ASIC_GEN) "$ASIC_LIB_BUNDLE/asic_src"
set env(LD_LIBRARY_PATH) "$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:${::env(LD_LIBRARY_PATH)}"
cd $ASIC_LIB_BUNDLE/asic_src/ip/cosim/tclsh
source .tclrc.diag.sal
### initialize card properties
set slot $slot
set port $slot
set ::slot $slot
set ::port $port
set uut "UUT_$slot"
set card_type $::env($uut)
plog_msg "card type: $card_type; UUT: $uut"

if { $logEn == "yes" } {
    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    if { $sn == "" } { set sn SLOT$slot }
    set log_file $ASIC_SRC/ip/cosim/tclsh/sal_prp_${sn}_${cur_time}.log
    plog_stop
    plog_start $log_file 1000000000
}

plog_msg "Opening j2c"
set err_cnt_init [ plog_get_err_count ]
exec jtag_accpcie_salina clr $slot
exec fpgautil spimode $slot off
sal_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]

reset_to_proto_mode
sal_set_vmarg $vmarg
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt [expr $err_cnt_fnl - $err_cnt_init]
if {$err_cnt != 0} {
    plog_err "PRP TEST INIT FAILED"
    exit -2
}

set hvt [sal_harvested_asic]
if {$test_type == "FULL"} {
    sal_ms_ring_full_test 0 $hvt
} elseif {$test_type == "SHORT"} {
    sal_ms_ring_test
}

set err_cnt_fnl [ plog_get_err_count ]
set err_cnt [expr $err_cnt_fnl - $err_cnt_init]
if {$err_cnt != 0} {
    plog_err "PRP TEST FAILED"
    exit -2
} else {
    plog_msg "PRP TEST PASSED"
    exit 0
}
