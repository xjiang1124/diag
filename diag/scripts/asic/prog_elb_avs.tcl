set slot_list [list 1 2 3 5 6 7 8 9]
set slot_list [list 1 2 4 5 6 7 8 9]
set slot_list [list 1]

#set arm_vdd_list [list arm vdd arm vdd]
#set freq_list [list 3000 1100 2000 833]
set arm_vdd_list [list arm vdd]
set freq_list [list 3000 833]

plog_start "elba_avs.log"
foreach slot $slot_list {
    diag_open_j2c_if 10 $slot

    plog_msg "=== Slot $slot ==="
    for {set idx 0} {$idx < 2} {incr idx} {
        set arm_vdd [lindex $arm_vdd_list $idx]
        set freq [lindex $freq_list $idx]
        plog_msg "=== $arm_vdd; $freq ==="
        elb_set_avs $arm_vdd $freq 0 0
        elb_print_voltage_temp
    }

    diag_close_j2c_if 10 $slot
}
plog_stop
