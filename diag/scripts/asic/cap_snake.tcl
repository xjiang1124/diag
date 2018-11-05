# !/usr/bin/tclsh

set sn [lindex $argv 0]
set slot_num [lindex $argv 1]
set mode [lindex $argv 2]
set mac_lb [lindex $argv 3]
set duration [lindex $argv 4]

puts "sn: $sn; slot_num: $slot_num; mode: $mode; mac_lb: $mac_lb; duration: $duration"

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "/home/diag/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.new
source $ASIC_SRC/ip/cosim/capri/cap_l1_tests.tcl
source $DIAG_SRC/asic_tests.tcl

diag_open_j2c_if 10 $slot_num
set err_cnt [cap_snake $sn $slot_num $mode $mac_lb $duration]

# Print twice for DSP to capture signature
if {$err_cnt == 0} {
    puts "PCIE PRBS PASSED"
    puts "PCIE PRBS PASSED"
} else {
    puts "PCIE PRBS FAILED"
    puts "PCIE PRBS FAILED"
}

