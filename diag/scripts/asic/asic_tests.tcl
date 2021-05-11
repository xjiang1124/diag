# !/usr/bin/tclsh

proc init {} {
    set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
    set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
    set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
    set ASIC_GEN "$ASIC_SRC"
    
    cd $ASIC_SRC/ip/cosim/tclsh
    source .tclrc.diag
}

proc disp_volt_temp { {board_id SN000001} {j2c_slot 1} {use_zmq 0} {zmq_conn ""} } {
    global G_USE_ZMQ
    global G_ZMQ_CONN
    global G_SLOT 0
    set G_USE_ZMQ $use_zmq
    set G_ZMQ_CONN $zmq_conn
    set G_SLOT $j2c_slot

    set chip_id [ cap_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file disp_volt_temp_${board_id}_${cur_time}.log
    set cur_dir [pwd]
    set j2c_port 10

    plog_stop
    plog_start $log_file 1000000000
    plog_msg "Running [info level 0]"

    if { $use_zmq == 1 } {
        diag_force_close_zmq_if $zmq_conn $j2c_slot
        diag_open_zmq_if $zmq_conn $j2c_slot
    } else {
        diag_open_j2c_if $j2c_port $j2c_slot
    }

    set in_err [plog_get_err_count]
    cap_print_voltage_temp

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt != 0} {
        plog_msg "set avs slot$slot failed:  $err_cnt"
    }

    if { $use_zmq == 1 } {
        diag_close_zmq_if
    } else {
        diag_close_j2c_if $j2c_port $j2c_slot
    }

    plog_stop

    return $err_cnt
}
proc set_avs { {board_id SN000001} {j2c_slot 1} {arm_vdd vdd} {core_freq 833} {arm_freq 2000} {use_zmq 0} {zmq_conn ""} {force 0} {vout 800} {use_pmro 0}} {
    global G_USE_ZMQ
    global G_ZMQ_CONN
    global G_SLOT 0
    set G_USE_ZMQ $use_zmq
    set G_ZMQ_CONN $zmq_conn
    set G_SLOT $j2c_slot

    set chip_id [ cap_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file set_avs_${board_id}_${cur_time}.log
    set cur_dir [pwd]
    set j2c_port 10

    plog_stop
    plog_start $log_file 1000000000
    plog_msg "Running [info level 0]"

    if { $use_zmq == 1} {
        diag_force_close_zmq_if $zmq_conn $j2c_slot
        diag_open_zmq_if $zmq_conn $j2c_slot
    } else {
        diag_open_j2c_if $j2c_port $j2c_slot
    }

    set in_err [plog_get_err_count]
    #proc cap_jtag_chip_rst { j2c_port j2c_slot {use_zmq 0} {zmq_conn ""} { first_article 1 } { proto_mode 1 } {bit6_power_cycle 0} {core_freq 833} {arm_freq 2200}}
    cap_jtag_chip_rst $j2c_port $j2c_slot $use_zmq $zmq_conn 1 1 0 $core_freq $arm_freq

    if {$arm_vdd == "vdd" } {
        set freq $core_freq
    } else {
        set freq $arm_freq
    }

    cap_set_avs $arm_vdd $freq $use_pmro 0 $force $vout

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt != 0} {
        plog_msg "set avs slot$j2c_slot failed:  $err_cnt"
    }

    if { $use_zmq == 1 } {
        diag_close_zmq_if
    } else {
        diag_close_j2c_if $j2c_port $j2c_slot
    }

    plog_stop

    return $err_cnt
}

proc set_avs_elb { {board_id SN000001} {j2c_slot 1} {core_freq 833} {arm_freq 2000} {use_zmq 0} {zmq_conn ""} } {
    global G_USE_ZMQ
    global G_ZMQ_CONN
    global G_SLOT 0
    set G_USE_ZMQ $use_zmq
    set G_ZMQ_CONN $zmq_conn
    set G_SLOT $j2c_slot

    set chip_id [ elb_get_cur_chip_id ]
    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file set_avs_${board_id}_${cur_time}.log
    set cur_dir [pwd]
    set j2c_port 10

    plog_stop
    plog_start $log_file 1000000000
    plog_msg "Running [info level 0]"

    if { $use_zmq == 1} {
        diag_force_close_zmq_if $zmq_conn $j2c_slot
        diag_open_zmq_if $zmq_conn $j2c_slot
    } else {
        diag_open_j2c_if $j2c_port $j2c_slot
    }

    set in_err [plog_get_err_count]
    elb_card_rst $j2c_port $j2c_slot nod 3200 1600 0 0 "127.0.0.1" 1 1 normal 0 0

    elb_set_avs $core_freq $arm_freq 

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    if {$err_cnt != 0} {
        plog_msg "set avs slot$j2c_slot failed:  $err_cnt"
    }

    if { $use_zmq == 1 } {
        diag_close_zmq_if
    } else {
        diag_close_j2c_if $j2c_port $j2c_slot
    }

    plog_stop

    return $err_cnt
}
proc asic_snake { {asic_type CAPRI} {board_id SN000001} {j2c_slot 1} {mode pcie_lb} {core_freq 833} {mac_serdes_int_lpbk 1} {duration 60} {use_zmq 0} {zmq_conn ""} {fan_ctrl 0} {tgt_temp 115} } {
    global G_USE_ZMQ
    global G_ZMQ_CONN
    global G_SLOT 0
    set G_USE_ZMQ $use_zmq
    set G_ZMQ_CONN $zmq_conn
    set G_SLOT $j2c_slot

    set cur_time [clock format [clock seconds] -format %y%m%d_%H%M%S]
    set log_file cap_snake_${mode}_${board_id}_${cur_time}.log
    set cur_dir [pwd]
    set j2c_port 10
 
    if {$mode == "pcie_lb"} {
        set snake_num 6
    } elseif {$mode == "hbm_lb"} {
        set snake_num 4
    } else {
        plog_msg "Invalie mode:", $mode
        plog_stop
        return -1
    }   
    
    if {$asic_type == ELBA} {
        set cmd_die_id elb_print_die_id
        set cmd_rst "elb_card_rst $j2c_port $j2c_slot "nod" 3200 1600 0 $use_zmq $zmq_conn 1 1"
        set cmd_snake "elb_snake_test_mtp $snake_num 4096 $mac_serdes_int_lpbk 1 $core_freq 1 $duration $fan_ctrl $tgt_temp"
    } else {
        set cmd_die_id cap_print_die_id
        set cmd_rst "cap_jtag_chip_rst $j2c_port $j2c_slot $use_zmq $zmq_conn 1 1 0 $core_freq"
        set cmd_snake "cap_snake_test_mtp $snake_num 8000 $mac_serdes_int_lpbk 1600 1 $core_freq 1 $duration $fan_ctrl $tgt_temp"
    }

    puts "use_zmq: $use_zmq; zmq_conn: $zmq_conn"
    plog_stop
    plog_start $log_file 1000000000
    plog_msg "Running [info level 0]"
   
    if { $use_zmq == 1} {
        diag_open_zmq_if $zmq_conn $j2c_slot
    } else {
        diag_open_j2c_if $j2c_port $j2c_slot
    }

    if { $use_zmq == 0 } {
        exec devmgr -dev=fan -status
    }

    set in_err [plog_get_err_count]
    eval $cmd_die_id
    eval $cmd_rst

    if {$asic_type == CAPRI} {
        sknobs_set_value  test/sbus/load_pcie_rom_file_frontdoor 1
    }

    #cap_snake_test_mtp $snake_num 8000 $mac_serdes_int_lpbk 1600 1 $core_freq 1 $duration $fan_ctrl $tgt_temp
    eval $cmd_snake

    set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
    plog_msg "============================================"
    if {$err_cnt != 0} {
        plog_msg "cap_snake $mode FAILED:  $err_cnt"
    } else {
        plog_msg "cap_snake $mode FASSED"
    }
    plog_msg "============================================"

    if { $use_zmq == 1 } {
        diag_close_zmq_if
    } else {
        diag_close_j2c_if $j2c_port $j2c_slot
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
