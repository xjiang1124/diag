# !/usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {slot.arg           ""                  "Slot number"}
    {card_type.arg      ""                  "Card type"}
    {vmarg.arg          "normal"            "Voltage margin"}
    {dura.arg           60                  "Test duration"}
    {mtp_clk.arg        0                   "MTP PCIe reference clock"}
    {aw_txfir_ow.arg    ""                  "Awave TXFIR overwrite: preset 1-9"}
    {macro_mask.arg     0xf                 "Macro mask"}
    {lane_mask.arg      0xf                 "Lane mask"}
    {tail.arg           ""                  "tail msg"}
    {ite.arg            1                   "Iteration"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }

puts "Turn off slot $slot"
exec turn_on_slot.sh off $slot
after 10000
puts "Turn on slot $slot"
exec turn_on_slot.sh on $slot

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

pcie_mtp_prbs_test 1100 $card_type 4 $dura 6 $macro_mask $lane_mask

plog_msg "PRBS TEST DONE"

#==============================================
plog_msg "Collecting FFE data"

for {set i 0} {$i < $ite} {incr i} {
    set tail1 "${tail}_${i}"
    set log_path "ffe_mmask${macro_mask}_lmask${lane_mask}_${tail}"
    try {
        exec mkdir -p "/home/diag/xin/log/$log_path"
    #    exec rm /home/diag/xin/log/$log_path/*
    } on error {errMsg} {
        plog_msg "Never mind"
    }


    for {set macro 0} {$macro < 4} {incr macro} {
        set macro_en [ expr {(1<<$macro) & $macro_mask} ]
        if { $macro_en == 0 } {
            continue
        }
    
        for {set ln 0} {$ln < 4} {incr ln} {
            set lane_en [ expr {(1<<$ln) & $lane_mask} ]
            if { $lane_en == 0 } {
                continue
            }
            set fn "/home/diag/xin/log/${log_path}/sal_ffe_data_mmask${macro_mask}_lmask${lane_mask}_${tail1}_slot${slot}_macro${macro}_ln${ln}.log"
            sal_aw_pma_dump_ffe_data $macro $ln 1000 $fn
        }
    }
    after 60000
}

exec cp /home/diag/diag/asic/asic_src/ip/cosim/tclsh/$fn /home/diag/xin/log/${log_path}


set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "PRBS test FAILED"
    exit -1
} else {
    plog_msg "PRBS test PASSED"
    exit 0
}
