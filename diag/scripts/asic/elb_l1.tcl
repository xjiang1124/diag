# 68.41
set slot_list [list 1 2 3 4 5 6 7 8 9 10]
set sn_list [list FLM21190001 FLM2119000D FLM21190000 FLM2119001E FLM21190019 FLM21190002 FLM2119001C FLM21190011 FLM2119000D FLM21190006]

# 68.214
set slot_list [list 1 2 3 4 5 6 7 8 9 10]
set sn_list [list FLM21190022 FLM2119000E FLM21190016 FLM2119000F FLM2119001A FLM21190001 FLM21190026 FLM21190013 FLM21190030 FLM21190004]

# 68.41
set slot_list [list 1 2 3 4 5 6 7 8 9 10]
set sn_list [list FLM21190006 FLM2119000D FLM2119001C FLM21190002 FLM21190019 FLM2119001E FLM21190000 FLM21190001 FLM2119000C FLM21190009]

set len [llength $slot_list]

for {set idx 0} {$idx < $len} {incr idx} {
    set slot [lindex $slot_list $idx]
    set sn [lindex $sn_list $idx]
    diag_open_j2c_if 10 $slot

    plog_msg "=== Slot $slot ==="
    #elb_l1_screen_diag $sn 10 $slot
    elb_l1_screen_diag $sn 10 $slot nod_550 0 0 127.0.0.1 0 1 0 1 1 1600 3200 0 normal 0 1 1

    diag_close_j2c_if 10 $slot
}
