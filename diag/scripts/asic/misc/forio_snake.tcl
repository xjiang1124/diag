#set slot_list [list 4 5 6]
set slot_list [list 4 6]
#set slot_list [list 4]
set mac_speed "mac100g"
set duration 600
set lpbk 1
set chamber_temp 50

foreach slot $slot_list {
    plog_start forio_snake.slot$slot.chamber$chamber_temp.log
    plog_msg "== Slot $slot ==="
    diag_open_j2c_if 10 $slot
    cap_jtag_chip_rst 10 $slot
    set err_cnt [cap_get_myerr_cnt [list cap_snake_test_mtp 6 8000 $lpbk 1600 1 833 1 $duration 0 105 $mac_speed] 0 1 1]
    if {$err_cnt == 0} {
        plog_msg "=== Slot $slot PASSED ==="
    } else {
        plog_msg "=== Slot $slot FAILED $err_cnt ==="
    }
    diag_close_j2c_if 10 $slot
    plog_stop
}
