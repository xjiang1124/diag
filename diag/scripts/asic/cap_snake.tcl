# !/usr/bin/tclsh
#
package require cmdline
set parameters {
    {sn.arg       "20" "Serial Number"}
    {slot.arg     ""   "Slot number"}
    {mode.arg     "hbm_lb"   "Mode: pcie_lb or hbm_lb"}
    {mac_lb.arg   1   "MAC loopback: 0 disable; 1 enable"}
    {duration.arg 60   "duation"}
    {use_zmq.arg  "0"    "Use ZMQ"}
    {mtp_ip.arg   ""   "MTP IP"}
    {zmq_port.arg ""   "ZMQ port"}
}

array set arg [cmdline::getoptions argv $parameters]
set sn $arg(sn)
set slot $arg(slot)
set mode $arg(mode)
set mac_lb $arg(mac_lb)
set duration $arg(duration)
set use_zmq $arg(use_zmq)
set mtp_ip $arg(mtp_ip)
set zmq_port $arg(zmq_port)

if { $arg(mtp_ip) == "" || $arg(slot) == "" || $arg(zmq_port) == ""} {
    error "Need MTP IP, port and slot args"
    exit
}

set zmq_conn "tcp://${arg(mtp_ip)}:${arg(zmq_port)}/"
puts "zmq_conn: $zmq_conn"

puts "sn: $sn; slot: $slot; mode: $mode; mac_lb: $mac_lb; duration: $duration"

set DIAG_DIR "/home/xguo2/workspace/temp/diag/"
#set DIAG_DIR "/home/diag/"
set ASIC_LIB_BUNDLE "$DIAG_DIR/diag/asic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag
source $DIAG_SRC/asic_tests.tcl

puts "sn: $sn; slot: $slot; mode: $mode; mac_lb: $mac_lb; duration: $duration; use_zmq: $use_zmq"

set ::SSI_OPERATION_TIMEOUT_S 10
diag_force_close_zmq_if $zmq_conn $slot

if { $use_zmq == 1 } {
    diag_open_zmq_if $zmq_conn $slot
} else {
    diag_open_j2c_if 10 $slot
}
set err_cnt [cap_snake $sn $slot $mode $mac_lb $duration $use_zmq $zmq_conn]

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "PCIE PRBS PASSED"
    puts "PCIE PRBS PASSED"
} else {
    puts "PCIE PRBS FAILED"
    puts "PCIE PRBS FAILED"
}

