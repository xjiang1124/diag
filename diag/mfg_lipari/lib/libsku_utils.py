from libmfg_cfg import Factory

# FLM[Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
FLX_SN_SUFFIX_FMT = r"\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
PEN_PN_FMT = r"68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2}"
PEN_PN_MINUS_REV_MASK = -3 # (last three digits)

MAC_OUI_1 = r"00%s[a,A][e,E]%s[c,C][d,D]%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}"
# MAC_OUI_2 = r"04%s90%s81%s(?:0[a-fA-F1-9]|[a-fA-F1-9][a-fA-F0-9])%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}"
MAC_OUI_2 = r"04%s90%s81%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}"
MAC_OUI_3 = r"74%s27%s2C%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}"
PEN_MAC_DASHES_FMT = MAC_OUI_1 % tuple(["-"]*5) + "|" + MAC_OUI_2 % tuple(["-"]*5) + "|" + MAC_OUI_3 % tuple(["-"]*5)
PEN_MAC_COLONS_FMT = MAC_OUI_1 % tuple([":"]*5) + "|" + MAC_OUI_2 % tuple([":"]*5) + "|" + MAC_OUI_3 % tuple([":"]*5)
PEN_MAC_NO_DASHES_FMT = MAC_OUI_1 % tuple([""]*5) + "|" + MAC_OUI_2 % tuple([""]*5) + "|" + MAC_OUI_3 % tuple([""]*5)
OCP_ADAPTER_FIXED_MAC = "FFFFFFFFFFFF"


class PART_NUMBERS_MATCH:
    LIPARI_CPU_PN = r"73-0068-0[0-9]{1} [A-Z0-9]{2}"
    LIPARI_SWI_PN = r"73-0067-0[0-9]{1} [A-Z0-9]{2}"
    LIPARI_BMC_PN = r"73-0076-0[0-9]{1} [A-Z0-9]{2}"
    # LIPARI_SYS_PN = r"68-0032-0[0-9]{1} [A-Z0-9]{2}"
    LIPARI_SYS_PN = r"68-0032-0[0-9]{1}"
    LIPARI_ELB_PN = r"73-0040-0[0-9]{1} [A-Z0-9]{2}"

SN_FORMAT_TABLE = {
    Factory.P1: {
        "DEFAULT":                                  "FPF" + FLX_SN_SUFFIX_FMT
    }
}

PN_FORMAT_TABLE = {
    PART_NUMBERS_MATCH.LIPARI_CPU_PN,
    PART_NUMBERS_MATCH.LIPARI_SWI_PN,
    PART_NUMBERS_MATCH.LIPARI_BMC_PN,
    PART_NUMBERS_MATCH.LIPARI_SYS_PN,
    PART_NUMBERS_MATCH.LIPARI_ELB_PN
}