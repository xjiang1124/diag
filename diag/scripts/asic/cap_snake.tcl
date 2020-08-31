# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {sn.arg         "Slotxxx"       "Serial Number"}
    {slot.arg       ""              "Slot number"}
    {mode.arg       "hbm_lb"        "Mode: pcie_lb or hbm_lb"}
    {mac_lb.arg     1               "MAC loopback: 0 disable; 1 enable"}
    {core_freq.arg  833.0           "Core freqence"}
    {duration.arg   60              "duation"}
    {use_zmq.arg    0               "Use ZMQ"}
    {zmq_srv_ip.arg ""              "MTP IP"}
    {zmq_port.arg   "55000"         "ZMQ port"}
    {diag_dir.arg   "/home/diag/"   "Diag home directory"}
    {fan_ctrl.arg   0               "Fan control"}
    {tgt_temp.arg   115             "Target temp"}
}

array set arg [cmdline::getoptions argv $parameters]
set sn          $arg(sn)
set slot        $arg(slot)
set mode        $arg(mode)
set mac_lb      $arg(mac_lb)
set core_freq   $arg(core_freq)
set duration    $arg(duration)
set use_zmq     $arg(use_zmq)
set zmq_srv_ip  $arg(zmq_srv_ip)
set zmq_port    $arg(zmq_port)
set DIAG_DIR    $arg(diag_dir)
set fan_ctrl    $arg(fan_ctrl)
set tgt_temp    $arg(tgt_temp)

if { $use_zmq != 0 } {
    if { $zmq_srv_ip == "" || $zmq_port == ""} {
        error "Need MTP IP and slot args"
        exit
    }
}

if { $slot == "" } {
    error "Need port arg"
    exit
}

set zmq_conn "tcp://${arg(zmq_srv_ip)}:${arg(zmq_port)}/"
puts "zmq_conn: $zmq_conn"

puts "sn: $sn; slot: $slot; mode: $mode; mac_lb: $mac_lb; duration: $duration"

#set DIAG_DIR "/home/xguo2/workspace/temp/diag/"
#set DIAG_DIR "/home/diag/"
#puts $DIAG_DIR

set ASIC_LIB_BUNDLE "$DIAG_DIR/diag/asic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

if {$MTP_TYPE == "MTP_ELBA"} {
    puts "Elba MTP"
    set tclrc_source .tclrc.diag.elb.new
    set asic_type ELBA
} else {
    puts "Capri MTP"
    set tclrc_source .tclrc.diag.new
    set asic_type CAPRI
}

cd $ASIC_SRC/ip/cosim/tclsh
source $tclrc_source
source $DIAG_SRC/asic_tests.tcl

puts "sn: $sn; slot: $slot; mode: $mode; mac_lb: $mac_lb; duration: $duration; use_zmq: $use_zmq"

if { $use_zmq == 1 } {
    set ::SSI_OPERATION_TIMEOUT_S 10
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot

    #diag_open_zmq_if $zmq_conn $slot
} else {
    diag_close_j2c_if 10 $slot
}
set err_cnt [asic_snake $asic_type $sn $slot $mode $core_freq $mac_lb $duration $use_zmq $zmq_conn $fan_ctrl $tgt_temp]
diag_close_zmq_if

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "PCIE PRBS PASSED"
    puts "PCIE PRBS PASSED"
} else {
    puts "PCIE PRBS FAILED"
    puts "PCIE PRBS FAILED"
}

