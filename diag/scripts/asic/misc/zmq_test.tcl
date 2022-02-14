set slot  [lindex $argv 0]

set time_pre [clock seconds]
set zmq_conn tcp://127.0.0.1:55000/
set use_zmq 1

global G_USE_ZMQ
global G_ZMQ_CONN
global G_SLOT
set G_USE_ZMQ $use_zmq
set G_ZMQ_CONN $zmq_conn
set G_SLOT $slot

diag_open_zmq_if $zmq_conn $slot
regrd 0 0x6a000000

cap_l1_screen_diag slot$slot 10 $slot $use_zmq $zmq_conn 0 1 1 1 1 833 0
diag_close_zmq_if
set time_post [clock seconds]
set test_time [expr {$time_post - $time_pre}]
puts "Slot: $slot; Start time: $time_pre; End time: $time_post; Test time: $test_time"

