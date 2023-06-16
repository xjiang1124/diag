# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {slot_list.arg      ""      "Slot list"}
    {mode.arg           "hod"   "ASIC mode: hod_1100/hod/nod/nod_525"}
    {type.arg           "ubootd"   "Image type"}
    {img.arg            "/home/diag/diag/scripts/asic/ubootd.img.hex"      "uboot image"}
}

array set arg [cmdline::getoptions argv $parameters]
set slot_list       $arg(slot_list)
set mode            $arg(mode)
set img             $arg(img)
set type            $arg(type)

set DIAG_DIR "/home/diag/"

puts "slot_list: $slot_list; mode: $mode"

set ASIC_LIB_BUNDLE "$DIAG_DIR/diag/asic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.elb

plog_start uboot_prog.log

set test_result [dict create]
dict append test_result "1" "NA"
dict append test_result "2" "NA"
dict append test_result "3" "NA"
dict append test_result "4" "NA"
dict append test_result "5" "NA"
dict append test_result "6" "NA"
dict append test_result "7" "NA"
dict append test_result "8" "NA"
dict append test_result "9" "NA"
dict append test_result "10" "NA"

set slot_list [split $slot_list ","]
foreach slot $slot_list {
    plog_msg "slot: $slot"

    set port [mtp_get_j2c_port $slot]
    set slot1 [mtp_get_j2c_slot $slot]
    diag_close_j2c_if $port $slot1

    plog_msg "Power cycling slot $slot"
    catch {exec /home/diag/diag/scripts/turn_on_slot.sh off $slot}
    exec sleep 2; 
    catch {exec /home/diag/diag/scripts/turn_on_slot.sh on $slot}

    diag_open_j2c_if $port $slot1
    set val [_msrd]
    if {$val != 0x1} {
        plog_err "Uboot PROG failed: slot $slot"
        dict set test_result $slot "FAIL"
        continue
    }

    elb_card_rst $port $slot1 $mode 3200 3000 0 0 "127" 0 1 normal 0 0

    set val [_msrd]
    if {$val != 0x1} {
        plog_err "Uboot PROG failed: slot $slot"
        dict set test_result $slot "FAIL"
        continue
    }

    try {
        if {$type == "env_clean"} {
            elb_erase_qspi 1024 0x7ffe0000
        } else {
            elb_prog_qspi_img $img $type
        }
    } on error {msg} {
        plog_msg $msg
        dict set test_result $slot "FAIL"
        continue
    }
    dict set test_result $slot "PASS"
    diag_close_j2c_if $port $slot1
}

plog_msg "====================="
foreach slot $slot_list {
    set result [dict get $test_result $slot]
    plog_msg "Slot $slot: $result"
}
plog_msg "====================="

plog_msg "uboot PROG DONE"

plog_stop
