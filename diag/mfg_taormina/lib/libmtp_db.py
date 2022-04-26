import libmfg_utils

class mtp_db(): 
    def __init__(self, mtp_cfg_file_list):
        # terminal server info
        self._ts_type = dict()
        self._ts = dict()
        self._ts_port = dict()
        self._ts_userid = dict()
        self._ts_passwd = dict()
        # apc info
        self._apc1_type = dict()
        self._apc1 = dict()
        self._apc1_port = dict()
        self._apc1_userid = dict()
        self._apc1_passwd = dict()
        self._apc2_type = dict()
        self._apc2 = dict()
        self._apc2_port = dict()
        self._apc2_userid = dict()
        self._apc2_passwd = dict()
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
            
            self._apc1[mtpid] = mtp_cfg[mtpid]["APC1"]
            self._apc1_port[mtpid] = mtp_cfg[mtpid]["APC1_PORT"]
            self._apc1_userid[mtpid] = mtp_cfg[mtpid]["APC1_USERID"]
            self._apc1_passwd[mtpid] = mtp_cfg[mtpid]["APC1_PASSWORD"]

            self._apc2[mtpid] = mtp_cfg[mtpid]["APC2"]
            self._apc2_port[mtpid] = mtp_cfg[mtpid]["APC2_PORT"]
            self._apc2_userid[mtpid] = mtp_cfg[mtpid]["APC2_USERID"]
            self._apc2_passwd[mtpid] = mtp_cfg[mtpid]["APC2_PASSWORD"]

            self._ip[mtpid] = mtp_cfg[mtpid]["IP"]
            self._userid[mtpid] = mtp_cfg[mtpid]["USERID"]
            self._passwd[mtpid] = mtp_cfg[mtpid]["PASSWORD"]

            self._max_slots[mtpid] = mtp_cfg[mtpid]["SLOTS"]
            self._slots_to_skip[mtpid] = [False]*self._max_slots[mtpid] #True=skip, False=dont skip
            if "SKIP_SLOTS" in mtp_cfg[mtpid].keys(): # for backward compatability with configs without SKIP_SLOTS field
                for slot in libmfg_utils.expand_range_of_numbers(mtp_cfg[mtpid]["SKIP_SLOTS"], range_min=1, range_max=self._max_slots[mtpid], dev=mtpid):
                    self._slots_to_skip[mtpid][slot-1] = True
            if isinstance(mtp_cfg[mtpid]["CAPABILITY"], str):
                self._capability[mtpid] = int(mtp_cfg[mtpid]["CAPABILITY"], 16)
            else:
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

        ts_cfg.append(self._ts_type[mtpid])
        ts_cfg.append(self._ts[mtpid])
        ts_cfg.append(self._ts_port[mtpid])
        ts_cfg.append(self._ts_userid[mtpid])
        ts_cfg.append(self._ts_passwd[mtpid])

        return ts_cfg


    def get_mtp_apc(self, mtpid):
        apc_cfg = list()
        if not self.mtpid_valid(mtpid):
            libmfg_utils.sys_exit("Invalid mtpid: " + mtpid)

        apc_cfg.append(self._apc1[mtpid])
        apc_cfg.append(self._apc1_port[mtpid])
        apc_cfg.append(self._apc1_userid[mtpid])
        apc_cfg.append(self._apc1_passwd[mtpid])

        apc_cfg.append(self._apc2[mtpid])
        apc_cfg.append(self._apc2_port[mtpid])
        apc_cfg.append(self._apc2_userid[mtpid])
        apc_cfg.append(self._apc2_passwd[mtpid])

        return apc_cfg


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
