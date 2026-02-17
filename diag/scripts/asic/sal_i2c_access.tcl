#! /usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {slot.arg       ""          "Slot number"}
    {vmarg.arg      "none"      "Voltage margin"}
    {arm_running.arg "no"       "Is ARM in uboot loaded before running test? (yes = sets protomode)"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }
parray arg

proc sal_rtc_access_test {} {
    # do a software reset
    sal_smbus_write_byte_data 2 0x51 0x2F 0x2C
    after 1000
    # read stop_en bit
    set stop_en [sal_smbus_read_byte_data 2 0x51 0x2E]
    plog_msg "stop_en: $stop_en"
    set secondPre [sal_smbus_read_byte_data 2 0x51 1]
    set secondPre [expr ($secondPre & 0xF) + (($secondPre >> 4) & 7) * 10]
    plog_msg "pre: $secondPre"
    after 3000
    set secondPost [sal_smbus_read_byte_data 2 0x51 1]
    set secondPost [expr ($secondPost & 0xF) + (($secondPost >> 4) & 7) * 10]
    plog_msg "post: $secondPost"
    if {$secondPost < $secondPre} {
        set secondPost [expr {$secondPost + 60}]
    }
    set diff [expr $secondPost - $secondPre]
    if {$diff < 2 || $diff > 4} {
        plog_err "RTC access test failed, expected time difference: 3, actual: $diff"
    }
}

proc sal_rc19008_access_test {} {
    set cpld_id [ssi_cpld_read 0x80]
    set pcb_rev [ssi_cpld_read 0x81]
    set val [sal_smbus_read_word 2 0x6c 6]
    set dev_id [expr ($val >> 8) & 0xFF]
    plog_msg "rc19008 devid read: [format "0x%x" $dev_id]"
    if {($cpld_id == "0x67" && $pcb_rev == "0x01")} {
        if {$dev_id != 0x84} {
            plog_err "RC19008 access test failed, exp: 0x84, act: [format "0x%x" $dev_id]"
        }
    } else {
        if {($dev_id != 0x88) && ($dev_id != 0x8)} {
            plog_err "RC19008 access test failed, exp: 0x88 or 0x08, act: [format "0x%x" $dev_id]"
        }
    }
}

proc sal_rc19004_access_test {} {
    set val [sal_smbus_read_word 2 0x6f 6]
    set dev_id [expr ($val >> 8) & 0xFF]
    plog_msg "rc19004 devid read: [format "0x%x" $dev_id]"
    if {($dev_id != 0x84) && ($dev_id != 0x4)} {
        plog_err "RC19004 access test failed, exp: 0x84 or 0x04, act: [format "0x%x" $dev_id]"
    }
}

source /home/diag/diag/scripts/asic/sal_diag_utils.tcl

set ASIC_SRC $::env(ASIC_SRC)
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set slot $slot
set port $slot
set ::slot $slot
set ::port $port

# start logfile
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set log_file $ASIC_SRC/ip/cosim/tclsh/sal_i2c_access_SLOT${slot}_${cur_time}.log
plog_stop
plog_start $log_file 1000000000

plog_msg "Opening j2c"
set err_cnt_init [ plog_get_err_count ]
exec jtag_accpcie_salina clr $slot
exec fpgautil spimode $slot off
sal_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]
if { $arm_running == "no" } { reset_to_proto_mode }
sal_set_vmarg $vmarg

# run test
sal_rtc_access_test
sal_rc19008_access_test
sal_rc19004_access_test
diag_close_j2c_if $port $slot

# close
plog_stop
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt  [ expr ( $err_cnt_fnl - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "I2C ACCESS TEST FAILED"
    exit -1
} else {
    plog_msg "I2C ACCESS TEST PASSED"
    exit 0
}
