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
current_fan_speed = 40  # Track fan speed for proportional control
fail_to_reach_target_count = 0  # Track unreachable target situations
previous_temp_for_derivative = None  # Track previous temperature for derivative calculation
FAN_MAX = 100
FAN_CHANGE_MAX = 15

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
            print("Failed to read temperature! Read back: {}".format(session.before))
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

def parse_fan_speed(output):
    lines = output.split('\n')
    for line in lines:
        # Skip header and separator lines
        if 'NAME' in line or '----' in line or 'PSU' in line:
            continue
        # Look for FAN entries with PWM values
        if 'FAN-' in line:
            parts = line.split()
            # Expected format: NAME prsnt error pwm inRPM outRPM
            # Index:           0     1     2     3   4     5
            if len(parts) >= 4:
                try:
                    pwm_value = int(parts[3])
                    fan_percent = round((pwm_value / 255.0) * 100)
                    return fan_percent
                except (ValueError, IndexError):
                    continue
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

def calculate_fan_speed_target(current_temp, target_temp, current_fan_speed, kp, kd, deadband,
                               previous_temp, control_interval, fan_min):
    """
    Calculate fan speed using PD (Proportional-Derivative) control to reach target temperature.

    Args:
        current_temp (float): Current average temperature in Celsius
        target_temp (int): Target temperature in Celsius
        current_fan_speed (int): Current fan speed percentage (0-100)
        kp (float): Proportional gain (fan % per degree C diff)
        kd (float): Derivative gain (fan % per degree C per second)
        deadband (int): Temperature deadband in Celsius
        previous_temp (float): Previous temperature reading (for derivative)
        control_interval (int): Time between control iterations in seconds
        fan_min (int): Minimum fan speed percentage

    Returns:
        int: New fan speed percentage (fan_min-100)
    """

    # Calculate temperature error (positive = too hot)
    error = current_temp - target_temp

    # Calculate derivative (rate of temperature change)
    derivative = 0
    if previous_temp is not None:
        # Derivative: degrees per second
        temp_change_rate = (current_temp - previous_temp) / control_interval
        derivative = temp_change_rate

    # Apply deadband only if temperature is stable (low derivative)
    if abs(error) <= deadband and abs(derivative) < 0.05:
        return current_fan_speed

    # PD control: Proportional + Derivative
    # Proportional term: respond to current error
    fan_change_p = kp * error

    # Derivative term: respond to rate of change
    # Positive derivative means temp rising -> increase fan
    fan_change_d = kd * derivative

    # Total fan change
    fan_change = fan_change_p + fan_change_d
    print("fan_change_p: {}, fan_change_d: {}, fan_change: {}".format(fan_change_p, fan_change_d, fan_change))

    # Rate limit: prevent aggressive changes
    fan_change = max(-FAN_CHANGE_MAX, min(FAN_CHANGE_MAX, fan_change))

    # Calculate new fan speed
    new_fan_speed = current_fan_speed + fan_change

    # Enforce limits
    new_fan_speed = max(fan_min, min(FAN_MAX, new_fan_speed))
    print("calculated new_fan_speed: {}".format(new_fan_speed))

    return int(new_fan_speed)

def run_fan_control(target, control_mode='fixed', target_temp=None, kp=3.0, kd=10.0, deadband=2, control_interval=30, fan_min=35):
    global last_average_temp, fail_to_read_temp_count, current_fan_speed, fail_to_reach_target_count, previous_temp_for_derivative
    slot_num = 0
    target_desc = "average"
    slot_list = []
    if target.isdigit():
        slot_num = int(target)
        if slot_num <= 0 or slot_num > 10:
            print("Invalid slot number: {}".format(slot_num))
            sys.exit()
        slot_list.append(slot_num)
        target_desc = "slot " + target
    elif ',' in target:
        slot_list = []
        for num in target.split(','):
            if num.isdigit():
                slot_num = int(num)
                if slot_num <= 0 or slot_num > 10:
                    print("Invalid slot number: {}".format(slot_num))
                    sys.exit()
                else:
                    slot_list.append(slot_num)
            else:
                print("Invalid slot number: {}".format(num))
                sys.exit()
        print("target slots: {}".format(slot_list))
        target_desc = "slots {} average".format(",".join(map(str, slot_list)))
    elif target != 'all':
        print("Invalid target: {}".format(target))
        sys.exit()

    # read current_fan_speed
    try:
        session = common.session_start()
        command = "fpgautil show fan"
        common.session_cmd(session, command)
        fan_speed_parsed = parse_fan_speed(session.before)
        if fan_speed_parsed is not None:
            current_fan_speed = fan_speed_parsed
            print("Current fan speed: {}%".format(current_fan_speed))
        else:
            print("Failed to parse current fan speed, using default {}%".format(current_fan_speed))
        common.session_stop(session)
    except pexpect.TIMEOUT:
        print("Timeout reading current fan speed, using default {}%".format(current_fan_speed))

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
                print("Unable to get temperature for {} iterations".format(fail_to_read_temp_count))
                print("=============================================")
        else:
            fail_to_read_temp_count = 0

            if control_mode == 'target':
                # Temperature targeting mode
                fan_speed = calculate_fan_speed_target(
                    average_temp, target_temp, current_fan_speed, kp, kd, deadband,
                    previous_temp_for_derivative, control_interval, fan_min
                )

                diff = average_temp - target_temp

                # Calculate temperature change rate for display
                temp_change_rate = 0
                if previous_temp_for_derivative is not None:
                    temp_change_rate = (average_temp - previous_temp_for_derivative) / control_interval

                # Update previous temperature for next iteration
                previous_temp_for_derivative = average_temp

                if fan_speed != current_fan_speed:
                    previous_fan_speed = current_fan_speed
                    current_fan_speed = fan_speed
                    print("===============================================================")
                    print("Target mode: Setting fan to {}% for {} temp {:.3f}C".format(
                        fan_speed, target_desc, average_temp))
                    print("  Target: {}C | Diff: {:+.0f}C | Rate: {:+.3f}C/s | Fan: {:+d}%".format(
                        target_temp, diff, temp_change_rate, int(fan_speed - previous_fan_speed)))
                    print("===============================================================")

                    # Execute fan control command
                    try:
                        session = common.session_start()
                        command = "devmgr_v2 fanctrl --pct={}".format(fan_speed)
                        common.session_cmd(session, command)
                        time.sleep(5)
                    except pexpect.TIMEOUT:
                        print("Timeout setting fan speed")
                else:
                    print("===========================================================")
                    print("Target mode: Fan stable at {}% for {} temp {:.3f}C".format(
                        fan_speed, target_desc, average_temp))
                    print("  Target: {}C | Diff: {:+.0f}C | Rate: {:+.3f}C/s".format(
                        target_temp, diff, temp_change_rate))
                    print("===========================================================")

                # Check if target is unreachable
                if current_fan_speed >= FAN_MAX and average_temp > target_temp + deadband:
                    fail_to_reach_target_count += 1
                    if fail_to_reach_target_count >= 50:
                        print("WARNING: Unable to reach target temperature")
                        print("         Fan at 100%, temp at {:.3f}C, target {}C".format(
                            average_temp, target_temp))
                elif current_fan_speed <= fan_min and average_temp < target_temp - deadband:
                    fail_to_reach_target_count += 1
                    if fail_to_reach_target_count >= 50:
                        print("WARNING: Unable to reach target temperature")
                        print("         Fan at minimum ({}%), temp at {:.3f}C, target {}C".format(
                            current_fan_speed, average_temp, target_temp))
                else:
                    fail_to_reach_target_count = 0

            else:
                # Fixed mapping mode
                if last_average_temp is None or abs(average_temp - last_average_temp) > 2:
                    fan_speed = calculate_fan_speed(average_temp)
                    last_average_temp = average_temp
                    print("===============================================================")
                    print("Fixed mode: Setting fan to {}% for {} temp {:.3f}C".format(
                        fan_speed, target_desc, average_temp))
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
                    print("Fixed mode: Fan unchanged for {} temp {:.3f}C".format(
                        target_desc, average_temp))
                    print("===========================================================")

        try:
            session = common.session_start()
            command = "fpgautil show fan"
            common.session_cmd(session, command)
            common.session_stop(session)
        except pexpect.TIMEOUT:
            print("Timeout reading fan speed")
        print("Sleeping for {}s...".format(control_interval))
        time.sleep(control_interval)

def main():
    parser = argparse.ArgumentParser(
        description='Fan control: fixed temp mapping or temperature targeting modes')
    parser.add_argument('--target_slots', type=str,
                       help='single slot, slot list (1,3,5), or "all" for average',
                       default='all')
    parser.add_argument('--target_temp', type=int,
                       help='target temperature in Celsius (enables targeting mode)',
                       default=None)
    parser.add_argument('--control_interval', type=int,
                       help='control loop interval in seconds',
                       default=30)
    parser.add_argument('--kp', type=float,
                       help='proportional gain (fan %% per degree C)',
                       default=2.0)
    parser.add_argument('--kd', type=float,
                       help='derivative gain (fan %% per degree C per second)',
                       default=10.0)
    parser.add_argument('--deadband', type=int,
                       help='temperature deadband in Celsius',
                       default=1)
    parser.add_argument('--fan_min', type=int,
                       help='minimum fan speed percentage',
                       default=38)
    args = parser.parse_args()

    # Determine control mode
    if args.target_temp is not None:
        control_mode = 'target'
        # Validate target temperature
        if args.target_temp < 20 or args.target_temp > 130:
            print("ERROR: Target temperature must be between 20 and 130C")
            sys.exit(1)
        print("=" * 60)
        print("Temperature Targeting Mode (PD Control)")
        print("=" * 60)
        print("Target Temperature: {}C".format(args.target_temp))
        print("Proportional Gain (Kp): {:.1f}".format(args.kp))
        print("Derivative Gain (Kd): {:.1f}".format(args.kd))
        print("Deadband: {}C".format(args.deadband))
        print("Fan Min: {}%".format(args.fan_min))
        print("Control Interval: {}s".format(args.control_interval))
        print("=" * 60)
    else:
        control_mode = 'fixed'
        print("=" * 60)
        print("Fixed Mapping Mode")
        print("=" * 60)
        print("Using default temperature-to-fan-speed mapping:")
        print("  40C -> 40%, 50C -> 60%, 60C -> 80%, 75C -> 100%")
        print("=" * 60)

    # File locking to prevent multiple instances
    lock_file = open("/tmp/fan_control.lock", "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Another instance of the script is already running.")
        sys.exit(1)

    # Start control loop
    run_fan_control(
        args.target_slots,
        control_mode=control_mode,
        target_temp=args.target_temp,
        kp=args.kp,
        kd=args.kd,
        deadband=args.deadband,
        control_interval=args.control_interval,
        fan_min=args.fan_min
    )

if __name__ == "__main__":
    main()