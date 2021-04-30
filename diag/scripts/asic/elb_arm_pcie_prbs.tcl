source .tclrc.diag.elb.arm.nointv

set DURATION [lindex $argv 0]

set card_type $::env(CARD_TYPE)
set LOG_FN ${card_type}_PRBS_PCIE.log

plog_start $LOG_FN

plog_msg "PCIEPRBS DURATION: $DURATION"

set in_err [plog_get_err_count]

elb_appl_set_srds_int_timeout 50000
set core_freq [get_freq]
set card_type ORTANO
set mtp_rev 04
set is_arm 1
elb_pcie_sbus_prbs_test $core_freq $card_type $mtp_rev $DURATION 16g 0 prbs31 $is_arm
set out_err [plog_get_err_count]

if { $in_err != $out_err } {
    plog_msg "PCIE PRBS FAILED"
} else {
    plog_msg "PCIE PRBS PASSED"
}

plog_stop

