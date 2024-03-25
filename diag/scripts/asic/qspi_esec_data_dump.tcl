# !/usr/bin/tclsh
#
#package require cmdline

set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

source ./cmdline.tcl


set parameters {
    {slot.arg        ""              "Slot list"}
    {mode.arg        "hod"           "Elba mode: hod/hod_1100/nod/nod_525"}
}

set usage "- Usage:"
if {[catch {array set options [cmdline::getoptions ::argv $parameters $usage]} errMsg]} {
    puts [cmdline::usage $parameters $usage]
    puts "errMsg: $errMsg"
    exit
} else {
    parray options
}

set slot        $options(slot)
set mode        $options(mode)

puts "slot: $slot; mode $mode"

if { $slot == "" } {
    error "Need slot arg"
    exit
}

set ASIC_TYPE $::env(ASIC_TYPE)

cd $ASIC_SRC/ip/cosim/tclsh
if { $ASIC_TYPE == "GIGLIO" } {
    source .tclrc.diag.gig
} else {
    source .tclrc.diag.elb
}

set port [mtp_get_j2c_port $slot]
set slot1 [mtp_get_j2c_slot $slot]
diag_close_j2c_if $port $slot1

puts "Slot $slot off"
catch {set output [exec /home/diag/diag/scripts/turn_on_slot.sh off $slot]}
puts $output
after 3000
puts "Slot $slot on"
catch {set output [exec /home/diag/diag/scripts/turn_on_slot.sh on $slot]}
puts $output
after 1000

diag_open_j2c_if $port $slot1
_msrd
if { $ASIC_TYPE == "GIGLIO" } {
    gig_card_rst $port $slot1 $mode 5600 3000 0 0 "127" 0 1 normal 0 0
    gig_qspi_pwr_up_chk 835 1
} else {
    elb_card_rst $port $slot1 $mode 3200 3000 0 0 "127" 0 1 normal 0 0
    elb_qspi_pwr_up_chk 835 1
}

