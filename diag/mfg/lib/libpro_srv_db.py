import libmfg_utils

class pro_srv_db(): 
    def __init__(self, pro_srv_cfg_file):
        # access info
        self._ip = dict()
        self._userid = dict()
        self._passwd = dict()
        self._mtp_chassis_cfg_file = dict()
        self._logpath = dict() 
        self._pro_srv_list = list()

        pro_srv_cfg = libmfg_utils.load_cfg_from_yaml(pro_srv_cfg_file)

        for pro_srv_id in pro_srv_cfg.keys():
            if pro_srv_id in self._pro_srv_list:
                libmfg_utils.sys_exit("Duplicate product server id: " + pro_srv_id + " detected in " + pro_srv_cfg_file)

            self._ip[pro_srv_id] = pro_srv_cfg[pro_srv_id]["IP"]
            self._userid[pro_srv_id] = pro_srv_cfg[pro_srv_id]["USERID"]
            self._passwd[pro_srv_id] = pro_srv_cfg[pro_srv_id]["PASSWORD"]
            self._mtp_chassis_cfg_file[pro_srv_id] = pro_srv_cfg[pro_srv_id]["MTP_CFG_FILE"]
            self._logpath[pro_srv_id] = pro_srv_cfg[pro_srv_id]["LOGPATH"]

            self._pro_srv_list.append(pro_srv_id)


    def get_pro_srv_id_list(self):
        return self._pro_srv_list;


    def pro_srv_id_valid(self, pro_srv_id):
        if pro_srv_id in self._pro_srv_list:
            return True
        else:
            return False


    def get_pro_srv_mgmt(self, pro_srv_id):
        mgmt_cfg = list()
        if not self.pro_srv_id_valid(pro_srv_id):
            libmfg_utils.sys_exit("Invalid product server id: " + pro_srv_id)

        mgmt_cfg.append(self._ip[pro_srv_id])
        mgmt_cfg.append(self._userid[pro_srv_id])
        mgmt_cfg.append(self._passwd[pro_srv_id])

        return mgmt_cfg


    def get_pro_srv_logpath(self, pro_srv_id):
        if not self.pro_srv_id_valid(pro_srv_id):
            libmfg_utils.sys_exit("Invalid product server id: " + pro_srv_id)

        return self._logpath[pro_srv_id]


    def get_pro_srv_barcode_cfgpath(self, pro_srv_id, card_type):
        return self.get_pro_srv_logpath(pro_srv_id) + "/".join([card_type, "DL", "barcode_cfg"]) + "/"


    def get_pro_srv_dl_logpath(self, pro_srv_id, card_type):
        return self.get_pro_srv_logpath(pro_srv_id) + "/".join([card_type, "DL"]) + "/"


    def get_pro_srv_p2c_logpath(self, pro_srv_id, card_type):
        return self.get_pro_srv_logpath(pro_srv_id) + "/".join([card_type, "P2C"]) + "/"


    def get_pro_srv_htlv_logpath(self, pro_srv_id, card_type):
        return self.get_pro_srv_logpath(pro_srv_id) + "/".join([card_type, "4C", "HTLV"]) + "/"


    def get_pro_srv_lthv_logpath(self, pro_srv_id, card_type):
        return self.get_pro_srv_logpath(pro_srv_id) + "/".join([card_type, "4C", "LTHV"]) + "/"


    def get_pro_srv_mtp_chassis_cfg_file(self, pro_srv_id):
        if not self.pro_srv_id_valid(pro_srv_id):
            libmfg_utils.sys_exit("Invalid product server id: " + pro_srv_id)

        return self._mtp_chassis_cfg_file[pro_srv_id]
