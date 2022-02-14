# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {sn.arg         "Slotxxx"   "Serial Number"}
    {slot.arg       ""          "Slot number"}
    {arm_vdd.arg    "vdd"       "arm or vdd"}
    {freq.arg       833         "freqency"}
    {use_zmq.arg    0           "Use ZMQ"}
    {zmq_srv_ip.arg ""          "MTP IP"}
    {zmq_port.arg   "55000"     "ZMQ port"}
    {diag_dir.arg   "/home/diag/" "Diag home directory"}
}

array set arg [cmdline::getoptions argv $parameters]
set sn          $arg(sn)
set slot        $arg(slot)
set arm_vdd     $arg(arm_vdd)
set freq        $arg(freq)
set use_zmq     $arg(use_zmq)
set zmq_srv_ip  $arg(zmq_srv_ip)
set zmq_port    $arg(zmq_port)
set DIAG_DIR    $arg(diag_dir)

if { $use_zmq != 0 } {
    if { $zmq_srv_ip == "" || $zmq_port == ""} {
        error "Need MTP IP and slot args"
        exit
    }
}

set ASIC_LIB_BUNDLE "$DIAG_DIR/diag/asic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag
source $DIAG_SRC/asic_tests.tcl

puts "sn: $sn; slot: $slot; arm_vdd: $arm_vdd; freq: $freq"
set zmq_conn "tcp://${arg(zmq_srv_ip)}:${arg(zmq_port)}/"
puts "zmq_conn: $zmq_conn"

if { $use_zmq == 1 } {
    set ::SSI_OPERATION_TIMEOUT_S 10
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot
}

if { $use_zmq } {
    diag_force_close_zmq_if $zmq_conn $slot
    diag_open_zmq_if $zmq_conn $slot
} else {
    diag_open_j2c_if 10 $slot
}

set chip_id [ cap_get_cur_chip_id ]
if { $freq == 833 } {
    cap_top_sbus_core_833 $chip_id 0
} elseif { $freq == 900 } {
    cap_top_sbus_core_900 $chip_id 0
} elseif { $freq == 967 } {
    cap_top_sbus_core_957 $chip_id 0
} elseif { $freq == 1033 } {
    cap_top_sbus_core_1033 $chip_id 0
} elseif { $freq == 1100 } {
    cap_top_sbus_core_1100 $chip_id 0
} else {
    puts "Invalid frequence $freq"
    return 1
}
puts "Core vdd clock set to $freq"

set freq [get_freq]
puts "Read freq at $freq"

diag_close_zmq_if

puts "SET FREQ PASSED"
puts "SET FREQ PASSED"


