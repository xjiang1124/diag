#! /usr/bin/tclsh
puts "argv: $argv"

set sn       [lindex $argv 0]
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

set ::MTP_SHELL 1
#set uut "UUT_$slot"
#set card_type $::env($uut)
#puts "card type: $card_type; UUT: $uut"

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

set err_cnt_init [ plog_get_err_count ]

puts "Vulcano L1"
set ::slot $slot
set ::port $port
set ::cpld_rev_major [vul_cpld_rd 0x0]
set ::cpld_rev_minor [vul_cpld_rd 0x1]
set ::cpld_rev_code [vul_get_cpld_rev_code $::cpld_rev_major $::cpld_rev_minor]

set ::board_rev [vul_get_board_rev]
if {${::board_rev} eq "board-other"} {
    plog_err "Failed to get board_rev, exit"
    exit -1
}

if {${::board_rev} eq "mortaro" || ${::board_rev} eq "saraceno"} {
    plog_msg "config MTP mode register"
    exec sucutil exec -s $::slot -c "cpld_reg write 0xd 0x40"
    plog_msg "config QSPI mux"
    set config_mux_fail 0
    if {[catch {set output [exec sucutil exec -s $::slot -c "gpio conf pb 0 o0"]}]} {
        set config_mux_fail 1
    }
    plog_msg $output
    # Strip ANSI codes and check for content
    set clean_output [regsub -all {\x1b\[[0-9;]*[a-zA-Z]} $output ""]
    if { [regexp {\[INFO\]\s+\[.+\]\s+\S} $clean_output] } {
        set config_mux_fail 1
    }
    if {$config_mux_fail == 1} {
        plog_err "Failed to config QSPI mux, exit"
        exit -1
    }
}

diag_close_j2c_if $::port $::slot
diag_open_j2c_if $::port $::slot

if {[vul_test_card_is_up] != 1} {
    plog_err "vul_test_card_is_up check failed, exit"
    diag_close_j2c_if $::port $::slot
    exit -1
}

plog_msg "J2C sanity check 1"
if {![mtp_shell_sanity_check $powercycle]} {
    diag_close_j2c_if $::port $::slot
    exit -1
}

vulcano_setup 0

if {$reset_cpu} {
    plog_msg "Running vul_card_rst 1 0"
    vul_card_rst 1 0
}

plog_msg "Running vul_pll_fix"
vul_pll_fix
plog_msg "Running vul_vt_init 0"
vul_vt_init 0

plog_msg "J2C sanity check 2"
if {![mtp_shell_sanity_check $powercycle]} {
    diag_close_j2c_if $::port $::slot
    exit -1
}

plog_msg "Setting the Serdes PN swap file for card:$::board_rev"
vul_set_serdes_pn_swap_file

vul_die_id_print
vul_get_git_rev

set err_cn [eval $l1_cmd]

diag_close_j2c_if $::port $::slot

set err_cnt_fnl [ plog_get_err_count ]

# Print twice for DSP to capture signature
#if { $err_cnt_init != $err_cnt_fnl || $err_cn != 0 } {
#    puts "L1 TEST FAILED"
#    puts "L1 TEST FAILED"
#    exit -1
#} else {
#    puts "L1 TEST PASSED"
#    puts "L1 TEST PASSED"
#    exit 0
#}
puts "L1 TEST DONE"
exit 0
