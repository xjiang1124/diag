#!/usr/bin/env python

import time
import fcntl
import sys
import argparse
import pexpect
import re

sys.path.append("../lib")
import common

last_average_temp = None
fail_to_read_temp_count = 0

def get_present_slots():
    try:
        session = common.session_start()
        common.session_cmd(session, "inventory -present")
        matches = re.findall(r"\[INFO\].*\s+UUT_(\d+)\s+(?!UUT_NONE)\w+", session.before)
        print(matches)
        slots = {int(match) for match in matches}
        common.session_stop(session)
        return slots
    except pexpect.TIMEOUT:
        print("Timeout reading FPGA MISC_STATUS")
        return 0

def read_temperature(slot):
    try:
        session = common.session_start()
        command = "sucutil exec -s {} -c \"tmp451 temperature\"".format(slot)
        common.session_cmd(session, command)
        result = re.findall(r"REMOTE TEMP:\s+(-?\d+\.\d+)", session.before)
        if result == []:
            print("Failed to read temperature! Read back: ", session.before)
            common.session_stop(session)
            return None
        temperature = float(result[0])
        common.session_stop(session)
        return temperature
    except pexpect.TIMEOUT:
        print("Timeout reading temperature for slot {}".format(slot))
        return None

def calculate_average_temperature(temperatures):
    valid_temperatures = [temp for temp in temperatures if temp is not None]
    if valid_temperatures:
        average_temp = sum(valid_temperatures) / len(valid_temperatures)
        return round(average_temp, 3)  # Round to 3 decimal places
    return None

'''
40C : 40%
50C : 60%
60C : 80%
75C : 100%
'''
def calculate_fan_speed(average_temp):
    if average_temp <= 40:
        fan_speed = 40
    elif average_temp <= 50:
        fan_speed = 40 + (average_temp - 40) * (60 - 40) / (50 - 40)
    elif average_temp <= 60:
        fan_speed = 60 + (average_temp - 50) * (80 - 60) / (60 - 50)
    elif average_temp <= 75:
        fan_speed = 80 + (average_temp - 60) * (100 - 80) / (75 - 60)
    else:
        fan_speed = 100
    fan_speed = int(fan_speed)
    return fan_speed

def run_fan_control(target):
    global last_average_temp, fail_to_read_temp_count
    slot_num = 0
    target_desc = "average"
    slot_list = []
    if target.isdigit():
        slot_num = int(target)
        if slot_num <= 0 or slot_num > 10:
            print("Invalid slot number:", slot_num)
            sys.exit()
        slot_list.append(slot_num)
        target_desc = "slot " + target
    elif ',' in target:
        slot_list = []
        for num in target.split(','):
            if num.isdigit():
                slot_num = int(num)
                if slot_num <= 0 or slot_num > 10:
                    print("Invalid slot number:", slot_num)
                    sys.exit()
                else:
                    slot_list.append(slot_num)
            else:
                print("Invalid slot number:", num)
                sys.exit()
        print("target slots: ", slot_list)
        target_desc = "slots {} average".format(",".join(map(str, slot_list)))
    elif target != 'all':
        print("Invalid target:", target)
        sys.exit()

    while True:
        present_slots = get_present_slots()
        temperatures = []
        if slot_list or target == 'all':
            if slot_list:
                slot_list_present = list(set(present_slots) & set(slot_list))
            else:
                slot_list_present = present_slots
            if not slot_list_present:
                print("target slot(s) not present")
                sys.exit()
            for slot in slot_list_present:
                temp = read_temperature(slot)
                temperatures.append(temp)
                average_temp = calculate_average_temperature(temperatures)
        else:
            average_temp = None
        if average_temp is None:
            fail_to_read_temp_count += 1
            if fail_to_read_temp_count >= 10:
                print("======================================================================")
                print("Unable to get temperature for 10 iterations. Setting fan speed to 100%")
                print("======================================================================")
                try:
                    session = common.session_start()
                    command = "devmgr_v2 fanctrl --pct=100"
                    common.session_cmd(session, command)
                except pexpect.TIMEOUT:
                    print("Timeout setting fan speed")
            else:
                print("=============================================")
                print("Unable to get temperature for {} iterations").format(fail_to_read_temp_count)
                print("=============================================")
        else:
            fail_to_read_temp_count = 0
            if last_average_temp is None or abs(average_temp - last_average_temp) > 2:
                fan_speed = calculate_fan_speed(average_temp)
                last_average_temp = average_temp
                print("===============================================================")
                print("Setting fan speed to {} percent for {} temperature {}C".format(fan_speed, target_desc, average_temp))
                print("===============================================================")
                try:
                    session = common.session_start()
                    command = "devmgr_v2 fanctrl --pct={}".format(fan_speed)
                    common.session_cmd(session, command)
                    time.sleep(5)
                except pexpect.TIMEOUT:
                    print("Timeout setting fan speed")
            else:
                print("===========================================================")
                print("Fan speed remains unchanged for {} temperature {}C".format(target_desc, average_temp))
                print("===========================================================")
            
        try:
            session = common.session_start()
            command = "fpgautil show fan"
            common.session_cmd(session, command)
            common.session_stop(session)
        except pexpect.TIMEOUT:
            print("Timeout reading fan speed")
        print("Sleeping for 60s...")
        time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description='Fan control script targeting single card or all.')
    parser.add_argument('--target', type=str, help='target single card (slot) or using average of all cards', default='all')
    args = parser.parse_args()

    lock_file = open("/tmp/fan_control.lock", "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Another instance of the script is already running.")
        sys.exit()
    run_fan_control(args.target)

if __name__ == "__main__":
    main()