# !/usr/bin/tclsh

puts "argv: $argv"

set brd_num  [lindex $argv 0]
set slot     [lindex $argv 1]
set int_lpbk [lindex $argv 2]
set vmarg    [lindex $argv 3]
set use_zmq  [lindex $argv 4]
set offload  [lindex $argv 5]
set esecEn   [lindex $argv 6]

puts "brd_num: $brd_num; slot: $slot; int_lpbk: $int_lpbk; vmarg: $vmarg; use_zmq: $use_zmq; offload: $offload; esecEn: $esecEn"
set err_cnt 0

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

set zmq_conn tcp://127.0.0.1:55000/
global G_USE_ZMQ
global G_ZMQ_CONN
global G_SLOT
set G_USE_ZMQ $use_zmq
set G_ZMQ_CONN $zmq_conn
set G_SLOT $slot

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.new

set uut "UUT_$slot"
set card_type $::env($uut)
if { $card_type == "NAPLES25" || $card_type == "NAPLES25SWM" || $card_type == "NAPLES25OCP"} {
    set core_freq 417.0
} else {
    set core_freq 833.0
}

puts "card type: $card_type; UUT: $uut"
puts "brd_num: $brd_num; slot: $slot"

# esec_l1 reboot wati time
set ::CAP_GPIO3_PWR_OFF_DUR 5000

if {$use_zmq == 0} {
    puts "Regular L1"
    diag_open_j2c_if 10 $slot
    set err_cnt [cap_l1_screen_diag $brd_num 10 $slot 0 $zmq_conn 0 1 1 1 1 $core_freq $int_lpbk $vmarg $offload $esecEn]
    set err_cnt 0

    diag_close_j2c_if 10 $slot
} else {
    puts "ZMQ L1"
    diag_open_zmq_if $zmq_conn $slot
    set err_cnt [cap_l1_screen_diag $brd_num 10 $slot 1 $zmq_conn 0 1 1 1 1 $core_freq $int_lpbk $vmarg $offload $esecEn]

    diag_close_zmq_if
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot

}

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "L1 TEST PASSED"
    puts "L1 TEST PASSED"
} else {
    puts "L1 TEST FAILED"
    puts "L1 TEST FAILED"
}

