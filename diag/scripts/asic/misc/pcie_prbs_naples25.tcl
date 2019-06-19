set slot_list [list 1 2 3 4 5 6 7 8 9 10]
set slot_list [list 7 8 9 10]
set freq_list [list 417 833]
set volt_list [list 700 750 800]

plog_start prbs_test.log
foreach slot $slot_list {
    foreach freq $freq_list {
        foreach volt $volt_list {
            set err_cnt 0
            plog_msg "=== slot $slot; freq $freq; volt $volt ==="
            diag_open_j2c_if 10 $slot
            cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200
            cap_set_avs_vdd $freq 0 1 $volt
            cap_print_voltage_temp

            cap_upload_pcie_spico
            set card_type [cap_get_card_type]
            set srds_list [cap_get_pcie_srds_list $card_type]
            set err_cnt [cap_get_myerr_cnt [list cap_pcie_srds_prbs $srds_list 600 16g 0] 0 1 1 ]
            diag_close_j2c_if 10 $slot

            if {$err_cnt == 0} {
                plog_msg "=== slot $slot PASSED ==="
            } else {
                plog_msg "=== slot $slot FAILED $err_cnt ==="
            }
        }
    }
    
}
plog_stop

