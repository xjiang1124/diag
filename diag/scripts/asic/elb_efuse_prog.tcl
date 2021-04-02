source .tclrc.diag.elb.arm.nointv

set hsm_rn [lindex $argv 0]

set card_type $::env(CARD_TYPE)
set LOG_FN ${card_type}_pac_efuse_prog.log

plog_start $LOG_FN

plog_msg "hsm_rn: $hsm_rn"

set in_err [plog_get_err_count]

set pac_rn [elb_get_pac $hsm_rn]
if { $pac_rn == -1} {
    plog_msg "EFUSE PROG FAILED"
    return
}

elb_fuse_prog $pac_rn

set out_err [plog_get_err_count]

if { $in_err != $out_err } {
    plog_msg "EFUSE PROG FAILED"
} else {
    plog_msg "EFUSE PROG PASSED"
}

plog_stop

