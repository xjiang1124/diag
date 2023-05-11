import sys, os
from datetime import datetime
import time

sys.path.append(os.path.relpath("../../lib"))
import libmfg_utils
import libtest_config
from ..diag import diag
from ..onie import onie
from libmfg_cfg import ENABLE_CONSOLE_SANITY_CHECK

param_cfg = libtest_config.parse_config("lib/tests/boot/parameters.yaml")

SONIC_BOOT = "SONiC"
ONIE_BOOT = "ONIE"

def tor_os_boot(test_ctrl):
	return lipari_grub_boot(test_ctrl,
        boot_selection = SONIC_BOOT,
        console_check_wait_time = param_cfg["CONSOLE_CHECK_WAIT_TIME"],
        bootup_max_wait_time = param_cfg["BOOTUP_MAX_WAIT_TIME"])


def tor_usb_boot(test_ctrl):
    return True


def tor_onie_boot(test_ctrl):
    test_ctrl.mtp._onie_boot = True
    return lipari_grub_boot(test_ctrl,
        boot_selection = ONIE_BOOT,
        console_check_wait_time = param_cfg["CONSOLE_CHECK_WAIT_TIME"],
        bootup_max_wait_time = param_cfg["BOOTUP_MAX_WAIT_TIME"])
    return True


def lipari_grub_boot(test_ctrl, boot_selection=SONIC_BOOT, console_sanity_check=False, console_check_wait_time=60, bootup_max_wait_time=1800):
    """
    ONIE BOOT:
        Keep pressing enter
        [will do ONIE Embed]
        keep waiting, keep pressing enter
        [will go to ONIE Install OS]
        expect "Please press Enter to activate this console. "
        press enter
        expect "ONIE:/ #"
        STOP pressing enter
        'onie-stop'
        scp sonic
        onie-nos-install sonic
        countdown 10 min
        expect login:

    SONIC BOOT:
        Keep pressing enter
        expect login:

    """
    test_ctrl.mtp_ac_pwr_off()

    if not test_ctrl.mtp.mtp_clear_console():
        return False

    test_ctrl.mtp_ac_pwr_on(no_wait=True)

    if not test_ctrl.mtp.mtp_console_connect():
        test_ctrl.cli_log_err("Failed to access console", level=0)
        return False

    # Keep entering selection number
    idx = -1
    starttosendselection = True
    retry_wait_time = console_check_wait_time
    retry_cnt = 3
    retry_start_time = datetime.now()

    boot_timeout = bootup_max_wait_time
    if bootup_max_wait_time < retry_wait_time:
        test_ctrl.cli_log_err("Script error: boot_timeout < retry_wait_time", level=0)
        return False
    boot_start_time = retry_start_time

    if boot_selection == ONIE_BOOT:
        test_ctrl.mtp._onie_boot = True
        test_ctrl.cli_log_inf("Booting ONIE", level=0)
    elif boot_selection == SONIC_BOOT:
        test_ctrl.cli_log_inf("Booting SONiC", level=0)

    ONIE_prompt_list = [" login:", "ONIE: Embedding ONIE", "ONIE: OS Install Mode", "ONIE:/ #"]
    SONIC_prompt_list = [" login:"]

    prompt_list = ONIE_prompt_list
    rescue_mode_set = False
    while True:
        if starttosendselection:
            test_ctrl.mtp._mgmt_handle.send(str("\r"))
        else:
            test_ctrl.mtp._mgmt_handle.sendline()
        idx = libmfg_utils.mfg_expect(test_ctrl.mtp._mgmt_handle, prompt_list, timeout=1)

        if starttosendselection: # if we're still waiting for a console
            difftime = datetime.now() - retry_start_time
            seconds = difftime.total_seconds()
            if seconds > retry_wait_time:
                retry_cnt -= 1
                if retry_cnt >= 0:
                    if ENABLE_CONSOLE_SANITY_CHECK:
                        test_ctrl.cli_log_err("Failed to get UUT console Login or Select profile prompt")
                        input("Please check that the console is connected then press any key to continue.\n")
                    retry_start_time = datetime.now()
                    test_ctrl.cli_log_inf("Retrying console...")
                    test_ctrl.mtp._mgmt_handle.sendline() # send line to see if already reached login prompt while console was disconnected
                    continue
                else:
                    break

        boot_elapsed_time = datetime.now() - boot_start_time
        if boot_elapsed_time.total_seconds() > boot_timeout:
            test_ctrl.cli_log_err("Took too long to reach prompt: hung or stuck in loop", level=0)
            return False

        if idx < 0:
            continue
        elif idx == 0:
            starttosendselection = False
            test_ctrl.cli_log_inf("Login to OS", level=0)
            break
        elif idx == 1:
            test_ctrl.cli_log_inf("Installing ONIE from USB", level=0)
            continue
        elif idx == 2:
            test_ctrl.cli_log_inf("Login to ONIE Install Mode", level=0)
            retry_start_time = datetime.now() # UUT rebooted here
            boot_start_time = retry_start_time
            continue
        elif idx == 3:
            # Stop it from rebooting automatically
            if not test_ctrl.mtp.mtp_console_connect(prompt_cfg=True, prompt_id="root"):
                test_ctrl.cli_log_err("Failed to connect console", level=0)
                return False
            time.sleep(3)
            if not test_ctrl.mtp.exec_cmd("onie-stop", timeout=60):
                test_ctrl.cli_log_err("Failed to reach ONIE shell", level=0)
                return False

            if boot_selection == ONIE_BOOT:
                if not rescue_mode_set:
                    # booted to Install Mode the first time; set to rescue and reboot
                    if not onie.set_onie_rescue_mode(test_ctrl):
                        return False
                    rescue_mode_set = True
                    test_ctrl.mtp._mgmt_handle.sendline("reboot")
                    time.sleep(5)
                    libmfg_utils.expect_clear_buffer(test_ctrl.mtp._mgmt_handle)
                    continue
                else:
                    starttosendselection = False
                    test_ctrl.cli_log_inf("Login to ONIE Rescue Mode", level=0)
                    break
            else:
                if not onie.install_sonic_from_onie(test_ctrl):
                    return False
                test_ctrl.mtp._onie_boot = False
                prompt_list = SONIC_prompt_list
                retry_start_time = datetime.now() # UUT rebooted here
                boot_start_time = retry_start_time

    if retry_cnt < 0:
        test_ctrl.cli_log_err("Failed to connect console in 3 retries", level=0)
        return False

    if boot_selection == ONIE_BOOT:
        if not test_ctrl.mtp.mtp_console_connect(prompt_cfg=True, prompt_id="root"):
            test_ctrl.cli_log_err("Failed to connect console", level=0)
            return False

    if boot_selection == SONIC_BOOT:
        if not test_ctrl.mtp.mtp_console_connect(prompt_cfg=True):
            test_ctrl.cli_log_err("Failed to connect console", level=0)
            return False

        # switch to ssh
        if not test_ctrl.mtp.tor_mgmt_init():
            test_ctrl.cli_log_err("Failed to obtain IP", level=0)
            return False

        if not test_ctrl.mtp.mtp_sync_clock():
            return False

        if not diag.tor_diag_init(test_ctrl):
            test_ctrl.cli_log_err("Diag SW Environment init failed", level=0)
            return False

        if not test_ctrl.mtp.tor_nic_init():
            return False

    return True

