# !/usr/bin/tclsh
#
# Script to test j2c can connect and _msrd works.
# Used for stress testing shared bus between spi and j2c
#
set slot        [lindex $argv 0]

set uut "UUT_$slot"
set card_type $::env($uut)
puts "card type: $card_type; UUT: $uut"

exec turn_on_slot.sh off $slot
after 5000
exec turn_on_slot.sh on $slot

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

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
    exit -1
}
sal_j2c
set j2c_secure 1
#sal_ow

set val [_msrd]
if { $val != 0x1 } {
    plog_msg "OW sanity test failed!"
    exit -1
}

set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "msrd_${slot}_${cur_time}.log"
plog_start $fn

_msrd

# Need a hard check for the link here to check the return code
set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if { ($err_cnt != 0) } {
    plog_err "MSRD test FAILED"
    plog_stop
    exit -1
} else {
    plog_msg "MSRD test PASSED"
    plog_stop
    exit 0
}
