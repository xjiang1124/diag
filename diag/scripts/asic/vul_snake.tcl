#! /usr/bin/tclsh

set slot        [lindex $argv 0]
set test_type   [lindex $argv 1]
set dura        [lindex $argv 2]
set card_type   [lindex $argv 3]
set vmarg       [lindex $argv 4]
set int_lpbk    [lindex $argv 5]
set mtp_clk     [lindex $argv 6]

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.vul
#source /home/diag/diag/scripts/asic/vul_diag_utils.tcl

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port
#exec jtag_accpcie_vulcano clr $slot
diag_close_j2c_if $port $slot
diag_open_j2c_if $port $slot

set ::env(MTP_PCIE_USE_REFCLK_0) $mtp_clk

set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "snake_slot${slot}_${cur_time}.log"
pwd
plog_start $fn

#set card_type [vul_get_card_type]
#set cpld_id [ vul_cpld_read 0x80 ]
plog_msg "card_type = $card_type"
#plog_msg "cpld_id = $cpld_id"
#vul_print_die_id
#vul_set_vmarg $vmarg

plog_msg "snake test_type: $test_type"
plog_msg "pcie done"
#vul_snake_test $card_type $test_type $dura $int_lpbk $mtp_clk

plog_stop
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt  [ expr ( $err_cnt_fnl - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "SNAKE TEST FAILED"
    set ret -1
} else {
    plog_msg "SNAKE TEST PASSED"
    set ret 0
}
plog_msg "SNAKE TEST DONE"
diag_close_j2c_if $port $slot
exit $ret
