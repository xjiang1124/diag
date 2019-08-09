#!/usr/bin/python3

import json
import time
import subprocess
import os

def cleanup(eth):
    tmp = subprocess.call(["sudo", "ifconfig", eth, "down"])
    time.sleep(1)
    print()

naples_env = os.environ.copy()
naples_env["NAPLES_URL"] = "http://169.254.0.1"

slot_bus_pair = [(1, '18:00.0'), (2, '3b:00.0'), (3, 'af:00.0'), (4, 'd8:00.0')]

eth_list = {'enp179s0', 'enp220s0', 'enp28s0', 'enp63s0'}
for eth in eth_list:
    subprocess.call(["sudo", "ifconfig", eth, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)

result = subprocess.check_output("lspci -d 1dd8:1000 | awk '{print $1}'", shell=True)
new_str = result.decode("utf-8")
bus_list = [y for y in (x.strip() for x in new_str.splitlines()) if y]
#if len(bus_list) == 4:
#    print("All devices are found")
#else:
#    print("Missing", 4-len(bus_list), "devices")
print("Found", len(bus_list), "devices")
for a, b in slot_bus_pair:
    if b in bus_list:
        print("slot"+str(a), b)
        result = subprocess.check_output("sudo lspci -vv -s "+b+" | grep LnkSta:", shell=True, stderr=subprocess.STDOUT)
        new_str = result.decode("utf-8")
        if new_str.find('8GT/s')>>0 and new_str.find('x16')>>0:
            print("slot"+str(a), b, "Speed and Width check pass")
        else:
            print("slot"+str(a), b, "Speed and Width are failed")
        bus_str = b.split(":", 1)[0]
        bus_int = int(bus_str, 16)+4
        eth = "enp"+str(bus_int)+"s0"
        tmp = subprocess.call(["sudo", "ifconfig", eth, "169.254.0.2/24"])
        time.sleep(1)
        try:
            x = subprocess.check_output("./penctl.linux show naples", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print("Get FRU failed")
            cleanup(eth)
            continue
        y = x.decode("utf-8")
        fru = json.loads(y)
        try:
            x = subprocess.check_output("./penctl.linux show firmware-version", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print("Get firmware failed")
            cleanup(eth)
            continue
        y = x.decode("utf-8")
        firmware = json.loads(y)
        print(fru["status"]["fru"]["serial-number"], fru["status"]["fru"]["product-name"].replace(" ", ""), 
        firmware['running-fw'], firmware['running-fw-version'])
        cleanup(eth)
