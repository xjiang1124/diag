# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {sn.arg         "Slotxxx"   "Serial Number"}
    {slot.arg       ""          "Slot number"}
    {use_zmq.arg    0           "Use ZMQ"}
    {zmq_srv_ip.arg ""          "MTP IP"}
    {zmq_port.arg   "55000"     "ZMQ port"}
    {diag_dir.arg   "/home/diag/" "Diag home directory"}
}

array set arg [cmdline::getoptions argv $parameters]
set sn          $arg(sn)
set slot        $arg(slot)
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

puts "sn: $sn; slot: $slot"
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
    diag_force_close_zmq_if $zmq_conn $slot
}

set xx [info args cap_set_avs]
puts "===== $xx ====="

set err_cnt [disp_volt_temp $sn $slot $use_zmq $zmq_conn]

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "DISP VOLT TEMP PASSED"
    puts "DISP VOLT TEMP PASSED"
} else {
    puts "DISP VOLT TEMP FAILED"
    puts "DISP VOLT TEMP FAILED"
}

