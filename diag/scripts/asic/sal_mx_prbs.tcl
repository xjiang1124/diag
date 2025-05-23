#! /usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl

set usage {
    {sn.arg                     ""                      "Serial number"}
    {slot.arg                   ""                      "Slot number"}
    {vmarg.arg                  "none"                  "Voltage margin"}
    {int_lpbk.arg               "no"                    "Internal loopback"}
    {cable_len.arg              "0"                     "Cable length: 0/50(0.5m)/100(1m)/200(2m)"}
    {media_type.arg             "CU"                    "Cable type: CU/Fiber"}
    {speed.arg                  "100"                   "Transceiver speed: 25/50/100"}
    {lt.arg                     "1"                     "Link training: 1=yes / 0=no"}
    {logEn.arg                  "yes"                   "Save to logfile"}
    {tcl_path.arg               ""                      "ASIC lib location"}
    {si_json_file.arg           "serdes_malfa.json"     "Serdes settings file (no-LT)"}
    {mx2mx.arg                  "no"                    "Cable test card-to-card. Cards can be in different MTP. Open different sessions for each slot."}
    {skip_init.arg              "no"                    "Skip sal_aw_srds_powerup_init"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit }
parray arg
### initialize asic lib
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
source .tclrc.diag.sal
### initialize card properties
set slot $slot
set port $slot
set ::slot $slot
set ::port $port
set uut "UUT_$slot"
set card_type $::env($uut)
plog_msg "card type: $card_type; UUT: $uut"

if { $logEn == "yes" } {
    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    if { $sn == "" } { set sn SLOT$slot }
    set log_file $ASIC_SRC/ip/cosim/tclsh/sal_mx_prbs_${sn}_${cur_time}.log
    plog_stop
    plog_start $log_file 1000000000
}

if {$int_lpbk == "no" || $int_lpbk == 0} {
    plog_msg "Starting MX PRBS with external loopback"
    set int_lpbk 0
} else {
    plog_msg "Starting MX PRBS with internal loopback"
    set int_lpbk 1
}
sleep 0.1

set ::SAL_FORCE_ASIC_SI_SRDS_PARAMS "${::env(ASIC_SRC)}/ip/cosim/salina/$si_json_file"

proc sal_mx_srds_prbs_init {
        { int_lpbk 1 }
        { speed 100 }
        { lt 0 }
        { cable_len 200 }
        { prbs prbs31 }
        { ln_bit_vector 0xff }
        { time_sec 3 }
        { media_type CU }
        { brd_rev 0 }
    } {
    set chip_id [ sal_get_cur_chip_id ]
    set si_json_file [ sal_get_srds_json_file ]
    set cfg 2x400g
    if { [ regexp -nocase 100 $speed a ] } { set cfg 2x400g }
    if { [ regexp -nocase 50 $speed a ] } { set cfg 8x50g }
    if { [ regexp -nocase 25 $speed a ] } { set cfg 8x25g }
    if { [ sal_load_port_speed_cfg $cfg ] } {
        plog_err "sal_mx_srds_prbs: sal_load_port_speed_cfg failed for cfg:$cfg"
        return 1
    }
    set active_srds [ sal_get_active_srds ]
    set ln_bit_vector [ format "0x%x" [expr $ln_bit_vector & $active_srds] ]
    sal_aw_srds_bringup $int_lpbk $prbs $media_type $lt $cable_len $si_json_file $brd_rev $ln_bit_vector
}

plog_msg "Opening j2c"
set err_cnt_init [ plog_get_err_count ]
exec jtag_accpcie_salina clr $slot
exec fpgautil spimode $slot off
sal_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]

if {$skip_init == "no"} {
    reset_to_proto_mode
    sal_set_vmarg $vmarg
}
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt [expr $err_cnt_fnl - $err_cnt_init]
if {$err_cnt != 0} {
    plog_err "MX PRBS FAILED"
    exit -2
}

if {$card_type == "POLLARA" || $card_type == "LINGUA"} {
    # Pollara 4 lanes
    set ln_mask 0xf
} else {
    set ln_mask 0xff
}

set dwell_time 30

if {$mx2mx == "no"} {
    sal_aw_srds_powerup_init
    sal_mx_srds_prbs $int_lpbk $speed $lt $cable_len "prbs31" $ln_mask $dwell_time $media_type 0
} else {
    ###############################################################
    # This option is to test card-to-card MX
    # Cards can be in different MTP.
    # Open two sessions for each slot
    # Start this script on the first session,
    # then between 0-5 seconds start it on the second session.
    ###############################################################
    if {$skip_init == "no"} {
        sal_aw_srds_powerup_init
        sal_mx_srds_prbs_init $int_lpbk $speed $lt $cable_len "prbs31" $ln_mask $dwell_time $media_type
        plog_msg "MX SRDS PRBS INIT DONE"
        return 0
    }
    sal_mx_srds_prbs_init $int_lpbk $speed $lt $cable_len "prbs31" $ln_mask $dwell_time $media_type

    after 500
    # wait here for other card
    plog_msg "Waiting for other card to finish prbs_init within 45 seconds"; sleep 5
    set ln_bit_vector [format "0x%x" [expr $ln_mask & [sal_get_active_srds]]]
    set time_sec 30
    set allowed_ber 6
    set my_err [plog_get_err_count]
    sal_aw_prbs_chk $ln_bit_vector $time_sec $allowed_ber
    set err [plog_get_err_count]
    # if { $err > $my_err } {
        sal_aw_port_status
    # }
}
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt [expr $err_cnt_fnl - $err_cnt_init]
if {$err_cnt != 0} {
    plog_err "MX PRBS FAILED"
    exit -2
} else {
    plog_msg "MX PRBS PASSED"
    exit 0
}
