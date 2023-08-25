# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {sn.arg         "Slotxxx"   "Serial Number"}
    {slot.arg       ""          "Slot number"}
    {core_freq.arg  1100        "core freqency"}
    {arm_freq.arg   3000        "arm freqency"}
    {use_zmq.arg    0           "Use ZMQ"}
    {zmq_srv_ip.arg ""          "MTP IP"}
    {zmq_port.arg   "55000"     "ZMQ port"}
    {diag_dir.arg   "/home/diag/" "Diag home directory"}
}

array set arg [cmdline::getoptions argv $parameters]
set sn          $arg(sn)
set slot        $arg(slot)
set core_freq   $arg(core_freq)
set arm_freq    $arg(arm_freq)
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

source asic_tests.tcl

puts "sn: $sn; slot: $slot; core_freq: $core_freq; arm_freq: $arm_freq"
set zmq_conn "tcp://${arg(zmq_srv_ip)}:${arg(zmq_port)}/"
puts "zmq_conn: $zmq_conn"

set ASIC_LIB_BUNDLE "$DIAG_DIR/diag/asic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.gig

set err_cnt [set_avs_gig $sn $slot $core_freq $arm_freq $use_zmq $zmq_conn]

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "SET AVS PASSED"
    puts "SET AVS PASSED"
} else {
    puts "SET AVS FAILED"
    puts "SET AVS FAILED"
}

