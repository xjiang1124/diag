# !/usr/bin/tclsh
#
#package require cmdline
#
# 


proc run_l1_test { {board_id SN000001} {j2c_slot 1} {core_freq 3000} {arm_freq 3200} {use_zmq 0} {zmq_conn ""} {vmarg "normal"} } {
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set j2c_port $j2c_slot
    set slot 0x10

    plog_msg "Running [info level 0]"
    plog_msg "Opening J2C Using Port-$j2c_port"

    diag_open_j2c_if $j2c_port $slot

    _msrd
    _msrd

    set in_err [plog_get_err_count]

    set SN "O2_SLOT2"
    elb_l1_screen_diag $SN $j2c_port 10 hod 0 0 127.0.0.1 0 1 0 1 1 $core_freq $arm_freq 0 $vmarg 1 0 1 0 0 1 
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt != 0} {
            plog_msg "L1 Test on slot$j2c_slot failed:  $err_cnt"
    }

    diag_close_j2c_if $j2c_port $j2c_slot
    plog_stop

    return $err_cnt
}


source ./cmdline.tcl
set parameters {
    {sn.arg         "Slotxxx"   "Serial Number"}
    {slot.arg       ""          "Slot number"}
    {core_freq.arg  3000        "core freqency"}
    {arm_freq.arg   3200        "arm freqency"}
    {use_zmq.arg    0           "Use ZMQ"}
    {zmq_srv_ip.arg ""          "MTP IP"}
    {zmq_port.arg   "55000"     "ZMQ port"}
    {diag_dir.arg   "/fs/nos/diag/" "Diag home directory"}
    {jtag_speed.arg 74          "Jtag speed Divider"}
    {vmarg.arg      "normal"   "Vmarg (higih/low/normal)"}


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
set JTAG_SPEED  $arg(jtag_speed)
set vmarg       $arg(vmarg)


#source asic_tests.tcl

puts "sn: $sn; slot: $slot; core_freq: $core_freq; arm_freq: $arm_freq"
set zmq_conn "tcp://${arg(zmq_srv_ip)}:${arg(zmq_port)}/"
puts "zmq_conn: $zmq_conn"

set ASIC_LIB_BUNDLE "$DIAG_DIR/nic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

if { $slot >6 } {
    puts "ERROR: Slot number must be 1-6"
    return -1
}


### SETUP J2C ###################################
#######        SET RESET MASK        ############
#######        RESET J2C.            ############
#######        SET J2C MUX TO INTERNAL ##########
#######        SET J2C SPEED TO 500KHZ ##########
#################################################
#export $slot=1
#./jtag_accpcie spiwrite $slot 0x3c0 0x990000
#./jtag_accpcie spiread $slot 0x3c0
#./jtag_accpcie wg $slot 0x24 0xD
#./jtag_accpcie rg $slot 0x24 
#./jtag_accpcie wg $slot 0x20 0x4A
#./jtag_accpcie rg $slot 0x20
#./jtag_accpcie wg $slot 0x28 0x1
#./jtag_accpcie rg $slot 0x28 
#################################################
if {[catch {exec $DIAG_DIR/jtag_accpcie spiwrite $slot 0x3c0 0x990000} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
} 
if {[catch {exec $DIAG_DIR/jtag_accpcie spiread $slot 0x3c0} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
} 
if {[catch {exec $DIAG_DIR/jtag_accpcie wg $slot 0x24 0xD} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
} 
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x24} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie wg $slot 0x20 $JTAG_SPEED} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x20} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie wg $slot 0x28 0x1} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x28} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x20 | grep "DATA READ" | awk {{print $4}} } result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
set j2cspeed [expr $result]
puts "Read J2C Divider for Clock Speed -> $j2cspeed"
if {$j2cspeed != [expr $JTAG_SPEED]} {
    puts "J2C CLOCK DIVIDER LOOKS INCORRECT FROM REGISTER 0x20 IN THE J2C MAILBOX"
    puts "READ $j2cspeed.   EXPECT $JTAG_SPEED"
    exit -1
}

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.elb

set err_cnt [run_l1_test $sn $slot $core_freq $arm_freq $use_zmq $zmq_conn $vmarg]

if {$err_cnt == 0} {
    puts "L1 TEST PASSED"
} else {
    puts "L1 TEST FAILED"
}




