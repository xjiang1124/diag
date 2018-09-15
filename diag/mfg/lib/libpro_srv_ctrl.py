import pexpect
import time
import os
import sys
import re
import libmfg_utils

class pro_srv_ctrl():
    def __init__(self, mgmt_cfg):
        self._mgmt_handle = None
        self._mgmt_cfg = mgmt_cfg
        self._prompt_list = ["#", "$", ">"]


    def pro_srv_cli_err(self, msg): 
        pro_srv_cli_id_str = "[PRO-SRV]: "
        libmfg_utils.cli_err(pro_srv_cli_id_str + msg)


    def pro_srv_cli_inf(self, msg): 
        pro_srv_cli_id_str = "[PRO-SRV]: "
        libmfg_utils.cli_inf(pro_srv_cli_id_str + msg)


    def pro_srv_mgmt_disconnect(self):
        if self._mgmt_handle:
            self._mgmt_handle.close()
            self._mgmt_handle = None


    def pro_srv_mgmt_connect(self):
        if not self._mgmt_cfg:
            self.pro_srv_cli_err("management port config is empty")
            return None

        self.pro_srv_mgmt_disconnect()

        # mgmt_cfg is a list with format [ip, userid, passwd]
        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        os.system("ssh-keygen -R " + ip + " > /dev/null")

        self._mgmt_handle = pexpect.spawn("ssh -l " + userid + " " + ip)
        while True:
            idx = self._mgmt_handle.expect_exact(["No route to host",
                                                  "continue connecting (yes/no)?",
                                                  "assword:",
                                                  pexpect.TIMEOUT], timeout = 10)
            if idx == 0:
                self.pro_srv_cli_inf("network failure, wait 1s and retry")
                time.sleep(1)
                self._mgmt_handle = pexpect.spawn("ssh -l " + userid + " " + ip)
                continue
            elif idx == 1: 
               self._mgmt_handle.sendline("yes")
               continue
            elif idx == 2:
                self._mgmt_handle.sendline(passwd)
                break
            else:
                self.pro_srv_cli_err("ssh to product server: " + ip + " timeout")
                return None

        try:
            idx = self._mgmt_handle.expect_exact(self._prompt_list, timeout = 5) 
            if (idx < len(self._prompt_list)):
                self._mgmt_handle.sendline("whoami")
                self._mgmt_handle.expect_exact(userid)
                self._mgmt_handle.expect_exact(self._prompt_list[idx])
                self._mgmt_prompt = self._prompt_list[idx]
                return self._mgmt_prompt
            else:
                self.pro_srv_cli_err("unknown linux prompt")
                return None

        except pexpect.TIMEOUT:
            self.pro_srv_cli_err("incorrect password")
            return None


    def file_xfer(self, filename, remote_path, remote_ip, userid, passwd):
        cmd = "md5sum " + filename
        session = pexpect.spawn(cmd)
        session.expect_exact(pexpect.EOF)
        match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
        session.close()
        if match:
            local_md5sum = match.group(1)
        else:
            self.pro_srv_cli_err("Execute command {:s} failed".format(cmd))
            return False

        os.system("ssh-keygen -R " + remote_ip + " > /dev/null")

        # copy file
        cmd = "scp " + filename + " " + userid + "@" + remote_ip + ":" + remote_path
        session = pexpect.spawn(cmd)
        session.setecho(False)
        while True:
            idx = session.expect_exact(["continue connecting (yes/no)?",
                                        "assword:",
                                        pexpect.TIMEOUT], timeout = 10)
            if idx == 0: 
               session.sendline("yes")
               continue
            elif idx == 1:
                session.sendline(passwd)
                break
            else:
                self.pro_srv_cli_err("scp to MTP chassis: {:s} timeout".format(remote_ip))
                return False

        session.expect_exact(pexpect.EOF)
        session.close()

        # verify the file md5sum
        session = pexpect.spawn('ssh -o "StrictHostKeyChecking no" -l ' + userid + ' ' + remote_ip)
        session.setecho(False)
        session.expect_exact("assword:")
        session.sendline(passwd)

        try:
            idx = session.expect_exact(self._prompt_list, timeout = 5)
            if idx < len(self._prompt_list):
                cmd = "md5sum " + remote_path + os.path.basename(filename)
                session.sendline(cmd)
                session.expect_exact(self._prompt_list[idx])
                match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
                session.close()
                # md5sum match
                if match:
                    if match.group(1) == local_md5sum:
                        return True
                    else:
                        self.pro_srv_cli_err("File md5sum mismatch")
                        return False
                else:
                    self.pro_srv_cli_err("Execute command {:s} failed".format(cmd))
                    return False

        except pexpect.TIMEOUT:
            self.pro_srv_cli_err("Product server connect timeout")
            return False


    def pro_srv_mgmt_connect_test(self):
        if not self.pro_srv_mgmt_connect():
            return False

        time.sleep(1)
        self.pro_srv_mgmt_disconnect()
        return True

