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
            Logger.error(f"Failed to load testsuite {testsuite_file} - Exception {e}")
            return defs.Result.INFRA_FAILURE
        return defs.Result.SUCCESS

    def __get_testbed_id(self, testbed_json):
        try:
            with open(testbed_json, 'r') as fh:
                testbed_spec = json.load(fh)
        except Exception as e:
            Logger.error(f"Failed to load {testbed_json} - Exception: {e}")
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

    def __parse_warmd(self, testbed_json):
        Logger.info(f"Loading {testbed_json} to parse MTP info")
        try:
            with open(testbed_json, 'r') as fh:
                testbed_spec = json.load(fh)
        except Exception as e:
            Logger.error(f"Failed to load {testbed_json} - Exception: {e}")
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
            Logger.error(f"Caught exception: {e}")
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
            'CAPABILITY': "0x3",
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
            Logger.error(f"Error writing yaml-file {mtp_cfg_yaml_file} to generate MTP test-cfg yaml")
            return defs.Result.INFRA_FAILURE

        self.__settings['MTP_CFG_YML'] = mtp_cfg_yaml_file
        self.__settings['MTP_ID'] = testbed_id
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
                fh.write(f'STOP\n')
        except Exception as e:
            Logger.error(f"Failed to write {scanDL_input}: {e}")
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __gen_mtp_sw_pn(self, mtp_resource_name, barcode_scans):
        # write to a file with all SW PNs in one line
        swi_input = "swi_input"
        Logger.info(f"Generating {mtp_resource_name} SW PN in input file: {swi_input}")

        sw_pn_test_args = ""
        for slot in barcode_scans.keys():
            if "SW_PN" not in barcode_scans[slot].keys():
                Logger.error(f"Missing 'SW_PN' field from slot {slot} in /vol/hw/diag/cicd/{mtp_resource_name}.yaml")
                return defs.Result.INFRA_FAILURE
            sw_pn = barcode_scans[slot]["SW_PN"]

            if not sw_pn.strip():
                sw_pn = "90-0000-0000" # enter something so we dont get stuck at "Scan SW PN:" input

            sw_pn_test_args += str(barcode_scans[slot]["SW_PN"]) + " "

        try:
            with open(os.path.join(GlobalOptions.topdir, swi_input), "w") as fh:
                fh.write(sw_pn_test_args)
        except Exception as e:
            Logger.error("Failed to write {:s}".format(swi_input))
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __gen_mtp_env(self):
        self.__settings["JOB_TYPE"] = self.__testsuite.config.job
        try:
            with open(os.path.join(GlobalOptions.topdir, "env.sh"), "w") as fh:
                for var, value in self.__settings.items():
                    fh.write(f'export {var}="{value}"\n')
        except Exception as e:
            Logger.error("Failed write env.sh")
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __load_image_manifest(self):

        manifest_file = os.path.join(GlobalOptions.image_manifest)

        with open(manifest_file, "r") as fh:
            manifest = json.load(fh)
            diag_images = list(filter(lambda x:
                                      x.get("Release", None) == GlobalOptions.diag_tool_version and
                                      x.get("Asic", None) == GlobalOptions.asic, manifest.get("MfgDiagImages", [])))

            if diag_images and diag_images[0].get("Images", None):
                imgs = diag_images[0].get("Images")
                self.__settings['DIAG_AMD64_IMAGE_PATH'] = os.path.join(GlobalOptions.diag_images, imgs.get("AMD64"))
                self.__settings['DIAG_ARM64_IMAGE_PATH'] = os.path.join(GlobalOptions.diag_images, imgs.get("ARM64"))
                self.__settings['DIAG_IMAGE_FOLDER'] = GlobalOptions.diag_images
            else:
                Logger.error("Could not load diag images from image-manifest:")
                Logger.error(diag_images)
                return defs.Result.INFRA_FAILURE

            asic_images = list(filter(lambda x:
                                      x.get("Release", None) == GlobalOptions.asic_lib_version and
                                      x.get("Asic", None) == GlobalOptions.asic, manifest.get("AsicLibraries", [])))

            if asic_images and asic_images[0].get("Images", None):
                imgs = asic_images[0].get("Images")
                self.__settings['ASIC_AMD64_IMAGE_PATH'] = os.path.join(GlobalOptions.asic_images, 
                                                                        GlobalOptions.asic, 
                                                                        imgs.get("AMD64"))
                self.__settings['ASIC_ARM64_IMAGE_PATH'] = os.path.join(GlobalOptions.asic_images, 
                                                                        GlobalOptions.asic, 
                                                                        imgs.get("ARM64"))
                self.__settings['ASIC_IMAGE_FOLDER'] = os.path.join(GlobalOptions.asic_images, GlobalOptions.asic)
            else:
                Logger.error("Could not load asic images from image-manifest:")
                Logger.error(asic_images)
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
                test_args += f" --skip-test {skip_list}"
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

        ret, barcode_scans = self.__gen_barcode_scans(mtp_resource_name)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract testing slots from /vol/hw/diag/cicd/{mtp_resource_name}.yaml - ABORT")
            return ret

        ret = self.__gen_mtp_inventory(mtp_resource, testbed_id, barcode_scans)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract mtp-inventory from {GlobalOptions.testbed_json} - ABORT")
            return ret

        ret = self.__gen_nic_barcodes(mtp_resource_name, barcode_scans)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract NIC SN, MAC, PN from /vol/hw/diag/cicd/{mtp_resource_name}.yaml - ABORT")
            return ret

        if self.__testsuite.config.job == "SWI":
            ret = self.__gen_mtp_sw_pn(mtp_resource_name, barcode_scans)
            if ret != defs.Result.SUCCESS:
                Logger.error(f"Failed to extract SW PNs from from /vol/hw/diag/cicd/{mtp_resource_name}.yaml - ABORT")
                return ret

        ret =  self.__load_image_manifest()
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to process image-manifest - ABORT")
            return ret

        ret = self.__build_test_cmdline_args()
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to build cmdline args - ABORT")
            return ret


        ret = self.__gen_mtp_env()
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to dump settings - ABORT")
            return ret

        return ret


if __name__ == '__main__':
    launcher = LaunchApp()
    ret = launcher.Main()
    sys.exit(ret.value) # Pass it on to jobd
