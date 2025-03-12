# !/usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {slot.arg           ""                  "Slot number"}
    {card_type.arg      ""                  "Card type"}
    {vmarg.arg          "normal"            "Voltage margin"}
    {dura.arg           60                  "Test duration"}
    {mtp_clk.arg        0                   "MTP PCIe reference clock"}
    {aw_txfir_ow.arg    ""                  "Awave TXFIR overwrite"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

exec fpgautil spimode $slot off
exec jtag_accpcie_salina clr $slot

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

set ::env(MTP_PCIE_USE_REFCLK_0) $mtp_clk

if { $aw_txfir_ow != "" } {
    if { ($aw_txfir_ow >= 0) && ($aw_txfir_ow <= 10) } {
        set ::env(SAL_AW_TXFIR_OW) $aw_txfir_ow
    } else {
        plog_msg "Invalid value of aw_txfir_ow: $aw_txfir_ow; ignore this setting!!!"
   } 
}

#csr_write sal0.txs.txs\[0].base 0xaabbcc
#rds sal0.txs.txs\[0].base
set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "pcie_prbs_slot${slot}_${cur_time}.log"
plog_start $fn

plog_msg "card_type = $card_type"
sal_print_die_id
sal_set_vmarg $vmarg 

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
