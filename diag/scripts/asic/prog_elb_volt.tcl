set slot_list [list 1 2 3 4 5 6 7 8 9]
set slot_list [list 1 2 3 4 5 7 8]
set slot_list [list 4 5 7 8]

set volt_vdd 665
set volt_arm 689

plog_start "elba_avs.log"
foreach slot $slot_list {
    plog_msg "=== Slot $slot ==="
    diag_open_j2c_if 10 $slot

    _msrd
    
    # Set Volt and Dell
    set volt_mode "nod"
    set ddr_freq 3200
    set arm_freq 2000
    ## Power cycle card..
    elb_card_rst 10 $slot $volt_mode $ddr_freq $arm_freq 0 0 "" 1 1 "none"
    
    diag_open_j2c_if 0xa  $slot
    elb_set_avs_vdd 1100 0 1 $volt_vdd
    elb_set_avs_arm 3000.0 0 1 $volt_arm
    elb_get_vout vdd
    elb_get_vout arm
    diag_close_j2c_if 10 $slot
}
plog_stop
