import liblog_utils

class pro_srv_db(): 
    def __init__(self, pro_srv_cfg_file):
        # access info
        self._ip = dict()
        self._userid = dict()
        self._passwd = dict()
        self._logpath = dict() 
        self._pro_srv_list = list()

        pro_srv_cfg = liblog_utils.load_cfg_from_yaml(pro_srv_cfg_file)

        for pro_srv_id in pro_srv_cfg.keys():
            if pro_srv_id in self._pro_srv_list:
                liblog_utils.sys_exit("Duplicate product server id: " + pro_srv_id + " detected in " + pro_srv_cfg_file)

            self._ip[pro_srv_id] = pro_srv_cfg[pro_srv_id]["IP"]
            self._userid[pro_srv_id] = pro_srv_cfg[pro_srv_id]["USERID"]
            self._passwd[pro_srv_id] = pro_srv_cfg[pro_srv_id]["PASSWORD"]
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
            liblog_utils.sys_exit("Invalid product server id: " + pro_srv_id)

        mgmt_cfg.append(self._ip[pro_srv_id])
        mgmt_cfg.append(self._userid[pro_srv_id])
        mgmt_cfg.append(self._passwd[pro_srv_id])

        return mgmt_cfg


    def get_pro_srv_logpath(self, pro_srv_id):
        if not self.pro_srv_id_valid(pro_srv_id):
            liblog_utils.sys_exit("Invalid product server id: " + pro_srv_id)

        return self._logpath[pro_srv_id]
