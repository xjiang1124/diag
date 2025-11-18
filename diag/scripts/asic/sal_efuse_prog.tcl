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
set hsm_rn [lindex $argv 1]
set dry_run [lindex $argv 2]

set card_type $::env(CARD_TYPE)
set LOG_FN ${card_type}_slot${slot}_pac_efuse_prog.log

set port $slot

plog_start $LOG_FN

plog_msg "hsm_rn: $hsm_rn"

exec fpgautil spimode $slot off

set in_err [plog_get_err_count]

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

diag_open_j2c_if $port $slot
puts "_msrd"
set rtn [eval _msrd]
puts $rtn

set out_err [plog_get_err_count]
if { $in_err != $out_err || $rtn != 1 } {
    plog_err "EFUSE CHECK WITH J2C ERROR"
    plog_err "EFUSE PROG FAILED"
    diag_close_j2c_if $port $slot
    plog_stop
    return -1
}

set in_err [plog_get_err_count]
#sal_arm_reset
reset_to_proto_mode cold
sal_print_voltage_temp_from_j2c

# Check if efuse[23:22] is already set
set bit22 [sal_fuse_get_bit 0 22 0]
set bit23 [sal_fuse_get_bit 0 23 0]
if { $bit22 != 0 || $bit23 != 0 } {
    plog_msg "Efuse PAC already been programmed, exit here"
    sal_fuse_dump
    plog_msg "EFUSE PROG PASSED"
    diag_close_j2c_if $port $slot
    plog_stop
    return 0
} else {
    set pac_sum 0
    for {set i 0} {$i < 8} {incr i} {
        set idx [expr $i + 4]
        set fuse_val [sal_fuse_get_line 0 $idx 0]
        set pac_sum [expr {$fuse_val | $pac_sum}]
        plog_msg "fuse_val($i): $fuse_val"
    }
    if { $pac_sum != 0 } {
        plog_err "PAC is programmed but read protection is not"
        sal_fuse_dump
        plog_err "EFUSE PROG FAILED"
        diag_close_j2c_if $port $slot
        plog_stop
        return 0
    }
}

set in_err [plog_get_err_count]
set pac_rn [sal_get_pac $hsm_rn]
if { $pac_rn == -1 } {
    plog_err "EFUSE PROG FAILED"
    diag_close_j2c_if $port $slot
    return
}

set str_start 0
set str_end 7
set len [string length $pac_rn]

for { set i 0 } { $str_start < $len } { incr i } {
    lappend list_result [ string range $pac_rn $str_start $str_end ]
    incr str_start 8
    incr str_end 8
}

set i 0
foreach n $list_result {
    set pac_val($i) "0x$n"
    incr i 1
}

sal_fuse_vddq_enable
set idx 4
for {set i 0} {$i < 8 } {incr i} {
    if { $dry_run  == 0 } {
        plog_msg "set fuse line $idx with value $pac_val($i)"
        sal_fuse_set_line 0 $idx $pac_val($i)
        incr idx 1
    }
}

for {set i 0} {$i < 8} {incr i} {
    set idx [expr $i + 4]
    set fuse_read($i) [sal_fuse_get_line 0 $idx 0]
    if { "$fuse_read($i)" != "$pac_val($i)" } {
        plog_err "failed to set fuse value read: $fuse_read($i) expected: $pac_val($i)"
        plog_err "EFUSE PROG FAILED"
        sal_fuse_dump
        diag_close_j2c_if $port $slot
        plog_stop
        return
    }
}

if { $dry_run  == 0 } {
    sal_fuse_vddq_enable
    plog_msg "set read disable bit 22"
    sal_fuse_set_bit 0 22 0 
    plog_msg "set read disable bit 23"
    sal_fuse_set_bit 0 23 0 
    sal_fuse_vddq_disable
}

set bit [sal_fuse_get_bit 0 22 0]
if { $bit != 1 } {
    plog_err "failed to set read disable bit 22"
    sal_fuse_dump
    plog_err "EFUSE PROG FAILED"
    diag_close_j2c_if $port $slot
    plog_stop
    return
}
set bit [sal_fuse_get_bit 0 23 0]
if { $bit != 1 } {
    plog_err "failed to set read disable bit 23"
    sal_fuse_dump
    plog_err "EFUSE PROG FAILED"
    diag_close_j2c_if $port $slot
    plog_stop
    return
}

set out_err [plog_get_err_count]
sal_fuse_dump

if { $in_err != $out_err } {
    plog_err "EFUSE PROG FAILED"
    plog_err "EFUSE PROG FAILED"
} else {
    plog_msg "EFUSE PROG PASSED"
    plog_msg "EFUSE PROG PASSED"
}

diag_close_j2c_if $port $slot
plog_stop

