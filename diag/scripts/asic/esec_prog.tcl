# !/usr/bin/tclsh
#
#package require cmdline

set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

source ./cmdline.tcl


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
    {fw_ptr.arg     ""              "FW image pointer file"}
    {esec_1.arg     ""              "Esecure image 1"}
    {esec_2.arg     ""              "Esecure image 2"}
    {host_1.arg     ""              "Host image 1"}
    {host_2.arg     ""              "Host image 2"}
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
set fw_ptr      $options(fw_ptr)
set esec_1      $options(esec_1)
set esec_2      $options(esec_2)
set host_1      $options(host_1)
set host_2      $options(host_2)

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
    plog_start read_pub_ek_${sn}_slot${slot}.log
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
    plog_msg "sn: $sn; slot: $slot; fn: $fn"
    plog_start puf_enroll_${sn}_slot${slot}.log
    if {$fn == ""} {
        plog_err "File name can not be empty"
        plog_stop
        return -1
    }
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    if {$card_type == "NAPLES25"} {
        set freq 417
    } else {
        set freq 833
    }
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200
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
    plog_msg "sn: $sn; slot: $slot; cm_file: $cm_file; sm_file: $sm_file"
    plog_start otp_init_cm_${sn}_slot${slot}.log
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

proc post_check { sn slot } {
    plog_start post_check_${sn}_slot${slot}.log

    cap_open_if 10 $slot
    regrd 0 0x6a000000

    set ret [cap_secure_post_check 10 10 $slot]
    cap_close_if 10 $slot
    plog_stop
    return $ret
}

proc show_status { sn slot } {
    plog_start show_status_${sn}_slot${slot}.log

    cap_open_if 10 $slot
    regrd 0 0x6a000000

    cap_show_esec_pins
    cap_dump_cpld_sts_spi
    cap_dump_cpld_sts_smb $slot

    cap_close_if 10 $slot
    plog_stop
    return 0
}

proc img_prog {slot fw_ptr esec_1 esec_2 host_1 host_2} {
    plog_start puf_enroll_slot${slot}.log

    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    if {$card_type == "NAPLES25"} {
        set freq 417
    } else {
        set freq 833
    }
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200

    set ret [cap_prog_qspi $fw_ptr 0x70010000]
    if {$ret != 0} {
        plog_msg "Failed to program fw_ptr"
        return $ret
    }
    set ret [cap_prog_qspi $esec_1 0x70020000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_1"
        return $ret
    }
    set ret [cap_prog_qspi $esec_2 0x70040000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_2"
        return $ret
    }
    set ret [cap_prog_qspi $host_1 0x70060000]
    if {$ret != 0} {
        plog_msg "Failed to program host_1"
        return $ret
    }
    set ret [cap_prog_qspi $host_2 0x70080000]
    if {$ret != 0} {
        plog_msg "Failed to program host_2"
        return $ret
    }

    plog_stop
    return $ret
}

proc efuse_test {slot} {
    set ret 0
    set bit_loc 127

    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    if {$card_type == "NAPLES25"} {
        set freq 417
    } else {
        set freq 833
    }
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200

    cpu_force_global_flags 1
    set bit_read_back [cap_efuse_get_bit $bit_loc]
    if {$bit_read_back == 1} {
        plog_msg "Efuse bit $bit_loc is already programmed; read back $bit_read_back"
    }

    cap_efuse_set_bit $bit_loc
    set bit_read_back [cap_efuse_get_bit $bit_loc]
    if {$bit_read_back != 1} {
        plog_err "Failed to valid efuse bit; read back $bit_read_back"
        set ret -1
    }
    diag_close_j2c_if 10 $slot
    return $ret
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
plog_msg "stage: $stage"
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
    "IMG_PROG" {
        set ret [img_prog $slot $fw_ptr $esec_1 $esec_2 $host_1 $host_2]
    }
    "EFUSE_TEST" {
        set ret [efuse_test $slot]
    }
    "POST_CHECK" {
        set ret [post_check $sn $slot]
    }
    "SHOW_STS" {
        set ret [show_status $sn $slot]
    }

    default {
        plog_msg "Invalide stage: $stage"
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
    plog_msg "ESEC PROG PASSED"
    plog_msg "ESEC PROG PASSED"
} else {
    plog_msg "ESEC PROG FAILED"
    plog_msg "ESEC PROG FAILED"
}

