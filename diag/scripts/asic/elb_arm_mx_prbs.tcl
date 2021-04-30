source .tclrc.diag.elb.arm.nointv

set DURATION [lindex $argv 0]
set INT_LB   [lindex $argv 1]

set card_type $::env(CARD_TYPE)
set LOG_FN ${card_type}_PRBS_MX.log

plog_start $LOG_FN

plog_msg "MX PRBS DURATION: $DURATION, INT_LB: $INT_LB"

set in_err [plog_get_err_count]

set pod 0
set aod 1
set pcie_upload 0
elb_set_sbus_clk_divider 6 $aod $pod 1
elb_upload_sbus_mstr _undefined_ $aod $pod

elb_bh_upload_ucode [elb_get_bh_ucode] 1 0
elb_aapl_rom_crc_chk 0x308

set lane_list [elb_get_mx_lane_list]
elb_mx_srds_prbs $lane_list $DURATION 25g,50g $INT_LB

set out_err [plog_get_err_count]

if { $in_err != $out_err } {
    plog_msg "MX PRBS FAILED"
} else {
    plog_msg "MX PRBS PASSED"
}

plog_stop

