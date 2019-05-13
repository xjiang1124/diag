# !/usr/bin/tclsh
#
#package require cmdline

set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

source $ASIC_SRC/ip/cosim/tclsh/cmdline.tcl


set parameters {
    {sn.arg         "Slotxxx"       "Serial Number"}
    {slot.arg       ""              "Slot number"}
    {use_zmq.arg    0               "Use ZMQ"}
    {zmq_srv_ip.arg ""              "MTP IP"}
    {zmq_port.arg   "55000"         "ZMQ port"}
    {stage.arg      ""              "Esecure program stage"}
    {fn.arg         ""              "File name"}
    {cm_file.arg    ""              "CM file"}
    {sm_file.arg    ""              "SM file"}
}

set usage "- Usage:"
if {[catch {array set options [cmdline::getoptions ::argv $parameters $usage]}]} {
    puts [cmdline::usage $parameters $usage]
    exit
} else {
    parray options
}

set sn          $options(sn)
set slot        $options(slot)
set use_zmq     $options(use_zmq)
set zmq_srv_ip  $options(zmq_srv_ip)
set zmq_port    $options(zmq_port)
set stage       $options(stage)
set fn          $options(fn)
set cm_file     $options(cm_file)
set sm_file     $options(sm_file)

puts "slot: $slot"

if { $use_zmq != 0 } {
    if { $zmq_srv_ip == "" || $zmq_port == ""} {
        error "Need ZMQ SRV IP and port args"
        exit
    }
}

if { $slot == "" } {
    error "Need slot arg"
    exit
}

if {$use_zmq != 0} {
    set zmq_conn "tcp://${arg(zmq_srv_ip)}:${arg(zmq_port)}/"
    puts "zmq_conn: $zmq_conn"
}

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag

proc read_pub_ek { sn slot fn } {
    plog_start read_pub_ek_${sn}_${slot}.log
    if {$fn == ""} {
        plog_err "File name can not be empty"
        plog_stop
        return -1
    }
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000

    set pub_ek [cap_chlng_read_pub_ek_str]
    set fp [open $fn w]
    puts -nonewline $fp $pub_ek
    close $fp

    plog_stop
    return 0
}

proc puf_enroll { sn slot fn } {
    puts "sn: $sn; slot: $slot; fn: $fn"
    plog_start puf_enroll_${sn}_${slot}.log
    if {$fn == ""} {
        plog_err "File name can not be empty"
        plog_stop
        return -1
    }
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    cap_jtag_chip_rst 10 $slot
    ssi_cpld_write 0x29 0x80
    cap_set_esec_enable_pin
    cap_power_cycle_chk 25 10 $slot
    
    set err_cnt [cap_get_myerr_cnt cap_chlng_enroll_puf_str 0 1 1]

    set pub_ek [cap_chlng_read_pub_ek_str]
    set fp [open $fn w]
    puts -nonewline $fp $pub_ek
    close $fp

    plog_stop
    return $err_cnt
}

proc otp_init { sn slot cm_file sm_file } {
    puts "sn: $sn; slot: $slot; cm_file: $cm_file; sm_file: $sm_file"
    plog_start otp_init_cm_${sn}_${slot}.log
    if {$cm_file == "" || $sm_file == ""} {
        plog_err "File name can not be empty"
        plog_stop
        return -1
    }
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000

    set cmd_cm [list cap_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
    set cmd_sm [list cap_chlng_init_otpf_str 0 0 1 0 70  $sm_file]

    set err_cnt_cm [cap_get_myerr_cnt $cmd_cm 0 1 1]
    set err_cnt_sm [cap_get_myerr_cnt $cmd_sm 0 1 1]

    set err_cnt [expr {$err_cnt_cm + $err_cnt_sm}]

    plog_stop
    return $err_cnt
}

if { $use_zmq == 1 } {
    set ::SSI_OPERATION_TIMEOUT_S 10
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot

    #diag_open_zmq_if $zmq_conn $slot
} else {
    diag_close_j2c_if 10 $slot
}

set stage [string toupper $stage]
puts "stage: $stage"
switch $stage {
    "PUF_ENROLL" {
        set ret [puf_enroll $sn $slot $fn]
    }
    "READ_PUB_EK" {
        set ret [read_pub_ek $sn $slot $fn]
    }
    "OTP_INIT" {
        set ret [otp_init $sn $slot $cm_file $sm_file]
    }
    default {
        puts "Invalide stage: $stage"
        set ret -1
    }
}

if { $use_zmq == 1 } {
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot
} else {
    diag_close_j2c_if 10 $slot
}

# Print twice for DSP to capture signature
if {$ret == 0} {
    puts "ESEC PROG PASSED"
    puts "ESEC PROG PASSED"
} else {
    puts "ESEC PROG FAILED"
    puts "ESEC PROG FAILED"
}

