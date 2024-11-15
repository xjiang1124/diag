proc clear_resetcode {} {
    plog_msg "Clearing CPLD resetcode register"
    ssi_cpld_write 0x30 0x0
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
    }
}

proc set_pollara_frequency {} {
    set card_type [sal_get_card_type]
    if { $card_type == "POLLARA" } {
        plog_msg "Lowering pollara frequency"
        ## this sets frequency using jtag
        ## which will block the j2c connection
        ## therefore it can only work over onewire
        sal_ow
        sal_set_pollara_freq
        sal_j2c
        # redo proto mode
        sal_proto_mode_unreset
        clear_resetcode
        plog_msg "nxc   freq: [sal_get_freq_nxc]"
        plog_msg "nxc_2 freq: [sal_get_freq_nxc_by2]"
    }
}

proc reset_to_proto_mode {} {
    # Avoid getting a VRD fault on Leni when
    #  protomode is set while ARM is running
    #  Ensure ARM is in reset, other cores out of reset
    #
    # The 2nd unreset may throw a VRD fault too
    #  To avoid that, put ARM in reset after sal_pc.
    #
    # Despite this, there is a timing issue, sometimes it works.
    sal_set_proto_mode 0
    sal_proto_mode_unreset
    plog_msg "Clearing expected VRD fault"
    #sal_tps53688_clear_fault 2 0x60 0
    sal_smbus_write_byte_data 2 0x60 0x0 0x0
    sal_smbus_write_byte 2 0x60 0x03
    set card_type [sal_get_card_type]
    if { $card_type != "POLLARA" } {
        #sal_tps53688_clear_fault 2 0x60 1
        sal_smbus_write_byte_data 2 0x60 0x0 0x1
        sal_smbus_write_byte 2 0x60 0x03
    }
    clear_resetcode
    plog_msg "Disabling WDT"
    ssi_cpld_write 0x1 0x0
    sal_arm_show_reset
    plog_msg "sal_soc_dump_slv_cntrs"
    sal_soc_dump_slv_cntrs
    plog_msg "sal_soc_dump_mst_cntrs"
    sal_soc_dump_mst_cntrs
    sal_dump_cpld_regs
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