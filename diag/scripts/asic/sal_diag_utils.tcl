proc clear_resetcode {expected_code} {
    set reg_data [ssi_cpld_read 0x30]
    if { $reg_data == $expected_code } {
        plog_msg "Clearing CPLD resetcode register"
        ssi_cpld_write 0x30 0x0
    } else {
        plog_err "CPLD resetcode register 0x30: $reg_data"
    }
}

proc clear_vrd_faults {} {
    plog_msg "Clearing VRD fault"
    sleep 2 ; # wait for power sequencing after an unreset
    sal_tps53688_clear_faults 2 0x60 0
    if {[dict exists [sal_i2c_tbl] ARM]} {
        sal_tps53688_clear_faults 2 0x60 1
    }
}

proc check_vrd_fault {} {
    ### make sure mbist didnt cause any current spikes
    set resetcode [ssi_cpld_read 0x30]
    set faultcode [ssi_cpld_read 0x32]
    plog_msg "CPLD reg 0x30: $resetcode"
    plog_msg "CPLD reg 0x32: $faultcode"
    if { $resetcode != "0x0" } {
        plog_err "Encountered abnormal reset code: $resetcode"
    }
    if { $faultcode != "0x0" } {
        plog_err "Encountered abnormal fault code: $faultcode"
        if { $faultcode == "0x08"} {
            sal_j2c
            plog_msg "Dumping VRM faultcodes:"
            sal_tps53688_explain_status 2 0x60 0
        }
    }
}

proc set_pollara_frequency {{arm_freq "1500"} {protomode "yes"}} {
    set card_type [sal_get_card_type]
    if { $card_type == "POLLARA" } {
        plog_msg "Changing ARM frequency to $arm_freq"
        ## this sets frequency using jtag
        ## which will block the j2c connection
        ## therefore it can only work over onewire
        sal_ow
        if { $arm_freq == "3000"} {
            sal_set_pollara_freq
        } elseif { $arm_freq == "2000" } {
            sal_set_pollara_freq_arm_2000; #waiting for stream, not implemented
        } elseif { $arm_freq == "1500" } {
            sal_set_pollara_freq_arm_1500
        } elseif { $arm_freq == "1250" } {
            sal_set_pollara_freq_arm_1250
        } elseif { $arm_freq == "750" } {
            sal_set_pollara_freq_arm_750
        }
        sal_j2c
        if { $protomode == "yes" } {
            # redo proto mode
            sal_proto_mode_unreset
        }
        clear_resetcode 0x0b
    }
}

proc cpld_disable_wdt {} {
    plog_msg "Disabling WDT"
    set reg_data [ssi_cpld_read 0x1]
    ssi_cpld_write 0x1 [expr {$reg_data & 0xFD}]
}

proc cpld_set_core_pll {{freq 1100}} {
    set reg_data [ssi_cpld_read 0x11]

    switch $freq {
        100     {set new_div 0}
        275     {set new_div 1}
        550     {set new_div 2}
        1100    {set new_div 3}
        default {set new_div 3}
    }
    plog_msg "Setting CORE PLL to $freq"
    ssi_cpld_write 0x11 [expr { ($reg_data & 0xFC) | ($new_div & 0x3) }]


    set reg_data [ssi_cpld_read 0x11]
    plog_msg "New CORE PLL: $reg_data"
}

proc cpld_set_cpu_pll {{freq 3000}} {
    set reg_data [ssi_cpld_read 0x11]
    switch $freq {
        100     {set new_div 0}
        750     {set new_div 1}
        1500    {set new_div 2}
        3000    {set new_div 3}
        default {set new_div 3}
    }
    plog_msg "Setting CPU PLL to $freq"
    ssi_cpld_write 0x11 [expr { ($reg_data & 0xF3) | ($new_div & 0xC) }]

    set reg_data [ssi_cpld_read 0x11]
    plog_msg "New CPU PLL: $reg_data"
}

proc verify_soc_cntrs {} {
    plog_msg "sal_soc_dump_slv_cntrs"
    sal_soc_dump_slv_cntrs
    plog_msg "sal_soc_dump_mst_cntrs"
    sal_soc_dump_mst_cntrs

    set regs { CNT_d_aw CNT_d_w CNT_d_b CNT_d_ar CNT_d_r }
    foreach j $regs {
        set a [csr_read sal0.np.npmaxi\[18\].${j}] ; # A35 cntrs at indx 18
        set b [expr {$a > 0 ? $a :  "-"}]
        if { $b != "-" } { plog_err "ARM counters are not zero" ; break }
    }
}

proc reset_to_proto_mode {{verbosity "noisy"}} {
    ### chip draws high current when in reset
    ### to avoid this, lower the clocks before putting in reset
    ### when coming out of reset, the CPLD will raise the clocks back

    # kill clock
    cpld_set_core_pll 100
    cpld_set_cpu_pll 100

    # set CPLD bit
    sal_set_proto_mode 0

    # keep ARM in reset. unreset other cores
    sal_proto_mode_powerup

    # current CPLD version does not reset CPU PLL to default
    # revert CPU PLL back
    cpld_set_cpu_pll 3000

    # cleanup
    sal_j2c
    cpld_disable_wdt
    clear_resetcode 0x13

    sal_arm_show_reset
    verify_soc_cntrs
    plog_msg [exec inventory -sts -slot $::slot]
}

proc set_pollara_low_power_mode {} {
    set card_type [sal_get_card_type]
    if { $card_type == "POLLARA" } {
        plog_msg "Setting clock gating for low power mode"
        plog_msg "sal_ainic_low_pwr_mode"
        sal_ainic_low_pwr_mode
        plog_msg "sal_ainic_chk_clk_gate"
        sal_ainic_chk_clk_gate
        plog_msg "ARM resets: (0=reset)"
        sal_arm_show_reset
    }
}