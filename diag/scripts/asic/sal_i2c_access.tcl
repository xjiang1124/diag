source /home/diag/diag/scripts/asic/cmdline.tcl
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl
set usage {
    {slot.arg       ""          "Slot number"}
    {vmarg.arg      "none"      "Voltage margin"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }

set ASIC_SRC $::env(ASIC_SRC)
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl

set ::FAN_SPD 80
set ::DEVMGR devmgr_v2

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port
diag_close_j2c_if $port $slot
diag_open_j2c_if $port $slot
diag_close_j2c_if $port $slot

after 500
diag_close_ow_if $port $slot
after 500
diag_open_ow_if $port $slot
after 2000
sal_ow_axi

set dd 0
set cnt 0
while { ($dd==0) && ($cnt<10) } {
    csr_write sal0.ms.ms.cfg_ow 3
    after 500
    set dd [ rd sal0.ms.ms.cfg_ow ]
    incr cnt
}
set ret 1
if { $cnt  >= 10 } {
    plog_err "\n\n==== J2C / OW is not working.... Ping HW team\n\n"
    return
}
sal_j2c
set j2c_secure 1
#sal_ow

set val [_msrd]
if { $val != 0x1 } {
    plog_msg "OW sanity test failed!"
    exit 0
}

proc sal_rtc_access_test {} {
    set secondPre [sal_smbus_read_byte_data 2 0x51 1]
    set secondPre [expr ($secondPre & 0xF) + (($secondPre >> 4) & 7) * 10]
    plog_msg "pre: $secondPre"
    after 3000
    set secondPost [sal_smbus_read_byte_data 2 0x51 1]
    set secondPost [expr ($secondPost & 0xF) + (($secondPost >> 4) & 7) * 10]
    plog_msg "post: $secondPost"
    if {$secondPost < $secondPre} {
        $secondPost = $secondPost + 60
    }
    set diff [expr $secondPost - $secondPre]
    if {$diff < 2 || $diff > 4} {
        plog_err "RTC access test failed, expected time difference: 3, actual: $diff"
    }
}

proc sal_rc19008_access_test {} {
    set val [sal_smbus_read_word 2 0x6c 6]
    set dev_id [expr ($val >> 8) & 0xFF]
    plog_msg "rc19008 devid read: [format "0x%x" $dev_id]"
    if {$dev_id != 0x88} {
        plog_err "RC19008 access test failed, exp: 0x88, act: [format "0x%x" $dev_id]"
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

# start logfile
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set log_file $ASIC_SRC/ip/cosim/tclsh/sal_i2c_access_SLOT${slot}_${cur_time}.log
plog_stop
plog_start $log_file 1000000000
set err_cnt_init [ plog_get_err_count ]

exec fpgautil spimode $slot off
exec jtag_accpcie_salina clr $slot
sal_set_proto_mode 0
#sal_proto_mode_powerup

# set vmarg
sal_set_vmarg $vmarg

# run test
sal_rtc_access_test
sal_rc19008_access_test
sal_rc19004_access_test
diag_close_j2c_if $::slot $::port

# close
plog_stop
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt  [ expr ( $err_cnt_fnl - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "I2C ACCESS TEST FAILED"
} else {
    plog_msg "I2C ACCESS TEST PASSED"
}
exit 0