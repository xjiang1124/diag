import libmfg_utils

class mtp_db(): 
    def __init__(self, mtp_cfg_file_list):
        # terminal server info
        self._ts_type = dict()
        self._ts = dict()
        self._ts_port = dict()
        self._ts_userid = dict()
        self._ts_passwd = dict()
        # usb terminal server info
        self._usb_ts_type = dict()
        self._usb_ts = dict()
        self._usb_ts_port = dict()
        self._usb_ts_userid = dict()
        self._usb_ts_passwd = dict()
        # pdu info
        self._pdu1_type = dict()
        self._pdu1 = dict()
        self._pdu1_port = dict()
        self._pdu1_userid = dict()
        self._pdu1_passwd = dict()
        self._pdu2_type = dict()
        self._pdu2 = dict()
        self._pdu2_port = dict()
        self._pdu2_userid = dict()
        self._pdu2_passwd = dict()
        # mtp info
        self._type = dict()
        self._ip = dict()
        self._userid = dict()
        self._passwd = dict()
        self._capability = dict()
        self._max_slots = dict()
        self._slots_to_skip = dict()
        self._mtpid_list = list()

        mtp_cfg = libmfg_utils.load_cfg_from_yaml_file_list(mtp_cfg_file_list)

        for mtpid in mtp_cfg.keys():
            if mtpid in self._mtpid_list:
                libmfg_utils.sys_exit("Duplicate mtpid: " + mtpid + " detected!")

            self._ts_type[mtpid] = ""
            self._ts[mtpid] = mtp_cfg[mtpid]["TS"]
            self._ts_port[mtpid] = mtp_cfg[mtpid]["TS_PORT"]
            self._ts_userid[mtpid] = mtp_cfg[mtpid]["TS_USERID"]
            self._ts_passwd[mtpid] = mtp_cfg[mtpid]["TS_PASSWORD"]

            if "USB_TS" in mtp_cfg[mtpid].keys():
                self._usb_ts_type[mtpid] = ""
                self._usb_ts[mtpid] = mtp_cfg[mtpid]["USB_TS"]
                self._usb_ts_port[mtpid] = mtp_cfg[mtpid]["USB_TS_PORT"]
                self._usb_ts_userid[mtpid] = mtp_cfg[mtpid]["USB_TS_USERID"]
                self._usb_ts_passwd[mtpid] = mtp_cfg[mtpid]["USB_TS_PASSWORD"]

            if "APC1" in mtp_cfg[mtpid].keys():
                self._pdu1[mtpid] = mtp_cfg[mtpid]["APC1"]
                self._pdu1_port[mtpid] = mtp_cfg[mtpid]["APC1_PORT"]
                self._pdu1_userid[mtpid] = mtp_cfg[mtpid]["APC1_USERID"]
                self._pdu1_passwd[mtpid] = mtp_cfg[mtpid]["APC1_PASSWORD"]

            if "PDU1" in mtp_cfg[mtpid].keys():
                self._pdu1[mtpid] = mtp_cfg[mtpid]["PDU1"]
                self._pdu1_port[mtpid] = mtp_cfg[mtpid]["PDU1_PORT"]
                self._pdu1_userid[mtpid] = mtp_cfg[mtpid]["PDU1_USERID"]
                self._pdu1_passwd[mtpid] = mtp_cfg[mtpid]["PDU1_PASSWORD"]

            if "APC2" in mtp_cfg[mtpid].keys():
                self._pdu2[mtpid] = mtp_cfg[mtpid]["APC2"]
                self._pdu2_port[mtpid] = mtp_cfg[mtpid]["APC2_PORT"]
                self._pdu2_userid[mtpid] = mtp_cfg[mtpid]["APC2_USERID"]
                self._pdu2_passwd[mtpid] = mtp_cfg[mtpid]["APC2_PASSWORD"]

            if "PDU2" in mtp_cfg[mtpid].keys():
                self._pdu1[mtpid] = mtp_cfg[mtpid]["PDU2"]
                self._pdu1_port[mtpid] = mtp_cfg[mtpid]["PDU2_PORT"]
                self._pdu1_userid[mtpid] = mtp_cfg[mtpid]["PDU2_USERID"]
                self._pdu1_passwd[mtpid] = mtp_cfg[mtpid]["PDU2_PASSWORD"]

            self._ip[mtpid] = mtp_cfg[mtpid]["IP"]
            self._userid[mtpid] = mtp_cfg[mtpid]["USERID"]
            self._passwd[mtpid] = mtp_cfg[mtpid]["PASSWORD"]

            if "SLOTS" in mtp_cfg[mtpid].keys():
                self._max_slots[mtpid] = mtp_cfg[mtpid]["SLOTS"]
            else:
                self._max_slots[mtpid] = 10

            self._slots_to_skip[mtpid] = [False]*self._max_slots[mtpid] #True=skip, False=dont skip
            if "SKIP_SLOTS" in mtp_cfg[mtpid].keys(): # for backward compatability with configs without SKIP_SLOTS field
                for slot in libmfg_utils.expand_range_of_numbers(mtp_cfg[mtpid]["SKIP_SLOTS"], range_min=1, range_max=self._max_slots[mtpid], dev=mtpid):
                    self._slots_to_skip[mtpid][slot-1] = True

            if "CAPABILITY" in mtp_cfg[mtpid].keys():
                self._capability[mtpid] = mtp_cfg[mtpid]["CAPABILITY"]

            self._mtpid_list.append(mtpid)


    def get_mtpid_list(self):
        return self._mtpid_list;


    def mtpid_valid(self, mtpid):
        if mtpid in self._mtpid_list:
            return True
        else:
            return False


    def get_mtp_console(self, mtpid):
        ts_cfg = list()
        if not self.mtpid_valid(mtpid):
            libmfg_utils.sys_exit("Invalid mtpid: " + mtpid)

        ts_cfg.append(self._ts[mtpid])
        ts_cfg.append(self._ts_port[mtpid])
        ts_cfg.append(self._ts_userid[mtpid])
        ts_cfg.append(self._ts_passwd[mtpid])
        ts_cfg.append(self._ts_type[mtpid])

        return ts_cfg


    def get_mtp_usb_console(self, mtpid):
        ts_cfg = list()
        if not self.mtpid_valid(mtpid):
            libmfg_utils.sys_exit("Invalid mtpid: " + mtpid)

        if mtpid not in self._usb_ts.keys():
            return list()

        ts_cfg.append(self._usb_ts[mtpid])
        ts_cfg.append(self._usb_ts_port[mtpid])
        ts_cfg.append(self._usb_ts_userid[mtpid])
        ts_cfg.append(self._usb_ts_passwd[mtpid])
        ts_cfg.append(self._usb_ts_type[mtpid])

        return ts_cfg


    def get_mtp_pdu(self, mtpid):
        pdu_cfg = list()
        if not self.mtpid_valid(mtpid):
            libmfg_utils.sys_exit("Invalid mtpid: " + mtpid)

        pdu_cfg.append(self._pdu1[mtpid])
        pdu_cfg.append(self._pdu1_port[mtpid])
        pdu_cfg.append(self._pdu1_userid[mtpid])
        pdu_cfg.append(self._pdu1_passwd[mtpid])

        pdu_cfg.append(self._pdu2[mtpid])
        pdu_cfg.append(self._pdu2_port[mtpid])
        pdu_cfg.append(self._pdu2_userid[mtpid])
        pdu_cfg.append(self._pdu2_passwd[mtpid])

        return pdu_cfg


    def get_mtp_mgmt(self, mtpid):
        mgmt_cfg = list()
        if not self.mtpid_valid(mtpid):
            libmfg_utils.sys_exit("Invalid mtpid: " + mtpid)

        mgmt_cfg.append(self._ip[mtpid])
        mgmt_cfg.append(self._userid[mtpid])
        mgmt_cfg.append(self._passwd[mtpid])

        return mgmt_cfg

    def get_mtp_capability(self, mtpid):
        if not self.mtpid_valid(mtpid):
            libmfg_utils.sys_exit("Invalid mtpid: " + mtpid)

        return self._capability[mtpid]

    def get_mtp_slots_to_skip(self, mtpid):
        if not self.mtpid_valid(mtpid):
            libmfg_utils.sys_exit("Invalid mtpid: " + mtpid)

        return self._slots_to_skip[mtpid]
