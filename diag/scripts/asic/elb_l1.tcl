set slot_list [list 1 2 3 5 6 7 8 9]
set card_no_list [list No41 No42 No43 No45 No46 No47 No48 No49]

set slot_list [list 8 9]
set card_no_list [list No48 No49]

#set slot_list [list 4 6 7 9]
#set card_no_list [list No44 No46 No43 No49]

set len [llength $slot_list]

for {set idx 0} {$idx < $len} {incr idx} {
    set slot [lindex $slot_list $idx]
    set card_no [lindex $card_no_list $idx]
    diag_open_j2c_if 10 $slot

    plog_msg "=== Slot $slot ==="
    elb_l1_screen_diag $card_no 10 $slot

    diag_close_j2c_if 10 $slot
}
