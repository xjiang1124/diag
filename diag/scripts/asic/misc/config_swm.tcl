set slot_list {1 3 5 7 9}
set slot_list {6}

catch {turn_on_slot.sh off all}

foreach slot $slot_list {
    plog_msg "=== Slot: $slot ==="
    catch {turn_on_slot.sh on $slot}
    sleep 30
    
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    cap_prog_qspi u-boot.img.hex
    diag_close_j2c_if 10 $slot

    catch {turn_on_slot.sh off $slot}
}
