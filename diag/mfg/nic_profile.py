#!/usr/bin/python3

import json
import time
import subprocess
import os

naples_env = os.environ.copy()
naples_env["NAPLES_URL"] = "http://localhost"

try:
    x = subprocess.check_output("penctl create naples-profile -p disable -n new_naples_profile", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError as e:
    print("Create naples profile failed")
    raise

try:
    x = subprocess.check_output("penctl update naples -f new_naples_profile", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError as e:
    print("Update naples profile failed")
    raise

try:
    x = subprocess.check_output("penctl show naples-profiles", env=naples_env, shell=True, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError as e:
    print("Get naples profile failed")
    raise
profiles = json.loads(x)
for item in profiles:
    # print(item)
    if item["meta"]["name"] == "new_naples_profile":
        # print(item["spec"]["default-port-admin"])
        if item["spec"]["default-port-admin"] == "PORT_ADMIN_STATE_DISABLE":
            print("Profile disable port successfully")
        else:
            print("Profile disable port failed")