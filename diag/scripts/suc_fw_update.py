#!/usr/bin/env python3

import os
import re
import sys
import time
import argparse
import threading
import pexpect
import subprocess
import concurrent.futures
import threading
from collections import deque

class MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Print error message
        sys.stderr.write(f"\nerror: {message}\n")
        # Print full help
        self.print_help()
        sys.exit(2)

def tail_fast(filename, n=50):

    try:
        with open(filename, "r") as f:
            return "".join(deque(f, n))
    except Exception as Err:
        return Err

def slot2_sn(slot=None, kernel=None):
    '''
    mapping slot to serial
    '''

    if slot is None:
        return None
    if kernel is None:
        return None

    sn_content_file = f'/sys/bus/usb/devices/{kernel}/serial'

    # check usb uart device present
    if not os.path.exists(sn_content_file):
        print(f'{sn_content_file} not exist')
        return False

    try:
        with open(sn_content_file, 'r', encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
    except Exception as Err:
        print(f"Failed to open {sn_content_file}")
        print(Err)
        return False
    print(f'Slot {slot} USB Serial {content}')
    return content

def zephyr_console_mon(slot, monitor_time=60):
    '''
    monitor uC console output from con_connect.sh <slot> 1
    '''

    logfile=f'suc_program_console_slot{slot}.log'
    bash_prompt = r":\$ "
    rc = False

    # kill previouse
    uart_slot = str(int(slot) - 1)
    kill_cmd = f"ps -ef | grep fpga_uart_panarea | grep {uart_slot}$ | awk '{{print $2}}' | xargs kill -9 "
    try:
        subprocess.run(kill_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.SubprocessError as Err:
        pass
        # do nothing to avoid following error message print on screening
        # Command 'ps -ef | grep fpga_uart_panarea | grep 1 | awk '{print $2}' | xargs kill -9' died with <Signals.SIGKILL: 9>.
        # print(Err)

    with open(logfile, 'wb') as uart_log:
        session = pexpect.spawn(f"bash", timeout=10, encoding=None)
        session.logfile = uart_log
        idx = session.expect([pexpect.TIMEOUT, pexpect.EOF, bash_prompt])
        if idx <= 1:
            print(F"Failed to Spawn Bash")
        elif idx == 2:
            session.sendline(f"/home/diag/diag/scripts/con_connect.sh {slot} 1")

        idx = session.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=monitor_time)
        if idx == 0:
            print(F"Monitor uC uart console for {monitor_time} seconds")
            rc = logfile
        elif idx == 1:
            print("Failed to lauch Uart Console Monitor")
        session.sendcontrol("a")
        session.sendcontrol("x")
        idx = session.expect([pexpect.TIMEOUT, pexpect.EOF, bash_prompt])
        if idx <= 1:
            print(F"Failed to exit con_connect")
        elif idx == 2:
            session.sendline("exit")

    return rc

def pldm_program(slot,  component_ids=None, kernel=None, image=None, debug=False, signature="Test case PldmFwUpdateSingleFDUpdateFlow has PASSED"):
    '''
    program uC firmware
    '''

    interface = 3
    cns_home = '/home/diag/cns-pmci'
    logfile=f'suc_pldm_program_slot{slot}_log.log'
    utility = f'{cns_home}/test_all.py'
    sn = slot2_sn(slot, kernel)
    if not sn:
        return False, logfile

    # util_args = ['--board-type', 'AinicSuc', '--usb', f'{sn}:{interface}', '--print-hdrs', '--print-msgs', '-vvv',  '--util', f'pldmfwpkg={image}', '--test-cases', 'PldmFwUpdateSingleFDUpdateFlow']
    # util_args = ['--board-type', 'AinicSuc', '--usb', f'{sn}:{interface}', '--detach-usb-kernel-driver', '--allow-early-update-completion', '--util', f'pldmfwpkg={image}', '--test-cases', 'PldmFwUpdateSingleFDUpdateFlow']
    # util_args = ['--board-type', 'AinicSuc', '--component-ids', '1', '--usb', f'{sn}:{interface}', '--detach-usb-kernel-driver', '--allow-early-update-completion', '--print-hdrs', '--print-msgs', '--util', f'pldmfwpkg={image}', '--test-cases', 'PldmFwUpdateSingleFDUpdateFlow']
    # util_args = ['--board-type', 'AinicSuc', '--usb', f'{sn}:{interface}', '--detach-usb-kernel-driver', '--print-hdrs', '--print-msgs', '--util', f'pldmfwpkg={image}', '--test-cases', 'PldmFwUpdateSingleFDUpdateFlow']
    # util_args = ['--board-type', 'AinicSuc', '--usb', f'{sn}', '--detach-usb-kernel-driver', '--no-logs', '--override-fd-descriptors', '/home/diag/cns-pmci/board/gelso.json', '--print-hdrs', '--print-msgs', '--util', f'pldmfwpkg={image}', '--test-cases', 'PldmFwUpdateSingleFDUpdateFlow']
    util_args = ['--board-type', 'AinicSuc', '--usb', f'{sn}', '--detach-usb-kernel-driver', '--no-logs', '--allow-early-update-completion',  '--print-hdrs', '--print-msgs', '--util', f'pldmfwpkg={image}', '--test-cases', 'PldmFwUpdateSingleFDUpdateFlow']
    if component_ids:
        util_args += ['--component-ids', component_ids]
    if debug:
        util_args += ['-vvv']
    cmd = [utility] + util_args

    print(f"slot {slot} programming ....")
    print(f'Slot {slot} Command: {" ".join(cmd)}')

    try:
        with open(logfile, "w") as logf:
            CompletedProcess = subprocess.run(cmd, text=True, stdout=logf, stderr=subprocess.STDOUT)
            cmd = ' '.join(CompletedProcess.args)
            rc = CompletedProcess.returncode
            cmdout = CompletedProcess.stdout
            cmderr = CompletedProcess.stderr
    except subprocess.SubprocessError as Err:
        print(Err)
        print(cmd)
        print(cmdout)
        print(cmderr)
        return False, logfile

    # check return code
    if rc != 0:
        return False, logfile
    # check log, if no pass signature in the log, return failure even return code is 0
    last_50 = tail_fast(logfile)
    if signature not in last_50:
        return False, logfile

    return True, logfile

def main():

    debug = args.debug
    imagefile = args.image
    if not os.path.isabs(imagefile):
        print("Image File Must In Absuolte Path")
        return False

    components = [str(c_id) for c_id in args.component_ids]
    console_monitor_time = 35 + len(components) * 15 if components else 60
    component_ids = ""
    if components:
        component_ids = " ".join(components)

    if not os.path.exists(imagefile):
        print("Specified Image File Not Exist")
        return False

    invalid_slots = [ str(slot) for slot in args.slot if slot < 1 or slot > 10]
    if invalid_slots:
        invalid_slots_str = " ".join(invalid_slots)
        print(f"\n\n ====== INVALID SLOT NUMBER {invalid_slots_str} =====")
        return False

    slots = list(set([str(slot) for slot in args.slot]))
    slots.sort()

    slot2kernels = {}
    suc_uart_rules = "/etc/udev/rules.d/99-suc-uart.rules"
    try:
        with open(suc_uart_rules, "r") as rules_file:
            for line in rules_file:
                match = re.findall(r'SUBSYSTEM=="tty",\s*KERNELS=="(\d-\d)",\s*SYMLINK\+="SUCUART(\d{1,2})"', line)
                if match:
                    slot2kernels[match[0][1]] = match[0][0]
    except Exception as Err:
        print(Err)
        return False
    else:
        if len(slot2kernels) != 10:
            print(F"Suc uart rules file {suc_uart_rules} may corrupted")
            return False

    # power on given slots if nessarary
    need_wait = False
    for slot in slots:
        if os.path.exists(f'/sys/bus/usb/devices/{slot2kernels[slot]}/serial'):
            continue
        need_wait = True
        try:
            CompletedProcess = subprocess.run(['/home/diag/diag/scripts/turn_on_slot.sh', 'on', slot], text=True, capture_output=True)
            cmd = ' '.join(CompletedProcess.args)
            rc = CompletedProcess.returncode
            cmdout = CompletedProcess.stdout
            cmderr = CompletedProcess.stderr
        except subprocess.SubprocessError as Err:
            print(Err)
            print(cmd)
            print(f'Failed to turn on slot {slot}')
            print(cmdout)
            print(cmderr)
            return False
        print(cmd)
        print(cmdout)
        print(cmderr)
        if rc != 0:
            print(f'Failed to turn on slot {slot}')
            return False

    # give a few seconds to let usb uart ready
    if need_wait:
        print("sleep 15 seconds for nic power on ...")
        time.sleep(15)

    passed_slots = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2*len(slots)) as executor:
        future_to_slot_task = {executor.submit(zephyr_console_mon, slot, console_monitor_time): (slot, f'{slot}_monitor_process') for slot in slots}
        future_to_slot_task.update({executor.submit(pldm_program, slot, component_ids, slot2kernels[slot], imagefile, debug): (slot, f'{slot}_program_process') for slot in slots})
        for future  in concurrent.futures.as_completed(future_to_slot_task):
            slot, process_name = future_to_slot_task[future]
            try:
                data = future.result()
            except Exception as Err:
                print(f'slot {process_name} generated an exception: {Err}')
            else:
                # we don't care if monitor thread is pass or failed
                if '_monitor_process' in process_name:
                    print(f'Slot {slot} uC UART Monitor Log File: {data}')
                    continue
                # summary program process results
                if '_program_process' in process_name:
                    if data[0]:
                        passed_slots.append(slot)
                    print(f'Slot {slot} Detail Log File: {data[1]}')

    # print out signature for out caller or wrapper
    result = True
    if not passed_slots:
        print("\n\n====== ALL SLOT FAILED =====")
        return False
    passed_slots.sort()
    if passed_slots:
        pass_str = " ".join(passed_slots)
        print(f"\n\n ====== SLOT {pass_str} PASSED =====")

    failed_slots = list(set(slots) - set(passed_slots))
    failed_slots.sort()
    if failed_slots:
        failed_str = " ".join(failed_slots)
        print(f"\n\n ====== SLOT {failed_str} FAILED =====")
        result = False

    return result

if __name__ == '__main__':
    parser = MyArgumentParser(description="Update Microntroller Firmwre",
                                     epilog='''Examples: %(prog)s -c 1 -i two_comp_gelso.pldm  #to program uC image only\n          %(prog)s -s 1 2 3 4 -i two_comp_gelso.pldm\n          %(prog)s -i two_comp_gelso.pldm''', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.2')
    parser.add_argument('-s', '--slot', help="blank space seperated slots,  default to %(default)s",  nargs="+", type=int, default=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    parser.add_argument('-c', '--component-ids', help=("blank space seperated components list to be program, default to all\n"
                                                      "please select single or multiple component ids from following id to name mapping\n"
                                                      "0: suc_boot\n"
                                                      "1: suc_app\n"
                                                      "2: soc_part_table\n"
                                                      "3: soc_goldubootspl\n"
                                                      "4: soc_goldzephyr\n"
                                                      "5: soc_pentrsrfw_0\n"
                                                      "6: soc_pentrsrfw_1\n"
                                                      "7: soc_pentrfw\n"
                                                      "8: soc_ubootspl\n"
                                                      "9: soc_uboot\n"
                                                      "10: soc_zephyr\n"
                                                      "11: soc_dtb\n"
                                                      "12: soc_fw_cfg\n"
                                                      "13: soc_oprom\n"
                                                      "16: soc_bootfpga\n"
                                                      "17: soc_cfgfpga\n"
                                                      "18: soc_uboottpl\n"),  nargs="+", type=int, default=[])
    parser.add_argument('-i', '--image', help="pldm type image file name, absuolte path", required=True)
    parser.add_argument('-d', '--debug', help="adding debug info into log files by provide '--print-hdrs', '--print-msgs', '-vvv' options", action='store_true', default=False)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)

    sys.exit(not main())