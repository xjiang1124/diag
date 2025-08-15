"""
    Utilities of MTP
"""
import time
import re
import os
import libmfg_utils
import json
import image_control
import random
import pexpect

from libdefs import MTP_DIAG_Path
from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import MTP_TYPE
from threading import Thread

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
    if mtp_mgmt_ctrl._mtp_type == MTP_TYPE.MATERA:
        host_nic_device = "BCM5720"

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
    elif host_nic_device.lower() == "bcm5720":
        # not implemented
        ret = True
    else:
        mtp_mgmt_ctrl.cli_log_err("Check on MTP NIC device {:s} not support yet".format(host_nic_device), level=0)
        ret = False
        pass

    return ret

def mtp_usb_fdisk_format(mtp_mgmt_ctrl, timeout=300):
    '''
    unmount /dev/sda1
    delete partion and re-create new partition with fdisk
    then make ext4 file system, using ext4 because ntfs take almost an hour to format the partition
    '''

    cmd = 'umount -f /dev/sda1'
    cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd_resp(cmd, timeout=timeout)
    cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()

    # delete and create a new partition
    cmd = 'echo -e "d\\nn\\np\\n1\\n\\n\\nw" | fdisk /dev/sda'
    cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd_resp(cmd, timeout=timeout)
    if not cmd_result:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False
    cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    # Refresh the Partition Table
    cmd = 'partprobe /dev/sda'
    cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd_resp(cmd, timeout=timeout)
    if not cmd_result:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False
    cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    # make file system
    cmd = 'mkfs.ext4 /dev/sda1'
    userid = mtp_mgmt_ctrl._mgmt_cfg[1]
    passwd = mtp_mgmt_ctrl._mgmt_cfg[2]
    mtp_mgmt_ctrl._mgmt_handle.sendline("sudo -k " + cmd)
    cmd_result = ""
    while True:
        idx = mtp_mgmt_ctrl._mgmt_handle.expect_exact([
            pexpect.TIMEOUT,
            pexpect.EOF,
            userid + ":",
            mtp_mgmt_ctrl._mgmt_prompt,
            "Proceed anyway",
            "Creating journal",
            "Writing superblocks and filesystem accounting information:"
            ], timeout=timeout)
        if idx == 0:
            mtp_mgmt_ctrl.cli_log_err("Command {:s} timeout".format(cmd))
            print(mtp_mgmt_ctrl._mgmt_handle.before)
            mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl._mgmt_handle.before)
            return False
        elif idx == 1:
            mtp_mgmt_ctrl.cli_log_err("Command {:s} run into EOF".format(cmd))
            print(mtp_mgmt_ctrl._mgmt_handle.before)
            mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl._mgmt_handle.before)
            return False
        elif idx == 2:
            print(passwd)
            mtp_mgmt_ctrl._mgmt_handle.sendline(passwd)
            cmd_result += mtp_mgmt_ctrl._mgmt_handle.before
            continue
        elif idx == 3:
            print(3)
            mtp_mgmt_ctrl.cli_log_inf("Command {:s} compelte")
            cmd_result += mtp_mgmt_ctrl._mgmt_handle.before
            break
        elif idx == 4:
            print( "Proceed anyway 4-Y")
            mtp_mgmt_ctrl._mgmt_handle.sendline("y")
            cmd_result += mtp_mgmt_ctrl._mgmt_handle.before
            continue
        elif idx == 5:
            print("5 Creating journal")
            mtp_mgmt_ctrl._mgmt_handle.sendline("")
            cmd_result += mtp_mgmt_ctrl._mgmt_handle.before
            continue
        elif idx == 6:
            print("6 Writing superblocks and filesystem accounting information:")
            mtp_mgmt_ctrl._mgmt_handle.sendline("")
            cmd_result += mtp_mgmt_ctrl._mgmt_handle.before
            continue
    if not cmd_result:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False

    return True

def check_mtp_usb_drive_prepare(mtp_mgmt_ctrl, devicetype='usb', timeout=10):
    """probe if use drive existing, if the device is existing but not mount, it will try to mount it to /home/diag/usb

    Args:
        mtp_mgmt_ctrl (_type_): _description_
        devicetype (str, optional): _description_. Defaults to 'usb'.
    """

    parse_result = {}
    mount_point = ""
    cmd = 'lsblk -o NAME,TRAN,SIZE,MODEL,MOUNTPOINTS'
    mtp_mgmt_ctrl.cli_log_inf(cmd)
    cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=timeout)
    if not cmd_result:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False
    cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    if devicetype.lower() not in cmd_result.lower() or 'sda1' not in cmd_result.lower():
        mtp_mgmt_ctrl.cli_log_err("{:s} device not found".format(devicetype))
        mtp_mgmt_ctrl.cli_log_err(cmd_result)
        return False
    for line in cmd_result.split("\n"):
        if devicetype.lower() in line:
            size = line.split()[2].strip()
            model = " ".join(line.split()[3:]).strip()
        if 'sda1' in line:
            mount_point = "" if len(line.split()) == 2 else line.split()[-1]

    if not mount_point:
        # try to mount use to /home/diag/usb
        my_mount_point = '/home/diag/usb'
        cmd = 'ls {:s}'.format(my_mount_point)
        cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=timeout)
        if not cmd_result:
            mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
            return False
        cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        if 'No such file or directory'.lower() in cmd_result.lower():
            cmd = 'mkdir {:s}'.format(my_mount_point)
            cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=timeout)
            if not cmd_result:
                mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
                return False
        cmd = 'mount /dev/sda1 {:s}'.format(my_mount_point)
        cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd(cmd, timeout=timeout)
        if not cmd_result:
            mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
            return False
        cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        if 'error' in cmd_result.lower() or 'wrong' in cmd_result.lower():
            mtp_mgmt_ctrl.cli_log_inf('Mount USB Failed, retry after delete partition and re-create a new partition, then format the USB drive')
            # start from partion and format the usb drive
            if not mtp_usb_fdisk_format(mtp_mgmt_ctrl):
                return False
            cmd = 'mount /dev/sda1 {:s}'.format(my_mount_point)
            cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd(cmd, timeout=timeout)
            if not cmd_result:
                mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
                return False
        mount_point = my_mount_point

    parse_result["SIZE"] = size
    parse_result["MODEL"] = model
    parse_result["MOUNTPOINTS"] = mount_point
    return parse_result

def mtp_usb_sanity_check(mtp_mgmt_ctrl):
    """run mtp usb sanity check. return False if Failed, return USB drive infomation if pass

    Args:
        mtp_mgmt_ctrl (_type_): _description_
        devicetype (str, optional): _description_. Defaults to 'usb'.
    """
    usb_drive_detected = False
    max_retries = 3

    while not usb_drive_detected:
        if max_retries == 0:
            break
        usb_drive_detected = check_mtp_usb_drive_prepare(mtp_mgmt_ctrl)
        if not usb_drive_detected:
            input("Please insert the USB Drive or replace new USB Drive then press any key to continue.\nWARNING: do not power off the MTP yet. ")
            mtp_mgmt_ctrl.cli_log_inf("Re-running sanity check...")
            max_retries -= 1

    return usb_drive_detected


def verify_img_mtp_host_nic(mtp_mgmt_ctrl, host_nic_device="i210"):
    if host_nic_device.lower() == "i210":
        cmd = "./eeupdate64e /NIC=1 /D=Dev_Start_I210_SerdesBX_NOMNG_16Mb_A2.bin"
        rs = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd_resp(cmd)
        if rs.startswith("[FAIL]:"):
            mtp_mgmt_ctrl.cli_log_err("MTP I210 command failed.{:s}".format(cmd), level=0)
            return False
        if "8086-1537" in rs and "8086-1533" in rs: 
            mtp_mgmt_ctrl.cli_log_inf("MTP I210 second command response Pass.", level=0)
            return True
        else:
            mtp_mgmt_ctrl.cli_log_err("MTP I210 second command response Fail.", level=0)
            return False
    else:
        mtp_mgmt_ctrl.cli_log_err("Check on MTP NIC device {:s} not support yet".format(host_nic_device), level=0)
        return False

def load_cpld_info_json(cpld_json_file, verbosity=False):
    """
    load new cpld bibary file info json file.
    return a dict
    """

    new_cpld_info = dict()
    try:
        with open(cpld_json_file) as json_file:
            new_cpld_info = json.load(json_file, parse_float=str, parse_int=str, parse_constant=str)
    except Exception as Err:
        print(str(Err))
        print("Failed to Load the New Version of CPLD JSON file, abort...")
        return
    else:
        if verbosity:
            print(new_cpld_info)

    return new_cpld_info

def generate_cpld_img_full_path_list(cpld_json_dict, verbosity=False):
    """
    generate a list of a full path cpld file name from pass in dict.
    return a list
    """

    cpld_files_with_path = []
    try:
        for images in list(cpld_json_dict.values()):
            for k, image_files in list(images.items()):
                if k == "working_imge" or k == "failsafe_imge" or k == "secure_imge" or k == "special_boot0_imge":
                    file_full_path = image_files["file_location"] + os.sep + image_files["name"]
                    if file_full_path not in cpld_files_with_path and image_files["name"]:
                        cpld_files_with_path.append(file_full_path)
    except Exception as Err:
        print(str(Err))
        print("Failed to Generate CPLD Binary File Full Path list from JSON dict, abort...")
        return
    else:
        if verbosity:
            print(cpld_files_with_path)

    return cpld_files_with_path

def mtp_issue_3v3powercycle(mtp_mgmt_ctrl, slot, pc_iter=100):
    """
    send turn on 3v3 before power on 12v command sequence in given MTP session.
    return True or False
    """

    pc_cmd = "turn_on_slot.sh off {:d}; ".format(slot+1)
    pc_cmd += "sleep 10; "
    pc_cmd += "turn_on_slot_3v3_new.sh on {:d}; ".format(slot+1)
    pc_cmd += "turn_on_slot.sh on {:d}".format(slot+1)

    for ite in range(1, pc_iter+1):
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "3V3_POWER_CYCLE Iteration {:d}, CMD: {:s}".format(ite, pc_cmd), level=0)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(pc_cmd):
            mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
            mtp_mgmt_ctrl.cli_log_err("Failed to execute 3V3_POWER_CYCL command", level = 0)
            return False
        time.sleep(MTP_Const.NIC_CON_INIT_DELAY)
    return True

def mtp_issue_ac_powercycle(mtp_mgmt_ctrl, slot, iteration_index):
    """
    send turn off/on 12v command sequence in given MTP session.
    return True or False
    """

    pc_cmd = "turn_on_slot.sh off {:d}; ".format(slot+1)
    pc_cmd += "sleep 10; "
    pc_cmd += "turn_on_slot.sh on {:d}".format(slot+1)

    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "AC power cycle at iteration {:d}, CMD: {:s}".format(iteration_index, pc_cmd), level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(pc_cmd):
        mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
        mtp_mgmt_ctrl.cli_log_err("Failed to execute AC power cycle command", level = 0)
        return False
    time.sleep(MTP_Const.NIC_CON_INIT_DELAY)
    return True

def mtp_issue_turn_on_slot(mtp_mgmt_ctrl, slot):
    """
    only send turn on 12v command sequence in given MTP session.
    return True or False
    """

    cmd = "turn_on_slot.sh on {:d}".format(slot+1)
    #mtp_mgmt_ctrl.cli_log_slot_inf(slot, "sending turn on slot CMD: {:s}".format(cmd), level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
        mtp_mgmt_ctrl.cli_log_err("Failed to send {:s} command".format(cmd), level = 0)
        return False
    time.sleep(MTP_Const.NIC_CON_INIT_DELAY)
    return True

def cpld_and_diag_boot_log_parser(mtp_mgmt_ctrl, slot,  logstring=None, occurrences=1, bootCheckStr=None, cpldId=None, cpldMajorVer=None, cpldMinorVer=None, cpldAsicCtrlReg=None):
    """
    parse the CPLD log (print out by boot0) and diagfw log (diagfw u-boot and diagfw), check the given signature
    return True or False
    """

    boot_check_strings = []
    cpld_ids = []
    cpld_major_vers = []
    cpld_minor_vers = []
    cpld_aisc_ctrl_register = []
    result = True

    if not any([bootCheckStr, cpldId, cpldMajorVer, cpldMinorVer, cpldAsicCtrlReg]):
        return result

    tmp = []
    for line in logstring.split("\n"):
        #remove control characters
        line = "".join(ch for ch in line if ord(ch) >= 30 and ord(ch) <= 127)
        # remove dulipicated word
        line = " ".join(list(set(re.split(r'\s+', line))))
        if line not in tmp:
            tmp.append(line)
        if cpldMajorVer and "0x0-" in line and "end" in line and "reg" in line:
            cpld_major_vers.append(tuple(tmp))
            tmp = []
        elif cpldMinorVer and "0x1e-" in line and "end" in line and "reg" in line:
            cpld_minor_vers.append(tuple(tmp))
            tmp = []
        elif cpldId and "0x80-" in line and "end" in line and "reg" in line:
            cpld_ids.append(tuple(tmp))
            tmp = []
        elif cpldAsicCtrlReg and "0x12-" in line  and "end" in line and "reg" in line:
            cpld_aisc_ctrl_register.append(tuple(tmp))
            tmp = []
        elif bootCheckStr and bootCheckStr in line:
            boot_check_strings.append(bootCheckStr)
            tmp = []

    if bootCheckStr:
        if len(boot_check_strings) < occurrences:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, 'The Signature String "{:s}" show up in boot Log occurn {:d},  not meet expected occurrences: {:d}'.format(bootCheckStr, len(boot_check_strings), occurrences))
            result = False
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, 'Boot String: "{:s}" founded in given diag boot log and meet expected occurrences'.format(bootCheckStr))

    if cpldMajorVer:
        if len(cpld_major_vers) != occurrences:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, 'The Section of CPLD Major Version Log occurrences {:d},  not match expected occurrences: {:d}'.format(len(cpld_major_vers), occurrences))
            result = False
        else:
            item_result = True
            for ite, cpld_major in enumerate(cpld_major_vers):
                matched = False
                for c_major in cpld_major:
                    if cpldMajorVer in c_major:
                        matched = True
                        break
                if not matched:
                    result = False
                    item_result = False
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, 'Specified CPLD Major Version: {:s} NOT Found in BOOT0 log at iteration {:d}'.format(cpldMajorVer, ite+1))
            if item_result:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, 'CPLD Major Version From BOOT0 Match Expected Value: {:s}'.format(cpldMajorVer))

    if cpldMinorVer:
        if  len(cpld_minor_vers) != occurrences:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, 'The Section of CPLD Minor Version Log occurrences {:d},  not match expected occurrences: {:d}'.format(len(cpld_minor_vers), occurrences))
            result = False
        else:
            item_result = True
            for ite, cpld_minor in enumerate(cpld_minor_vers):
                matched = False
                for c_minor in cpld_minor:
                    if cpldMinorVer in c_minor:
                        matched = True
                        break
                if not matched:
                    result = False
                    item_result = False
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, 'Specified CPLD Minor Version: {:s} NOT Found in BOOT0 log at iteration {:d}'.format(cpldMinorVer, ite+1))
            if item_result:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, 'CPLD Minor Version From BOOT0 Match Expected Value: {:s}'.format(cpldMinorVer))

    if cpldId:
        if len(cpld_ids) != occurrences:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, 'The Section of CPLD ID Log occurrences {:d},  not match expected occurrences: {:d}'.format(len(cpld_ids), occurrences))
            result = False
        else:
            item_result = True
            for ite, cpld_id in enumerate(cpld_ids):
                matched = False
                for c_id in cpld_id:
                    if cpldId in c_id:
                        matched = True
                        break
                if not matched:
                    result = False
                    item_result = False
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, 'Specified CPLD ID: {:s} NOT Found in BOOT0 log at iteration {:d}'.format(cpldId, ite+1))
            if item_result:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, 'CPLD ID From BOOT0 Match Expected Value: {:s}'.format(cpldId))

    if cpldAsicCtrlReg:
        if len(cpld_aisc_ctrl_register) != occurrences:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, 'The Section of CPLD ASIC Control Register occurrences {:d},  not match expected occurrences: {:d}'.format(len(cpld_aisc_ctrl_register), occurrences))
            result = False
        else:
            item_result = True
            for ite, cpld_aisc_ctrl in enumerate(cpld_aisc_ctrl_register):
                matched = False
                for c_asic in cpld_aisc_ctrl:
                    if cpldAsicCtrlReg in c_asic:
                        matched = True
                        break
                if not matched:
                    result = False
                    item_result = False
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, 'Specified CPLD ASIC Contrl Register 0x12: {:s} NOT Found in BOOT0 log at iteration {:d}'.format(cpldAsicCtrlReg, ite+1))
            if item_result:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, 'CPLD ASIC Contrl Register 0x12 From BOOT0 Match Expected Value: {:s}'.format(cpldAsicCtrlReg))

    return result

def cpld_version_compare(mtp_mgmt_ctrl, slot, expMajorVer=None, expMinorVer=None, expNanoVer=None):
    """
    Read CPLD versions by SPI bus, id expected value passed in, compare, otherwise versions display only
    return True or False
    """

    rc = True
    read_reg_cmd_list = ["cpldapp -r {:s}", "/data/nic_util/xo3dcpld -r {:s}"]

    # read and compare major version
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_exec_cmd(random.choice(read_reg_cmd_list).format("0x00")):
        rc = False
    if rc and expMajorVer:
        cur_ver = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1].strip("\r")
        if int(cur_ver.lower(), 16) != int(expMajorVer.lower(), 16):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Current CPLD major version: {:s} NOT match expected major version: {:s}".format(cur_ver.lower(), expMajorVer.lower()), level=0)
            rc = False
    # read and compare minor version
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_exec_cmd(random.choice(read_reg_cmd_list).format("0x1e")):
        rc = False
    if rc and expMinorVer:
        cur_ver = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1].strip("\r")
        if int(cur_ver.lower(), 16) != int(expMinorVer.lower(), 16):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Current CPLD minor version: {:s} NOT match expected minor version: {:s}".format(cur_ver.lower(), expMinorVer.lower()), level=0)
            rc = False
    # read and compare nano version
    if not  mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_exec_cmd(random.choice(read_reg_cmd_list).format("0x1f")):
        rc = False
    if rc and expNanoVer:
        cur_ver = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1].strip("\r")
        if int(cur_ver.lower(), 16) != int(expNanoVer.lower(), 16):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Current CPLD nano version: {:s} NOT match expected nano version: {:s}".format(cur_ver.lower(), expNanoVer.lower()), level=0)
            rc = False
    return rc

def cpld_3v3_powercycle_test(mtp_mgmt_ctrl, slot, new_cpld_json_dict, pc_cycles=100):
    """
    For MTP, to see the console print of registers 0x0, 0x1E, 0x80, 0x12 from special boot0 image, we need turn on 3.3V first, then turn on 12v.
    """

    rc = True
    pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot)    # get the PN format like this 68-0015-02 01 or 0X322F X/A
    pn = pn.split()[0]
    first6_pn = pn[0:7] if "-" in pn else pn[0:6]
    pn = first6_pn

    # new cpld version, validation target.
    new_working_img_ver = new_cpld_json_dict[pn]["working_imge"]["version"]
    expMajorVer = "%02x" % int(new_working_img_ver.lower(), 16)
    new_working_img_min_ver = new_cpld_json_dict[pn]["working_imge"]["minor_version"]
    expMinorVer = "%02x" % int(new_working_img_min_ver.lower(), 16)

    if mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_attach_without_login():
        # run power cycle tests in two thread, one is power cycle, the other one is monitoring booting
        t1 = Thread(target=mtp_mgmt_ctrl._nic_ctrl_list[slot].wait_nic_bootup, args=[pc_cycles])
        t2 = Thread(target=mtp_issue_3v3powercycle, args=[mtp_mgmt_ctrl, slot, pc_cycles])
        t1.start()
        time.sleep(1)
        t2.start()
        for t in (t1, t2):
            t.join()

        result = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf()
        if not cpld_and_diag_boot_log_parser(mtp_mgmt_ctrl, slot, logstring=result, occurrences=pc_cycles, bootCheckStr="login",  cpldMajorVer=expMajorVer, cpldMinorVer=expMinorVer):
            rc = False
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_detach():
            rc = False

        return rc

def cpld_gpio3_powercycle_test(mtp_mgmt_ctrl, slot, pc_cycles=100, stop_on_err=False):
    """
    call sysreset.sh which will toggle gpio3 and let NIC card power cycle
    """

    rc = True
    for i in range(1, pc_cycles+1):
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "GPIO3 POWER CYCLE Iteration {:d}".format(i), level=0)
        if  not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_call_sysresetsh():
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC did not boot to login after sysreset.sh command")
            rc = False
        result = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf()
        if not cpld_and_diag_boot_log_parser(mtp_mgmt_ctrl, slot, logstring=result, occurrences=1, bootCheckStr="Restarting system"):
            rc = False
        if not rc and stop_on_err:
            return rc
    return rc

def cpld_ac_powercycle_test(mtp_mgmt_ctrl, slot, pc_cycles=100, stop_on_err=False, expMajorVer=None, expMinorVer=None):
    """
    Call turn_on_slot.sh off {slot}, then turn_on_slot.sh on {slot} to AC cycle the NIC cards
    """

    rc = True
    if mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_attach_without_login():
        for i in range(1, pc_cycles+1):
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "AC POWER CYCLE AT Iteration {:d}".format(i), level=0)

            # run power cycle tests in two thread
            t1 = Thread(target=mtp_mgmt_ctrl._nic_ctrl_list[slot].wait_nic_bootup, args=[1, "login"])
            t2 = Thread(target=mtp_issue_ac_powercycle, args=[mtp_mgmt_ctrl, slot, i])
            t1.start()
            time.sleep(1)
            t2.start()
            for t in (t1, t2):
                t.join()

            result = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf()
            if not cpld_and_diag_boot_log_parser(mtp_mgmt_ctrl, slot, logstring=result, occurrences=1, bootCheckStr="login", cpldMajorVer=expMajorVer, cpldMinorVer=expMinorVer):
                rc = False

            if not rc and stop_on_err:
                if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_detach():
                    rc = False
                return rc
            time.sleep(1)

        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_detach():
            rc = False
    return rc

def cpld_cpldapp_reload(mtp_mgmt_ctrl, slot, iteration_index):
    """
    send cpldapp from console session of mtp_mgmt_ctrl, then send turn on 12v only in given MTP session.
    return True or False
    """
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "cpldapp reload power cycle at Iteration {:d}, CMD: {:s}".format(iteration_index, "cpldapp -reload"), level=0)
    mtp_mgmt_ctrl._nic_ctrl_list[slot]._nic_handle.sendline("cpldapp -reload")
    # after 'cpldapp -reload' command, console will default to three pin header, send a turn on slot command to bring the console to mtp
    if not mtp_issue_turn_on_slot(mtp_mgmt_ctrl, slot):
        return False
    return True

def cpld_console_program(mtp_mgmt_ctrl, slot, progCmd, imgFile, writePartition="cfg0", iterIndex=1, expMajorVer=None, expMinorVer=None, expNanoVer=None, expBootPartion=None):
    """
    Program CPLD in a console session, check NIC card can boot to login after power cycle.
    if expected versions or expected boot partion specified, verify them.
    return False if any above failed
    """

    cpldapp_verifyid_cmd = "cpldapp -verifyid"
    rc = True
    expBootPartionMask = 0b00000100
    if expBootPartion == 'cfg0':
        expBootPartionValue = 0
    if expBootPartion == 'cfg1':
        expBootPartionValue = 4

    # run upgrade from console
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_login():
        rc = False
    # display current running version when first upgrade
    if iterIndex <= 1:
        if not cpld_version_compare(mtp_mgmt_ctrl, slot):
            rc = False
    # Program CPLD
    prog_cmd = progCmd.format(imgFile, writePartition)
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Programming with CMD: {:s}".format(prog_cmd), level=0)
    if not  mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_exec_cmd(prog_cmd):
        rc = False
    if not  mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_exec_cmd(cpldapp_verifyid_cmd):
        rc = False
    # power cycle card
    pc_func = random.choice([mtp_issue_ac_powercycle, cpld_cpldapp_reload])
    if not pc_func(mtp_mgmt_ctrl, slot, iterIndex):
        rc = False
    # bootup
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].wait_nic_bootup(1, "login"):
        rc = False
    result = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf()
    if not cpld_and_diag_boot_log_parser(mtp_mgmt_ctrl, slot, logstring=result, occurrences=1, bootCheckStr="login"):
        rc = False
    # re-login after bootup
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_login():
        rc = False
    # verify boot partition
    read_reg_cmd_list = ["cpldapp -r {:s}", "/data/nic_util/xo3dcpld -r {:s}"]
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_exec_cmd(random.choice(read_reg_cmd_list).format("0x01")):
        rc = False
    if rc and expBootPartion in ('cfg0', 'cfg1'):
        cur_val = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1].strip("\r")
        if int(cur_val.lower(), 16) & expBootPartionMask != expBootPartionValue:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Current CPLD boot partion(register 0x01) : {:s} NOT match expected major version: 0x0{:x}".format(cur_val.lower(), expBootPartionValue), level=0)
            rc = False
    # compare version after upgrade
    if not cpld_version_compare(mtp_mgmt_ctrl, slot, expMajorVer, expMinorVer, expNanoVer):
        rc = False

    return rc

def cpld_upgrade_downgrade_utility_function_test(mtp_mgmt_ctrl, slot, new_cpld_json_dict, pc_cycles=100, stop_on_err=False):

    """
    Upgrade/Downgrade Function and Stress Test:
        This test will loop update/downgrade working image with FW utility cpldapp or Diag utility xo3dcpld, which script will random choice. In every iteration, script will excute following steps:
        1. Upgrade. Load new working CPLD binary file to flash, and make sure CPLD is functional after power cycle. Following steps are example with FW utility cpldapp command format 
            Display CPLD current running version before load
            cpldapp -r 0x0      ### major version portion
            cpldapp -r 0x1e     ### minor version portion
            cpldapp -r 0x1f     ### nano version portion
            cpldapp -writeflash <working binary file name> cfg0
            cpldapp -verifyid
            cpldapp -reload
            verify CPLD running the correct version
            ### Tips: "cpldapp -reload" command will switch cpld console output to three pin headers, to switch back to MTP,  run turn_on_slot.sh on <slot> even when card already on.   
        2. Downgrade. Load MFG released working image file to flash,and make sure CPLD is functional after power cycle. Following steps are example with Diag Utility /data/nic_util/xo3dcpld format
            /data/nic_util/xo3dcpld -prog <file name> cfg0
            power cycle NIC with turn_on_slot.sh utility
            Read and compare CPLD running version
            /data/nic_util/xo3dcpld -r 0x0      ### major version portion
            /data/nic_util/xo3dcpld -r 0x1e     ### minor version portion
            /data/nic_util/xo3dcpld -r 0x1f     ### minor version portion
            2.2 Upgrade working image.
            ### Tips: cfg0 means to program working image; cfg1 means to program failsafe image
            ### Tips: before using xo3dcpld, we need make sure emmc partition 10 /dev/mmcblk0p10  mount to /data,  then untar ARM diag image to /data, in which xo3dcpld bundled in.
                Run 'cd ~/diag/python/regression; ./nic_test.py -setup_multi -slot_list $slot -mgmt' from MTP to mount emmc to /data and config IP address for NIC
                copy arm diag image to NIC,  scp /home/diag/ image_arm64_giglio.tar root@10.1.1.104:/data/
                untar diag image to /data, tar xf /data/image_arm64_elba.tar -C /data/
        3. Loop above steps in specified iterations as stress test. Return if failed and stop_on_err
    Negative Test
        1. Erase cfg0 using Diag utility xo3dcpld, check failover boot to failsafe
            /data/nic_util/xo3dcpld -erase cfg0
            Power cycle NIC, using cpldapp or turn_on_slot.sh, check CPLD boot from gold
            #cpldapp -reload
            # ./xo3dcpld -r 0x01  from NIC or inventory -sts -slot 9 from MTP,
            It should 04, which indicate CPLD boot from gold
            ###Tips:  Check Ginestra CPLD register definition for bitwise description
        2. Program main, make sure it can boot from main.
    """

    pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot)    # get the PN format like this 68-0015-02 01 or 0X322F X/A
    pn = pn.split()[0]
    first6_pn = pn[0:7] if "-" in pn else pn[0:6]
    pn = first6_pn
    stage = FF_Stage.FF_DL
    dest_dir = "/data/"
    prog_cmd_list = ["cpldapp -writeflash {:s} {:s}", "/data/nic_util/xo3dcpld -prog {:s} {:s}"]

    # new cpld version, validation target.
    new_working_img_file =  MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + new_cpld_json_dict[pn]["working_imge"]["name"]
    new_working_img_ver = new_cpld_json_dict[pn]["working_imge"]["version"]
    new_working_img_min_ver = new_cpld_json_dict[pn]["working_imge"]["minor_version"]
    new_working_img_nano_ver = new_cpld_json_dict[pn]["working_imge"]["nano_version"]
    new_working_img_sha512sum = new_cpld_json_dict[pn]["working_imge"]["sha512sum"]
    new_failsafe_img_file =  MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + new_cpld_json_dict[pn]["failsafe_imge"]["name"]
    new_failsafe_img_ver = new_cpld_json_dict[pn]["failsafe_imge"]["version"]
    new_failsafe_img_min_ver = new_cpld_json_dict[pn]["failsafe_imge"]["minor_version"]
    new_failsafe_img_nano_ver = new_cpld_json_dict[pn]["failsafe_imge"]["nano_version"]
    new_failsafe_img_sha512sum = new_cpld_json_dict[pn]["failsafe_imge"]["sha512sum"]
    # old cpld version, usisng current MFG released cpld version.
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    old_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, stage)["filename"]
    old_cpld_img_ver   = image_control.get_cpld(mtp_mgmt_ctrl, slot, stage)["version"]
    old_cpld_img_min_ver = image_control.get_cpld(mtp_mgmt_ctrl, slot, stage)["timestamp"]
    old_failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, stage)["filename"]
    old_fea_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fea_cpld(mtp_mgmt_ctrl, slot, stage)["filename"]

    # copy cpld image files from MTP to NIC
    for cpld_img_file in [new_working_img_file, new_failsafe_img_file, old_cpld_img_file, old_failsafe_cpld_img_file, old_fea_cpld_img_file]:
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_copy_image(cpld_img_file,  dest_dir):
            return False
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image file {:s} Copied to NIC {:s}".format(cpld_img_file, dest_dir), level=0)

    # attach console only
    rc = True
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_attach_without_login():
        rc = False
        return rc

    # upgrade/downgrade/utility function and stress test
    for i in range(1, pc_cycles+1):
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "UPGRADE_DOWNGRADE_UTILITY_FUNCTION_STRESS Test Iteration {:d}".format(i), level=0)
        ### upgrade cfg0 to validation target
        progCmd = random.choice(prog_cmd_list)
        imgFile = dest_dir + os.path.basename(new_working_img_file)
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Upgrading of Iteration {:d} ......".format(i), level=0)
        if not cpld_console_program(mtp_mgmt_ctrl, slot, progCmd, imgFile, writePartition="cfg0", iterIndex=i, expMajorVer=new_working_img_ver, expMinorVer=new_working_img_min_ver, expNanoVer=new_working_img_nano_ver):
            rc = False

        ### downgrade mfg release version of CPLD cfg0
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Downgrading of Iteration {:d} ......".format(i), level=0)
        progCmd = random.choice(prog_cmd_list)
        imgFile = dest_dir + os.path.basename(old_cpld_img_file)
        if not cpld_console_program(mtp_mgmt_ctrl, slot, progCmd, imgFile, writePartition="cfg0", iterIndex=i, expMajorVer=old_cpld_img_ver, expMinorVer=old_cpld_img_min_ver, expNanoVer=None):
            rc = False

        if not rc and stop_on_err:
            if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_detach():
                rc = False
            return rc
        time.sleep(1)

    # failsafe and negtive tests
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "UPGRADE_DOWNGRADE_UTILITY_FUNCTION_FAILSAFE_NEGTIVE Test", level=0)
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Upgrade failsafe image ...", level=0)
    progCmd = random.choice(prog_cmd_list)
    imgFile = dest_dir + os.path.basename(new_failsafe_img_file)
    if not cpld_console_program(mtp_mgmt_ctrl, slot, progCmd, imgFile, writePartition="cfg1", expMajorVer=old_cpld_img_ver, expMinorVer=old_cpld_img_min_ver, expNanoVer=None):
        rc = False

    # erase working image and check if CPLD boot from golden
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Erase working image ...", level=0)
    progCmd = "/data/nic_util/xo3dcpld -erase {:s} {:s}"
    imgFile = ""
    if not cpld_console_program(mtp_mgmt_ctrl, slot, progCmd, imgFile, writePartition="cfg0", expMajorVer=new_failsafe_img_ver, expMinorVer=new_failsafe_img_min_ver, expNanoVer=new_failsafe_img_nano_ver, expBootPartion="cfg1"):
        rc = False

    # Write working image back and verify CPLD boot from default main
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Write working image back and verify CPLD boot from default main", level=0)
    progCmd = random.choice(prog_cmd_list)
    imgFile = dest_dir + os.path.basename(new_working_img_file)
    if not cpld_console_program(mtp_mgmt_ctrl, slot, progCmd, imgFile, writePartition="cfg0", expMajorVer=new_working_img_ver, expMinorVer=new_working_img_min_ver, expNanoVer=new_working_img_nano_ver, expBootPartion="cfg0"):
        rc = False

    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Now both main and gold CPLD are validation target new version, so following tests running on new version", level=0)
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_detach():
        rc = False

    return rc
