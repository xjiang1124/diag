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

proc verify_arm_frequency {{arm_freq "1500"}} {
    return [sal_PLL_SYSPLL_T_ARM_PLL_DFX_CLK_OBS $arm_freq]
}

proc verify_nxc_frequency {{nxc_freq 750}} {
    set exp_freq [expr {$nxc_freq/10}]
    set got_freq [sal_jtag_nxc_clk_obs_pad]
    if {[expr {$exp_freq - $got_freq}] > 1} {
        plog_err "set_pollara_frequency :: Incorrect NXC frequency, expecting $nxc_freq Mhz, got $got_freq"
        return -1
    }
    return 0
}

proc verify_frequencies {} {
    set card_type [sal_get_card_type]
    if { $card_type != "POLLARA" } {
        # not supported
        plog_msg "set_pollara_frequency :: not pollara, skipping verify_arm_frequency"
        return 0
    }
    verify_arm_frequency
    verify_nxc_frequency
}

proc set_pollara_frequency {{arm_freq "none"}} {
    set card_type [sal_get_card_type]
    if { $arm_freq != "none" && $card_type == "POLLARA" } {
        plog_msg "set_pollara_frequency :: Changing ARM frequency to $arm_freq"
        ## this sets frequency using jtag
        ## which will block the j2c connection
        ## therefore it can only work over onewire
        sal_ow

        # keep setting until readback is correct
        for {set retry 0} {$retry < 3} {incr retry} {
            if { $arm_freq == "2000" } {
                sal_jtag_arm_nxc_ddr_pll_no_rdbk 40 0 1 1 1 64 1 0 1 0 64 1 2 1 1
            } elseif { $arm_freq == "1500" } {
                # sal_jtag_arm_nxc_ddr_pll_no_rdbk 60 0 2 1 1 64 1 0 1 0 64 1 2 1 1
                ## above command only sets some clocks.
                ## if UFM1 is in play, it may change other clocks MBIST relies on so above command is not enough.
                ## using below command will reconfigure ALL clocks:
                ## arm core ddr eth flash gmac stg nxc fcw0 refclk postdiv dpll pll_out_sel
                sal_pll_lock_max 60 1 1 1 0 44 1 1 3 1 64 1 0 1 0 44 1 1 3 1 32 2 1 2 1 40 1 1 3 1 60 1 1 1 1 60 2 1 2 1
            }
            plog_msg "set_pollara_frequency :: Verifying CLKs are at $arm_freq MHz"
            if {[verify_arm_frequency $arm_freq] != 0} {
                plog_msg "set_pollara_frequency :: Could not read consistent ARM frequency on clk_obs...retrying."
                plog_clr_err_count
                continue
            } else {
                break
            }
        }
        if {$retry == 3} {
            plog_err "set_pollara_frequency :: Could not read consistent ARM frequency on clk_obs...aborting."
        }
    } else {
        plog_msg "set_pollara_frequency :: skipping changing PLLs by JTAG sequence"
    }
    plog_msg "set_pollara_frequency :: running with repairs"; sal_jtag_smsg_ctrl_saferr
    sal_j2c
    sal_cpld_warm_reset
    clear_resetcode 0x12
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
    if { $reset != "no_proto" } { sal_verify_arm_cntrs }
    cpld_disable_wdt
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
