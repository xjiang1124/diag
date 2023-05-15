import sys, os, re

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libmfg_utils
import libtest_utils

param_cfg = libtest_config.parse_config("lib/tests/nic_pcie/parameters.yaml")

fpgautil_path = "/home/admin/eeupdate"
PENSANDO_ID = "1dd8"
ELBA_ROOT_ID = "0002"
MEMTUN_BRIDGE_ID = "1001"

SYS_PCIE_BUS_RE = r"([0-9a-f]{4})[\.:]([0-9a-f]{2})[\.:]([0-9a-f]{2})"
LS_PCIE_BUS_RE = r"([0-9a-f]{2})[\.:]([0-9a-f]{2}).([0-9a-f]{2})"


class PCIE_Address:
    # dict{elba#: value}

    PCI_SLOT = {
        0:  "0-1",
        1:  "0-3",
        2:  "0-5",
        3:  "0-7",
        4:  "0-6",
        5:  "0-4",
        6:  "0-2",
        7:  "0"
    }
    # 169.1.13.{pcislot}1
    MEMTUN_IP = {
        0:  "169.1.13.11",
        1:  "169.1.13.31",
        2:  "169.1.13.51",
        3:  "169.1.13.71",
        4:  "169.1.13.61",
        5:  "169.1.13.41",
        6:  "169.1.13.21",
        7:  "169.1.13.01"
    }
    # 169.1.13.{pcislot}2
    MGMT_IP = {
        0:  "169.1.13.12",
        1:  "169.1.13.32",
        2:  "169.1.13.52",
        3:  "169.1.13.72",
        4:  "169.1.13.62",
        5:  "169.1.13.42",
        6:  "169.1.13.22",
        7:  "169.1.13.02"
    }


@libtest_utils.parallel_combined_test
def memtun_init(test_ctrl, slot):
    """
        ./memtun -s <1001 bus> 169.1.13.{slot}1 &
        ping 169.1.13.{slot}2
    """
    pcie_mgmt_bus = test_ctrl.nic[slot]._pcie_mgmt_bus
    memtun_ip = PCIE_Address.MEMTUN_IP[slot]

    if not pcie_mgmt_bus:
        test_ctrl.cli_log_slot_err(slot, "Cannot start memtun connection")
        return False

    cmd = "{:s}/memtun -s {:s} {:s} &".format(fpgautil_path, pcie_mgmt_bus, memtun_ip)
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd):
        test_ctrl.cli_log_slot_err(slot, "{:s} command failed".format(cmd))
        return False

    if not memtun_verify(test_ctrl, slot):
        return False

    return True
    

def memtun_verify(test_ctrl, slot):
    nic_mgmt_ip = PCIE_Address.MGMT_IP[slot]
    cmd = "ping -c 4 {:s}".format(nic_mgmt_ip)
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd):
        test_ctrl.cli_log_slot_err(slot, "{:s} command failed".format(cmd))
        return False

    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    match = re.findall(r" 0% packet loss", cmd_buf)
    if match:
        test_ctrl.nic[slot]._ip_addr = nic_mgmt_ip
        return True
    else:
        test_ctrl.cli_log_slot_err(slot, "Ping to NIC failed")
        return False


def nic_pcie_scan(test_ctrl, fpo=True):
    return nic_pcie_init(test_ctrl)


def nic_pcie_init(test_ctrl, fpo=True):
    if not close_memtun(test_ctrl):
        return False

    if fpo:
        if not bringup_dummy_fru(test_ctrl):
            return False

    test_ctrl.cli_log_inf("Scanning for PCIE devices...", level=0)
    cmd = "echo 1 > /sys/bus/pci/rescan"
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=param_cfg["PCIE_RESCAN_DELAY"]):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    pci_devices = parse_lspci_devices(test_ctrl)
    if not pci_devices:
        test_ctrl.cli_log_err("No NIC devices found on PCIE", level=0)
        return False

    if not nic_pcie_verify(test_ctrl, pci_devices):
        return False

    return True


@libtest_utils.parallel_combined_test
def bringup_dummy_fru(test_ctrl, slot):
    if not test_ctrl.nic[slot].nic_dummy_fru():
        test_ctrl.cli_log_slot_err(slot, "Failed to bringup PCIE with dummy FRU")
        return False

    nic_cmd_list = list()
    nic_cmd_list.append("cat /tmp/fru.json")
    nic_cmd_list.append("killall pciemgrd-gold")
    nic_cmd_list.append("/platform/bin/pciemgrd-gold &")
    # nic_cmd_list.append("rm -rf /data/core/*")
    # nic_cmd_list.append("rm -rf /obfl/*")
    # nic_cmd_list.append("rm -rf /data/logstash/*")
    # nic_cmd_list.append("rm -rf /data/techsupport/*")

    if not test_ctrl.nic[slot].nic_exec_console_cmds(nic_cmd_list):
        return False

    return True


def parse_lspci_devices(test_ctrl):
    """
    Parse output of 'lspci -n' and look for groups of buses that form one endpoint

    01:00.0 0580: 1dd8:0009
    02:00.0 0580: 1dd8:000a
    06:00.0 0604: 1dd8:0002 (rev 18)
    07:00.0 0604: 1dd8:1001 (rev 18)
    08:00.0 ff00: 1dd8:8000 (rev 18)
    0a:00.0 0604: 1dd8:0002
    0b:00.0 0604: 1dd8:1001
    0c:00.0 ff00: 1dd8:8000

    pci_devices is a dict as:

    {'06:00.0': 
        [('06:00.0', '0604:', '1dd8:0002'), 
         ('07:00.0', '0604:', '1dd8:1001'), 
         ('08:00.0', 'ff00:', '1dd8:8000')], 
    '0a:00.0': 
        [('0a:00.0', '0604:', '1dd8:0002'), 
         ('0b:00.0', '0604:', '1dd8:1001'), 
         ('0c:00.0', 'ff00:', '1dd8:8000')]
    }
    """

    cmd = "lspci -n | grep 1dd8"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return None

    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    if not cmd_buf:
        return None

    pci_devices = {}
    try:
        pci_device = []
        for line in cmd_buf.splitlines():
            line = line.strip()
            if not line:
                continue
            if PENSANDO_ID not in line:
                continue
            bus_num, addr, pci_id, *rev = line.split(" ")
            if "{:s}:{:s}".format(PENSANDO_ID, ELBA_ROOT_ID) in pci_id:
                # end
                if pci_device:
                    pci_devices[pci_device[0][0]] = pci_device #save previous
                # start
                pci_device = [(bus_num, addr, pci_id)]
            elif PENSANDO_ID in pci_id:
                # middle
                if pci_device:
                    pci_device.append((bus_num, addr, pci_id))
            else:
                # end
                pci_device = []

        if pci_device:
            pci_devices[pci_device[0][0]] = pci_device #save last
    except Exception as e:
        test_ctrl.cli_log_err(str(e), level=0)
        test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(cmd_buf))
        return None

    return pci_devices


def find_pcie_root_bus(test_ctrl, slot):
    """
        Save each Elba's root bus number
    """
    cmd = "cat /sys/bus/pci/slots/{:s}/address".format(PCIE_Address.PCI_SLOT[slot])
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd):
        test_ctrl.cli_log_slot_err(slot, "{:s} command failed".format(cmd))
        return False

    nic_cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not nic_cmd_buf:
        test_ctrl.cli_log_slot_err(slot, "Elba PCIE not correct")
        return False

    match = re.search(SYS_PCIE_BUS_RE, nic_cmd_buf)
    if match:
        test_ctrl.nic[slot].set_pcie_root_bus(sys_pcie_bus_to_lspci_format(match.group(0).strip()))
    else:
        test_ctrl.cli_log_slot_err(slot, "Missing output from {:s}".format(cmd))
        test_ctrl.log_nic_file(slot, "SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(nic_cmd_buf))
        return False

    test_ctrl.cli_log_slot_inf(slot, "Found Elba on PCIE bus {:s}".format(test_ctrl.nic[slot].get_pcie_root_bus()))

    return True


def find_pcie_mgmt_bus(test_ctrl, slot, pci_devices):
    """
        0a:00.0 PCI bridge: Pensando Systems Device 0002
        0b:00.0 PCI bridge: Pensando Systems DSC Virtual Downstream Port 1001
        0c:00.0 Unassigned class [ff00]: Pensando Systems Device 8000

        pci_devices is a dict as:
        {'06:00.0': 
            [('06:00.0', '0604:', '1dd8:0002'), 
             ('07:00.0', '0604:', '1dd8:1001'), 
             ('08:00.0', 'ff00:', '1dd8:8000')], 
        '0a:00.0': 
            [('0a:00.0', '0604:', '1dd8:0002'), 
             ('0b:00.0', '0604:', '1dd8:1001'), 
             ('0c:00.0', 'ff00:', '1dd8:8000')]
        }
    """
    pcie_root_bus = test_ctrl.nic[slot]._pcie_root_bus
    if pcie_root_bus not in pci_devices.keys():
        test_ctrl.cli_log_slot_err(slot, "Failed to detect Elba bus {:s} on PCIE bus".format(pcie_root_bus))
        return False

    # search in pci_devices
    endpoint_devices = pci_devices[pcie_root_bus]
    downstream_bridge, unknown = "",""
    for bus_num, addr, pci_id in endpoint_devices:
        if "1dd8:1001" in pci_id:
            downstream_bridge = bus_num
        else:
            unknown = bus_num
    if not downstream_bridge:
        test_ctrl.cli_log_slot_err(slot, "Missing PCIE downstream bridge")
        return False

    test_ctrl.nic[slot].set_pcie_mgmt_bus(downstream_bridge)
    test_ctrl.cli_log_slot_inf(slot, "Found Elba downstream bus at {:s}".format(test_ctrl.nic[slot].get_pcie_mgmt_bus()))

    return True


@libtest_utils.parallel_combined_test
def nic_pcie_verify(test_ctrl, slot, pci_devices):
    if not find_pcie_root_bus(test_ctrl, slot):
        return False

    if not find_pcie_mgmt_bus(test_ctrl, slot, pci_devices):
        return False

    pcie_root_bus = test_ctrl.nic[slot]._pcie_root_bus
    pcie_mgmt_bus = test_ctrl.nic[slot]._pcie_mgmt_bus
    if not pcie_root_bus:
        test_ctrl.cli_log_slot_err(slot, "Elba did not show up on PCIE tree")
        return False

    if not pcie_mgmt_bus:
        test_ctrl.cli_log_slot_err(slot, "Elba downstream bus did not show up on PCIE tree")
        return False

    ### DUMP JUST FOR INFO
    cmd = "lspci -vvv -s {:s}".format(pcie_root_bus)
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd):
        test_ctrl.cli_log_slot_err(slot, "Unable to retrieve PCIE bus properties")
        return False

    cmd = "lspci -vvv -s {:s}".format(pcie_mgmt_bus)
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd):
        test_ctrl.cli_log_slot_err(slot, "Unable to retrieve PCIE downstream bus properties")
        return False


    ### CHECK SPEED AND WIDTH
    cmd = "lspci -vv -s {:s} | grep LnkSta:".format(pcie_root_bus)
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd):
        test_ctrl.cli_log_slot_err(slot, "Unable to retrieve PCIE link speed and width")
        return False
    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    expected_speed = param_cfg["ELBA_PCIE_LINK_SPEED"]
    expected_width = param_cfg["ELBA_PCIE_LINK_WIDTH"]
    if "Speed {:d}GT/s".format(expected_speed) not in cmd_buf:
        test_ctrl.cli_log_slot_err(slot, "PCIE link came up as {:s}".format(cmd_buf))
        return False

    if "Width {:s}".format(expected_width) not in cmd_buf:
        test_ctrl.cli_log_slot_err(slot, "PCIE link came up as {:s}".format(cmd_buf))
        return False

    test_ctrl.cli_log_slot_inf(slot, "PCIE link came up {:d}GT/s {:s}".format(expected_speed, expected_width))

    return True


def sys_pcie_bus_to_lspci_format(sys_bus_format):
    """ reformat 0000:0a:00 to 0a:00.0 """
    match = re.search(SYS_PCIE_BUS_RE, sys_bus_format)
    if match:
        _ = match.group(1)
        addr = match.group(2)
        subaddr = match.group(3)
        resource = "0"

        return "{}:{}.{}".format(addr, subaddr, resource)


def close_memtun(test_ctrl):
    cmd = "killall memtun"
    if not test_ctrl.mtp.exec_cmd(cmd):
        return False

    return True
