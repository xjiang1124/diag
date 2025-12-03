#!/usr/bin/python

import json
import sys
import yaml
import os
import logging
import subprocess
import pdb


topdir = os.path.abspath(os.getcwd())
sys.path.insert(0, topdir)

# This import will parse all the command line options.
from glopts import GlobalOptions
import defs
GlobalOptions.topdir = topdir

# Initialize the logger
import logger
import parser
import traceback


Logger = logger.InitLogger()

class LaunchApp(object):

    def __init__(self):
        self.__settings = {}
        self.__testsuite = None

    def __lookup_testsuite(self, testsuite_file):
        if testsuite_file == None:
            Logger.error(f"Failed to load testsuite, error: testsuite-file is None") 
            return defs.Result.INFRA_FAILURE

        try:
            self.__testsuite = parser.YmlParse(testsuite_file)
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Failed to load testsuite {testsuite_file} - Exception {err_msg}")
            return defs.Result.INFRA_FAILURE
        return defs.Result.SUCCESS

    def __get_testbed_id(self, testbed_json):
        try:
            with open(testbed_json, 'r') as fh:
                testbed_spec = json.load(fh)
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Failed to load {testbed_json} - Exception: {err_msg}")
            return None

        ## get testbed_id
        testbed_id = testbed_spec.get('ID').split("-")[1]

        ## get mtp_resource_name
        instances = testbed_spec.get('Instances', None)
        if instances == None or len(instances) == 0:
            return defs.Result.INFRA_FAILURE, None
        mtp_instance = instances[0]
        mtp_resource_name = mtp_instance.get('Name')

        return testbed_id, mtp_resource_name

    def __check_mtp_available(self, mtp_resource_name):
        try:
            with open("/vol/hw/diag/cicd/mtp.db", "r") as mtp_db_fh:
                for line in mtp_db_fh.readlines():
                    mtp_id, mtp_status = line.strip().split(" ")
                    if mtp_id == mtp_resource_name:
                        if mtp_status.lower().strip() == "online":
                            return True
                        else:
                            return False
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Caught exception: {err_msg}")
            return defs.Result.INFRA_FAILURE

    def __parse_warmd(self, testbed_json):
        Logger.info(f"Loading {testbed_json} to parse MTP info")
        try:
            with open(testbed_json, 'r') as fh:
                testbed_spec = json.load(fh)
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Failed to load {testbed_json} - Exception: {err_msg}")
            return defs.Result.INFRA_FAILURE, None

        instances = testbed_spec.get('Instances', None)
        if instances == None or len(instances) == 0:
            return defs.Result.INFRA_FAILURE, None

        mtp_instance = instances[0]
        mtp_resource = mtp_instance.get('Resource', None)
        if mtp_resource == None:
            Logger.error(f"Failed to extract MTP resource JSON from {GlobalOptions.testbed_json} - ABORT")
            return defs.Result.INFRA_FAILURE, None

        cleaned_mtp_resource = dict()
        for key in mtp_resource.keys():
            cleaned_mtp_resource[key.strip()] = mtp_resource[key]
        mtp_resource = cleaned_mtp_resource
        print(mtp_resource)

        return defs.Result.SUCCESS, mtp_resource

    def __gen_barcode_scans(self, mtp_resource_name):
        nic_type = GlobalOptions.nic_type.upper()

        import yaml
        barcode_scans = dict()
        try:
            with open("/vol/hw/diag/cicd/{:s}.yaml".format(mtp_resource_name), "r") as mtp_yml:
              scans_yml = yaml.load(mtp_yml, yaml.SafeLoader)
            for slot in range(1,11):
              if slot not in scans_yml.keys():
                # empty slot
                continue
              if "SKUs" not in scans_yml[slot].keys():
                Logger.error(f"Bad MTP barcodes - Missing 'SKUs' field in /vol/hw/diag/cicd/{mtp_resource_name}.yaml:")
                Logger.error(f"{scans_yml[slot]}")
                return defs.Result.INFRA_FAILURE
              node = scans_yml[slot]["SKUs"]
              for key, value in zip(node.keys(), node.values()):
                key = key.upper()
                if nic_type != key:
                  # not the nic_type for this job
                  continue
                barcode_scans[slot] = value
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Caught exception: {err_msg}")
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS, barcode_scans

    def __gen_mtp_inventory(self, mtp_resource, testbed_id, barcode_scans):
        mtp_cfg_yaml_file = os.path.join(GlobalOptions.cfgfolder, 'jobd_mtp_cfg.yml')
        mtp_ip = mtp_resource.get("host-ip")

        data = {
            'MODE': "",
            'TS': "",
            'TS_PORT': "",
            'TS_USERID': "admin",
            'TS_PASSWORD': "N0isystem$",
            'APC1': "",
            'APC1_PORT': "",
            'APC1_USERID': "",
            'APC1_PASSWORD': "",
            'APC2': "",
            'APC2_PORT': "",
            'APC2_USERID': "",
            'APC2_PASSWORD': "",
            'IP': mtp_ip,
            'USERID': "diag",
            'PASSWORD': "lab123",
            'ALIAS': f"{self.__testsuite.config.testbed.lower()}{testbed_id}",
            'SLOTS': 10,
            'SKIP_SLOTS': "",
            'CAPABILITY': "0x7",
        }

        # add in APC info
        for idx, pdu_idx in enumerate(["", "2"]):
            pdu_info = mtp_resource.get("pdu-ip"+pdu_idx, None)
            if pdu_info:
                data[f"APC{idx+1}"] = mtp_resource.get("pdu-ip"+pdu_idx, "")
                data[f"APC{idx+1}_PORT"] = mtp_resource.get("pdu-port"+pdu_idx, "")
                if mtp_resource.get("pdu-username"+pdu_idx):
                    data[f'APC{idx+1}_USERID'] =  mtp_resource.get("pdu-username"+pdu_idx, "")
                    data[f'APC{idx+1}_PASSWORD'] =  mtp_resource.get("pdu-password"+pdu_idx, "")
                else:
                    data[f'APC{idx+1}_USERID'] =  "apc"
                    data[f'APC{idx+1}_PASSWORD'] =  "apc"

        # change SKIP_SLOTS to test only slots that match the nic_type
        def list_subtract(a, b):
            """ set(A) - set(B) but keep the ordering """
            return list(x for x in a if x not in b)

        def make_skip_slots_string(slots_to_test):
          skip_slots = list_subtract(range(1,11), slots_to_test)
          return ",".join(map(str, skip_slots))

        slots_to_test = list(barcode_scans.keys())
        slots_to_test.sort()
        data['SKIP_SLOTS'] = make_skip_slots_string(slots_to_test)

        testbed_id = f"{self.__testsuite.config.testbed}-{testbed_id}"
        mtp_yaml_data = {
                testbed_id : data,
        }

        Logger.info(f"Generating {testbed_id} in cfg-yaml file: {mtp_cfg_yaml_file}")
        try:
            with open(mtp_cfg_yaml_file, 'w') as fh:
                yaml.dump(mtp_yaml_data, fh)
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Error writing yaml-file {mtp_cfg_yaml_file} to generate MTP test-cfg yaml")
            Logger.error(f"{err_msg}")
            return defs.Result.INFRA_FAILURE

        self.__settings['MTP_CFG_YML'] = mtp_cfg_yaml_file
        self.__settings['MTP_ID'] = testbed_id
        return defs.Result.SUCCESS

    def __gen_mtp_barcodes(self, mtp_resource_name):
        if self.__testsuite.config.job != "SRN":
            return defs.Result.SUCCESS
        ## READ
        try:
            mtp_barcode_scans = dict()
            with open("/vol/hw/diag/cicd/srn.db", "r") as mtp_db_fh:
                for line in mtp_db_fh.readlines():
                    mtp_id, mtp_sn, mtp_mac = line.split(" ")
                    if mtp_id == mtp_resource_name:
                        mtp_barcode_scans["SN"] = mtp_sn
                        mtp_barcode_scans["MAC"] = mtp_mac
                        try:
                            SRN_input = "mtp_barcode_scan"
                            Logger.info(f"Generating {mtp_resource_name} MTP barcodes in input file: {SRN_input}")
                            with open(os.path.join(GlobalOptions.topdir, SRN_input), "w") as fh:
                                if "SN" not in mtp_barcode_scans.keys():
                                    Logger.error(f"Missing SN column from {mtp_resource_name} in mtp.db")
                                    return defs.Result.INFRA_FAILURE
                                if "MAC" not in mtp_barcode_scans.keys():
                                    Logger.error(f"Missing MAC column from {mtp_resource_name} in mtp.db")
                                    return defs.Result.INFRA_FAILURE
                                fh.write(mtp_barcode_scans['SN'] + "\n")
                                fh.write(mtp_barcode_scans['MAC'] + "\n")
                        except Exception as e:
                            err_msg = traceback.format_exc()
                            Logger.error(f"Failed to write {SRN_input}: {err_msg}")
                            return defs.Result.INFRA_FAILURE

        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Caught exception: {err_msg}")
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __gen_nic_barcodes(self, mtp_resource_name, barcode_scans):
        # write to a file same as it is scanned into scan_dl...
        scanDL_input = "nic_barcode_scan"
        Logger.info(f"Generating {mtp_resource_name} NIC barcodes in input file: {scanDL_input}")
        try:
            with open(os.path.join(GlobalOptions.topdir, scanDL_input), "w") as fh:
                for slot in barcode_scans.keys():
                    if "SN" not in barcode_scans[slot].keys():
                        Logger.error(f"Missing 'SN' field from slot {slot} in /vol/hw/diag/cicd/{mtp_resource_name}.yaml")
                        return defs.Result.INFRA_FAILURE
                    if "MAC" not in barcode_scans[slot].keys():
                        Logger.error(f"Missing 'MAC' field from slot {slot} in /vol/hw/diag/cicd/{mtp_resource_name}.yaml")
                        return defs.Result.INFRA_FAILURE
                    if "PN" not in barcode_scans[slot].keys():
                        # Dont throw error for missing PN since it can be empty for Dell-monterey label
                        barcode_scans[slot]['PN'] = ""

                    fh.write('NIC-{:02d}\n'.format(slot))
                    fh.write(barcode_scans[slot]['SN'] + "\n")
                    fh.write(barcode_scans[slot]['MAC'] + "\n")
                    if barcode_scans[slot]['PN']:
                        fh.write(barcode_scans[slot]['PN'] + "\n")
                    if "DPN" in barcode_scans[slot]:
                        fh.write(barcode_scans[slot]["DPN"] + "\n")
                    if "SKU" in barcode_scans[slot]:
                        fh.write(barcode_scans[slot]["SKU"] + "\n")
                    if "HPESN" in barcode_scans[slot]:
                        fh.write(barcode_scans[slot]["HPESN"] + "\n")
                    if "HPECT" in barcode_scans[slot]:
                        fh.write(barcode_scans[slot]["HPECT"] + "\n")
                    if "HPEMAC" in barcode_scans[slot]:
                        fh.write(barcode_scans[slot]["HPEMAC"] + "\n")
                    if self.__testsuite.config.job == "FST":
                        fh.write("ROT-000{:02d}".format(slot) + "\n")

                fh.write(f'STOP\n')
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error(f"Failed to write {scanDL_input}: {err_msg}")
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __gen_nic_serial_number_list(self, mtp_resource_name, barcode_scans):
        # write to a file same as it is scanned into scan_dl...
        scanDL_input = "parser_sn.txt"
        Logger.info(f"Generating {mtp_resource_name} NIC Serial Numbers in input file: {scanDL_input}")
        try:
            with open(os.path.join(GlobalOptions.topdir, scanDL_input), "w") as fh:
                for slot in barcode_scans.keys():
                    if "SN" not in barcode_scans[slot].keys():
                        Logger.error(f"Missing 'SN' field from slot {slot} in /vol/hw/diag/cicd/{mtp_resource_name}.yaml")
                        return defs.Result.INFRA_FAILURE
                    if barcode_scans[slot]["SN"].startswith("US") or barcode_scans[slot]["SN"].startswith("MY"):
                        dell_ppid = barcode_scans[slot]["SN"]
                        barcode_scans[slot]["SN"] = dell_ppid[0:2] + dell_ppid[8:20]
                    fh.write(barcode_scans[slot]['SN'] + "\n")
        except Exception as e:
            Logger.error(f"Failed to write {scanDL_input}: {e}")
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __gen_mtp_env(self, mtp_resource):
        self.__settings["JOB_TYPE"] = self.__testsuite.config.job
        self.__settings["NIC_TYPE"] = GlobalOptions.nic_type.lower()

        mtp_type = mtp_resource.get("mtp-nic-processor", "FST").upper()
        if mtp_type == "ELBA":
            mtp_type = "TURBO_ELBA"
        self.__settings["MTP_TYPE"] = mtp_type
        try:
            with open(os.path.join(GlobalOptions.topdir, "env.sh"), "w") as fh:
                for var, value in self.__settings.items():
                    fh.write(f'export {var}="{value}"\n')
        except Exception as e:
            err_msg = traceback.format_exc()
            Logger.error("Failed write env.sh")
            Logger.error(f"{err_msg}")
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __load_image_manifest(self):

        manifest_file = os.path.join(GlobalOptions.image_manifest)

        with open(manifest_file, "r") as fh:
            manifest = json.load(fh)
            diag_images = list(filter(lambda x:
                                      x.get("Release", None) == GlobalOptions.diag_tool_version and
                                      x.get("Asic", None) == GlobalOptions.asic, manifest.get("MfgDiagImages", [])))

            self.__settings["ASIC"] = GlobalOptions.asic

            if diag_images and diag_images[0].get("Images", None):
                imgs = diag_images[0].get("Images")
                self.__settings['DIAG_AMD64_IMAGE_PATH'] = os.path.join(GlobalOptions.diag_images, imgs.get("AMD64"))
                self.__settings['DIAG_ARM64_IMAGE_PATH'] = os.path.join(GlobalOptions.diag_images, imgs.get("ARM64"))
                self.__settings['DIAG_IMAGE_FOLDER'] = GlobalOptions.diag_images
            else:
                Logger.error("Could not load diag images from image-manifest:")
                Logger.error(diag_images)
                return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __build_test_cmdline_args(self):
        """
        Build TEST_ARGS
        diag-sanity: --mtpcfg ${MTP_CFG_YML} --iteration {testsuite.iteration} --mtpid ${MTP_ID}
        diag-regression: --mtpcfg ${MTP_CFG_YML} --iteration {testsuite.iteration} --mtpid ${MTP_ID}
        diag-precheckin: --mtpcfg ${MTP_CFG_YML} --iteration {testsuite.iteration} --skip-test <skip-list> --mtpid ${MTP_ID}
        """

        ret = defs.Result.SUCCESS
        if hasattr(self.__testsuite.test_types, GlobalOptions.testtype):
            test_spec = getattr(self.__testsuite.test_types, GlobalOptions.testtype)
            test_args = (f"--mtpcfg {self.__settings['MTP_CFG_YML']} " +
                         f"--mtpid {self.__settings['MTP_ID']} ")
            if hasattr(test_spec, 'iteration'):
                test_args += f"--iteration {getattr(test_spec, 'iteration', 1)} "
            if hasattr(test_spec, 'skip') and test_spec.skip != None:
                skip_list = " ".join(test_spec.skip)
                # Special args for particular nic_type
                ############################################
                nic_type = GlobalOptions.nic_type.lower()
                test_stage = self.__testsuite.config.job
                if "naples25swm" in nic_type.lower() and test_stage.upper() in ("P2C", "4C"):
                    skip_list += " SNAKE_HBM"
                ############################################
                test_args += f" --skip_test {skip_list}"
            self.__settings["TEST_ARGS"] = test_args

            if hasattr(self.__testsuite.config, 'card_type'):
                self.__settings["CARD_TYPE"] = self.__testsuite.config.card_type
        else:
            ret = defs.Result.INFRA_FAILURE

        return ret

    def Main(self):
        ret = defs.Result.SUCCESS

        ret = self.__lookup_testsuite(GlobalOptions.testsuite)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to lookup testsuite from {GlobalOptions.testbed_json} - ABORT")
            return ret

        ret, mtp_resource = self.__parse_warmd(GlobalOptions.testbed_json)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract MTP resource JSON from {GlobalOptions.testbed_json} - ABORT")
            return ret

        testbed_id, mtp_resource_name = self.__get_testbed_id(GlobalOptions.testbed_json)

        if not self.__check_mtp_available(mtp_resource_name):
            Logger.info(f"{mtp_resource_name} is down for maintenance. Once resolved, please cancel and re-run this job.")
            Logger.info(f"{mtp_resource_name} is down for maintenance. Once resolved, please cancel and re-run this job.")
            Logger.info(f"{mtp_resource_name} is down for maintenance. Once resolved, please cancel and re-run this job.")
            while not self.__check_mtp_available(mtp_resource_name):
                continue

        ret, barcode_scans = self.__gen_barcode_scans(mtp_resource_name)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract testing slots from /vol/hw/diag/cicd/{mtp_resource_name}.yaml - ABORT")
            return ret

        ret = self.__gen_mtp_inventory(mtp_resource, testbed_id, barcode_scans)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract mtp-inventory from {GlobalOptions.testbed_json} - ABORT")
            return ret

        ret = self.__gen_mtp_barcodes(mtp_resource_name)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract MTP SN, MAC from /vol/hw/diag/cicd/srn.db for {mtp_resource_name} - ABORT")
            return ret

        ret = self.__gen_nic_barcodes(mtp_resource_name, barcode_scans)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract NIC SN, MAC, PN from /vol/hw/diag/cicd/{mtp_resource_name}.yaml - ABORT")
            return ret

        ret = self.__gen_nic_serial_number_list(mtp_resource_name, barcode_scans)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract NIC SN from /vol/hw/diag/cicd/{mtp_resource_name}.yaml - ABORT")
            return ret

        ret =  self.__load_image_manifest()
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to process image-manifest - ABORT")
            return ret

        ret = self.__build_test_cmdline_args()
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to build cmdline args - ABORT")
            return ret


        ret = self.__gen_mtp_env(mtp_resource)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to dump settings - ABORT")
            return ret

        return ret


if __name__ == '__main__':
    launcher = LaunchApp()
    ret = launcher.Main()
    sys.exit(ret.value) # Pass it on to jobd
