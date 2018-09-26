# !/usr/bin/tclsh

set sn [lindex $argv 0]
set slot_num [lindex $argv 1]
set time_sec [lindex $argv 2]
set prbs [lindex $argv 3]

puts "sn: $sn; slot_num: $slot_num; time_sec: $time_sec; prbs: $prbs"

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.new

exit 0

diag_open_j2c_if 10 $slot_num
source $ASIC_SRC/ip/cosim/capri/cap_l1_tests.tcl
eth_eth_prbs $sn 10 $slot_num $time_sec $prbs

proc ext_eth_prbs { board_id j2c_port j2c_slot {time_sec 60} {prbs prbs31} } {

    set chip_id [ cap_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file cap_eth_prbs_${board_id}_${cur_time}.log
    set cur_dir [pwd]
    
    plog_stop
    plog_start $log_file 1000000000
    plog_msg "Running [info level 0]"
    
    set in_err [plog_get_err_count]
    # === reset
    cap_jtag_chip_rst $j2c_port $j2c_slot

    cap_upload_spico
    # proc cap_eth_srds_prbs { { srds_start 34 } { srds_end 42 } { time_sec 60 }  { speed all } { int_lpbk 1 }  { prbs prbs31 }
    cap_eth_srds_prbs 34 42 $time_sec all 0 $prbs

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt == 0} {
        plog_msg "ETH PRBS PASSED"
    } else {
        plog_msg "ETH PRBS FAILED"
    }

    plog_stop
}

proc ext_pcie_prbs { board_id j2c_port j2c_slot {time_sec 60} {prbs prbs31} } {

    set chip_id [ cap_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file cap_pcie_prbs_${board_id}_${cur_time}.log
    set cur_dir [pwd]
    
    plog_stop
    plog_start $log_file 1000000000
    plog_msg "Running [info level 0]"
    
    set in_err [plog_get_err_count]
    # === reset
    cap_jtag_chip_rst $j2c_port $j2c_slot

    cap_upload_pcie_spico
    # proc cap_pcie_srds_prbs { { srds_start 2 } { srds_end 32 } { time_sec 60 }  { speed 16g } { int_lpbk 1 }  { prbs prbs31 }
    cap_pcie_srds_prb 2 32 $time_sec 16g 0 $prbs

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt == 0} {
        plog_msg "PCIE PRBS PASSED"
    } else {
        plog_msg "PCIE PRBS FAILED"
    }

    plog_stop
}
