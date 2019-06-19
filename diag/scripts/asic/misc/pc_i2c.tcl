set slot 9
set num_ite 3
plog_start pc_i2c.log
diag_open_j2c_if 10 $slot
for {set ite 0} {$ite < $num_ite} {incr ite} {
    plog_msg "=== Starting ITE $ite"
    rst_arm0_set
    ssi_cpld_write 0x20 0x0
    cap_power_cycle_thro_gpio3 10 $slot
    sleep 2
    diag_close_j2c_if 10 $slot
    
    diag_open_j2c_if 10 $slot
    rst_arm0_set
    plog_msg "P000"
    cap_ic_setup 2
    plog_msg "P001"
    #set err_cnt [ cap_get_myerr_cnt [list cap_get_vin vdd] 1 1 1 ]
    set err_cnt [ cap_get_myerr_cnt [list cap_set_vmarg "normal"] 1 1 1 ]
    if {$err_cnt != 0} {
        break
    }
    plog_msg "P002"
    plog_msg "=== Ending ITE $ite"
}
diag_close_j2c_if 10 $slot
plog_stop
