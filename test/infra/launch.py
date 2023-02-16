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

    def __gen_mtp_inventory(self, testbed_json):
        Logger.info(f"Loading {testbed_json} to generate MTP test-cfg yaml")
        try:
            with open(testbed_json, 'r') as fh:
                testbed_spec = json.load(fh)
        except Exception as e:
            Logger.error(f"Failed to load {testbed_json} - Exception: {e}")
            return defs.Result.INFRA_FAILURE
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
            return defs.Result.INFRA_FAILURE

        mtp_instance = instances[0]
        mtp_resource = mtp_instance.get('Resource', None)

        if mtp_resource == None:
            return defs.Result.INFRA_FAILURE

        mtp_ip = mtp_resource.get("host-ip")

        testbed_id = testbed_spec.get('ID').split("-")[1]
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

        # change SKIP_SLOTS to skip none or use outermost 2 even slots
        test_spec = getattr(self.__testsuite.test_types, GlobalOptions.testtype)
        if hasattr(test_spec, 'slots') and int(test_spec.slots) != 10:
            data['SKIP_SLOTS'] = "1,3-9"

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

    def __gen_nic_barcodes(self, testbed_json):
        Logger.info(f"Loading {testbed_json} to generate barcode scanning input")
        try:
            with open(testbed_json, 'r') as fh:
                testbed_spec = json.load(fh)
        except Exception as e:
            Logger.error(f"Failed to load {testbed_json} - Exception: {e}")
            return defs.Result.INFRA_FAILURE

        instances = testbed_spec.get('Instances', None)
        if instances == None or len(instances) == 0:
            return defs.Result.INFRA_FAILURE

        mtp_instance = instances[0]
        mtp_resource = mtp_instance.get('Resource', None)

        if mtp_resource == None:
            return defs.Result.INFRA_FAILURE

        data = dict()

        # scan all barcodes, or only 2, based on what test spec says
        test_spec = getattr(self.__testsuite.test_types, GlobalOptions.testtype)
        if hasattr(test_spec, 'slots') and int(test_spec.slots) != 10:
            slot_range = [2,10]
        else:
            slot_range = range(1,11)

        for slot in slot_range:
            nic_slot = "NIC-{:02d}".format(slot)
            data[nic_slot] = {
                'SN': mtp_resource.get("nic{:d}-serial-number".format(slot)),
                'MAC': mtp_resource.get("nic{:d}-mac-address".format(slot)),
                'PN': mtp_resource.get("nic{:d}-part-number".format(slot))
            }

        # write to a file same as it is scanned into scan_dl...
        scanDL_input = "nic_barcode_scan"
        testbed_id = testbed_spec.get('ID').split("-")[1]
        testbed_id = f"{self.__testsuite.config.testbed}-{testbed_id}"
        Logger.info(f"Generating {testbed_id} NIC barcodes in input file: {scanDL_input}")
        try:
            with open(os.path.join(GlobalOptions.topdir, scanDL_input), "w") as fh:
                for slot in data.keys():
                    if not data[slot]['SN'] or not data[slot]['MAC']:
                        # skip empty slot
                        continue

                    fh.write(f'{slot}\n')
                    fh.write(data[slot]['SN'] + "\n")
                    fh.write(data[slot]['MAC'] + "\n")
                    if data[slot]['PN']:
                        fh.write(data[slot]['PN'] + "\n")
                fh.write(f'STOP\n')
        except Exception as e:
            Logger.error("Failed to write {:s}".format(scanDL_input))
            return defs.Result.INFRA_FAILURE

        return defs.Result.SUCCESS

    def __gen_mtp_sw_pn(self, testbed_json):
        Logger.info(f"Loading {testbed_json} to generate SW PN scanning input")
        try:
            with open(testbed_json, 'r') as fh:
                testbed_spec = json.load(fh)
        except Exception as e:
            Logger.error(f"Failed to load {testbed_json} - Exception: {e}")
            return defs.Result.INFRA_FAILURE

        instances = testbed_spec.get('Instances', None)
        if instances == None or len(instances) == 0:
            return defs.Result.INFRA_FAILURE

        mtp_instance = instances[0]
        mtp_resource = mtp_instance.get('Resource', None)

        if mtp_resource == None:
            return defs.Result.INFRA_FAILURE

        # data = dict()
        # for slot in slot_range:
        #     nic_slot = "NIC-{:02d}".format(slot)
        #     data[nic_slot] = {
        #         'SN': mtp_resource.get("nic{:d}-serial-number".format(slot)),
        #         'MAC': mtp_resource.get("nic{:d}-mac-address".format(slot)),
        #         'PN': mtp_resource.get("nic{:d}-part-number".format(slot))
        #     }

        # write to a file with all SW PNs in one line
        swi_input = "swi_input"
        testbed_id = testbed_spec.get('ID').split("-")[1]
        testbed_id = f"{self.__testsuite.config.testbed}-{testbed_id}"
        Logger.info(f"Generating {testbed_id} SW PN in input file: {swi_input}")

        sw_pn_test_args = ""
        for swpn_idx in range(1,11):
            if mtp_resource.get("nic{:d}-sw-pn".format(swpn_idx)):
                sw_pn_test_args += mtp_resource.get("nic{:d}-sw-pn".format(swpn_idx)) + " "
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

        ret = self.__gen_mtp_inventory(GlobalOptions.testbed_json)

        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract mtp-inventory from {GlobalOptions.testbed_json} - ABORT")
            return ret

        ret = self.__gen_nic_barcodes(GlobalOptions.testbed_json)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract NIC SN, MAC, PN from {GlobalOptions.testbed_json} - ABORT")
            return ret

        ret = self.__gen_mtp_sw_pn(GlobalOptions.testbed_json)
        if ret != defs.Result.SUCCESS:
            Logger.error(f"Failed to extract SW PNs from {GlobalOptions.testbed_json} - ABORT")
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
