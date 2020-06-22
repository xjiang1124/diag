set slot_list [list 2]

set mac_speed "mac25g"
set duration 60
set lpbk 0
set chamber_temp 25
set freq 417

foreach slot $slot_list {
    plog_start naples25_snake.slot$slot.chamber$chamber_temp.log
    plog_msg "== Slot $slot ==="
    diag_open_j2c_if 10 $slot
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200
    set err_cnt [cap_get_myerr_cnt [list cap_snake_test_mtp 4 8000 $lpbk 1600 1 $freq 1 $duration 0 105 $mac_speed] 1 1 1]
    if {$err_cnt == 0} {
        plog_msg "=== Slot $slot PASSED ==="
    } else {
        plog_msg "=== Slot $slot FAILED $err_cnt ==="
    }
    diag_close_j2c_if 10 $slot
    plog_stop
}
