# !/usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {slot.arg           ""                  "Slot number"}
    {vmarg.arg          "nom"              "Voltage margin"}
    {pcie_gen.arg       1                   "PCIe Gen"}
    {int_lpbk.arg       0                   "pma internal loopback (1 or 0)"}
    {runtime.arg        50                  "Run time in seconds"}
    {prbs_pattern.arg   31                  "prbs pattern"}
    {ow_refclk.arg      -1                  "ow refclk"}
    {vreg_code.arg      -1                  "vreg code"}
    {lane_inc.arg       ""                  "Lanes included"}
    {lane_exc.arg       ""                  "Lanes excluded"}
    {fw_ver.arg         ""                  "FW version"}
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
exec jtag_accpcie_vulcano clr $slot
vul_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]

set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "vul_pcie_prbs_slot${slot}_${cur_time}.log"
plog_start $fn

set ::board_rev [vul_get_board_rev]
vulcano_setup 0
vul_card_rst 1 0
plog_msg "calling vul_pll_fix"
vul_pll_fix
vul_vt_init 0
after 1000
vul_set_serdes_pn_swap_file

vul_die_id_print
vul_get_git_rev
if { $vmarg != "none" } {
    vul_set_vmarg $vmarg all
}

vul_card_rst 2 0
vul_pcie_sd_prbs_check $pcie_gen $int_lpbk $runtime $prbs_pattern $ow_refclk 0 $vreg_code $lane_inc $lane_exc $fw_ver

set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "PCIE PRBS test FAILED"
    exit -1
} else {
    plog_msg "PCIE PRBS test PASSED"
    exit 0
}
