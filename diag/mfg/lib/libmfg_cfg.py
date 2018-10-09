# No valid content in the Fru
MFG_CFG_NIC_FRU_VALID = False
DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
DIAG_SSH_OPTIONS = " -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null'"

# please check the label specification
# FL[M,Z,G][Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
NAPLES_SN_FMT = r"FL[M,Z,G]\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
NAPLES_MAC_FMT = r"00AECD[A-F0-9]+$"
