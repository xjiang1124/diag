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
}

set usage "- Usage:"
if {[catch {array set options [cmdline::getoptions ::argv $parameters $usage]}]} {
    puts [cmdline::usage $parameters $usage]
    exit
} else {
    parray options
}

set slot        $options(slot)

puts "slot: $slot"

if { $slot == "" } {
    error "Need slot arg"
    exit
}

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.elb

proc elb_get_err_cnt { proc_to_run } {
   plog_msg "===> running  $proc_to_run"
   set in_err [plog_get_err_count]
   {*}$proc_to_run
   set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
   return $err_cnt
}

proc img_prog {slot} {
    set ret 0
    set fw_ptr $::env(ASIC_SRC)/ip/cosim/elba/esec_flash_7001_0000.hex

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd
    elb_card_rst $port $turbo_slot nod 3200 2000 0 0 "127" 0 1 normal 0 0
    elb_esec_set_proto_mode

    set ret [elb_prog_qspi $fw_ptr 0x70010000]
    if {$ret != 0} {
        plog_msg "Failed to program fw_ptr"
        return $ret
    }
    return $ret
}

set port [mtp_get_j2c_port $slot]
set turbo_slot [mtp_get_j2c_slot $slot]

diag_open_j2c_if $port $turbo_slot
set ret [img_prog $slot]
diag_close_j2c_if $port $turbo_slot


# Print twice for DSP to capture signature
if {$ret == 0} {
    plog_msg "L1 ESEC PROG PASSED"
    plog_msg "L1 ESEC PROG PASSED"
} else {
    plog_msg "L1 ESEC PROG FAILED"
    plog_msg "L1 ESEC PROG FAILED"
}

