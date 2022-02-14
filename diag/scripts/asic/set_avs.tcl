# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {sn.arg         "Slotxxx"   "Serial Number"}
    {slot.arg       ""          "Slot number"}
    {arm_vdd.arg    "vdd"       "arm or vdd"}
    {core_freq.arg  833         "core freqency"}
    {arm_freq.arg   1600        "arm freqency"}
    {use_zmq.arg    0           "Use ZMQ"}
    {zmq_srv_ip.arg ""          "MTP IP"}
    {zmq_port.arg   "55000"     "ZMQ port"}
    {diag_dir.arg   "/home/diag/" "Diag home directory"}
    {force.arg      0           "Change force"}
    {vout.arg       800         "Target vout"}
    {use_pmro.arg   0           "0: not use pmro; 1: use pmro"}
}

array set arg [cmdline::getoptions argv $parameters]
set sn          $arg(sn)
set slot        $arg(slot)
set arm_vdd     $arg(arm_vdd)
set core_freq   $arg(core_freq)
set arm_freq    $arg(arm_freq)
set use_zmq     $arg(use_zmq)
set zmq_srv_ip  $arg(zmq_srv_ip)
set zmq_port    $arg(zmq_port)
set DIAG_DIR    $arg(diag_dir)
set force       $arg(force)
set vout        $arg(vout)
set use_pmro    $arg(use_pmro)

if { $use_zmq != 0 } {
    if { $zmq_srv_ip == "" || $zmq_port == ""} {
        error "Need MTP IP and slot args"
        exit
    }
}

puts "sn: $sn; slot: $slot; arm_vdd: $arm_vdd; core_freq: $core_freq; arm_freq: $arm_freq"
set zmq_conn "tcp://${arg(zmq_srv_ip)}:${arg(zmq_port)}/"
puts "zmq_conn: $zmq_conn"

set ASIC_LIB_BUNDLE "$DIAG_DIR/diag/asic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag
source $DIAG_SRC/asic_tests.tcl

if { $use_zmq == 1 } {
    set ::SSI_OPERATION_TIMEOUT_S 10
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot
}

set err_cnt [set_avs $sn $slot $arm_vdd $core_freq $arm_freq $use_zmq $zmq_conn $force $vout $use_pmro]

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "SET AVS PASSED"
    puts "SET AVS PASSED"
} else {
    puts "SET AVS FAILED"
    puts "SET AVS FAILED"
}

