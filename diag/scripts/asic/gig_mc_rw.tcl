# !/usr/bin/tclsh
#
#package require cmdline

set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

source ./cmdline.tcl


set parameters {
    {sn.arg          "FLM000"        "Serial number"}
    {slot.arg        ""              "Slot list"}
    {mode.arg        "hod"           "Elba mode: hod/hod_1100/nod/nod_525"}
    {hc.arg          0               "Hardcoded training"}
    {ctrl_pi.arg     0xC             "CTRL/PI channel bit mask; 0xC: CTRL; 0x3: PI"}
    {addr_space.arg  34              "DDR address space; 34: 16G; 32: 8G; 28: 256MB"}
    {dual_rank.arg   0               "Dual rank"}
    {ddr_freq.arg    4400            "DDR frequency"}
    {ddr5.arg        0               "DDR5 option"}
    {vmarg.arg       "normal"        "Voltage margin: normal/high/low"}
    {pc.arg          1               "Power cycle"}
    {vdd_margin_pct.arg  "0"             "Core margin pct"}
    {arm_margin_pct.arg  "0"             "Arm margin pct"}
    {margin_pct.arg      "0"             "ddr_vdd/ddr_vddq/ddr_vpp/vdd_ddr margin pct"}
}

set usage "- Usage:"
if {[catch {array set options [cmdline::getoptions ::argv $parameters $usage]} errMsg]} {
    puts [cmdline::usage $parameters $usage]
    puts "errMsg: $errMsg"
    exit
} else {
    parray options
}

set sn          $options(sn)
set slot        $options(slot)
set mode        $options(mode)
set hc          $options(hc)
set ctrl_pi     $options(ctrl_pi)
set addr_space  $options(addr_space)
set dual_rank   $options(dual_rank)
set ddr_freq    $options(ddr_freq)
set ddr5        $options(ddr5)
set vmarg       $options(vmarg)
set pc          $options(pc)
set vdd_margin_pct $options(vdd_margin_pct)
set arm_margin_pct $options(arm_margin_pct)
set margin_pct $options(margin_pct)


puts "sn: $sn; slot: $slot; mode $mode; hc: $hc; ctrl_pi: $ctrl_pi; addr_space: $addr_space; dual_rank: $dual_rank; ddr5: $ddr5; vmarg: $vmarg; pc: $pc"

if { $slot == "" } {
    error "Need slot arg"
    exit
}

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.gig

set port [mtp_get_j2c_port $slot]
set slot1 [mtp_get_j2c_slot $slot]
diag_close_j2c_if $port $slot1

if { $pc != 0 } {
    puts "Slot $slot off"
    catch {set output [exec /home/diag/diag/scripts/turn_on_slot.sh off $slot]}
    puts $output
    after 3000
    puts "Slot $slot on"
    catch {set output [exec /home/diag/diag/scripts/turn_on_slot.sh on $slot]}
    puts $output
    after 1000
}

diag_open_j2c_if $port $slot1
_msrd


set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set log_fn "ddr_bist_sn_${sn}_slot_${slot}_${cur_time}.log"

plog_start $log_fn

set in_err [plog_get_err_count]

gig_card_rst $port $slot1 hod_1100 $ddr_freq 3000 0 0 "127" 0 1 $vmarg 0 1 $vdd_margin_pct $arm_margin_pct $margin_pct
gig_platform
gig_ddr_init_ddr $::ddr5 $ddr_freq
gig_ddr_bist
gig_platform
gig_mc_check_ecc  -1  -1  $::ddr5  $::board_type
gig_mc_clear_ecc_irq  -1  -1  -1  $::ddr5
gig_mc_clear_ecc_counter  -1  -1  $::ddr5

set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
# Print twice for DSP to capture signature
plog_msg "\n\n\n"
plog_msg "============================="
if {$err_cnt == 0} {
    plog_msg "DDR BIST PASSED"
    plog_msg "DDR BIST PASSED"
    plog_msg "============================="
    plog_stop
    exit
} else {
    plog_msg "DDR BIST FAILED"
    plog_msg "DDR BIST FAILED"
    plog_msg "============================="
    plog_stop
}

set full_log_fn $::env(ASIC_SRC)/ip/cosim/tclsh/$log_fn
plog_msg "\n\n\n"
plog_msg "====== FULL ERROR INFO ======"
catch {set output1 [exec grep -a "ERROR :" $full_log_fn]}
plog_msg $output1
plog_msg "============================="
#plog_msg "\n\n\n"
#plog_msg "====== SLICE ERROR INFO ======"
#catch {set output2 [exec grep -a "ERROR :" $full_log_fn | grep "SLICE"]}
#plog_msg $output2
#plog_msg "============================="

