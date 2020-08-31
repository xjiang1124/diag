# !/usr/bin/tclsh
puts "argv: $argv"

proc test_proc {input} {
    return $input
}


set sn       [lindex $argv 0]
set slot     [lindex $argv 1]
set int_lpbk [lindex $argv 2]
set vmarg    [lindex $argv 3]
set use_zmq  [lindex $argv 4]
set offload  [lindex $argv 5]
set esecEn   [lindex $argv 6]

puts "sn: $sn; slot: $slot; int_lpbk: $int_lpbk; vmarg: $vmarg; use_zmq: $use_zmq; offload: $offload; esecEn: $esecEn"
set err_cnt 0

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

set MTP_TYPE $::env(MTP_TYPE)

set zmq_conn tcp://127.0.0.1:55000/
global G_USE_ZMQ
global G_ZMQ_CONN
global G_SLOT
set G_USE_ZMQ $use_zmq
set G_ZMQ_CONN $zmq_conn
set G_SLOT $slot

cd $ASIC_SRC/ip/cosim/tclsh
if {$MTP_TYPE == "MTP_ELBA"} {
    puts "Elba MTP"
    set l1_cmd "elb_l1_screen_diag $sn 10 $slot nod 0 $use_zmq 127.0.0.1 0 1 1 0 0 1600 3200 $int_lpbk $vmarg $offload $esecEn" 
    #set l1_cmd "elb_l1_screen_diag $sn 10 $slot nod 0 0" 
    source .tclrc.diag.elb.new
} else {
    puts "Capri MTP"
    set l1_cmd "cap_l1_screen_diag $sn 10 $slot 0 $zmq_conn 0 1 1 1 1 $core_freq $int_lpbk $vmarg $offload $esecEn"
    source .tclrc.diag.new
}

set uut "UUT_$slot"
set card_type $::env($uut)
if { $card_type == "NAPLES25"    ||
     $card_type == "NAPLES25SWM" ||
     $card_type == "NAPLES25OCP" ||
     $card_type == "NAPLES25WFG"} {
    set core_freq 417.0
} else {
    set core_freq 833.0
}

puts "card type: $card_type; UUT: $uut"
puts "sn: $sn; slot: $slot"

# esec_l1 reboot wati time
set ::CAP_GPIO3_PWR_OFF_DUR 5000

if {$use_zmq == 0} {
    puts "Regular L1"
    diag_open_j2c_if 10 $slot
    #set err_cnt [cap_l1_screen_diag $sn 10 $slot 0 $zmq_conn 0 1 1 1 1 $core_freq $int_lpbk $vmarg $offload $esecEn]
    set err_cn [eval $l1_cmd]
    set err_cnt 0

    diag_close_j2c_if 10 $slot
} else {
    puts "ZMQ L1"
    diag_open_zmq_if $zmq_conn $slot
    set err_cnt [cap_l1_screen_diag $sn 10 $slot 1 $zmq_conn 0 1 1 1 1 $core_freq $int_lpbk $vmarg $offload $esecEn]

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

