source .tclrc.diag.arm

set SNAKE_MODE [lindex $argv 0]
set DURATION [lindex $argv 1]

if { $SNAKE_MODE == "PCIE_LB" } {
    set SNAKE_NUM 6
    set LOG_FN "snake_pcie.log"
} elseif {$SNAKE_MODE == "HBM_LB"} {
    set SNAKE_NUM 4
    set LOG_FN "snake_hbm.log"
} else {
    plog_msg "Invalide snake mode $SNAKE_MODE"
    plog_msg "Snake Failed"
    plog_stop
    exit 0
}

plog_start $LOG_FN

set card_type $::env(CARD_TYPE)
if {$card_type == "NAPLES25"} {
    set MAC_SPEED "mac25g_ext_port2port_lpbk"
    set CORE_CLK 417.0
} elseif {$card_type == "NAPLES100"} {
    set MAC_SPEED "mac100g"
    set CORE_CLK 833.0
} else {
    set MAC_SPEED "mac100g"
    set CORE_CLK 833.0
}

set INT_LB 0
if {$card_type == "FORIO"} {
    set INT_LB 1
}

plog_msg "SNAKE_NUM: $SNAKE_NUM; INT_LB: $INT_LB; CORE_CLK: $CORE_CLK; DURATION: $DURATION; MAC_SPEED: $MAC_SPEED"

#cap_snake_test_mtp { snake_num  { pktsize 8000 } { mac_serdes_int_lpbk 1 } { hbm_speed 1600 }  { is_mtp 1 } { core_freq 833.0 } { delete_stream_cfg 1 } {duration 60} {fan_ctrl 0} {tgt_temp 105} {mac_speed "mac100g"} {is_arm 0} }
cap_snake_test_mtp $SNAKE_NUM 8000 $INT_LB 1600 1 $CORE_CLK 1 $DURATION 0 105 $MAC_SPEED 1

plog_msg "Snake Done"

plog_stop

