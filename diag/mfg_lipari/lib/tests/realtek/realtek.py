import sys, os, re

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libmfg_utils
from ..barcode import barcode

param_cfg = libtest_config.parse_config("lib/tests/realtek/parameters.yaml")

default_mac_addr = "00 E0 4C 68 00 01"

def rt_nic_prog(test_ctrl, test_config):
    """
        cd linuxpg
        ./pgload.sh
        cp /rt.bin ./8116FL.bin
        ./rtnicpg-x86_64 /flash /wr
        # powercycle needed
    """

    # copy file before loading pgdrv, since it takes down mgmt
    rt_img_file = "release/" + test_config["rt_img"]
    test_ctrl.cli_log_inf("Downloading RT NIC image", level=0)
    if not test_ctrl.mtp.copy_file_to_mtp(rt_img_file, "/home/admin/"):
        return False

    if not param_cfg["FORCE_UPDATE_RTNIC"] and rt_nic_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("RT NIC already up-to-date", level=0)
        return True

    cmd = "cp {:s}/{:s} ./8116FL.bin".format("/home/admin", os.path.basename(rt_img_file))
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    cmd = "./rtnicpg-x86_64 /flash /wr"
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=param_cfg["RTNIC_PROG_DELAY"]):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    return True


def rt_nic_init(test_ctrl):
    if not setup_pgload(test_ctrl):
        return False

    cmd = "./rtnicpg-x86_64 /flash /version"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False
    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    if not cmd_buf:
        test_ctrl.cli_log_err("Unable to read RT flash version", level=0)
        return False
    match = re.findall("Firmware Version *: *([\d\w\.]+) *Build", cmd_buf)
    if match:
        test_ctrl.mtp._rt_ver = match[0]
    else:
        test_ctrl.cli_log_err("Unable to parse RT flash version", level=0)
        test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(cmd_buf)))
        return False

    return True


def rt_nic_verify(test_ctrl, test_config, silently=False):
    """
        cd linuxpg
        ./pgload.sh
        ./rtnicpg-x86_64 /flash /version
        *************************************************************************
        *       EEPROM/EFUSE/FLASH Programming Utility for                      *
        *    Realtek PCI(e) FE/GbE/2.5GbE Family Ethernet Controller            *
        *   Version : 2.77.0.2                                                  *
        * Copyright (C) 2022 Realtek Semiconductor Corp.. All Rights Reserved.  *
        *************************************************************************

         This is RTL8116
         Program Flash
         Flash Manufacturer: Winbond
         Device Code : 4016     Flash ID:  W25Q32

         Executed Executed Firmware Version : 5.1.23 Build b53271e(189998878)
         PartA Executed Firmware Version : 5.1.23 Build b53271e
         Bootloader version :  1.0.1
    """
    if not rt_nic_init(test_ctrl):
        return False

    got_ver = test_ctrl.mtp._rt_ver
    exp_ver = test_config["rt_ver"]

    if got_ver != exp_ver:
        if not silently:
            test_ctrl.cli_log_err("Incorrect realtek flash build date: {:s}, expected {:s}".format(got_ver, exp_ver), level=0)
        return False

    return True


def rt_mac_prog(test_ctrl, fru_config):
    """
        cd linuxpg
        sed -i -e 's/NODEID = 00 E0 4C 68 00 01/NODEID = 04 90 81 AB CD EF/g' linuxpg/8116EF.cfg
        ./pgload.sh
        ./rtnicpg-x86_64 /efuse /r
        ./rtnicpg-x86_64 /efuse /w
        ./rtnicpg-x86_64 /efuse /r
    """
    prog_mac_addr = libmfg_utils.mac_address_add_separator(fru_config[barcode.MAC], " ")
    cmd = "cd /home/admin/eeupdate/linuxpg"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    cmd = "sed -i -e 's/NODEID = {:s}/NODEID = {:s}/g' 8116EF.cfg".format(default_mac_addr, prog_mac_addr)
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    cmd = "head 8116EF.cfg"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    if not setup_pgload(test_ctrl):
        return False

    cmd = "./rtnicpg-x86_64 /efuse /r"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    cmd = "./rtnicpg-x86_64 /efuse /w"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    cmd = "./rtnicpg-x86_64 /efuse /r"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    return True


def rt_mac_verify(test_ctrl, fru_config, silently=False):
    """
        ip link eth0

        cd linuxpg
        ./pgload.sh
        ./rtnicpg-x86_64 /efuse /r
        
        *************************************************************************
        *       EEPROM/EFUSE/FLASH Programming Utility for                      *
        *    Realtek PCI(e) FE/GbE/2.5GbE Family Ethernet Controller            *
        *   Version : 2.77.0.2                                                  *
        * Copyright (C) 2022 Realtek Semiconductor Corp.. All Rights Reserved.  *
        *************************************************************************

         This is RTL8116
         Use EFuse
         Start to Dump and Parse EFuse Content
         FB 00 00 90 81 00 F9 04 7C 00 25 2C FC EC 10 25
         2E FC 23 01 F8 53 3C 27 6C FD 00 E0 4C 68 27 70
         FD 00 00 00 01 F9 18 87 00 F9 4C 4D 02 F8 00 04
         F8 04 FF FF FF FF FF FF FF FF FF FF FF FF FF FF
         FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
         FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
         FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
         FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FC
         NODEID = 04 90 81 00 FF 00
         SVID = 10 EC
         SMID = 01 23
         CONFIG2 = 3C
         SN = 00 E0 4C 68 00 00 00 01
         LEDCFG = 00 87
         Efuse Write Count = 2
         PG Version (EFUSE) = V2.77
         EFuse Remain 73 Bytes!!!

    """

    exp_mac = fru_config[barcode.MAC]
    got_mac = get_eth0_mac(test_ctrl)
    if got_mac is None:
        return False
    got_mac = libmfg_utils.mac_address_remove_separator(got_mac).upper()

    if not setup_pgload(test_ctrl):
        return False
    cmd = "./rtnicpg-x86_64 /efuse /r"
    if not test_ctrl.mtp.exec_cmd(cmd):
        return False

    if got_mac != exp_mac:
        if not silently:
            test_ctrl.cli_log_err("Incorrect Realtek MAC: {:s}, expected {:s}".format(got_mac, exp_mac), level=0)
        return False
    return True


def setup_pgload(test_ctrl):
    if not test_ctrl.mtp.mtp_console_connect(prompt_cfg=True):
        test_ctrl.cli_log_err("Failed to connect console", level=0)
        return False

    cmd = "cd /home/admin/eeupdate/linuxpg/"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False
    
    cmd = "./pgload.sh"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    return True

def get_eth0_mac(test_ctrl):
    cmd = "ifconfig eth0 | grep 'ether '"
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=60):
        test_ctrl.cli_log_err("{:s} failed".format(cmd))
        return None
    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    match = re.search("ether *((?:[0-9A-Fa-f]{2}\:){5}(?:[0-9A-Fa-f]{2}))", cmd_buf)
    if match:
        return match.group(1)
    else:
        return None
