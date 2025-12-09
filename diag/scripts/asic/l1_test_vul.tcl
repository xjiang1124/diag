#! /usr/bin/tclsh
puts "argv: $argv"

set sn       [lindex $argv 0]
set slot     [lindex $argv 1]
set int_lpbk [lindex $argv 2]
set vmarg    [lindex $argv 3]
set esecEn   [lindex $argv 4]
set logEn    [lindex $argv 5]
set pct      [lindex $argv 6]
set joo      [lindex $argv 7]
set prbslt   [lindex $argv 8]
set tcl_path [lindex $argv 9]
set port 10

if {$logEn == ""} {
    set logEn 1
}

puts "sn: $sn; slot: $slot; int_lpbk: $int_lpbk; vmarg: $vmarg; pct: $pct; joo: $joo; esecEn: $esecEn; logEn: $logEn; prbslt:$prbslt; tcl_path: $tcl_path"
set err_cnt 0
if { $tcl_path != "" } {
    set ASIC_LIB_BUNDLE "$tcl_path"
} elseif { $::env(ASIC_LIB_BUNDLE) != "" } {
    set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
} else {
    set ASIC_LIB_BUNDLE "/home/diag/diag/asic"
}
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set LD_LIBRARY_PATH "$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:${::env(LD_LIBRARY_PATH)}"

set MTP_TYPE $::env(MTP_TYPE)
set ASIC_TYPE $::env(ASIC_TYPE)
set ::VEL_SHELL 0

source /home/diag/diag/scripts/asic/asic_tests.tcl

set G_SLOT $slot
set arm_freq 3000

puts "sn: $sn; slot: $slot"
puts "ASIC_LIB_BUNDLE: $ASIC_LIB_BUNDLE"
puts "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
cd $ASIC_SRC/ip/cosim/tclsh

if {($MTP_TYPE == "MTP_PANAREA")} {
    set uut "UUT_$slot"
    set card_type $::env($uut)
    puts "card type: $card_type; UUT: $uut"

    set port $slot
    set slot $slot

    #set l1_cmd "vul_l1_screen_diag $sn 0 1 0 1 $vmarg $esecEn $logEn $prbslt"
    set l1_cmd "vul_l1_screen_diag $sn"
    source .tclrc.diag.vul
    #source /home/diag/diag/scripts/asic/vul_diag_utils.tcl
} else {
   plog_err "INVALID PLATFORM/MTP TYPE: $MTP_TYPE\n"
   exit -1
}

set err_cnt_init [ plog_get_err_count ]

if {$ASIC_TYPE == "VULCANO"} {
    puts "Vulcano L1"
    set ::slot $slot
    set ::port $port
    vul_j2c

    puts "_msrd"
    set rtn [eval _msrd]
    puts $rtn

    set ::board_rev [vul_get_board_rev]

    plog_msg "calling vul_pll_fix"
    vul_pll_fix
    after 10000

    #reset_to_proto_mode
    #vul_print_voltage_temp
    vul_print_die_id
    #plog_msg "Measuring frequencies:"
    #vul_get_freq

    set err_cn [eval $l1_cmd]

    diag_close_j2c_if $port $slot
}

set err_cnt_fnl [ plog_get_err_count ]

# Print twice for DSP to capture signature
if { $err_cnt_init != $err_cnt_fnl || $err_cn != 0 } {
    puts "L1 TEST FAILED"
    puts "L1 TEST FAILED"
    exit -1
} else {
    puts "L1 TEST PASSED"
    puts "L1 TEST PASSED"
    exit 0
}

