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

proc verify_clk_obs {arm_freq} {
    set err_cnt 0
    foreach tile [list 1_1 1_2 2_1 2_2 3_1 3_2 4_1 4_2] {
        set x [sal_jtag_arm_${tile}_clk_obs_pad_func]
        plog_msg "set_pollara_frequency :: Checking ARM_${tile} clk_obs Exp: $arm_freq Act: $x"
        if {$x != $arm_freq} { set err_cnt 1 }
    }
    return $err_cnt
}

proc set_pollara_frequency_2000_workaround {} {
    # keep setting until readback is correct
    set arm_freq 200 ; #=Freq/10
    for {set retry 0} {$retry < 3} {incr retry} {
        sal_jtag_arm_nxc_ddr_pll_no_rdbk 40 0 1 1 0 64 1 0 1 0 64 1 2 1 1
        sal_warm_rst
        if {[verify_clk_obs $arm_freq] == 0} { break }
        plog_msg "set_pollara_frequency :: Could not read consistent ARM frequency on clk_obs...retrying."
    }
    if {$retry == 3} {
        plog_err "set_pollara_frequency :: Could not read consistent ARM frequency on clk_obs...aborting."
        return -1
    }
    return 0
}

proc verify_arm_frequency {{arm_freq "1500"}} {
    sal_PLL_SYSPLL_T_ARM_PLL_DFX_CLK_OBS $arm_freq
}

proc set_pollara_frequency_2000 {} {
    sal_jtag_arm_nxc_ddr_pll_no_rdbk 40 0 1 1 1 64 1 0 1 0 64 1 2 1 1
    plog_msg "set_pollara_frequency :: Verify CLKs are at 2000 MHz"
    verify_arm_frequency 2000
    sal_warm_rst
}

proc set_pollara_frequency_1500 {} {
    sal_jtag_arm_nxc_ddr_pll_no_rdbk 60 0 2 1 1 64 1 0 1 0 64 1 2 1 1
    plog_msg "set_pollara_frequency :: Verify CLKs are at 1500 MHz"
    verify_arm_frequency 1500
    sal_warm_rst
}

proc set_pollara_frequency {{arm_freq "1500"}} {
    set card_type [sal_get_card_type]
    if { $card_type == "POLLARA" } {
        plog_msg "set_pollara_frequency :: Changing ARM frequency to $arm_freq"
        ## this sets frequency using jtag
        ## which will block the j2c connection
        ## therefore it can only work over onewire
        sal_ow
        if { $arm_freq == "3000"} {
            sal_set_pollara_freq
            plog_msg "wr sal0.ms.soc.cfg_clk 0x6"
            wr sal0.ms.soc.cfg_clk 0x6
        } elseif { $arm_freq == "2000" } {
            set_pollara_frequency_2000
        } elseif { $arm_freq == "1500" } {
            set_pollara_frequency_1500
        } elseif { $arm_freq == "1250" } {
            sal_set_pollara_freq_arm_1250
        } elseif { $arm_freq == "750" } {
            sal_set_pollara_freq_arm_750
        }
        sal_j2c
        clear_resetcode 0x0b
    }
    plog_msg "Measuring frequencies:"
    set freq_core  [sal_get_freq_core];    plog_msg "  freq_core:  $freq_core"
    set freq_stg   [sal_get_freq_stg];     plog_msg "  freq_stg:   $freq_stg"
    set freq_nxc   [sal_get_freq_nxc];     plog_msg "  freq_nxc:   $freq_nxc"
    set freq_nxc2  [sal_get_freq_nxc_by2]; plog_msg "  freq_nxc2:  $freq_nxc2"
    set freq_flash [sal_get_freq_flash];   plog_msg "  freq_flash: $freq_flash"
}

proc cpld_disable_wdt {} {
    plog_msg "Disabling WDT"
    set reg_data [ssi_cpld_read 0x1]
    ssi_cpld_write 0x1 [expr {$reg_data & 0xFD}]
}

proc sal_verify_arm_cntrs {} {
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

proc reset_to_proto_mode {{reset "cold"}} {
    cpld_disable_wdt
    if { $reset == "warm" } {
        sal_irstn_no_arm warm
        clear_resetcode 0x12
    } elseif { $reset == "cold" } {
        sal_irstn_no_arm cold
        clear_resetcode 0x15
    } elseif { $reset == "no_proto" } {
        sal_irstn_no_arm no_proto
        clear_resetcode 0x13
    }
    # verify ARM is truly in reset
    sal_arm_show_reset
    sal_verify_arm_cntrs
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
        plog_msg [exec inventory -sts -slot $::slot]
    }
}
