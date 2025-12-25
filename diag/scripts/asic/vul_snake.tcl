#! /usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {slot.arg           ""                  "Slot number"}
    {vmarg.arg          "nom"               "Voltage margin high/low/nom"}
    {snake_num.arg      1                   "snake number"}
    {int_lpbk.arg       1                   "mac serdes internal loopback"}
    {duration.arg       60                  "duration"}
    {tcl_path.arg       ""                  "ASIC lib location"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit -1 }
parray arg

### initialize asic lib
set ::VEL_SHELL 0
set ::SHELL_MODE mtp
set ::MTP_SHELL 1
set ::JCS_SHELL 0
set ::ts_present 0
set ::reset_cpu 0

if { $tcl_path != "" } {
    set ASIC_LIB_BUNDLE "$tcl_path"
} elseif { $::env(ASIC_LIB_BUNDLE) != "" } {
    set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
} else {
    set ASIC_LIB_BUNDLE "/home/diag/diag/asic"
}
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set env(ASIC_LIB_BUNDLE) "$ASIC_LIB_BUNDLE"
set env(ASIC_LIB) "$ASIC_LIB_BUNDLE/asic_lib"
set env(ASIC_SRC) "$ASIC_LIB_BUNDLE/asic_src"
set env(ASIC_GEN) "$ASIC_LIB_BUNDLE/asic_src"
set env(LD_LIBRARY_PATH) "$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:${::env(LD_LIBRARY_PATH)}"
cd $ASIC_LIB_BUNDLE/asic_src/ip/cosim/tclsh
source .tclrc.diag.vul

### initialize card properties
set slot $slot
set port $slot
set ::slot $slot
set ::port $port
set uut "UUT_$slot"
set card_type $::env($uut)
plog_msg "card type: $card_type; UUT: $uut"
exec jtag_accpcie_vulcano clr $slot
vul_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]

set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "vul_snake_slot${slot}_${cur_time}.log"
plog_start $fn

set ::board_rev [vul_get_board_rev]

plog_msg "calling vul_pll_fix"
vul_pll_fix
after 10000

#set card_type [vul_get_card_type]
#set cpld_id [ vul_cpld_read 0x80 ]
#plog_msg "card_type = $card_type"
#plog_msg "cpld_id = $cpld_id"
#vul_print_die_id
vul_set_vmarg $vmarg all

plog_msg "start snake"
vul_l1_snake $snake_num 0 $int_lpbk $duration 1500
plog_msg "check result"
vul_print_pass_fail vul_l1_snake $err_cnt_init
plog_stop
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt  [ expr ( $err_cnt_fnl - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "SNAKE TEST FAILED"
    set ret -1
} else {
    plog_msg "SNAKE TEST PASSED"
    set ret 0
}
plog_msg "SNAKE TEST DONE"
diag_close_j2c_if $port $slot
exit $ret
