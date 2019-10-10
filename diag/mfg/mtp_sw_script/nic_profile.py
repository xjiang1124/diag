#!/usr/bin/python3

import json
import time
import subprocess
import os

def cleanup():
    try:
        x = subprocess.check_output("penctl delete naples-profile -n new_naples_profile", env=naples_env, shell=True)
    except subprocess.CalledProcessError as e:
        print("Delete naples profile failed")
    pass

naples_env = os.environ.copy()
naples_env["NAPLES_URL"] = "http://localhost"

try:
    x = subprocess.check_output("penctl create naples-profile -p disable -n new_naples_profile", env=naples_env, shell=True)
except subprocess.CalledProcessError as e:
    print("ERROR Create naples profile failed")
    raise

try:
    x = subprocess.check_output("penctl update naples -f new_naples_profile", env=naples_env, shell=True)
except subprocess.CalledProcessError as e:
    print("ERROR Update naples profile failed")
    cleanup()
    raise

try:
    x = subprocess.check_output("penctl show naples-profiles", env=naples_env, shell=True)
except subprocess.CalledProcessError as e:
    print("ERROR Get naples profile failed")
    cleanup()
    raise
profiles = json.loads(x)
for item in profiles:
    # print(item)
    if item["meta"]["name"] == "new_naples_profile":
        # print(item["spec"]["default-port-admin"])
        if item["spec"]["default-port-admin"] == "PORT_ADMIN_STATE_DISABLE":
            print("PASS Netapp Profile disable port successfully")
        else:
            print("ERROR Netapp Profile disable port failed")
            cleanup()
