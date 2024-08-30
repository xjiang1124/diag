#!/usr/bin/env python

import argparse
import pexpect
import os
import sys
import time
from enum import Enum

sys.path.append("../lib")
import common
from nic_con import nic_con

class stage(Enum):
    stage1 = a35_uboot = "a35_uboot"
    stage3 = n1_uboot = "n1_uboot"
    stage2 = a35_zephyr = "zephyr"
    stage4 = n1_linux = "linux"

    def __str__(self):
        return self.value

def boot_to_step(parsed_args):
    ret = 0
    slot = parsed_args.slot
    boot_to = parsed_args.boot_to[0]
    session = common.session_start()
    if boot_to == stage.stage1:
        ret = enter_a35_uboot(slot, session, warm_reset=parsed_args.warm_reset)
    elif boot_to == stage.stage2:
        ret = enter_a35_zephyr(slot, session, warm_reset=parsed_args.warm_reset)
    elif boot_to == stage.stage3:
        ret = enter_n1_uboot(slot, session, warm_reset=parsed_args.warm_reset)
    elif boot_to == stage.stage4:
        ret = enter_n1_linux(slot, session, warm_reset=parsed_args.warm_reset)
    else:
        print("Unknown stage: {}".format(parsed_args.boot_to))
        ret = -1
    common.session_stop(session)

    return ret

def boot_to_step_v2(slot, boot_to, warm_reset=False):
    ret = 0
    session = common.session_start()
    if boot_to == "a35_uboot":
        ret = enter_a35_uboot(slot, session, warm_reset)
    elif boot_to == "zephyr":
        ret = enter_a35_zephyr(slot, session, warm_reset)
    elif boot_to == "n1_uboot":
        ret = enter_n1_uboot(slot, session, warm_reset)
    elif boot_to == "inux":
        ret = enter_n1_linux(slot, session, warm_reset)
    else:
        print("Unknown stage: {}".format(boot_to))
        ret = -1
    common.session_stop(session)

    return ret


def exp_cmd(session, cmd, timeout=1, pass_sig_list=[], fail_sig_list=[]):
    session.sendline(cmd)
    exp_list = [pexpect.TIMEOUT] + fail_sig_list + pass_sig_list
    idx = session.expect(exp_list, timeout)
    if idx < 1:
        print("\n==== TIMEOUT after command {}".format(cmd))
        return False
    elif 1 <= idx < 1+len(fail_sig_list):
        return False
    else:
        return True


def enter_a35_uboot(slot, session, *args, **kwargs):
    session.sendline(f"con_cleanup.sh {slot}")

    con_ctrl = nic_con()
    if con_ctrl.enter_uboot(session, slot, num_retry=1, uart_id=0, warm_reset=kwargs.get('warm_reset', False)) != 0:
        print("==== FAILED: slot {} couldn't enter a35 uboot".format(slot))
        return -1

    print("\n=================== STAGE 1 BOOT (A35 UBOOT) DONE ===================")
    return 0


def enter_a35_zephyr(slot, session, *args, **kwargs):
    if 0 != enter_a35_uboot(slot, session, *args, **kwargs):
        return -1

    con_ctrl = nic_con()
    con_ctrl.uart_session_connect(session, slot, uart_id=0)

    if not exp_cmd(session, "", pass_sig_list=["DSC#"], timeout=1):
        print("===== FAILED: slot {} couldn't enter a35 uboot".format(slot))
        return -1

    if con_ctrl.get_card_type(slot) in ["POLLARA"]:
        cmd = "bootm 0x78580000"
    elif con_ctrl.get_card_type(slot) in ["MALFA", "LENI"]:
        cmd = "go 0x7E500000"

    if not exp_cmd(session, cmd, pass_sig_list=["uart:~\$", "any key to stop"], timeout=5):
        print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
        return -1

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
    
    if not exp_cmd(session, "", pass_sig_list=["uart:~\$"], timeout=1):
        print("===== FAILED: slot {} couldn't enter zephyr".format(slot))
        return -1

    if not exp_cmd(session, "n1 fwsel goldfw", pass_sig_list=["uart:~\$"], timeout=5):
        print("===== FAILED: slot {} fwsel command failed".format(slot))
        return -1

    if not exp_cmd(session, "n1 boot", pass_sig_list=["Releasing CPU reset"], timeout=30):
        print("===== FAILED: slot {} boot didn't go through".format(slot))
        return -1

    if con_ctrl.uart_session_stop(session) != 0:
        return -1

    if con_ctrl.enter_uboot(session, slot, uboot_delay=120, num_retry=1, uart_id=1) != 0:
        print("==== FAILED: slot {} couldn't reach n1 uboot".format(slot))
        return -1

    session.sendline("")
    print("\n=================== STAGE 3 BOOT (N1 UBOOT) DONE ===================")
    return 0


def enter_n1_linux(slot, session, *args, **kwargs):
    if 0 != enter_n1_uboot(slot, session, *args, **kwargs):
        return -1

    con_ctrl = nic_con()
    con_ctrl.uart_session_connect(session, slot, uart_id=1)

    if not exp_cmd(session, "", pass_sig_list=["DSC#"], timeout=1):
        print("===== FAILED: slot {} couldn't enter n1 uboot".format(slot))
        return -1

    session.sendline("bootm 0x80500000")

    if con_ctrl.uart_session_stop(session) != 0:
        return -1

    if con_ctrl.uart_session_start_login(session, slot) != 0:
        return -1

    if con_ctrl.uart_session_stop(session) != 0:
        print("==== FAILED: couldn't exit uart cleanly")
        return -1

    print("\n=================== STAGE 4 BOOT (N1 LINUX) DONE ===================")
    return 0


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("boot_to", type=stage, choices=list(stage), nargs=1)
    parser.add_argument("--slot", "-slot", help="NIC slot", type=int, required=True)
    parser.add_argument("--warm_reset", "-w", help="Warm reset instead of powercycle", action='store_true', default=False)

    try:
        parsed_args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)

    if boot_to_step(parsed_args) != 0:
        print(f"Slot {slot} FAILED")
    else:
        print(f"Slot {slot} PASSED")
