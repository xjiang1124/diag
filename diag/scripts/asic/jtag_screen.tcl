# !/usr/bin/tclsh
puts "argv: $argv"

proc test_proc {input} {
    return $input
}

set slot [lindex $argv 0]
set teststage [lindex $argv 1]
set port $slot

set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set MTP_TYPE $::env(MTP_TYPE)
set ASIC_TYPE $::env(ASIC_TYPE)

source /home/diag/diag/scripts/asic/asic_tests.tcl

cd $ASIC_SRC/ip/cosim/tclsh
set slot $slot
set port $slot
source .tclrc.diag.sal
set uut "UUT_$slot"
set card_type $::env($uut)
puts "card type: $card_type; UUT: $uut"

if { $teststage == 2 } {
    ## failing if freq_test is not tested in its own powercycle...
    set test_list [ list sal_jtag_freq_test ]
} else {
    set test_list [ list sal_jtag_id sal_jtag_mbist ]
}

plog_clr_err_count
set err_cnt 0
set err_cnt2 0
foreach test_func $test_list {
    sal_j2c
    puts "_msrd"
    set rtn [eval _msrd]
    puts $rtn

    set err_cnt2 [eval $test_func]
    set err_cnt [plog_get_err_count]
    diag_close_j2c_if $port $slot
    after 1000
}

# Print twice for DSP to capture signature
if { $err_cnt != 0 } {
    puts "JTAG TESTS FAILED"
    puts "JTAG TESTS FAILED"
} else {
    puts "JTAG TESTS PASSED"
    puts "JTAG TESTS PASSED"
}

