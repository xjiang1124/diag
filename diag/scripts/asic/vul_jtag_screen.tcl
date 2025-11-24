# !/usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {sn.arg         ""                      "Serial number"}
    {slot.arg       ""                      "Slot number"}
    {vmarg.arg      "none"                  "Voltage margin"}
    {logEn.arg      "yes"                   "Save to logfile"}
    {loops.arg      "1"                     "Number of loops to run tests"}
    {test_list.arg  ""                      "Run only some tests. For multiple tests pass as \'test1 test2\'"}
    {tcl_path.arg   ""                      "ASIC lib location"}
    {reset.arg      "cold"                  "Reset method: warm/cold; default: cold"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit }
parray arg

proc define_test_list {{override_test_list ""}} {
    # borrowed from L1 test list format

    plog_msg "Got override_test_list = $override_test_list"
    
    if { $override_test_list == "" } {
        set names_list [list ID MBIST] ; # DEFAULT TEST LIST
    } else {
        set names_list [split $override_test_list]
    }

    set test_list [dict create]
    foreach test_name $names_list {
        switch $test_name {
            # #TEST NAME ##################### RST PRE              COMMAND                       POST
            MBIST_ORIG_EAST { set cmd_list [list 0 ""               vul_jtag_east_mbist           ""      ] }
            MBIST_ORIG_WEST { set cmd_list [list 0 ""               vul_jtag_west_mbist           ""      ] }
            ALGO22_EAST     { set cmd_list [list 0 ""               vul_jtag_east_mbist_algo22    ""      ] }
            ALGO22_WEST     { set cmd_list [list 0 ""               vul_jtag_west_mbist_algo22    ""      ] }

            default         { set cmd_list [list 0 "" "" ""] }
        }
        dict append test_list $test_name $cmd_list
    }
    return $test_list
}

proc display_test_list {{test_list {}}} {
    # borrow from L1 test display
    set test_name_list [dict keys $test_list]
    set fmtStr "%-4s%-25s%-80s%-25s"
    plog_msg "========================= JTAG: Test List ======================================"
    plog_msg [ format $fmtStr "RST" "PRE" "CMD" "POST" ]
    foreach test_name $test_name_list {
        set cmd_list [dict get $test_list $test_name]
        set cmd_0 [lindex $cmd_list 0]
        set cmd_1 [lindex $cmd_list 1]
        set cmd_2 [lindex $cmd_list 2]
        set cmd_3 [lindex $cmd_list 3]

        plog_msg [ format $fmtStr $cmd_0 $cmd_1 $cmd_2 $cmd_3 ]
    }
    plog_msg "============================================================================="
}

#source /home/diag/diag/scripts/asic/vul_diag_utils.tcl

### initialize asic lib
set ::VEL_SHELL 0
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

if { $logEn == "yes" } {
    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    if { $sn == "" } { set sn SLOT$slot }
    set log_file $ASIC_SRC/ip/cosim/tclsh/vul_jtag_mbist_${sn}_${cur_time}.log
    plog_stop
    plog_start $log_file 1000000000
}

plog_msg "Opening j2c"
set err_cnt_init [ plog_get_err_count ]
exec jtag_accpcie_vulcano clr $slot
vul_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]

if { $reset == "cold" } {
    vul_p450_reset 0
    vul_p450_show_reset
} else {
    #reset_to_proto_mode warm_rot
}

#vul_set_vmarg $vmarg
vul_print_die_id
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt [expr $err_cnt_fnl - $err_cnt_init]
if {$err_cnt != 0} {
    plog_err "JTAG TESTS FAILED"
    plog_err "JTAG TESTS FAILED"
    exit -2
}


### run tests
set final_rslt 0
set test_name_list [dict keys $test_list]
foreach test_name $test_name_list {
    set cmd_list [dict get $test_list $test_name]
    set err_cnt1 0
    set err_cnt2 0
    set err_cnt3 0

    for { set iter 1 } { $iter <= $loops } {incr iter} {
        if { $iter > 1 } {
            plog_msg "===== JTAG Screen: LOOP $iter of $test_name ======"
        } else {
            plog_msg "== JTAG Screen: Started $test_name TEST ==" }

        set start_time [clock seconds]

        ## exec reset command
        set cmd [lindex $cmd_list 0]
        set jtag_rst_cmd reset_to_proto_mode
        if {$cmd == 1 || $cmd == 2} {
            plog_msg "cmd $jtag_rst_cmd"
            eval $jtag_rst_cmd
        }

        ## exec prepare command
        set cmd [lindex $cmd_list 1]
        if {$cmd != ""} {
            plog_msg "cmd $cmd"
            set err_cnt1 [sal_get_myerr_cnt $cmd]
        }

        ## exec test command
        # sal_print_voltage_temp
        set cmd [lindex $cmd_list 2]
        if {$cmd != ""} {
            plog_msg "cmd $cmd"
            set err_cnt2 [sal_get_myerr_cnt $cmd 0 0 1]
        }

        ## exec post command
        set cmd [lindex $cmd_list 3]
        if {$cmd != ""} {
            plog_msg "cmd $cmd"
            set err_cnt3 [sal_get_myerr_cnt $cmd]
        }

        set err_cnt [expr $err_cnt1 + $err_cnt2 + $err_cnt3]

        if {$err_cnt != 0} {
            set final_rslt 1
            plog_err "== JTAG Screen: Failed $test_name =="
            plog_msg ""
        } else {
            plog_msg "== JTAG Screen: Passed $test_name =="
            plog_msg ""
        }

        set end_time [clock seconds]
        set test_time [expr {$end_time-$start_time}]
        set test_time_min [expr {$test_time/60}]
        set test_time_sec [expr {$test_time%60}]
        set test_time_out [format "%d:%02d" $test_time_min $test_time_sec]
        plog_msg "Test time used: $test_time_out; Test time(sec): $test_time"
    }
}

diag_close_j2c_if $port $slot

### Print twice for DSP to capture signature
if { $final_rslt != 0 } {
    plog_msg "JTAG TESTS FAILED"
    plog_msg "JTAG TESTS FAILED"
    set ret -1
} else {
    plog_msg "JTAG TESTS PASSED"
    plog_msg "JTAG TESTS PASSED"
    set ret 0
}

if { $logEn == "yes" } { plog_stop }

### Parse and summarize error messages
if {$ret != 0} {
    puts [exec /home/diag/diag/python/regression/parse_mbist_err.py $log_file]
}

exit $ret
