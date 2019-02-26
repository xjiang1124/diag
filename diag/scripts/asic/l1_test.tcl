# !/usr/bin/tclsh

set brd_num  [lindex $argv 0]
set slot_id  [lindex $argv 1]
set int_lpbk [lindex $argv 2]
puts "brd_num: $brd_num; slot_id: $slot_id"

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.new

set uut "UUT_$slot_id"
set card_type $::env($uut)
if { $card_type == "NAPLES25" } {
    set core_freq 417.0
} else {
    set core_freq 833.0
}
puts "card type: $card_type; UUT: $uut"

puts "brd_num: $brd_num; slot_id: $slot_id"
diag_open_j2c_if 10 $slot_id
set err_cnt [cap_l1_screen $brd_num 10 $slot_id 0 "" 0 1 0 1 1 833.0 $int_lpbk]

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "L1 TEST PASSED"
    puts "L1 TEST PASSED"
} else {
    puts "L1 TEST FAILED"
    puts "L1 TEST FAILED"
}

