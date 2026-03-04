#! /usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {slot.arg           ""                  "Slot number"}
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
set ::ZMTP_SHELL 0
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
set ::board_rev [vul_get_board_rev]
if {${::board_rev} eq "board-other"} {
    plog_err "Failed to get board_rev, exit"
    plog_err "QSPI ERASE FAILED"
    exit
}
if {${::board_rev} eq "mortaro" || ${::board_rev} eq "saraceno"} {
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
        plog_err "QSPI ERASE FAILED"
        diag_close_j2c_if $port $slot
        exit
    }
}

vul_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]
vulcano_setup 0
plog_msg "calling vul_pll_fix"
vul_pll_fix
vul_vt_init 0
after 1000
set err_cnt_init [ plog_get_err_count ]
vul_qspi_erase 0x70100000
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt  [ expr ( $err_cnt_fnl - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "QSPI ERASE FAILED"
} else {
    plog_msg "QSPI ERASE PASSED"
}
diag_close_j2c_if $port $slot
exit
