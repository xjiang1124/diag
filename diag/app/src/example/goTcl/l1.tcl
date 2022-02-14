source .tclrc.diag
diag_open_j2c_if 10 [lindex $argv 0]
source $::env(ASIC_SRC)/ip/cosim/capri/cap_l1_tests.tcl
cap_l1_screen 2 10 [lindex $argv 0]

