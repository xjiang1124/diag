import libmfg_utils
from libdefs import FF_Stage
from libdefs import MFG_DIAG_CMDS
from libdefs import Voltage_Margin

class diag_db():
    def __init__(self, stage, diag_cfg_file):
        diag_test_cfg = libmfg_utils.load_cfg_from_yaml(diag_cfg_file)
        self._init_cmd_list = list()
        self._skip_test_list = list()
        self._test_param_list = list()
        self._seq_test_id_list = list()
        self._pre_test_intf_list = list()
        self._mtp_para_test_list = list()
        self._post_test_intf_list = list()
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
        if stage == FF_Stage.FF_P2C or stage == FF_Stage.FF_ORT:
            param_list = diag_test_cfg["PARAMS"]["P2C"]
        else:
            param_list = diag_test_cfg["PARAMS"]["4C"]

        for tmp in param_list:
            # yaml format is CARD#DSP#TEST#Param_list
            tmp_list = tmp.split('#')
            if len(tmp_list) != 4:
                libmfg_utils.sys_exit("Diag Test Yaml file {:s} parameter format error".format(diag_cfg_file))
            else:
                param_cmd = libmfg_utils.diag_param_cmd(tmp_list)
                self._test_param_list.append(param_cmd)

        # pre test interface check:
        for intf in list(diag_test_cfg["MTP_PRE"].keys()):
            if diag_test_cfg["MTP_PRE"][intf]:
                self._pre_test_intf_list.append(intf)

        # sequential test:
        if "MTP_SEQ" in list(diag_test_cfg.keys()) and len(diag_test_cfg["MTP_SEQ"]):
            for dsp in list(diag_test_cfg["MTP_SEQ"].keys()):
                for test in diag_test_cfg["MTP_SEQ"][dsp]:
                    self._seq_test_id_list.append((dsp, test))

        # mtp parallel test:
        if "MTP_PARA" in list(diag_test_cfg.keys()) and len(diag_test_cfg["MTP_PARA"]):
            for test in list(diag_test_cfg["MTP_PARA"].keys()):
                if diag_test_cfg["MTP_PARA"][test]:
                    self._mtp_para_test_list.append(test)

        # parallel test:
        if "NIC_PARA" in list(diag_test_cfg.keys()) and len(diag_test_cfg["NIC_PARA"]):
            for dsp in list(diag_test_cfg["NIC_PARA"].keys()):
                for test in diag_test_cfg["NIC_PARA"][dsp]:
                    self._para_test_id_list.append((dsp, test))

        # post test interface check:
        for intf in list(diag_test_cfg["MTP_POST"].keys()):
            if diag_test_cfg["MTP_POST"][intf]:
                self._post_test_intf_list.append(intf)

        if "MTP_SEQ" in list(diag_test_cfg.keys()) and len(diag_test_cfg["MTP_SEQ"]):
            self._seq_tests = diag_test_cfg["MTP_SEQ"]
        if "NIC_PARA" in list(diag_test_cfg.keys()) and len(diag_test_cfg["NIC_PARA"]):
            self._para_tests = diag_test_cfg["NIC_PARA"]


    def get_init_cmd_list(self):
        return self._init_cmd_list


    def get_skip_test_list(self):
        return self._skip_test_list


    def get_skip_test_cmd_list(self, nic_list):
        skip_list = list()
        for slot in nic_list:
            nic_str = "NIC{:d}".format(slot+1)
            for skip in self._skip_test_list:
                cmd = "./diag -skip -c " + nic_str + skip
                skip_list.append(cmd)
        return skip_list


    def get_test_param_list(self):
        return self._test_param_list


    def get_test_param_cmd_list(self):
        param_list = list()
        for param in self._test_param_list:
            cmd = MFG_DIAG_CMDS().MTP_DSP_PARAM_FMT.format(param)
            param_list.append(cmd)
        return param_list


    def get_diag_seq_test_list(self):
        return self._seq_test_id_list


    def get_diag_para_test_list(self):
        return self._para_test_id_list


    def get_pre_diag_test_intf_list(self):
        return self._pre_test_intf_list


    def get_mtp_para_test_list(self):
        return self._mtp_para_test_list


    def get_post_diag_test_intf_list(self):
        return self._post_test_intf_list


    def get_diag_seq_test_run_cmd(self, dsp, test, slot, opts, sn, vmarg=Voltage_Margin.normal, mode=""):
        if opts["NIC_NAME"]:
            card_name = "NIC{:d}".format(slot+1)
        else:
            card_name = "MTP1"

        param = '"'
        if "SN" in opts and opts["SN"]:
            param += 'sn={:s}'.format(sn)
        if "SLOT" in opts and opts["SLOT"]:
            param += ' slot={:d}'.format(slot+1)
        if "VMARG" in opts and opts["VMARG"]:
            param += ' vmarg={:s}'.format(vmarg)
        if "MODE" in opts and opts["MODE"]:
            param += ' mode={:s}'.format(mode)
        if "SIMPLIFIED" in opts and opts["SIMPLIFIED"]:
            param += ' simplified=1'
        param += '"'

        return libmfg_utils.diag_seq_run_cmd(card_name, dsp, test, param)


    def get_diag_para_test_run_cmd(self, dsp, test, slot, opts, sn, mode=""):
        if opts["NIC_NAME"]:
            card_name = "NIC{:d}".format(slot+1)
        else:
            card_name = "MTP1"

        param = '"'
        if "SN" in opts and opts["SN"]:
            param += 'sn={:s} '.format(sn)
        if "SLOT" in opts and opts["SLOT"]:
            param += 'slot={:d}'.format(slot+1)
        if "MODE" in opts and opts["MODE"]:
            param += 'mode={:s}'.format(mode)
        param += '"'

        return libmfg_utils.diag_para_run_cmd(card_name, dsp, test, param)


    def get_diag_seq_test_errcode_cmd(self, dsp, slot, opts):
        if "NIC_NAME" in opts and opts["NIC_NAME"]:
            card_name = "NIC{:d}".format(slot+1)
        else:
            card_name = "MTP1"

        return libmfg_utils.diag_seq_errcode_cmd(card_name, dsp)


    def get_diag_para_test_errcode_cmd(self, dsp, slot, opts):
        if "NIC_NAME" in opts and opts["NIC_NAME"]:
            card_name = "NIC{:d}".format(slot+1)
        else:
            card_name = "MTP1"

        return libmfg_utils.diag_para_errcode_cmd(card_name, dsp)


    def get_diag_seq_test(self, dsp, test):
        return self._seq_tests[dsp][test]


    def get_diag_seq_dsp_list(self):
        return list(self._seq_tests.keys())


    def get_diag_para_test(self, dsp, test):
        return self._para_tests[dsp][test]


    def get_diag_para_dsp_list(self):
        return list(self._para_tests.keys())


