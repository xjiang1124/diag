# !/usr/bin/tclsh

set slot        [lindex $argv 0]

set uut "UUT_$slot"
set card_type $::env($uut)
puts "card type: $card_type; UUT: $uut"

if { $card_type != "LINGUA" } {
    puts "ERROR: Test can only be run on LINGUA"
    puts "RMII test FAILED"
    exit -1
}


set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set ::FAN_SPD 80
set ::DEVMGR devmgr_v2

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port
exec jtag_accpcie_salina clr $slot
exec fpgautil spimode $slot off
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

set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "rmii_test_slot${slot}_${cur_time}.log"
plog_start $fn

sal_mes_rmii_test 

# Need a hard check for the link here to check the return code
set rc [sal_ix_check_sync 0 0]
plog_msg "RMII SYNC=$rc"
if {$rc == 0} {
    plog_err "ERROR RMII DID NOT LINK UP.  SYNC RETURNED 0"
}

plog_msg "RMII TEST DONE"

set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if { ($err_cnt != 0) || ($rc == 0) } {
    plog_err "RMII test FAILED"
    plog_stop
    exit -1
} else {
    plog_msg "RMII test PASSED"
    plog_stop
    exit 0
}
