#!/usr/bin/env python2

import libmfg_utils
import requests

# ------------------------------------------------------------------------------

class MES():

    def __init__(self):
        '''
        MES constructor
        '''

        self.mgmt_ctrl = ''
        self.next_test_station = ''
        self.do_push_to_mes = True

        self.mes_uut_info = dict()

        self.mes_ip_addr = "10.118.20.4"
        self.mes_port = ":8080"
        self.mes_url_pfx = \
            "http://" + self.mes_ip_addr + self.mes_port + "/MesAPI/mesapi/"

        self.pull_uut_info_api = "GetWWNInformation"
        self.pull_uut_edc_api = "GetKPInformation"
        self.pull_next_test_station_api = "GetNextStation"
        self.push_results_api = "Upload_R_TEST_HPE"

        self.results_for_mes = {
            'Chassis_Base_SN' : 'N/A',
            'Test_Station' : 'N/A',
            'Test_Status' : 'FAIL',
            'START_TIME' : 'N/A',
            'END_TIME' : 'N/A',
            'OPERATOR_ID' : 'N/A',
            'Passmark_Timestamp' : 'N/A',
            'Test_Fail_Mode' : 'N/A',
            'Test_Fail_Signature' : 'N/A',
            'Test_Rack' : 'N/A',
            'SW_Version' : 'N/A',
        }

        self.upload_r_test_hpe_headers = {
            'Content-type' : 'application/json',
            'Accept' : 'json'
        }

    # --------------------------------------------------------------------------

    def get_res_chassis_sn(self):
        return self.results_for_mes['Chassis_Base_SN']
    def get_res_test_station(self):
        return self.results_for_mes['Test_Station']
    def get_res_test_status(self):
        return self.results_for_mes['Test_Status']
    def get_res_test_start_timestamp(self):
        return self.results_for_mes['START_TIME']
    def get_res_test_end_timestamp(self):
        return self.results_for_mes['END_TIME']
    def get_res_operator_id(self):
        return self.results_for_mes['OPERATOR_ID']
    def get_res_passmark(self):
        return self.results_for_mes['Passmark_Timestamp']
    def get_res_fail_mode(self):
        return self.results_for_mes['Test_Fail_Mode']
    def get_res_fail_signature(self):
        return self.results_for_mes['Test_Fail_Signature']
    def get_res_test_location(self):
        return self.results_for_mes['Test_Rack']
    def get_res_cxos_version(self):
        return self.results_for_mes['SW_Version']

    # --------------------------------------------------------------------------

    def save_res_chassis_sn(self, chassis_sn):
        self.results_for_mes['Chassis_Base_SN'] = chassis_sn
    def save_res_test_station(self, test_station):
        self.results_for_mes['Test_Station'] = test_station
    def save_res_test_status(self, test_status):
        self.results_for_mes['Test_Status'] = test_status
    def save_res_test_start_timestamp(self, test_start_ts):
        self.results_for_mes['START_TIME'] = str(test_start_ts)
    def save_res_test_end_timestamp(self, test_end_ts):
        self.results_for_mes['END_TIME'] = str(test_end_ts)
    def save_res_operator_id(self, operator_id):
        self.results_for_mes['OPERATOR_ID'] = operator_id
    def save_res_passmark(self, passmark):
        self.results_for_mes['Passmark_Timestamp'] = passmark
    def save_res_fail_mode(self, fail_mode):
        self.results_for_mes['Test_Fail_Mode'] = fail_mode
    def save_res_fail_signature(self, fail_signature):
        self.results_for_mes['Test_Fail_Signature'] = fail_signature
    def save_res_test_location(self, test_location):
        self.results_for_mes['Test_Rack'] = test_location
    def save_res_cxos_version(self, cxos_version):
        self.results_for_mes['SW_Version'] = cxos_version

    # --------------------------------------------------------------------------

    def store_mgmt_ctrl(self, mgmt_ctrl):
        self.mgmt_ctrl = mgmt_ctrl

    def save_mes_next_test_station(self, next_test_station):
        self.next_test_station = next_test_station
    def clear_push_to_mes(self):
        self.do_push_to_mes = False
    def save_mes_uut_cssn(self, cssn):
        # CSSN - Shipping-level SN
        self.mes_uut_info['CSSN'] = cssn
    def save_mes_uut_vssn(self, vssn):
        # VSSN - Chassis Base SN
        self.mes_uut_info['VSSN'] = vssn
    def save_mes_uut_wsn(self, wsn):
        # WSN - PCBA SN
        self.mes_uut_info['WSN'] = wsn
    def save_mes_uut_mac(self, mac):
        self.mes_uut_info['MAC'] = mac
    def save_mes_uut_edc(self, edc):
        self.mes_uut_info['EDC'] = edc
    def save_mes_uut_csku(self, csku):
        self.mes_uut_info['CSKU'] = csku

    # --------------------------------------------------------------------------

    def get_mgmt_ctrl(self):
        return self.mgmt_ctrl
    def get_push_to_mes(self):
        return self.do_push_to_mes
    def get_mes_ip(self):
        return self.mes_ip_addr
    def get_mes_url_pfx(self):
        return self.mes_url_pfx

    def get_uut_info_api(self):
        return self.pull_uut_info_api
    def get_uut_edc_api(self):
        return self.pull_uut_edc_api
    def get_next_test_station_api(self):
        return self.pull_next_test_station_api
    def get_upload_results_api(self):
        return self.push_results_api

    def get_mes_uut_info_url(self):
        return self.get_mes_url_pfx() + self.get_uut_info_api()
    def get_mes_uut_edc_url(self):
        return self.get_mes_url_pfx() + self.get_uut_edc_api()
    def get_mes_next_test_station_url(self):
        return self.get_mes_url_pfx() + self.get_next_test_station_api()
    def get_mes_upload_results_url(self):
        return self.get_mes_url_pfx() + self.get_upload_results_api()
    def get_upload_test_headers(self):
        return self.upload_r_test_hpe_headers

    def get_mes_next_test_station(self):
        return self.next_test_station
    def get_mes_uut_cssn(self):
        # CSSN - Shipping-level SN
        return self.mes_uut_info['CSSN']
    def get_mes_uut_vssn(self):
        # VSSN - Chassis Base SN
        return self.mes_uut_info['VSSN']
    def get_mes_uut_wsn(self):
        # WSN - PCBA SN
        return self.mes_uut_info['WSN']
    def get_mes_uut_mac(self):
        return self.mes_uut_info['MAC']
    def get_mes_uut_edc(self):
        return self.mes_uut_info['EDC']
    def get_mes_uut_csku(self):
        return self.mes_uut_info['CSKU']

    # --------------------------------------------------------------------------

    def pull_mes_info(self, chassis_sn):

        error = False
        if not self.pull_uut_info_from_mes(chassis_sn):
            error = True
        if not self.pull_uut_edc_from_mes(chassis_sn):
            error = True
        try:
            cssn = self.get_mes_uut_cssn()
            if not self.pull_next_test_station_from_mes(cssn):
                error = True
        except:
            error = True

        if error:
            return False
        else:
            return True

    # --------------------------------------------------------------------------

    def pull_next_test_station_from_mes(self, chassis_sn):

        # Access the MES API
        try:
            info = requests.get(self.get_mes_next_test_station_url(),
                params={"SN": chassis_sn}, timeout=10)
        except:
            self.get_mgmt_ctrl().cli_log_err("Failed to access the MES system")
            return False

        # Verify MES API response
        if not self._verify_mes_api_response(
            info, self.get_next_test_station_api(), chassis_sn):
            return False

        if not unicode(u'NEXT_STATION') in info.json()[u'ResData'][0].keys():
            self.get_mgmt_ctrl().cli_log_err(
                "Failed to pull UUT's next test station info from MES API: " + \
                self.get_next_test_station_api())
            return False

        self.save_mes_next_test_station(
            str(info.json()[u'ResData'][0][unicode('NEXT_STATION')]))

        return True

    # --------------------------------------------------------------------------

    def pull_uut_info_from_mes(self, chassis_sn):

        error = False

        # Access the MES API
        try:
            info = requests.get(self.get_mes_uut_info_url(),
                params={"SN": chassis_sn}, timeout=10)
        except:
            self.get_mgmt_ctrl().cli_log_err("Failed to access the MES system")
            return False

        # Verify MES API response
        if not self._verify_mes_api_response(info, self.get_uut_info_api(), chassis_sn):
            self.get_mgmt_ctrl().cli_log_inf("Test data will NOT be pushed to MES")
            self.clear_push_to_mes()
            return False

        # Save the Shipping-level SN (CSSN) from MES
        if unicode('CSSN') in info.json()[u'ResData'][0].keys():
            self.save_mes_uut_cssn(str(info.json()[u'ResData'][0][unicode('CSSN')]))
        else:
            error = True
            self.get_mgmt_ctrl().cli_log_err(
                "Failed to pull Chassis Base SN info from MES API: " + \
                self.get_uut_info_api())

        # Save the Chassis Base SN (VSSN) from MES
        if unicode('VSSN') in info.json()[u'ResData'][0].keys():
            self.save_mes_uut_vssn(str(info.json()[u'ResData'][0][unicode('VSSN')]))
        else:
            error = True
            self.get_mgmt_ctrl().cli_log_err(
                "Failed to pull Scanned SN info from MES API: " + \
                self.get_uut_info_api())

        # Save the PCBA SN (WSN) from MES
        if unicode('WSN') in info.json()[u'ResData'][0].keys():
            self.save_mes_uut_wsn(str(info.json()[u'ResData'][0][unicode('WSN')]))
        else:
            error = True
            self.get_mgmt_ctrl().cli_log_err(
                "Failed to pull PCBA SN info from MES API: " + \
                self.get_uut_info_api())

        # Save the MAC from MES
        if unicode('MAC') in info.json()[u'ResData'][0].keys():
            self.save_mes_uut_mac(str(info.json()[u'ResData'][0][unicode('MAC')]))
        else:
            error = True
            self.get_mgmt_ctrl().cli_log_err(
                "Failed to pull MAC info from MES API: " + \
                self.get_uut_info_api())

        if error:
            return False
        else:
            return True

    # --------------------------------------------------------------------------

    def pull_uut_edc_from_mes(self, chassis_sn):

        error = False

        # Access the MES API
        try:
            scan_type = "EDC"
            info = requests.post(self.get_mes_uut_edc_url(),
                params={"SN": chassis_sn, "SCANTYPE": scan_type}, timeout=10)
        except:
            self.get_mgmt_ctrl().cli_log_err("Failed to access the MES system")
            return False

        # Verify MES API response
        if not self._verify_mes_api_response(info, self.get_uut_edc_api(), chassis_sn):
            return False

        # Save the EDC from MES
        if unicode('VALUE') in info.json()[u'ResData'][0].keys():
            self.save_mes_uut_edc(str(info.json()[u'ResData'][0][unicode('VALUE')]))
        else:
            error = True
            self.get_mgmt_ctrl().cli_log_err(
                "Failed to pull EDC from MES API: " + \
                self.get_uut_edc_api())

        if error:
            return False
        else:
            return True

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------

    def verify_next_test_station(self, test_station):
        return test_station == self.get_mes_next_test_station()

    # --------------------------------------------------------------------------

    def verify_scanned_input_against_mes(self, scanned_input):

        error = False

        # Verify scanned Chassis Base SN against MES data (VSSN)
        if not "UUT_SN" in scanned_input.keys():
            self.get_mgmt_ctrl().cli_log_err("Failed to capture scanned Chassis Base SN info")
            error = True
        else:
            self.get_mgmt_ctrl().cli_log_inf(
                "Serial Number scanned: " + scanned_input["UUT_SN"], level=0)

            if scanned_input["UUT_SN"] != self.get_mes_uut_vssn():
                error = True
                self.get_mgmt_ctrl().cli_log_err(
                    "Chassis Base SN mismatch detected between scanned and MES data")
                self.get_mgmt_ctrl().cli_log_err("Scanned data : " + scanned_input["UUT_SN"])
                self.get_mgmt_ctrl().cli_log_err("From MES     : " + self.get_mes_uut_vssn())
                self.get_mgmt_ctrl().cli_log_inf("Test data will NOT be pushed to MES")
                self.clear_push_to_mes()
            else:
                self.get_mgmt_ctrl().cli_log_inf(
                    "Scanned Chassis Base SN matches MES record", level=0)


        # Verify scanned EDC against MES data (EDC)
        if not "UUT_EDC" in scanned_input.keys():
            self.get_mgmt_ctrl().cli_log_err("Failed to capture scanned EDC info")
            error = True
        else:
            self.get_mgmt_ctrl().cli_log_inf(
                "EDC scanned: " + scanned_input["UUT_EDC"], level=0)

            if scanned_input["UUT_EDC"] != self.get_mes_uut_edc():
                error = True
                self.get_mgmt_ctrl().cli_log_err(
                    "EDC mismatch detected between scanned and MES data")
                self.get_mgmt_ctrl().cli_log_err("Scanned data : " + scanned_input["UUT_EDC"])
                self.get_mgmt_ctrl().cli_log_err("From MES     : " + self.get_mes_uut_edc())
            else:
                self.get_mgmt_ctrl().cli_log_inf("Scanned EDC matches MES record", level=0)


        # Verify scanned MAC against MES data (MAC)
        if not "UUT_MAC" in scanned_input.keys():
            self.get_mgmt_ctrl().cli_log_err("Failed to capture scanned MAC info")
            error = True
        else:
            self.get_mgmt_ctrl().cli_log_inf(
                "MAC scanned: " + scanned_input["UUT_MAC"], level=0)

            if scanned_input["UUT_MAC"] != self.get_mes_uut_mac():
                error = True
                self.get_mgmt_ctrl().cli_log_err(
                    "MAC mismatch detected between scanned and MES data")
                self.get_mgmt_ctrl().cli_log_err("Scanned data : " + scanned_input["UUT_MAC"])
                self.get_mgmt_ctrl().cli_log_err("From MES     : " + self.get_mes_uut_mac())
            else:
                self.get_mgmt_ctrl().cli_log_inf("Scanned MAC matches MES record", level=0)

        if error:
            return False
        else:
            return True

    # --------------------------------------------------------------------------

    def verify_eeprom_against_mes(self, eeprom_contents, eeprom_type='fru'):

        error = False

        mes_data = {
            'Serial Number' : self.get_mes_uut_vssn(),
            'TPM Serial Number' : self.get_mes_uut_wsn(),
            'Base MAC Address' : self.get_mes_uut_mac(),

            'assy_rev_edc' : self.get_mes_uut_edc(),
            'serial_nr' : self.get_mes_uut_vssn(),

            'pca_serial_num' : self.get_mes_uut_wsn(),
            'pca_edc' : self.get_mes_uut_edc(),
        }

        if eeprom_type == 'mfg_l':
            label = 'Locked MFG'
            field_list = ['assy_rev_edc', 'serial_nr']
        elif eeprom_type == 'mfg_ul':
            label = 'Unlocked MFG'
            field_list = ['pca_serial_num', 'pca_edc']
        else:
            label = 'FRU'
            field_list = ['Serial Number', 'TPM Serial Number', 'Base MAC Address']

        for field in field_list:
            if field not in eeprom_contents.keys():
                error = True
                self.get_mgmt_ctrl().cli_log_err(
                    label + " EEPROM field " + field + " is not captured")
                continue
            value = eeprom_contents[field].replace(":", "").replace("\x00", "")
            if value != mes_data[field]:
                self.get_mgmt_ctrl().cli_log_err(
                    "Detected " + field + " mismatch between " + label + \
                    " EEPROM and MES record")
                self.get_mgmt_ctrl().cli_log_err("EEPROM data : " + value)
                self.get_mgmt_ctrl().cli_log_err("From MES    : " + mes_data[field])
                error = True
            else:
                self.get_mgmt_ctrl().cli_log_inf(
                    label + " EEPROM " + field + " = " + value + " is OK", level=0)

        if error:
            return False
        else:
            self.get_mgmt_ctrl().cli_log_inf(
                label + " EEPROM is verified against MES data", level=0)
            return True

    # --------------------------------------------------------------------------

    def push_results_to_mes(self):

        if not self.get_push_to_mes():
            self.get_mgmt_ctrl().cli_log_inf("Skip data push to MES")
            return

        vssn = self.get_res_chassis_sn()
        test_station = self.get_res_test_station()
        test_status = self.get_res_test_status()
        start_time = self.get_res_test_start_timestamp()
        end_time = self.get_res_test_end_timestamp()
        operator_id = self.get_res_operator_id()
        passmark_timestamp = self.get_res_passmark()
        fail_mode = self.get_res_fail_mode()
        fail_signature = self.get_res_fail_signature()
        test_rack = self.get_res_test_location()
        cxos_version = self.get_res_cxos_version()

        self.get_mgmt_ctrl().cli_log_inf("The following data will be pushed to MES:")
        self.get_mgmt_ctrl().cli_log_inf("VSSN       : " + vssn)
        self.get_mgmt_ctrl().cli_log_inf("Test Stn   : " + test_station)
        self.get_mgmt_ctrl().cli_log_inf("Test Stat  : " + test_status)
        self.get_mgmt_ctrl().cli_log_inf("Test Start : " + start_time)
        self.get_mgmt_ctrl().cli_log_inf("Test End   : " + end_time)
        self.get_mgmt_ctrl().cli_log_inf("Op ID      : " + operator_id)
        self.get_mgmt_ctrl().cli_log_inf("Passmark   : " + passmark_timestamp)
        self.get_mgmt_ctrl().cli_log_inf("Fail Mode  : " + fail_mode)
        self.get_mgmt_ctrl().cli_log_inf("Fail Sig   : " + fail_signature)
        self.get_mgmt_ctrl().cli_log_inf("Test Loc   : " + test_rack)
        self.get_mgmt_ctrl().cli_log_inf("Ship OS ver: " + cxos_version)

        post_json = {
            "Chassis_Base_SN": vssn,
            "Test_Station": test_station,
            "Test_Status": test_status,
            "START_TIME": start_time,
            "END_TIME": end_time,
            "OPERATER_ID": operator_id,
            "Passmark_Timestamp": passmark_timestamp,
            "Test_Fail_Mode": fail_mode,
            "Test_Fail_Signature": fail_signature,
            "Test_Rack": test_rack,
            "SW_Version": cxos_version,
        }

        info = requests.post(
            self.get_mes_upload_results_url(),
            json=post_json,
            headers=self.get_upload_test_headers())

        if unicode(u'Status') not in info.json().keys() or \
            unicode(u'ErrorMessage') not in info.json().keys() or \
            unicode(u'ResData') not in info.json().keys():
            self.get_mgmt_ctrl().cli_log_err(
                "Unable to push info to MES API: " + api)
        else:
            if info.json()['Status'] == 0:
                self.get_mgmt_ctrl().cli_log_inf("Info is pushed to MES")
                self.get_mgmt_ctrl().cli_log_inf(
                    "Result Data: " + str(info.json()['ResData'][0]))
            else:
                self.get_mgmt_ctrl().cli_log_err("Failed to push info to MES")
                self.get_mgmt_ctrl().cli_log_err(
                    "ErrorMessage: " + str(info.json()['ErrorMessage']))

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------

    def _verify_mes_api_response(self, info, api_name, chassis_sn):

        # Verify that the API response data structure is valid
        if unicode('Status') not in info.json().keys() or \
            unicode('ErrorMessage') not in info.json().keys() or \
            unicode('ResData') not in info.json().keys():
            self.get_mgmt_ctrl().cli_log_err(
                "Unable to pull info from MES API: " + api_name)
            return False

        # Verify the API response status
        if info.json()[u'Status'] != 0:
            error_msg = str(info.json()[u'ErrorMessage'])
            self.get_mgmt_ctrl().cli_log_err(chassis_sn + " : " + error_msg)
            return False

        return True

################################################################################
# MAIN
################################################################################

if __name__ == "__main__":
    print("This is a user-defined libmes python2 library!")

