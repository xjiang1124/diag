set slot_list [list 1 2 3 4 5 6 7 8 9 10]
set speed_list [list 16g]
set num_ite 1
set freq 417
set hbm_speed 1600
set vmarg low

set duration 600
set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
set cur_pwd [pwd]

plog_start prbs_test_vmarg_${vmarg}_${cur_time}.log
foreach slot $slot_list {
    for {set ite 0} {$ite < $num_ite} {incr ite} {
        set err_cnt 0
        plog_msg "=== slot $slot; ite $ite ==="
        diag_open_j2c_if 10 $slot
        cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200 $vmarg

        set mac_speed "mac25g_ext_port2port_lpbk"
        set snake_num 6
        set pktsize 8000
        set mac_serdes_int_lpbk 0
        
        set snake_name [cap_get_snake_name  $snake_num]
        set snake_name "${snake_name}_${mac_speed}"
        cd  $::env(ASIC_LIB_BUNDLE)/../snake${snake_num}_${snake_name}/stream_copy
        plog_msg " running snake${snake_num}_${snake_name}, pktsize:$pktsize, mac_serdes_int_lpbk:$mac_serdes_int_lpbk, hbm_speed : $hbm_speed"
        cap_print_snake_topology $snake_num
        
        sknobs_load_file sknobs.out
        sknobs_set_value cap_top_stream_cfg/cap0/stream/10/pktgen/const_jumbo/value  $pktsize
        
        sknobs_set_value "chip/0/pcie_port/logical/0/lanes" 4
        sknobs_set_value "chip/0/pcie_port/logical/1/lanes" 4
        sknobs_set_value "chip/0/pcie_port/logical/0/speed" 4
        sknobs_set_value "chip/0/pcie_port/logical/1/speed" 4
        sknobs_set_value "chip/0/pcie_port/logical/1/phy_port" 2
        sknobs_set_value "ext_lpbk_rc_port" 2
        ssi_cpld_write 0x1 0xe
        ssi_cpld_write 0x21 0x1
        
        source $::env(ASIC_SRC)/ip/cosim/capri/pcie/pp_ltssm_asic.tcl
        source $::env(ASIC_SRC)/ip/cosim/capri/pcie/multiport_ltssm_asic.tcl
        
        cap_pcie_soft_reset 0 0
        cap_pcie_init_start 0 0

        cd $cur_pwd
        cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200 $vmarg
        #cap_set_avs_vdd $freq 0 1 $volt
        #cap_print_voltage_temp
        set card_type [cap_get_card_type]

        cap_upload_pcie_spico
        #cap_upload_pcie_spico
        set srds_list [cap_get_pcie_srds_list $card_type]
        foreach speed $speed_list {
            set err_cnt [cap_get_myerr_cnt [list cap_pcie_srds_prbs $srds_list $duration $speed 0] 0 1 1 ]
            if {$err_cnt == 0} {
                plog_msg "=== slot $slot PASSED; speed: $speed ==="
            } else {
                plog_msg "=== slot $slot FAILED; speed $speed ==="
            }
        }

        diag_close_j2c_if 10 $slot
    }
    
}
plog_stop

