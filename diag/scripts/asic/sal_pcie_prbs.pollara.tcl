# !/usr/bin/tclsh

set slot        [lindex $argv 0]
set card_type   [lindex $argv 1]
set vmarg       [lindex $argv 2]
set dura        [lindex $argv 3]
set mtp_clk     [lindex $argv 4]
set vmarg_core  [lindex $argv 5]
set vmarg_arm   [lindex $argv 6]

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set ::FAN_SPD 80
set ::DEVMGR devmgr_v2

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port
diag_close_j2c_if $port $slot
diag_open_j2c_if $port $slot
diag_close_j2c_if $port $slot

after 500
diag_close_ow_if $port $slot
after 500
diag_open_ow_if $port $slot
after 2000
sal_ow_axi

set dd 0
set cnt 0
while { ($dd==0) && ($cnt<10) } {
    csr_write sal0.ms.ms.cfg_ow 3
    after 500
    set dd [ rd sal0.ms.ms.cfg_ow ]
    incr cnt
}
set ret 1
if { $cnt  >= 10 } {
    plog_err "\n\n==== J2C / OW is not working.... Ping HW team\n\n"
    return
}
sal_j2c
set j2c_secure 1
#sal_ow

set val [_msrd]
if { $val != 0x1 } {
    plog_msg "OW sanity test failed!"
    exit 0
}

set ::env(MTP_PCIE_USE_REFCLK_0) $mtp_clk

#csr_write sal0.txs.txs\[0].base 0xaabbcc
#rds sal0.txs.txs\[0].base
set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "pcie_prbs_slot${slot}_${cur_time}.log"
plog_start $fn

plog_msg "card_type = $card_type"
sal_print_die_id
sal_set_vmarg $vmarg 
if {$vmarg_core != "0"} {
    plog_msg "set vmarg VDD: $vmarg_arm"
    sal_set_margin_by_value VDD $vmarg_core
    set new_vout [sal_get_vout VDD]
    plog_msg "New VDD vout: $new_vout"
}
if {$vmarg_arm != "0" && [dict exists [sal_i2c_tbl] ARM]} {
    plog_msg "set vmarg ARM: $vmarg_arm"
    sal_set_margin_by_value ARM $vmarg_arm
    set new_vout [sal_get_vout ARM]
    plog_msg "New ARM vout: $new_vout"
}
sal_print_voltage_temp

pcie_mtp_prbs_test 1100 $card_type 4 $dura 6

plog_msg "PRBS TEST DONE"

set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "PRBS test FAILED"
    exit -1
} else {
    plog_msg "PRBS test PASSED"
    exit 0
}
