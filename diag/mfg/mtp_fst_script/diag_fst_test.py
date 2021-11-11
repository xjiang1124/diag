#!/usr/bin/python3

import argparse
import json
import os
import time
import subprocess
import re
import sys

def cleanup(eth):
    subprocess.call(["ifconfig", eth, "down"])
    time.sleep(1)
    print()

def get_ssh_cmd(ip, cmd):
    ssh_cmd_fmt = "/home/diag/mtp_fst_script/sshpass -p pen123 ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' root@{} {}"
    ssh_cmd_fmt = "/home/diag/mtp_fst_script/sshpass -p pen123 ssh -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' root@{} {}"
    ssh_cmd = ssh_cmd_fmt.format(ip, cmd)
    return ssh_cmd

def get_bus_list(card_type="CAPRI"):
    if card_type == "ORTANO":
        upstream_port = "0002"
    else:
        upstream_port = "1000"
    result = subprocess.check_output("lspci -d 1dd8:"+upstream_port+" | awk '{print $1}'", shell=True)
    new_str = result.decode("utf-8")
    bus_list = [y for y in (x.strip() for x in new_str.splitlines()) if y]
    print("Found", len(bus_list), "devices", "\n")
    return bus_list

def get_product_name_from_pn(pn):
    if "68-0013-01" in pn:
        product_name = "NAPLES100IBM"
    elif "P26968" in pn:
        product_name = "NAPLES25SWM"
    elif "68-0005-04" in pn or "P18669" in pn:
        product_name = "NAPLES25"
    elif "68-0011-02" in pn:
        product_name = "VOMERO2"
    elif "P37692" in pn:
        product_name = "NAPLES100HPE"
    elif "68-0014-01" in pn:
        product_name = "NAPLES25SWMDELL"
    elif "P41851-001" in pn:
        product_name = "NAPLES25SWM"
    elif "P41854-001" in pn:
        product_name = "NAPLES100HPE"    
    elif "68-0017-01" in pn:
        product_name = "NAPLES25SWM"
    elif "68-0013-01" in pn:
        product_name = "NAPLES25SWM"
    elif "P37689-001" in pn:
        product_name = "NAPLES25OCP"
    elif "P41857-001" in pn:
        product_name = "NAPLES25OCP"
    elif "68-0010" in pn:
        product_name = "NAPLES25OCP"
    elif "DSC1-2S25-4P8P-DS" in pn:
        product_name = "NAPLES25OCP"
    elif "DSC1-2S25-4H8P-SL" in pn:
        product_name = "NAPLES25SWM833"
    elif "DSC1-2S25-4H8P-ST" in pn:
        product_name = "NAPLES25SWM"
    elif "DSC1-2S25-4H8P-S" in pn:
        product_name = "NAPLES25SWM"
    elif "DSC2-2Q200-32R32F64P-R" in pn:
        product_name = "ORTANO2"
    elif "68-0015-02" in pn:
        product_name = "ORTANO2"
    elif "DSC1-2S25-4H8P-DS" in pn:
        product_name = "NAPLES25SWMDELL"
    elif "DSC1-2Q100-8F16P-D" in pn:
        product_name = "NAPLES100DELL"
    else:
        product_name = "UNKNOWN"
        print("Unknow PN:", pn)

    return product_name

def config_eth(card_type="", fst=0):

    if fst == 1:
        slot_bus_dict = { 1:'2a:00.0', 2:'08:00.0', 3:'61:00.0', 4:'21:00.0', 5:'41:00.0' }
        eth_list = {'enp46s0', 'enp12s0', 'enp101s0', 'enp37s0', 'enp69s0'}
    else:
        slot_bus_dict = {1:'18:00.0', 2:'3b:00.0', 3:'d8:00.0', 4:'af:00.0'}
        eth_list = {'enp179s0', 'enp220s0', 'enp28s0', 'enp63s0'}
    
    for eth in eth_list:
        subprocess.call(["ifconfig", eth, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    bus_list = get_bus_list(card_type)

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

def fst_general_old(fst):
    naples_env = os.environ.copy()
    naples_env["NAPLES_URL"] = "http://169.254.0.1"
    
    if fst == 1:
        slot_bus_pair = [(1, '2a:00.0'), (2, '08:00.0'), (3, '61:00.0'), (4, '21:00.0'), (5, '41:00.0')]
        eth_list = {'enp46s0', 'enp12s0', 'enp101s0', 'enp37s0', 'enp69s0'}
    else:
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
            tmp = subprocess.call(["ifconfig", eth, "169.254.0.2/24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            tmp = subprocess.call(["ifconfig", eth, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            try:
                x = subprocess.check_output("/home/diag/penctl.linux show naples", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                print("slot"+str(a), b, "sn: UNKNOWN", "type: UNKNOWN", "failed")
                print("Get FRU failed")
                print(str(e))
                cleanup(eth)
                continue
            y = x.decode("utf-8")
            fru = json.loads(y)
            try:
                x = subprocess.check_output("/home/diag/penctl.linux show firmware-version", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                print("slot"+str(a), "sn:", fru["status"]["fru"]["serial-number"], "type:", fru["status"]["fru"]["product-name"].replace(" ", ""), "failed")
                print("Get firmware failed")
                cleanup(eth)
                continue
            y = x.decode("utf-8")
            firmware = json.loads(y)

            sn = fru["status"]["fru"]["serial-number"]
            product_name = fru["status"]["fru"]["product-name"]

            if fru["status"]["fru"]["product-name"] == "NAPLES 25 ":
                if "8GT/s" in new_str and "x8" in new_str:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name.replace(" ", ""), "pass")
                    print("PCIE link: x8 at 8GT/s")
                else:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name.replace(" ", ""), "failed")
                    print("Speed and Width are failed")
                    print(new_str.replace("\n", ""))
            else:
                if "8GT/s" in new_str and "x16" in new_str:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name.replace(" ", ""), "pass")
                    print("PCIE link: x8 at 16GT/s")
                elif "16GT/s" in new_str and "x16" in new_str:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name.replace(" ", ""), "pass")
                    print("PCIE link: x8 at 16GT/s")
                else:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name.replace(" ", ""), "failed")
                    print("Speed and Width are failed")
                    print(new_str.replace("\n", ""))
            #print(fru["status"]["fru"]["serial-number"], fru["status"]["fru"]["product-name"].replace(" ", ""))
            print(firmware["running-fw"]+":", firmware["running-fw-version"])
            print("uboot:", firmware["running-uboot"])
            print("goldfw:", firmware["all-installed-fw"]["goldfw"]["kernel_fit"]["software_version"])
            cleanup(eth)

def fst_general(fst):
    naples_env = os.environ.copy()
    naples_env["DSC_URL"] = "http://169.254.0.1"
    
    if fst == 1:
        slot_bus_pair = [(1, '2a:00.0'), (2, '08:00.0'), (3, '61:00.0'), (4, '21:00.0'), (5, '41:00.0')]
        eth_list = {'enp46s0', 'enp12s0', 'enp101s0', 'enp37s0', 'enp69s0'}
    else:
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
            nic_ip = "169.254."+str(bus_int)+".1"
            naples_env["DSC_URL"] = "http://"+nic_ip
            time.sleep(1)
            try:
                x = subprocess.check_output("/home/diag/penctl.linux.02012021 show naples", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                print("slot:", str(a), b, "sn: UNKNOWN", "type: UNKNOWN", "failed")
                print("Get FRU failed")
                cleanup(eth)
                continue
            y = x.decode("utf-8")
            fru = json.loads(y)
            sn = fru["status"]["fru"]["serial-number"]
            product_name = fru["status"]["fru"]["product-name"].replace(" ", "")
            pn = fru["status"]["fru"]["part-number"]
            product_name = get_product_name_from_pn(pn)

            if product_name == "SSH_DETECT":
                print("SSH_DETECT")
                try:
                    x = subprocess.check_output("/home/diag/penctl.linux.02012021 -a /home/diag/penctl.token system enable-sshd", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
                    y = subprocess.check_output("/home/diag/penctl.linux.02012021 -a /home/diag/penctl.token update ssh-pub-key -f ~/.ssh/id_rsa.pub", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
                    cmd = "cat /tmp/fru.json"
                    ssh_cmd = get_ssh_cmd(nic_ip, cmd)
                    print(ssh_cmd)
                    z = subprocess.check_output(ssh_cmd, env=naples_env, shell=True, stderr=subprocess.DEVNULL)
                except:
                    print("Failed to use ssh to detect PN")
                    print("slot:", str(a), b, "sn: UNKNOWN", "type: UNKNOWN", "failed")
                    cleanup(eth)
                    continue

                #print(x.decode("utf-8"))
                #print(y.decode("utf-8"))
                #print(z.decode("utf-8"))
            
                zz = z.decode("utf-8")
                nic_fru = json.loads(zz)
                #print(nic_fru)
                pn = nic_fru["board-assembly-area"]
                product_name = get_product_name_from_pn(pn)

            try:
                x = subprocess.check_output("/home/diag/penctl.linux.02012021 show firmware-version", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                print("slot:", str(a), "sn:", sn, "type:", product_name, "failed")
                print("Get firmware failed")
                print(e.output)
                cleanup(eth)
                continue
            y = x.decode("utf-8")
            firmware = json.loads(y)

            if product_name == "NAPLES25" or product_name == "NAPLES25SWM" or product_name == "NAPLES25SWMDELL" or product_name == "NAPLES25SWM833" or product_name == "NAPLES25OCP":
                if "8GT/s" in new_str and "x8" in new_str:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name, "pass")
                    print("PCIE link: x8 at 8GT/s")
                else:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name, "failed")
                    print("Speed and Width are failed")
                    print(new_str.replace("\n", ""))
            else:
                if "8GT/s" in new_str and "x16" in new_str:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name, "pass")
                    print("PCIE link: x8 at 16GT/s")
                else:
                    print("slot:", str(a), b, "sn:", sn, "type:", product_name, "failed")
                    print("Speed and Width are failed")
                    print(new_str.replace("\n", ""))
            #print(fru["status"]["fru"]["serial-number"], fru["status"]["fru"]["product-name"].replace(" ", ""))
            print(firmware["running-fw"]+":", firmware["running-fw-version"])
            print("uboot:", firmware["running-uboot"])
            print("goldfw:", firmware["all-installed-fw"]["goldfw"]["kernel_fit"]["software_version"])
            cleanup(eth)

def fst_general_oracle(fst):
    if fst == 1:
        slot_bus_pair = [(1, '2a:00.0'), (2, '08:00.0'), (3, '61:00.0'), (4, '21:00.0'), (5, '41:00.0')]
        slot_bus_dict = {1:42, 2:8, 3:97, 4:33, 5:65}
    else:
        slot_bus_pair = [(1, '18:00.0'), (2, '3b:00.0'), (3, 'd8:00.0'), (4, 'af:00.0')]
        slot_bus_dict = {1:24, 2:59, 3:216, 4:175}
    
    card_slot_list = config_eth(fst)
    card_info_dict = dict()

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
            print(e.output)
            continue

        output1 = output.decode("utf-8")
        #print(output1)
        fru = json.loads(output1)
        sn = fru["serial-number"]
        pn = fru["board-assembly-area"]
        product_name =  get_product_name_from_pn(pn)

        card_info_dict[slot] = sn+':'+product_name

    for slot, sn_pn in card_info_dict.items():
        sn = sn_pn.split(":")[0]
        product_name = sn_pn.split(":")[1]

        bus = slot_bus_dict1[int(slot)]

        result = subprocess.check_output("lspci -vv -s "+bus+" | grep LnkSta:", shell=True, stderr=subprocess.STDOUT)
        result1 = result.decode("utf-8")

        if product_name == "UNKNOWN":
            print("slot:", str(slot), bus, "sn:", sn, "type:", product_name, "failed")
        elif "8GT/s" in result1 and "x16" in result1:
            print("slot:", str(slot), bus, "sn:", sn, "type:", product_name, "pass")
            print("PCIE link: x8 at 16GT/s")
        else:
            print("slot:", str(slot), bus, "sn:", sn, "type:", product_name, "failed")
            print("Speed and Width are failed")
            print(result1.replace("\n", ""))

def fst_cloud_fetch_sn(card_type, fst):
    print("Fetching SN with goldfw")

    try:
        os.remove("/home/diag/mtp_fst_script/card_info_dict.txt")
    except OSError:
        print("card_info_dict.txt not exist")
      
    if fst == 1:
        slot_bus_dict = {1:42, 2:8, 3:97, 4:33, 5:65}
    else:
        slot_bus_dict = {1:24, 2:59, 3:216, 4:175}
    
    card_slot_list = config_eth(card_type, fst)
    card_info_dict = dict()

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
            print("slot:", slot, "sn: SN_UNKNOWN type: UNKNOWN failed")
            print(e.output)
            continue

        output1 = output.decode("utf-8")
        print(output1)
        fru = json.loads(output1)
        sn = fru["serial-number"]
        match = re.findall("board-assembly-area", output1 )
        if match:
            pn = fru["board-assembly-area"]
        else:
            pn = fru["part-number"]

        print(sn, pn)
        product_name =  get_product_name_from_pn(pn)

        if product_name == "UNKNOWN":
            print("slot:", slot, "sn:", sn, "type:", product_name, "failed")
            continue
        else:
            print("slot:", slot, "sn:", sn, "type:", product_name, "pass")

        card_info_dict[slot] = sn+':'+product_name

        # Display all firmware versions
        cmd = "/nic/tools/fwupdate -l"
        ssh_cmd = get_ssh_cmd(ip, cmd)
        try:
            output = subprocess.check_output(ssh_cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(output.decode("utf-8"))
            print("slot:", str(slot), "sn", sn, "failed to execute fwupdate -l") 
            continue
        output1 = output.decode("utf-8")
        print(output1)
        fwlist = json.loads(output1)
        print("---------")
        try:
            if "boot0" in fwlist:
                print("boot0:     {:15s}   {:s} ".format(fwlist["boot0"]["image"]["software_version"], fwlist["boot0"]["image"]["build_date"]) )
            else:
                print("[ERROR] FWLIST missing boot0 info")
            if "mainfwa" in fwlist:
                print("mainfwa:   {:15s}   {:s} ".format(fwlist["mainfwa"]["kernel_fit"]["software_version"], fwlist["mainfwa"]["kernel_fit"]["build_date"]) )
            else:
                print("[ERROR] FWLIST missing mainfwa info")
            if "mainfwb" in fwlist:
                print("mainfwb:   {:15s}   {:s} ".format(fwlist["mainfwb"]["kernel_fit"]["software_version"], fwlist["mainfwb"]["kernel_fit"]["build_date"]) )
            else:
                print("[ERROR] FWLIST missing mainfwb info")
            if "goldfw" in fwlist:
                print("goldfw:    {:15s}   {:s} ".format(fwlist["goldfw"]["kernel_fit"]["software_version"], fwlist["goldfw"]["kernel_fit"]["build_date"]) )
            else:
                print("[ERROR] FWLIST missing goldfw info")
            if "diagfw" in fwlist:
                print("diagfw:    {:15s}   {:s} ".format(fwlist["diagfw"]["kernel_fit"]["software_version"], fwlist["diagfw"]["kernel_fit"]["build_date"]) )
            else:
                print("[ERROR] FWLIST missing diagfw info")
        except KeyError as e:
            print("[ERROR] FWLIST missing info")
            print(e)
        print("---------")

        # Switch to mainfw
        cmd = "/nic/tools/fwupdate -s mainfwa"
        ssh_cmd = get_ssh_cmd(ip, cmd)
        try:
            output = subprocess.check_output(ssh_cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(output.decode("utf-8"))
            print("slot:", str(slot), "sn", sn, "failed to switch to mainfw") 
            continue
        print("slot", slot, "sn:", sn, "switched to mainfwa")

    json.dump(card_info_dict, open("/home/diag/mtp_fst_script/card_info_dict.txt",'w'))


def fst_cloud_check_pcie(fst):

    card_info_dict = json.load(open("/home/diag/mtp_fst_script/card_info_dict.txt"))

    if fst == 1:
        slot_bus_dict = { 1:'2a:00.0', 2:'08:00.0', 3:'61:00.0', 4:'21:00.0', 5:'41:00.0' }
    else:
        slot_bus_dict = {1:'18:00.0', 2:'3b:00.0', 3:'d8:00.0', 4:'af:00.0'}

    for slot, sn_pn in card_info_dict.items():
        sn = sn_pn.split(":")[0]
        product_name = sn_pn.split(":")[1]

        bus = slot_bus_dict[int(slot)]

        result = subprocess.check_output("lspci -vv -s "+bus+" | grep LnkSta:", shell=True, stderr=subprocess.STDOUT)
        result1 = result.decode("utf-8")

        if product_name == "UNKNOWN":
            print("slot:", str(slot), bus, "sn:", sn, "type:", product_name, "failed")
            print(result1.replace("\n", ""))
            continue
        elif "NAPLES25" in product_name:
            tgt_width = 'x8'
        else:
            tgt_width = 'x16'

        if "ORTANO" in product_name:
            tgt_speed = "16GT/s"
        else:
            tgt_speed = "8GT/s"

        if tgt_speed in result1 and tgt_width in result1:
            print("slot:", str(slot), bus, "sn:", sn, "type:", product_name, "pass")
        else:
            print("slot:", str(slot), bus, "sn:", sn, "type:", product_name, "failed")
            print("speed and width are failed")
            print(result1.replace("\n", ""))


def main():
    parser = argparse.ArgumentParser(description="MTP Final Stage Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-card_type", "--card_type", help="card type", type=str, default="general")
    parser.add_argument("-stage", "--stage", help="stage: fetch_sn/check_pcie", type=str, default="fetch_sn")
    parser.add_argument("-fst", "--fst", help="fst type", type=int, default=0)
    args = parser.parse_args()

    card_type = args.card_type.upper()
    stage = args.stage.upper()
    fst_type = args.fst

    if card_type == "GENERAL":
        fst_general(fst_type)
    elif card_type == "GENERAL_OLD":
        fst_general_old(fst_type)
    elif card_type == "ORACLE":
        fst_general_oracle(fst_type)
    elif card_type == "NAPLES100IBM" or "CLOUD" in card_type:
        if stage == "FETCH_SN":
            fst_cloud_fetch_sn(card_type, fst_type)
        elif stage == "CHECK_PCIE":
            fst_cloud_check_pcie(fst_type)
        else:
            print("Wrong stage:", stage)
    else:
        print("Invalid card_type: ", card_type)

if __name__ == "__main__":
    main()
