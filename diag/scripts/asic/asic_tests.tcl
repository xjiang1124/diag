# !/usr/bin/tclsh

proc init {} {
    set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
    set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
    set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
    set ASIC_GEN "$ASIC_SRC"
    
    cd $ASIC_SRC/ip/cosim/tclsh
    source .tclrc.diag
}

proc cap_snake { {board_id SN000001} {j2c_slot 1} {mode pcie_lb} {mac_serdes_int_lpbk 1} {duration 60} {use_zmq 0} {zmq_conn ""} } {
    set chip_id [ cap_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file cap_snake_${mode}_${board_id}_${cur_time}.log
    set cur_dir [pwd]
    set j2c_port 10
    
    puts "use_zmq: $use_zmq; zmq_conn: $zmq_conn"
    plog_stop
    plog_start $log_file 1000000000
    plog_msg "Running [info level 0]"
    
    if { $use_zmq } {
        diag_open_zmq_if $zmq_conn $j2c_slot
    } else {
        diag_open_j2c_if $j2c_port $j2c_slot
    }

    set in_err [plog_get_err_count]
    # === reset
    cap_jtag_chip_rst $j2c_port $j2c_slot $use_zmq $zmq_conn

    sknobs_set_value  test/sbus/load_pcie_rom_file_frontdoor 1
    if {$mode == "pcie_lb"} {
        set snake_num 6
    } elseif {$mode == "hbm_lb"} {
        set snake_num 4
    } else {
        plog_msg "Invalie mode:", $mode
        plog_stop
        return -1
    }

    #cap_snake_test_mtp $snake_num 8000 $mac_serdes_int_lpbk 1600 1 833.0 1 $duration
    cap_snake_test_mtp $snake_num
    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt != 0} {
        plog_msg "cap_snake $mode failed:  $err_cnt"
    }

    plog_stop

    return $err_cnt
}
proc ext_eth_prbs { {board_id SN000001} {j2c_port 10} {j2c_slot 1} {time_sec 60} {prbs prbs31} } {
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

    sknobs_set_value  test/sbus/load_pcie_rom_file_frontdoor 1
    cap_upload_spico
    cap_eth_srds_prbs 34 41 $time_sec all 0 $prbs

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    plog_stop

    return $err_cnt
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
    cap_pcie_srds_prbs 2 32 $time_sec 16g 0 $prbs

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    plog_stop
    return $err_cnt
}

proc ext_snake {{mode "pcie_lb"} {board_id SN000001} {duration 60}} {
    if {$mode == "pcie_lb"} {
        set snake_num 6
    } elseif {$mode == "hbm_lb"} {
        set snake_num 4
    } else {
        puts "Invalide snake mode: $mode"
        return -1
    }
    set chip_id [ cap_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file ext_snake_${mode}_${board_id}_${cur_time}.log
    set cur_dir [pwd]

    set errCnt [cap_get_myerr_cnt "cap_snake_test_mtp $snake_num 8000 1 1600 1 $duration"]
    return $errCnt
}
