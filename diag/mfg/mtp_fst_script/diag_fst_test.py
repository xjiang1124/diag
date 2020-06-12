#!/usr/bin/python3

import argparse
import json
import os
import time
import subprocess

def cleanup(eth):
    subprocess.call(["ifconfig", eth, "down"])
    time.sleep(1)
    print()

def get_ssh_cmd(ip, cmd):
    ssh_cmd_fmt = "./sshpass -p pen123 ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' root@{} {}"
    ssh_cmd = ssh_cmd_fmt.format(ip, cmd)
    return ssh_cmd

def get_bus_list():
    result = subprocess.check_output("lspci -d 1dd8:1000 | awk '{print $1}'", shell=True)
    new_str = result.decode("utf-8")
    bus_list = [y for y in (x.strip() for x in new_str.splitlines()) if y]
    print("Found", len(bus_list), "devices", "\n")
    return bus_list

def get_product_name_from_pn(pn):
    if "68-0013-01" in pn:
        product_name = "NAPLES100IBM"
    elif "P26968" in pn:
        product_name = "NAPLES25SWM"
    else:
        product_name = "UNKNOWN"
    return product_name
def config_eth():
    slot_bus_dict = {1:'18:00.0', 2:'3b:00.0', 3:'d8:00.0', 4:'af:00.0'}
    
    eth_list = {'enp179s0', 'enp220s0', 'enp28s0', 'enp63s0'}
    for eth in eth_list:
        subprocess.call(["ifconfig", eth, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    bus_list = get_bus_list()

    card_slot_list = []
    
    for slot, bus in slot_bus_dict.items():
        if bus not in bus_list:
            continue

        print("slot"+str(slot))
        result = subprocess.check_output("lspci -vv -s "+bus+" | grep LnkSta:", shell=True, stderr=subprocess.STDOUT)
        new_str = result.decode("utf-8")
        bus_str = bus.split(":", 1)[0]
        bus_int = int(bus_str, 16)+4
        eth = "enp"+str(bus_int)+"s0"
        tmp = subprocess.call(["ifconfig", eth, "169.254."+str(bus_int)+".2/24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["ifconfig", eth, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        card_slot_list.append(slot)
        
    time.sleep(1)
    return card_slot_list

def fst_general():
    naples_env = os.environ.copy()
    naples_env["NAPLES_URL"] = "http://169.254.0.1"
    
    slot_bus_pair = [(1, '18:00.0'), (2, '3b:00.0'), (3, 'd8:00.0'), (4, 'af:00.0')]
    
    eth_list = {'enp179s0', 'enp220s0', 'enp28s0', 'enp63s0'}
    for eth in eth_list:
        subprocess.call(["ifconfig", eth, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    bus_list = get_bus_list()
    
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
            sn = fru["status"]["fru"]["serial-number"]
            product_name = fru["status"]["fru"]["product-name"].replace(" ", "")
            pn = fru["status"]["fru"]["part-number"]
            product_name = get_product_name_from_pn(pn)

            try:
                x = subprocess.check_output("/home/diag/penctl.linux.0302 show firmware-version", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                print("slot"+str(a), "sn:", sn, "type:", product_name, "failed")
                print("Get firmware failed")
                cleanup(eth)
                continue
            y = x.decode("utf-8")
            firmware = json.loads(y)

            if product_name == "NAPLES 25 " or product_name == "NAPLES25SWM":
                if "8GT/s" in new_str and "x8" in new_str:
                    print("slot"+str(a), b, "sn:", sn, "type:", product_name, "pass")
                else:
                    print("slot"+str(a), b, "sn:", sn, "type:", product_name, "failed")
                    print("Speed and Width are failed")
                    print(new_str.replace("\n", ""))
            else:
                if "8GT/s" in new_str and "x16" in new_str:
                    print("slot"+str(a), b, "sn:", sn, "type:", sn, "pass")
                else:
                    print("slot"+str(a), b, "sn:", sn, "type:", sn, "failed")
                    print("Speed and Width are failed")
                    print(new_str.replace("\n", ""))
            #print(fru["status"]["fru"]["serial-number"], fru["status"]["fru"]["product-name"].replace(" ", ""))
            print(firmware["running-fw"]+":", firmware["running-fw-version"])
            print("uboot:", firmware["running-uboot"])
            print("goldfw:", firmware["all-installed-fw"]["goldfw"]["kernel_fit"]["software_version"])
            cleanup(eth)

def fst_ibm_fetch_sn():
    print("Fetching SN with goldfw")
      
    slot_bus_dict = {1:24, 2:59, 3:216, 4:175}
    
    card_slot_list = config_eth()

    for slot in card_slot_list:
        bus = slot_bus_dict[slot]
        # Get SN
        ip = "169.254."+str(bus+4)+".1"
        cmd = "cat /tmp/fru.json"
        ssh_cmd = get_ssh_cmd(ip, cmd)
        try:
            output = subprocess.check_output(ssh_cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print("slot"+str(slot), "failed to fetch SN") 
            print("Get FRU failed")
            continue

        output1 = output.decode("utf-8")
        #print(output1)
        fru = json.loads(output1)
        sn = fru["serial-number"]
        pn = fru["board-assembly-area"]
        print("Slot", slot, "SN:", sn, "PN:", pn)

        # Switch to mainfw
        cmd = "/nic/tools/fwupdate -s mainfwa"
        ssh_cmd = get_ssh_cmd(ip, cmd)
        try:
            output = subprocess.check_output(ssh_cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(output.decode("utf-8"))
            print("slot"+str(slot), "sn", sn, "failed to switch to mainfw") 
            continue
        print("Slot", slot, "SN:", sn, "switched to mainfwa")

def fst_ibm_check_pcie(slot_list, sn_list):
    slot_bus_dict = {1:'18:00.0', 2:'3b:00.0', 3:'d8:00.0', 4:'af:00.0'}

    for i in range(len(slot_list)):
        slot = slot_list[i]
        sn = sn_list[i]
        bus = slot_bus_dict[int(slot)]

        result = subprocess.check_output("lspci -vv -s "+bus+" | grep LnkSta:", shell=True, stderr=subprocess.STDOUT)
        result1 = result.decode("utf-8")

        if "8GT/s" in result1 and "x16" in result1:
            print("slot"+str(slot), bus, "sn:", sn, "type: NAPLES100IBM", "pass")
        else:
            print("slot"+str(slot), bus, "sn:", sn, "type: NAPLES100IBM", "failed")
            print("Speed and Width are failed")
            print(result1.replace("\n", ""))


def main():
    parser = argparse.ArgumentParser(description="MTP Final Stage Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-card_type", "--card_type", help="card type", type=str, default="general")
    parser.add_argument("-stage", "--stage", help="stage: fetch_sn/check_pcie", type=str, default="fetch_sn")
    parser.add_argument("-slot_list", "--slot_list", help="slot list", type=str, default="")
    parser.add_argument("-sn_list", "--sn_list", help="SN list", type=str, default="")
    args = parser.parse_args()

    card_type = args.card_type.upper()
    stage = args.stage.upper()
    slot_list = args.slot_list.split(',')
    sn_list = args.sn_list.split(',')

    if card_type == "GENERAL":
        fst_general()
    elif card_type == "NAPLES100IBM":
        if stage == "FETCH_SN":
            fst_ibm_fetch_sn()
        elif stage == "CHECK_PCIE":
            fst_ibm_check_pcie(slot_list, sn_list)
        else:
            print("Wrong stage:", stage)
    else:
        print("Invalid card_type: ", card_type)

if __name__ == "__main__":
    main()
