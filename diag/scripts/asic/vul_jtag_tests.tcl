#! /usr/bin/tclsh
source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {sn.arg           ""                    "SN"}
    {slot.arg           ""                  "Slot number"}
    {vmarg.arg          "nom"               "Voltage margin high/low/nom"}
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
exec jtag_accpcie_vulcano clr $slot
vul_j2c
plog_msg "_msrd"
plog_msg [eval _msrd]

set err_cnt_init [ plog_get_err_count ]
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set fn "vul_jtag_slot${slot}_${cur_time}.log"
plog_start $fn

set ::board_rev [vul_get_board_rev]
vulcano_setup 0
vul_card_rst 1 0
plog_msg "calling vul_pll_fix"
vul_pll_fix
vul_vt_init 0
after 1000
vul_set_serdes_pn_swap_file

proc vul_l1_testlist_jtag { } {

    set test_common [dict create]

    #set proto_mode 1
    set org_dir [pwd]
    set brd_rev [vul_get_board_rev]

    # JTAG test
    set cmd "vul_l1_jtag_test "
    set cmd_list [list 1 "" $cmd ""]
    dict append test_common "JTAG TEST" $cmd_list

    # MBIST WEST test
    set cmd "vul_jtag_west_mbist"
    set cmd_list [list 0 "" $cmd ""]
    dict append test_common "MBIST_WEST TEST" $cmd_list

    # MBIST WEST algo22 test
    set cmd "vul_jtag_west_mbist_algo22"
    set cmd_list [list 0 "" $cmd ""]
    dict append test_common "MBIST_WEST_ALGO22 TEST" $cmd_list

    # MBIST EAST test
    set cmd_l "vul_jtag_east_mbist"
    set cmd_list [list 0 "" $cmd_l ""]
    dict append test_common "MBIST_EAST TEST" $cmd_list

    # MBIST EAST algo22 test
    set cmd_l "vul_jtag_east_mbist_algo22"
    set cmd_list [list 0 "" $cmd_l ""]
    dict append test_common "MBIST_EAST_ALGO22 TEST" $cmd_list

    return $test_common
}

proc vul_l1_jtag_diag { board_id
		          {exit_on_err 0}
		          {verbose 1}
		          {vmarg "nom"}
                {log_en 1}
                {skip_l1_report_mode 0}} {

    global G_USE_ZMQ
    global G_ZMQ_CONN
    global G_SLOT 0
    set G_USE_ZMQ 0
    set G_ZMQ_CONN ""
    set G_SLOT 0
    set ::VUL_L1_TEST 1

    #unset -nocomplain ::VULCANO_DIE_ID_FIELD_TABLE
    unset -nocomplain ::VULCANO_DIE_ID_CACHE

    global array l1_screen_report
    unset -nocomplain l1_screen_report
    array set l1_screen_report {}

    #set chip_id [ vul_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    set log_file vul_l1_screen_board_${board_id}_${cur_time}.log
    set cur_dir [pwd]

    if { $log_en==1 } {
      plog_stop
      plog_start $log_file 1000000000
    }
    plog_msg "Running [info level 0]"

    set start_time [clock seconds]

    # Use warm reset
    set reset_mode 2
    set jtag_rst_proto_cmd "vul_card_rst $reset_mode 0"
    set jtag_rst_production_cmd "vul_card_rst $reset_mode 1"

    #log the die id
    plog_msg "Card Serial Number : [vul_card_print_serial_number -1 0]"
    vul_die_id_print

    #log the git rev
    vul_get_git_rev

    #set the voltage and check it
    if { $vmarg != "none" } {
       vul_set_vmarg $vmarg all
       #vul_check_voltages $vmarg all
    }

    set test_list [vul_l1_testlist_jtag] 
    vul_l1_testlist_disp $test_list

    set test_name_list [dict keys $test_list]

    foreach test_name $test_name_list {
        plog_msg ""
        plog_msg "=== L1: $test_name Started ==="
        set cmd_list [dict get $test_list $test_name]

        set cmd [lindex $cmd_list 0]
        if {$cmd == 1} {
            plog_msg "cmd0 $jtag_rst_proto_cmd"
            eval $jtag_rst_proto_cmd
        }
        if {$cmd == 2} {
            plog_msg "cmd0 $jtag_rst_production_cmd"
            eval $jtag_rst_production_cmd
        }

        set cmd [lindex $cmd_list 1]
        if {$cmd != ""} {
            plog_msg "cmd_1 $cmd"
            eval $cmd
        }

        set cmd [lindex $cmd_list 2]
        if {$cmd != ""} {
            plog_msg "cmd_2 $cmd"
            plog_clr_err_count
            vul_get_myerr_cnt $cmd $exit_on_err $verbose 1
        }

        set cmd [lindex $cmd_list 3]
        if {$cmd != ""} {
            plog_msg "cmd_3 $cmd"
            eval $cmd
        }

        plog_msg "VUL_PWR_VOLT_TEMP AFTER test $test_name"
        vul_vrm_get_pwr_total_brd
        vul_devmgr_status
        vul_print_power_summary

        plog_msg "=== L1: $test_name Done==="
        plog_msg ""
    }

    unset -nocomplain ::VUL_L1_TEST
    set err_cnt [vul_dump_l1_report $skip_l1_report_mode]

    set end_time [clock seconds]
    set test_time [expr {$end_time-$start_time}]
    set test_time_min [expr {$test_time/60}]
    set test_time_sec [expr {$test_time%60}]
    set test_time_out [format "%d:%02d" $test_time_min $test_time_sec]
    plog_msg "Test time used: $test_time_out; Test time(sec): $test_time"

    if { $log_en==1 } {
       plog_stop
    }
    return $err_cnt
}
set l1_cmd "vul_l1_jtag_diag $sn 0 1 $vmarg 1 0"
set err_cn [eval $l1_cmd]
diag_close_j2c_if $port $slot
exit
