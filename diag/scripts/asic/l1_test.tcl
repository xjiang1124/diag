# !/usr/bin/tclsh

set brd_num [lindex $argv 0]
set slot_id [lindex $argv 1]
puts "brd_num: $brd_num; slot_id: $slot_id"

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.new

puts "brd_num: $brd_num; slot_id: $slot_id"
diag_open_j2c_if 10 $slot_id
source $ASIC_SRC/ip/cosim/capri/cap_l1_tests.tcl
set err_cnt [cap_l1_screen $brd_num 10 $slot_id]

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "L1 TEST PASSED"
    puts "L1 TEST PASSED"
} else {
    puts "L1 TEST FAILED"
    puts "L1 TEST FAILED"
}

