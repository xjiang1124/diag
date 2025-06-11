class DpnMfgDiagCmd_58_0007_01:
    """
    overwrite the command here if dpn based command or parameters are not same as the one defined in
    class MFG_DIAG_CMDS in module libdef.py
    also define dpn specific new commands here,
    then instant class MFG_DIAG_CMDS with parameters like MFG_DIAG_CMDS("58-0007-01", "dpn").MFG_MK_DIR_FMT
    """

    NIC_ESEC_SALINA_HMAC_FUSE_CHK_FMT = "./esec_ctrl.py -hmac_fuse_prog -slot {:d} -hmac_file check_only"
    MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT = "fpgautil command {:s} {:s} {:s} {:s}"
    # above two commands can be delete when there are real dpn specific command


class DpnMfgDiagCmd_58_0003_01:
    """
    overwrite the command here if dpn based command or parameters are not same as the one defined in
    class MFG_DIAG_CMDS in module libdef.py
    also define dpn specific new commands here,
    then instant class MFG_DIAG_CMDS with parameters like MFG_DIAG_CMDS("58-0007-01", "dpn").MFG_MK_DIR_FMT
    """

    NIC_ESEC_SALINA_HMAC_FUSE_CHK_FMT = "./esec_ctrl.py -hmac_fuse_prog -slot {:d} -hmac_file check_only"
    MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT = "fpgautil command {:s} {:s} {:s} {:s}"
    # above two commands can be delete when there are real dpn specific command

dpnMfgDiagCmd = {
    "58-0007-01" : DpnMfgDiagCmd_58_0007_01,
    "58-0003-01" : DpnMfgDiagCmd_58_0003_01,
}