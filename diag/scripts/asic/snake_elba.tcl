source .tclrc.diag.elb.arm.nointv

set SNAKE_MODE [lindex $argv 0]
set DURATION [lindex $argv 1]
set INT_LPBK [lindex $argv 2]

set SNAKE_MODE [string tolower $SNAKE_MODE]

if { $SNAKE_MODE == "hod" } {
    set arm_freq 3000
} elseif {$SNAKE_MODE == "nod"} {
    set arm_freq 2000
} else {
    plog_msg "Invalide snake mode $SNAKE_MODE"
    plog_msg "Snake Failed"
    plog_stop
    exit 0
}

set LOG_FN "elba_snake.log"
plog_start $LOG_FN

plog_msg "SNAKE_MDOE: $SNAKE_MODE; DURATION: $DURATION"

elb_appl_set_srds_int_timeout 5000
sleep 1
set volt_mode $SNAKE_MODE

#set core_freq {}.0".format(core_freq)
#set arm_freq {}".format(arm_freq)
set core_freq1 [elb_core_freq_for_mode $volt_mode]
set stg_freq  [elb_stg_freq_for_mode $volt_mode]
set eth_freq  900
elb_set_freq $core_freq1
elb_soc_stg_pll_init 0 0 $stg_freq
elb_mm_eth_pll_init  0 0 $eth_freq
elb_top_sbus_cpu_${arm_freq} 0 0
get_freq
elb_top_sbus_get_cpu_freq  0 0

elb_snake_test_mtp 6 4096 $INT_LPBK 1 $core_freq1 1 $DURATION

plog_msg "Snake Done"
plog_msg "Snake Done"

plog_stop

