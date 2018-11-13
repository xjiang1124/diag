import libmfg_utils

class diag_db(): 
    def __init__(self, diag_cfg_file):
        diag_test_cfg = libmfg_utils.load_cfg_from_yaml(diag_cfg_file)
        self._init_cmd_list = list()
        self._skip_test_list = list()
        self._test_param_list = list()
        self._seq_test_id_list = list()
        self._para_test_id_list = list()
        self._seq_tests = dict()
        self._para_tests = dict()

        # build init command list
        cmd_list = diag_test_cfg["INIT"]
        for cmd in cmd_list:
            self._init_cmd_list.append(cmd)
        
        # build skip list
        skip_list = diag_test_cfg["SKIP"]
        for tmp in skip_list:
            # yaml format is DSP#ALL, DSP#TEST1, DSP#TEST1#TEST2, etc
            tmp_list = tmp.split('#')
            if len(tmp_list) < 2:
                libmfg_utils.sys_exit("Diag Test Yaml file {:s} skip format error".format(diag_cfg_file))
            elif len(tmp_list) == 2:
                # skip the whole dsp
                if tmp_list[1] == "ALL":
                    skip_cmd = libmfg_utils.diag_skip_cmd(tmp_list[0])
                    self._skip_test_list.append(skip_cmd)
                # skip a single test from dsp
                else:
                    skip_cmd = libmfg_utils.diag_skip_cmd(tmp_list[0], tmp_list[1])
                    self._skip_test_list.append(skip_cmd)
            else:
                for name in tmp_list[1:]:
                    skip_cmd = libmfg_utils.diag_skip_cmd(tmp_list[0], name)
                    self._skip_test_list.append(skip_cmd)

        # build parameter list
        param_list = diag_test_cfg["PARAMS"]
        for tmp in param_list:
            # yaml format is CARD#DSP#TEST#Param_list
            tmp_list = tmp.split('#')
            if len(tmp_list) != 4:
                libmfg_utils.sys_exit("Diag Test Yaml file {:s} parameter format error".format(diag_cfg_file))
            else:
                param_cmd = libmfg_utils.diag_param_cmd(tmp_list)
                self._test_param_list.append(param_cmd)

        # sequential test:
        for dsp in diag_test_cfg["MTP_SEQ"].keys():
            for test in diag_test_cfg["MTP_SEQ"][dsp]:
                self._seq_test_id_list.append((dsp, test))

#        # parallel test:
#        for dsp in diag_test_cfg["MTP_PARA"].keys():
#            for test in diag_test_cfg["MTP_PARA"][dsp]:
#                self._para_test_id_list.append((dsp, test))

        self._seq_tests = diag_test_cfg["MTP_SEQ"]
#        self._para_tests = diag_test_cfg["MTP_PARA"]


    def get_init_cmd_list(self):   
        return self._init_cmd_list


    def get_skip_test_list(self):   
        return self._skip_test_list


    def get_skip_test_cmd_list(self, nic_list):   
        skip_list = list()
        for slot in nic_list:
            nic_str = "nic{:d}".format(slot+1)
            for skip in self._skip_test_list:
                cmd = "./diag -skip -c " + nic_str + skip 
                skip_list.append(cmd)
        return skip_list


    def get_test_param_list(self):   
        return self._test_param_list


    def get_test_param_cmd_list(self):   
        param_list = list()
        for param in self._test_param_list:
            cmd = "./diag -param {:s}".format(param)
            param_list.append(cmd)
        return param_list


    def get_diag_seq_test_list(self):   
        return self._seq_test_id_list


    def get_diag_seq_test_run_cmd(self, dsp, test, slot, opts, sn):   
        if dsp == "MISC":
            return ""

        if opts["NIC_NAME"]:
            card_name = "nic{:d}".format(slot+1)
        else:
            card_name = "MTP1"

        param = '"'
        if opts["SN"]:
            param += 'sn={:s} '.format(sn)
        if opts["SLOT"]:
            param += 'slot={:d}'.format(slot+1)
        param += '"'

        return libmfg_utils.diag_seq_run_cmd(card_name, dsp, test, param)


    def get_diag_seq_test_errcode_cmd(self, dsp, slot, opts):   
        if dsp == "MISC":
            return "sys_sanity.sh {:d}".format(slot+1)

        if opts["NIC_NAME"]:
            card_name = "nic{:d}".format(slot+1)
        else:
            card_name = "MTP1"

        return libmfg_utils.diag_seq_errcode_cmd(card_name, dsp)


    def get_diag_seq_test(self, dsp, test):   
        return self._seq_tests[dsp][test]


    def get_diag_seq_dsp_list(self):
        return self._seq_tests.keys()


    def get_diag_para_test_list(self):   
        return self._para_test_id_list


    def get_diag_para_test(self, dsp, test):   
        return self._para_tests[dsp][test]


    def get_diag_para_dsp_list(self):
        return self._para_tests.keys()


