#!/usr/bin/python

import json
import sys
import yaml
import os
import logging
import subprocess
import pdb


topdir = os.path.dirname(sys.argv[0]) + '/../../'
topdir = os.path.abspath(topdir)
sys.path.insert(0, topdir)

# This import will parse all the command line options.
from glopts import GlobalOptions
import defs
GlobalOptions.topdir = topdir

# Initialize the logger
import logger


Logger = logger.InitLogger()

def __gen_mtp_inventory(json_file):
    Logger.info(f"Loading {json_file} to generate MTP test-cfg yaml")
    try:
        with open(json_file, 'r') as fh:
            testbed_spec = json.load(fh)
    except Exception as e:
        Logger.error(f"Failed to load {json_file} - Exception: {e}")
        return None, None
    mtp_cfg_yaml_file = os.path.join(GlobalOptions.cfgfolder, 'jobd_mtp_cfg.yml')

    # Build specific details required for mfg test (example)
    #MTP-002:
    #    MODE: ""
    #    TS: "192.168.74.208"
    #    TS_PORT: "2008"
    #    TS_USERID: "admin"
    #    TS_PASSWORD: "N0isystem$"
    #    APC1: ""
    #    APC1_PORT: ""
    #    APC1_USERID: ""
    #    APC1_PASSWORD: ""
    #    APC2: "192.168.70.161"
    #    APC2_PORT: "12"
    #    APC2_USERID: "apc"
    #    APC2_PASSWORD: "apc"
    #    IP: "192.168.68.182"
    #    USERID: "diag"
    #    PASSWORD: "lab123"
    #    ALIAS: "mtp001"
    #    SLOTS: 10
    #    CAPABILITY: 0x2

    instances = testbed_spec.get('Instances', None)
    if instances == None or len(instances) == 0:
        return None

    mtp_instance = instances[0]
    mtp_resource = mtp_instance.get('Resource', None)

    if mtp_resource == None:
        return None

    testbed_id = testbed_spec.get('ID').split("-")[1]
    data = {
        'MODE': "",
        'TS': "",
        'TS_PORT': "",
        'TS_USERID': "admin",
        'TS_PASSWORD': "N0isystem$",
        'APC1': mtp_resource.get('ApcIP', ""),
        'APC1_PORT': mtp_resource.get('ApcPort', ""),
        'APC1_USERID': mtp_resource.get('ApcUsername', ""),
        'APC1_PASSWORD': mtp_resource.get('ApcPassword', ""),
        'APC2': "",
        'APC2_PORT': "",
        'APC2_USERID': "",
        'APC2_PASSWORD': "",
        'IP': mtp_instance.get("NodeCimcIP", ""),
        'USERID': "diag",
        'PASSWORD': "lab123",
        'ALIAS': f"mtp{testbed_id}",
        'SLOTS': 10,
        'CAPABILITY': "0x3",
    }

    mtp_id = f"MTP-{testbed_id}"
    mtp_yaml_data = {
            mtp_id : data,
    }

    Logger.info(f"Generating {mtp_id} in cfg-yaml file: {mtp_cfg_yaml_file}")
    try:
        with open(mtp_cfg_yaml_file, 'w') as fh:
            yaml.dump(mtp_yaml_data, fh)
    except Exception as e:
        Logger.error(f"Error writing yaml-file {mtp_cfg_yaml_file} to generate MTP test-cfg yaml")
        return None
    return  mtp_id, mtp_cfg_yaml_file

def __gen_mtp_env(var_values):
    try:
        with open(os.path.join(GlobalOptions.topdir, "env.sh"), "w") as fh:
            for var, value in var_values.items():
                fh.write(f"export {var}={value}\n")
    except Exception as e:
        Logger.error("Failed write env.sh")
        return defs.Result.INFRA_FAILURE

    return defs.Result.SUCCESS

def __download_assets(version, tmp_folder):
    ret = defs.Result.SUCCESS

    out_file = f"{os.path.join(tmp_folder, 'asset.tgz')}"
    try:
        download_cmd = f"/usr/bin/asset-pull --bucket hw-repository  released-diag-sw {version} {out_file}"
        process = subprocess.Popen(download_cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        Logger.info(output)
    except Exception as e:
        Logger.error(e)
        ret = defs.Result.INFRA_FAILURE

    try:
        extract_cmd = f"tar --directory {tmp_folder} -zxf {out_file}"
        process = subprocess.Popen(extract_cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        Logger.info(output)
    except Exception as e:
        Logger.error(e)
        ret = defs.Result.INFRA_FAILURE

    return ret

def __launch_mfg_test(mtp_yaml_file):
    if os.path.exists(mtp_yaml_file):
        return defs.Result.SUCCESS
    return defs.Result.INFRA_FAILURE

def Main():
    ret = defs.Result.SUCCESS

    var_values = {}
    mtp_id, mtp_yaml_file = __gen_mtp_inventory(GlobalOptions.testbed_json)

    if mtp_yaml_file == None:
        Logger.error(f"Failed to extract mtp-inventory from {GlobalOptions.testbed_json} - ABORT")
        return defs.Result.INFRA_FAILURE
    var_values['MTP_CFG_YML'] = mtp_yaml_file
    var_values['MTP_ID'] = mtp_id

    if GlobalOptions.version:
        var_values['DIAG_VERSION'] = GlobalOptions.version
        if GlobalOptions.version != "latest":
            ret = __download_assets(GlobalOptions.version, GlobalOptions.tmp_folder)
            if ret == defs.Result.INFRA_FAILURE:
                Logger.error(f"Failed to download mtp diag-sw from minio/assets - ABORT")
                return defs.Result.INFRA_FAILURE

            # Load MANIFEST-file
            asset_folder = os.path.join(GlobalOptions.tmp_folder, "asset")
            manifest_file = os.path.join(asset_folder, "manifest.json")
        else:
            manifest_file = os.path.join(GlobalOptions.topdir, "test", "infra", "manifests", "latest.json")
            asset_folder = os.path.join(GlobalOptions.topdir, "build", "images")
        try:
            with open(manifest_file, "r") as fh:
                manifest = json.load(fh)
            diag_images = list(filter(lambda x:
                                      x.get("Release", None) == GlobalOptions.version and
                                      x.get("Asic", None) == GlobalOptions.asic, manifest.get("MfgDiagImages", [])))

            if diag_images and diag_images[0].get("Images", None):
                imgs = diag_images[0].get("Images")
                var_values['DIAG_AMD64_IMAGE_PATH'] = os.path.join(asset_folder, imgs.get("AMD64"))
                var_values['DIAG_ARM64_IMAGE_PATH'] = os.path.join(asset_folder, imgs.get("ARM64"))
                var_values['DIAG_IMAGE_FOLDER'] = asset_folder
            else:
                return defs.Result.INFRA_FAILURE
        except Exception as e:
            return defs.Result.INFRA_FAILURE

    ret = __gen_mtp_env(var_values)

    return ret


if __name__ == '__main__':
    ret = Main()
    sys.exit(ret.value) # Pass it on to jobd
