# !/usr/bin/tclsh
#
#package require cmdline

set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

source /home/diag/diag/scripts/asic/cmdline.tcl

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl

set slot [lindex $argv 0]
set hmac_file [lindex $argv 1]
set dry_run [lindex $argv 2]

set card_type $::env(CARD_TYPE)
set LOG_FN ${card_type}_hmac_efuse_prog.log

set port $slot

plog_start $LOG_FN

plog_msg "HMAC file: $hmac_file"

exec fpgautil spimode $slot off
diag_close_j2c_if $port $slot
diag_open_j2c_if $port $slot
diag_close_j2c_if $port $slot

after 1000
diag_close_ow_if $port $slot
after 1000
diag_open_ow_if $port $slot
after 1000
sal_ow_axi

csr_write sal0.ms.ms.cfg_ow 3
after 500
rd sal0.ms.ms.cfg_ow

_msrd

diag_close_ow_if $port $slot
after 1000
diag_open_j2c_if $port $slot
puts "_msrd"
set rtn [eval _msrd]
puts $rtn

#sal_arm_reset
reset_to_proto_mode cold
sal_print_voltage_temp_from_j2c

# Check if efuse[47:46] is already set
set bit46 [sal_fuse_get_bit 0 46 0]
set bit47 [sal_fuse_get_bit 0 47 0]
if { $bit46 != 0 || $bit47 != 0 } {
    plog_msg "Efuse HAM already been programmed, exit here"
    sal_fuse_dump
    plog_msg "EFUSE PROG PASSED"
    diag_close_j2c_if $port $slot
    plog_stop
    return 0
} else {
    set hmac_sum 0
    for {set i 0} {$i < 16} {incr i} {
        set idx [expr $i + 16]
        set fuse_val [sal_fuse_get_line 0 $idx 0]
        set hmac_sum [expr {$fuse_val | $hmac_sum}]
    }
    if { $hmac_sum != 0 } {
        plog_msg "HMAC is programmed but read protection is not"
        sal_fuse_dump
        plog_msg "EFUSE PROG FAILED"
        diag_close_j2c_if $port $slot
        plog_stop
        return 0
    }
}

set in_err [plog_get_err_count]
set fp [open $hmac_file r]
set hmac_str [read $fp]
close $fp
 
set str_start 0
set str_end 7
set len [string length $hmac_str]

for { set i 0 } { $str_start < $len } { incr i } {
    lappend list_result [ string range $hmac_str $str_start $str_end ]
    incr str_start 8
    incr str_end 8
}

set i 0
foreach n $list_result {
    set hmac_val($i) "0x$n"
    incr i 1
}

sal_fuse_vddq_enable
set idx 16 
for {set i 0} {$i < 16 } {incr i} {
    plog_msg "set fuse line $idx with value $hmac_val($i)"
    if { $dry_run  == 0 } {
        sal_fuse_set_line 0 $idx $hmac_val($i)
    }
    incr idx 1
}
sal_fuse_vddq_disable

sal_fuse_dump

for {set i 0} {$i < 16} {incr i} {
    set idx [expr $i + 16]
    set fuse_read($i) [sal_fuse_get_line 0 $idx 0]
    if { "$fuse_read($i)" != "$hmac_val($i)" } {
        plog_msg "failed to set fuse value read: $fuse_read($i) expected: $hmac_val($i)"
        sal_fuse_dump
        plog_msg "EFUSE PROG FAILED"
        diag_close_j2c_if $port $slot
        plog_stop
        return
    }
}

plog_msg "set read disable bit 22"
plog_msg "set read disable bit 23"
if { $dry_run  == 0 } {
    sal_fuse_vddq_enable
    sal_fuse_set_bit 0 46 0 
    sal_fuse_set_bit 0 47 0 
    sal_fuse_vddq_disable
}

set bit46 [sal_fuse_get_bit 0 46 0]
set bit47 [sal_fuse_get_bit 0 43 0]
if { $bit46 != 0 || $bit47 != 0 } {
    plog_msg "failed to set read disable bits $bit46 $bit47"
    sal_fuse_dump
    plog_msg "EFUSE PROG FAILED"
    diag_close_j2c_if $port $slot
    plog_stop
    return
}

set out_err [plog_get_err_count]

if { $in_err != $out_err } {
    plog_msg "EFUSE PROG FAILED"
    plog_msg "EFUSE PROG FAILED"
} else {
    plog_msg "EFUSE PROG PASSED"
    plog_msg "EFUSE PROG PASSED"
}

diag_close_j2c_if $port $slot
plog_stop

