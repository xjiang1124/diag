#! /usr/bin/tclsh
puts "argv: $argv"

# reuse slot as vulcano_index for Vulsei
set slot     [lindex $argv 0]
set tcl_path [lindex $argv 1]
set port 10

puts "slot: $slot; tcl_path: $tcl_path"
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
puts "power on Vulcano"
catch "exec sucutil vul_power_on -i $slot " catch_error
puts "wait for 2 seconds"
after 2000

set port $slot
set slot $slot

source .tclrc.diag.vul
source /home/diag/diag/scripts/asic/vul_diag_utils.tcl

set err_cnt_init [ plog_get_err_count ]

set ::slot $slot
set ::port $port

set ::board_rev [vul_get_board_rev]
if {$::board_rev != "vulsei"} {
    plog_err "\$::board_rev   = $::board_rev"
    puts "L1 SANITY CHECK FAILED"
    exit -1
}

diag_close_zmtpj2c_if $::port $::slot
diag_open_zmtpj2c_if $::port $::slot

if {[vul_test_card_is_up] != 1} {
    puts "L1 SANITY CHECK FAILED"
    diag_close_zmtpj2c_if $::port $::slot
    exit -1
}
plog_msg "J2C sanity check 1"
if {![mtp_shell_sanity_check $powercycle]} {
    puts "L1 SANITY CHECK FAILED"
    diag_close_zmtpj2c_if $::port $::slot
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
    puts "L1 SANITY CHECK FAILED"
    diag_close_zmtpj2c_if $::port $::slot
    exit -1
}

plog_msg "Setting the Serdes PN swap file for card:$::board_rev"
vul_set_serdes_pn_swap_file

diag_close_zmtpj2c_if $::port $::slot

puts "L1 SANITY CHECK PASSED"

exit 0
