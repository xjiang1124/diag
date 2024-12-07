#!/usr/bin/env python

import argparse
import pexpect
import os
import sys
import time
#from enum import Enum

sys.path.append("../lib")
import common
from nic_con import nic_con

stage = (
    "a35_uboot",
    "zephyr",
    "n1_uboot",
    "linux",
    "diag",
    "nondiag",
)

def _boot_to_step(parsed_args):
    """
        Input: parsed_args: Namespace object from argparse.
        This function will call downstream (public) functions.
        To prevent 'slot' from being passed twice, it's better to delete it from the Namespace.
    """
    ret = 0
    slot = parsed_args.__dict__.pop('slot')
    boot_to = parsed_args.__dict__.pop('boot_to')[0].lower()
    session = common.session_start()
    if boot_to == stage[0]:
        ret = enter_a35_uboot(slot, session, **vars(parsed_args))
    elif boot_to == stage[1]:
        ret = enter_a35_zephyr(slot, session, **vars(parsed_args))
    elif boot_to == stage[2]:
        ret = enter_n1_uboot(slot, session, **vars(parsed_args))
    elif boot_to == stage[3]:
        ret = enter_n1_linux(slot, session, **vars(parsed_args))
    elif boot_to == stage[4]:
        ret = boot_goldfw_diagmode(slot, session, **vars(parsed_args))
    elif boot_to == stage[5]:
        ret = boot_goldfw_nondiagmode(slot, session, **vars(parsed_args))
    else:
        print("Unknown stage: {}".format(boot_to))
        ret = -1
    common.session_stop(session)

    return ret

def exp_cmd(session, cmd, timeout=1, pass_sig_list=[], fail_sig_list=[]):
    ret = 0
    nc = nic_con()
    cmdret, output = nc.uart_session_cmd_w_ot(session, cmd, timeout=timeout, ending=pass_sig_list)
    if cmdret != 0:
        print("Command {} failed".format(cmd))
        ret = -1
    for sig in fail_sig_list:
        if sig in output:
            print("Command {} returned error: {}".format(cmd, sig))
            ret = -1
    return ret, output


def enter_a35_uboot(slot, session, *args, **kwargs):
    session.sendline("con_cleanup.sh {}".format(slot))
    session.sendline("") # to get out of "Terminated message" and prevent it confusing the prompt
    session.sendline("")

    con_ctrl = nic_con()
    if con_ctrl.enter_uboot_salina(session, slot, uart_id=0, warm_reset=kwargs.get('warm_reset', False), v12_reset=kwargs.get('v12_reset', False)) != 0:
        print("==== FAILED: slot {} couldn't enter a35 uboot".format(slot))
        return -1

    print("\n=================== STAGE 1 BOOT (A35 UBOOT) DONE ===================")
    return 0


def enter_a35_zephyr(slot, session, *args, **kwargs):
    if 0 != enter_a35_uboot(slot, session, *args, **kwargs):
        return -1

    con_ctrl = nic_con()
    con_ctrl.uart_session_connect(session, slot, uart_id=0)

    if 0 != exp_cmd(session, "", pass_sig_list=["DSC#"], timeout=1)[0]:
        print("===== FAILED: slot {} couldn't enter a35 uboot".format(slot))
        return -1

    if con_ctrl.get_card_type(slot) in ["POLLARA"]:
        new_ainic_layout = kwargs.get('new_ainic_layout', False)
        if new_ainic_layout:
            cmd = "bootm 0x78300000"
        else:
            cmd = "bootm 0x78140000"
    elif kwargs.get("raw_zephyr_binary", False):
        cmd = "bootm 0x7E500000"
    else:
        cmd = "boot" #"bootm 0x8000000"

    # For ainic, the "uart:~$" prompt may be truncated
    if 0 != exp_cmd(session, cmd, pass_sig_list=["rt:~\$", "any key to stop"], timeout=10)[0]:
        print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
        return -1

    time.sleep(3)
    exp_cmd(session, "pcieawd showparams", pass_sig_list="uart:~\$", timeout=10)

    # For non-ainic, keep pressing any key to stop N1 autoboot
    for i in range(kwargs.get('n1_autoboot_delay', 10)): #10 = 2 keypresses per sec
        if con_ctrl.get_card_type(slot) in ["POLLARA"]:
            break
        session.timeout = 0.5
        try:
            print("C+C")
            session.send(chr(3))
            idx = session.expect(["Releasing CPU reset", "Asserting CPU reset", "any key to stop", "Stopping autoboot"])
            #time.sleep(1)
            if idx == 0 or idx == 1:
                print("Missed the chance to stop N1 autoboot")
                ret = -1
                break
            elif idx == 2 or idx == 3:
                ret = 0
                # two enters to see clean prompt instead of in between bootup messages
                session.send("")
                session.send("")
                session.expect(["uart:~\$"])
                break
        except pexpect.TIMEOUT:
            print("timeout:", i)
            ret = -1

    if con_ctrl.uart_session_stop(session) != 0:
        print("==== FAILED: couldn't exit uart cleanly")
        return -1

    print("\n=================== STAGE 2 BOOT (ZEPHYR) DONE ===================")
    return 0


def enter_n1_uboot(slot, session, *args, **kwargs):
    if 0 != enter_a35_zephyr(slot, session, *args, **kwargs):
        return -1

    con_ctrl = nic_con()
    con_ctrl.uart_session_connect(session, slot, uart_id=0)

    ret, help_output = exp_cmd(session, "help", pass_sig_list=["uart:~\$"], timeout=1)
    if ret != 0:
        print("===== FAILED: slot {} couldn't enter zephyr".format(slot))
        return -1

    if "system   :System commands" in help_output:
        fwsel_cmd = "system fwsel dpu"
        boot_cmd = "system boot-dpu"
    else:
        fwsel_cmd = "n1 fwsel goldfw"
        boot_cmd = "n1 boot"

    if 0 != exp_cmd(session, fwsel_cmd, pass_sig_list=["uart:~\$"], timeout=5)[0]:
        print("===== FAILED: slot {} fwsel command failed".format(slot))
        return -1

    # get earliest signature that will catch error messages from previous a35 command,
    # while getting maximum messages from n1 uboot
    if 0 != exp_cmd(session, boot_cmd, pass_sig_list=["Loading U-Boot image goldfw"], timeout=80)[0]:
        print("===== FAILED: slot {} boot didn't go through".format(slot))
        return -1

    if con_ctrl.uart_session_stop(session) != 0:
        return -1

    # A higher timeout may be required for a larger fw.
    if con_ctrl.enter_uboot_salina(session, slot, timeout=80, uart_id=1, pc=0) != 0:
        print("==== FAILED: slot {} couldn't reach n1 uboot".format(slot))
        return -1

    #session.sendline("")
    print("\n=================== STAGE 3 BOOT (N1 UBOOT) DONE ===================")
    return 0


def enter_n1_linux(slot, session, *args, **kwargs):
    if 0 != enter_n1_uboot(slot, session, *args, **kwargs):
        return -1

    con_ctrl = nic_con()
    con_ctrl.uart_session_connect(session, slot, uart_id=1)

    if 0 != exp_cmd(session, "", pass_sig_list=["DSC#"], timeout=1)[0]:
        print("===== FAILED: slot {} couldn't enter n1 uboot".format(slot))
        return -1

    session.sendline("bootm 0x80500000")

    if con_ctrl.uart_session_stop(session) != 0:
        return -1

    if con_ctrl.uart_session_start_login(session, slot) != 0:
        print("Couldnt get N1 login prompt")
        return -1

    if con_ctrl.uart_session_stop(session) != 0:
        print("==== FAILED: couldn't exit uart cleanly")
        return -1

    print("\n=================== STAGE 4 BOOT (N1 LINUX) DONE ===================")
    return 0

def boot_goldfw_diagmode(slot, session, *args, **kwargs):

    if 0 != enter_n1_linux(slot, session, *args, **kwargs):
        print("======= FAILED: slot {} couldn't enter n1 linux".format(slot))
        return -1
    con_ctrl = nic_con()
    if con_ctrl.uart_session_connect(session, slot, uart_id=1) != 0:
        print("set diagmode failed entering uart console")
        return - 1
    if con_ctrl.uart_session_cmd(session, "board_config -M 1") != 0:
        print("set diagmode failed issuing board config command")
        return -1
    if con_ctrl.uart_session_stop(session) != 0:
        print("set diagmode failed to exit uart")
        return -1

    print("\n===================set golfw in diag mode finished ===================")
    return 0

def boot_goldfw_nondiagmode(slot, session, *args, **kwargs):

    if 0 != enter_n1_linux(slot, session, *args, **kwargs):
        print("======= FAILED: slot {} couldn't enter n1 linux".format(slot))
        return -1
    con_ctrl = nic_con()
    if con_ctrl.uart_session_connect(session, slot, uart_id=1) != 0:
        print("set nondiag failed entering uart console")
        return - 1
    if con_ctrl.uart_session_cmd(session, "board_config -M 0") != 0:
        print("set nondiag failed issuing board config command")
        return -1
    if con_ctrl.uart_session_stop(session) != 0:
        print("set nondiag failed to exit uart")
        return -1

    print("\n===================set golfw in non-diag mode finished===================")
    return 0

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--boot_to", "-b", type=str, choices=stage, default=[stage[3]], help="Boot stage: a35_uboot/zephyr/n1_uboot/linux", nargs=1)
    parser.add_argument("--slot", "-slot", "-s", help="NIC slot", type=int, required=True)
    parser.add_argument("--warm_reset", "-w", help="Warm reset instead of powercycle", action='store_true', default=False)
    parser.add_argument("--v12_reset", "-v12", help="v12 reset instead of powercycle", action='store_true', default=False)
    parser.add_argument("--raw_zephyr_binary", "-f", help="zephyr.bin is loaded instead of zephyr.fit", action='store_true')
    parser.add_argument("--new_ainic_layout", "-na", help="following new Pollara flash layout after Oct25", action='store_true', default=False)

    try:
        parsed_args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)

    slot = parsed_args.slot

    if _boot_to_step(parsed_args) != 0:
        print("Slot {} FAILED".format(slot))
        sys.exit(1)
    else:
        print("Slot {} PASSED".format(slot))
