proc mtp_shell_sanity_check { powercycle } {
    #salina ms scratch reg
    set sanity_check_addr   0x60f80000
    #vulcano ms scratch reg
    #if {$::VEL_SHELL} {
    set sanity_check_addr  0x10600000
    #}

    if {$powercycle == 0} {
        set val 13
        vul_reg_write $sanity_check_addr $val
        set val2 [vul_reg_read $sanity_check_addr]
        if {$val2 != $val} {
            plog_msg "\[ERROR\] write $val to ms scratch reg 0x[format %08X $sanity_check_addr], but read $val2"
            return 0
        }
        vul_reg_write $sanity_check_addr 1
    }

    set val2 [vul_reg_read $sanity_check_addr]
    if {$val2 == 1} {
        plog_msg "==================================="
        plog_msg "read 1 from ms scratch reg 0x[format %08X $sanity_check_addr], sanity check PASSED"
        plog_msg "==================================="
        return 1
    } else {
        plog_err "==================================="
        plog_err "\[ERROR\] read $val2 from ms scratch reg 0x[format %08X $sanity_check_addr], sanity check FAILED"
        plog_err "==================================="
        return 0
    }

}
