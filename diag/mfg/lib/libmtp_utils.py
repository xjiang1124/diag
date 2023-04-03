"""
    Utilities of MTP
"""

from libdefs import MTP_DIAG_Path

def check_mtp_host_nic_presence(mtp_mgmt_ctrl, host_nic_device="i210"):
    """
    This function check if MTP host nic device is present.

    Parameters
    ----------
    mtp_mgmt_ctrl : object
        instance of class mtp_ctrl
    host_nic_device : str, optional
        A Inidicator of the MTP NIC device Name  (default is Intel i210)

    Returns
    -------
    Boolean
        True if MTP NIC device check pass
        False if MTP NIC device check failed
    """

    ret = True
    if host_nic_device.lower() == 'i210':
        cmd = "cd {:s}{:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH, "tools/i210")
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "./eeupdate64e"
        rs = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd_resp(cmd)
        if rs.startswith("[FAIL]:"):
            ret = False
            mtp_mgmt_ctrl.cli_log_err("MTP I210 command failed.{:s}".format(cmd), level=0)
            mtp_mgmt_ctrl.cli_log_err(rs)
        else:
            if "8086-1537" in rs  and "Intel(R) I210 Gigabit Backplane Connection" in rs and "8086-1533" in rs and "Intel(R) I210 Gigabit Network Connection" in rs:
                mtp_mgmt_ctrl.cli_log_inf("MTP Host NIC I210 Presence Check Pass.", level=0)
            else:
                mtp_mgmt_ctrl.cli_log_err("MTP Host NIC I210 Presence Check Fail.", level=0)
                mtp_mgmt_ctrl.cli_log_err(rs)
                ret = False
    else:
        mtp_mgmt_ctrl.cli_log_err("Check on MTP NIC device {:s} not support yet".format(host_nic_device), level=0)
        ret = False
        pass

    return ret