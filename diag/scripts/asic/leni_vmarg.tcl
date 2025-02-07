#! /usr/bin/tclsh

set slot [lindex $argv 0]
set card_type [lindex $argv 1]
set vmarg [lindex $argv 2]

set ASIC_SRC $::env(ASIC_SRC)
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set slot $slot
set port $slot
set ::slot $slot
set ::port $port

exec jtag_accpcie_salina clr $slot
exec fpgautil spimode $slot off

diag_close_j2c_if $port $slot
diag_open_j2c_if $port $slot
diag_close_j2c_if $port $slot

after 500
diag_close_ow_if $port $slot
after 500
diag_open_ow_if $port $slot
after 500
sal_ow_axi

csr_write sal0.ms.ms.cfg_ow 3
after 500
rd sal0.ms.ms.cfg_ow

plog_msg "set vmarg: $vmarg"
sal_set_vmarg $vmarg
diag_close_ow_if $port $slot
plog_msg "vmarg set"
exit 0

