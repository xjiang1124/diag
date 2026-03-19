#! /usr/bin/tclsh
puts "argv: $argv"

set sn       [lindex $argv 0]
# reuse slot as vulcano_index for Vulsei
set slot     [lindex $argv 1]
set int_lpbk [lindex $argv 2]
set vmarg    [lindex $argv 3]
set esecEn   [lindex $argv 4]
set logEn    [lindex $argv 5]
set pct      [lindex $argv 6]
set skip_l1_report_mode   [lindex $argv 7]
set skip_serdes_tests     [lindex $argv 8]
set tcl_path [lindex $argv 9]
set test_list [lindex $argv 10]
set port 10

if {$logEn == ""} {
    set logEn 1
}

puts "sn: $sn; slot: $slot; int_lpbk: $int_lpbk; vmarg: $vmarg; esecEn: $esecEn; logEn: $logEn; \
      skip_l1_report_mode: $skip_l1_report_mode; skip_serdes_tests: $skip_serdes_tests; \
      tcl_path: $tcl_path; test_list: $test_list"
set err_cnt 0
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

set MTP_TYPE $::env(MTP_TYPE)
set ASIC_TYPE $::env(ASIC_TYPE)
set ::VEL_SHELL 0
set ::SHELL_MODE mtp
set ::MTP_SHELL 0
set ::ZMTP_SHELL 0
set ::JCS_SHELL 0
set ::ts_present 0
set ::reset_cpu 0
set ::powercycle 1
set ::board_powercycle 0
set ::WS "$ASIC_SRC/ip/cosim/tclsh"

source /home/diag/diag/scripts/asic/asic_tests.tcl

cd $ASIC_LIB_BUNDLE/asic_src/ip/cosim/tclsh

set ::ZMTP_SHELL 1

set port $slot
set slot $slot

if { $test_list != ""} {
    set l1_cmd "vul_l1_screen_diag $sn 0 1 1 $int_lpbk $vmarg $esecEn $logEn $skip_l1_report_mode $skip_serdes_tests \"$test_list\""
} else {
    set l1_cmd "vul_l1_screen_diag $sn 0 1 1 $int_lpbk $vmarg $esecEn $logEn $skip_l1_report_mode $skip_serdes_tests"
}
puts $l1_cmd
source .tclrc.diag.vul
source /home/diag/diag/scripts/asic/vul_diag_utils.tcl

#set err_cnt_init [ plog_get_err_count ]

puts "Vulcano L1 Test Execution"
set ::slot $slot
set ::port $port

set ::board_rev [vul_get_board_rev]
if {$::board_rev != "vulsei"} {
    plog_err "\$::board_rev   = $::board_rev"
    exit -1
}

# Re-open the zmtpj2c interface for test execution
diag_open_zmtpj2c_if $::port $::slot

vul_die_id_print
vul_get_git_rev

set err_cn [eval $l1_cmd]

diag_close_zmtpj2c_if $::port $::slot

#set err_cnt_fnl [ plog_get_err_count ]

puts "L1 TEST DONE"
exit 0
