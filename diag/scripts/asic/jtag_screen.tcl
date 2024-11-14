# !/usr/bin/tclsh

##################################
# Tests for screening Salina JTAG
##################################

proc define_test_list {{override_test_list ""}} {
    # borrowed from L1 test list format
    
    if { $override_test_list == "" } {
        set names_list [list ID MBIST]
    } else {
        set names_list [list $override_test_list]
    }

    set test_list [dict create]
    foreach test_name $names_list {
        switch $test_name {
            # #TEST NAME ############# RST PRE                      COMMAND              POST
            ID         { set cmd_list [list 0 ""                       sal_jtag_id          ""  ] }
            FREQ       { set cmd_list [list 0 ""                       sal_jtag_freq_test   sal_pcc  ] } ; # this test will lower the stage freq. need reset to restore 1.5GHz.
            MBIST      { set cmd_list [list 0 set_pollara_frequency    mbist_with_diag      "" ] }

            MBIST_ARM  { set cmd_list [list 0 set_pollara_frequency    sal_jtag_arm_stp     "" ] }
            MBIST_EAST { set cmd_list [list 0 set_pollara_frequency    sal_jtag_east_stp    "" ] }
            MBIST_WEST { set cmd_list [list 0 set_pollara_frequency    sal_jtag_west_stp    "" ] }

            DIAG_ARM   { set cmd_list [list 0 set_pollara_frequency    sal_jtag_arm_diag    "" ] }
            DIAG_EAST  { set cmd_list [list 0 set_pollara_frequency    sal_jtag_east_diag   "" ] }
            DIAG_WEST  { set cmd_list [list 0 set_pollara_frequency    sal_jtag_west_diag   "" ] }
            default    { set cmd_list [list 0 "" "" ""] }
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

proc mbist_with_diag {} {
    ### copy of sal_jtag_mbist_stp
    set arm_err  0
    set east_err 0
    set west_err 0

    set arm_err  [sal_jtag_arm_stp]
    set east_err [sal_jtag_east_stp]
    set west_err [sal_jtag_west_stp]

    set err [ expr { $arm_err | $east_err | $west_err } ]
    if {$err == 0} {
        plog_msg "sal_jtag_mbist_stp::Test PASSED"
    } else {
       plog_err "sal_jtag_mbist_stp::Test FAILED"
       plog_msg "Arm Error $arm_err East Error $east_err West Error $west_err"
    }

    ### diagnostics to report which memory bit failed.
    ### (they'll cover mbist as well but takes longer)
    if {$arm_err != 0} {
        plog_err "Errors encountered in ARM MBIST. Running diagnostics..."
        set_pollara_frequency
        sal_jtag_arm_diag
    } elseif {$east_err != 0} {
        plog_err "Errors encountered in East MBIST. Running diagnostics..."
        set_pollara_frequency
        sal_jtag_east_diag
    } elseif {$west_err != 0} {
        plog_err "Errors encountered in West MBIST. Running diagnostics..."
        set_pollara_frequency
        sal_jtag_west_diag
    }
    check_vrd_fault
}

### handle args
#package require cmdline
source /home/diag/diag/scripts/asic/cmdline.tcl
set usage {
    {sn.arg         ""                      "Serial number"}
    {slot.arg       ""                      "Slot number"}
    {vmarg.arg      "none"                  "Voltage margin"}
    {loops.arg      "1"                     "Number of loops to run tests"}
    {test_list.arg  ""                      "Run only some tests. For multiple tests pass as \'test1 test2\'"}
    {DIAG_DIR.arg   "/home/diag/diag/asic/" "ASIC lib location"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit }
parray arg ; # print them out

### initialize asic lib
source /home/diag/diag/scripts/asic/asic_tests.tcl
set ASIC_LIB_BUNDLE "$DIAG_DIR"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
#source /home/diag/diag/scripts/asic/sal_init.tcl
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl

### initialize card properties
set slot $slot
set port $slot
set ::slot $slot
set ::port $port
set uut "UUT_$slot"
set card_type $::env($uut)
plog_msg "card type: $card_type; UUT: $uut"

### handle test list
set test_list [define_test_list $test_list]
display_test_list $test_list

plog_msg "Opening j2c"
set err_cnt_init [ plog_get_err_count ]
exec jtag_accpcie_salina clr $slot
exec fpgautil spimode $slot off
sal_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]
reset_to_proto_mode
sal_set_vmarg $vmarg
sal_print_voltage_temp_from_j2c
set err_cnt_fnl [ plog_get_err_count ]
set err_cnt [expr $err_cnt_fnl - $err_cnt_init]
if {$err_cnt != 0} {
    plog_err "JTAG TESTS FAILED"
    plog_err "JTAG TESTS FAILED"
    return 0
}

### run tests
set final_rslt 0
set test_name_list [dict keys $test_list]
foreach test_name $test_name_list {
    set cmd_list [dict get $test_list $test_name]
    set cmd_0 [lindex $cmd_list 0]
    set cmd_1 [lindex $cmd_list 1]
    set cmd_2 [lindex $cmd_list 2]
    set cmd_3 [lindex $cmd_list 3]

    for { set iter 1 } { $iter <= $loops } {incr iter} {
        if { $iter > 1 } {
            plog_msg "===== JTAG Screen: LOOP $iter of $test_name ======"
        } else {
            plog_msg "== JTAG Screen: Started $test_name TEST ==" }

        set start_time [clock seconds]

        ## exec reset command
        set cmd [lindex $cmd_list 0]
        if {$cmd == 1 || $cmd == 2} {
            plog_msg "cmd0 $jtag_rst_cmd"
            eval $jtag_rst_cmd
            #if {$cmd == 2} {
            #   run_ddr 6400
            #}
        }

        ## exec prepare command
        set cmd [lindex $cmd_list 1]
        if {$cmd != ""} {
            plog_msg "cmd_1 $cmd"
            eval $cmd
        }

        ## exec test command
        # sal_print_voltage_temp
        set cmd [lindex $cmd_list 2]
        if {$cmd != ""} {
            plog_msg "cmd_2 $cmd"
            set err_cnt [sal_get_myerr_cnt $cmd 0 0 1]
        }

        ## exec post command
        set cmd [lindex $cmd_list 3]
        if {$cmd != ""} {
            plog_msg "cmd_3 $cmd"
            eval $cmd
        }

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
} else {
    plog_msg "JTAG TESTS PASSED"
    plog_msg "JTAG TESTS PASSED"
}

