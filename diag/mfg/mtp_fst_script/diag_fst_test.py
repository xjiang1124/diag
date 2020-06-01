#!/usr/bin/python3

import json
import time
import subprocess
import os

def cleanup(eth):
    subprocess.call(["ifconfig", eth, "down"])
    time.sleep(1)
    print()


naples_env = os.environ.copy()
naples_env["NAPLES_URL"] = "http://169.254.0.1"

slot_bus_pair = [(1, '18:00.0'), (2, '3b:00.0'), (3, 'd8:00.0'), (4, 'af:00.0')]

eth_list = {'enp179s0', 'enp220s0', 'enp28s0', 'enp63s0'}
for eth in eth_list:
    subprocess.call(["ifconfig", eth, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)

result = subprocess.check_output("lspci -d 1dd8:1000 | awk '{print $1}'", shell=True)
new_str = result.decode("utf-8")
bus_list = [y for y in (x.strip() for x in new_str.splitlines()) if y]
#if len(bus_list) == 4:
#    print("All devices are found")
#else:
#    print("Missing", 4-len(bus_list), "devices")
print("Found", len(bus_list), "devices", "\n")

for a, b in slot_bus_pair:
    if b in bus_list:
        print("slot"+str(a))
        result = subprocess.check_output("lspci -vv -s "+b+" | grep LnkSta:", shell=True, stderr=subprocess.STDOUT)
        new_str = result.decode("utf-8")
        #if "8GT/s" in new_str and "x16" in new_str:
        #    print("slot"+str(a), b, "Speed and Width check pass")
        #else:
        #    print("slot"+str(a), b, "Speed and Width are failed")
        bus_str = b.split(":", 1)[0]
        bus_int = int(bus_str, 16)+4
        eth = "enp"+str(bus_int)+"s0"
        tmp = subprocess.call(["ifconfig", eth, "169.254."+str(bus_int)+".2/24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["ifconfig", eth, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        naples_env["NAPLES_URL"] = "http://169.254."+str(bus_int)+".1"
        time.sleep(1)
        try:
            x = subprocess.check_output("/home/diag/penctl.linux.0302 show naples", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print("slot"+str(a), b, "sn: unknown", "type: unknown", "failed") 
            print("Get FRU failed")
            cleanup(eth)
            continue
        y = x.decode("utf-8")
        fru = json.loads(y)
        try:
            x = subprocess.check_output("/home/diag/penctl.linux.0302 show firmware-version", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print("slot"+str(a), "sn:", fru["status"]["fru"]["serial-number"], "type:", fru["status"]["fru"]["product-name"].replace(" ", ""), "failed")
            print("Get firmware failed")
            cleanup(eth)
            continue
        y = x.decode("utf-8")
        firmware = json.loads(y)
        if fru["status"]["fru"]["product-name"] == "NAPLES 25 " or "DSC-25" in fru["status"]["fru"]["product-name"]:
            if "8GT/s" in new_str and "x8" in new_str:
                print("slot"+str(a), b, "sn:", fru["status"]["fru"]["serial-number"], "type:", fru["status"]["fru"]["product-name"].replace(" ", ""), "pass")
            else:
                print("slot"+str(a), b, "sn:", fru["status"]["fru"]["serial-number"], "type:", fru["status"]["fru"]["product-name"].replace(" ", ""), "failed")
                print("Speed and Width are failed")
                print(new_str.replace("\n", ""))
        else:
            if "8GT/s" in new_str and "x16" in new_str:
                print("slot"+str(a), b, "sn:", fru["status"]["fru"]["serial-number"], "type:", fru["status"]["fru"]["product-name"].replace(" ", ""), "pass")
            else:
                print("slot"+str(a), b, "sn:", fru["status"]["fru"]["serial-number"], "type:", fru["status"]["fru"]["product-name"].replace(" ", ""), "failed")
                print("Speed and Width are failed")
                print(new_str.replace("\n", ""))
        #print(fru["status"]["fru"]["serial-number"], fru["status"]["fru"]["product-name"].replace(" ", ""))
        print(firmware["running-fw"]+":", firmware["running-fw-version"])
        print("uboot:", firmware["running-uboot"])
        print("goldfw:", firmware["all-installed-fw"]["goldfw"]["kernel_fit"]["software_version"])
        cleanup(eth)
