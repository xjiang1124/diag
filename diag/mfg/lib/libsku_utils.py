from enum import Enum
from libdefs import NIC_Type
from libdefs import Factory

# FLM[Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
FLX_SN_SUFFIX_FMT = r"\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
PEN_PN_FMT = r"68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2}"
PEN_PN_MINUS_REV_MASK = -3 # (last three digits)
OCP_ADAPTER_FIXED_PN = "73-0024-03"

# [Sitecode][Year last digit][Week: 00-52][4 alphanumeric minus vowels]
HPE_SUFFIX_FMT = r"\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
HPE_MILP_SN_FMT = r"5UP"
HPE_FSP_SN_FMT = r"(?:2YU|3Y1)"
HPE_P1_SN_FMT = r"4YA"
HPE_PART_NUM_FMT = r"([A-Z0-9]{6}-B[0-9]{2})"
HPE_PROD_NUM_FMT = r"([A-Z0-9]{6}-B[0-9]{2})"
HPE_CT_FMT = r"PZGKHFVEE5I[0-5]{1}\d{1}[A-F0-9]{3}"
HPE_SN_FMT = HPE_P1_SN_FMT + HPE_SUFFIX_FMT

# DC: [last digit of year][month 1-9,A-C][day1-9,A-K=10-20,L-V:21-31]
DELL_PPID_COUNTRY_FMT = r"(?:US|MY)"
DELL_PPID_PART_NUM_FMT = r"(?:0PCFPC|0X322F|0W5WGK|0745T9)"
DELL_PPID_MFG_ID_FMT = r"(?:FLUPK|FLEPK|FLPAM)"
DELL_PPID_DATE_CODE_FMT = r"[0-9][1-9A-C][1-9A-V]"
DELL_PPID_SER_NUM_FMT = r"[0-9A-O][0-9A-Z]{3}"
DELL_PPID_REV_FMT = r"[X|A][0-9]{2}"
DELL_PPID_FMT = DELL_PPID_COUNTRY_FMT + DELL_PPID_PART_NUM_FMT + DELL_PPID_MFG_ID_FMT + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT
# DO NOT put older DELL PN into this table
DELL_SKU_TO_DELL_PN = {
    "POLLARA-1Q400P-D": ["0745T9"],
    }

HPE_SKU = ["POLLARA-1Q400P-H"]

MAC_OUI_1 = r"00%s[a,A][e,E]%s[c,C][d,D]%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}"
MAC_OUI_2 = r"04%s90%s81%s(?:0[a-fA-F1-9]|[a-fA-F1-9][a-fA-F0-9])%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}"
MAC_OUI_3 = r"74%s27%s2C%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}%s[a-fA-F0-9]{2}"
PEN_MAC_DASHES_FMT = MAC_OUI_1 % tuple(["-"]*5) + "|" + MAC_OUI_2 % tuple(["-"]*5) + "|" + MAC_OUI_3 % tuple(["-"]*5)
PEN_MAC_NO_DASHES_FMT = MAC_OUI_1 % tuple([""]*5) + "|" + MAC_OUI_2 % tuple([""]*5) + "|" + MAC_OUI_3 % tuple([""]*5)
OCP_ADAPTER_FIXED_MAC = "FFFFFFFFFFFF"


class PART_NUMBERS_MATCH:
    N100_PEN_PN_FMT = r"68-0003-0[0-9]{1} [A-Z0-9]{2}"                                              #68-0003-01 01    NAPLES100 PENSANDO
    N100_NET_PN_FMT = r"111-(?:04635|05363)"                                                        #111-05363        NAPLES100 NETAPP

    N100_IBM_PN_FMT = r"68-0013-0[0-9]{1} [A-Z0-9]{2}"                                              #68-0013-01 03    NAPLES100 IBM

    N100_HPE_PN_FMT     = r"P37692-00[0-9]{1}"                                                      #P37692-001       NAPLES100 HPE
    N100_HPE_CLD_PN_FMT = r"P41854-00[0-9]{1}"                                                      #P41854-001       NAPLES100 HPE CLOUD

    N100_DELL_PN_FMT  = r"68-0024-0[0-9]{1} [A-Z0-9]{2}"                                            #68-0024-01 XX    NAPLES100 DELL

    N25_PEN_PN_FMT = r"68-0005-0[0-9]{1} [A-Z0-9]{2}"                                               #68-0005-03 01    NAPLES25 PENSANDO
    N25_HPE_PN_FMT = r"P18669-00[0-9]{1}"                                                           #P18669-001       NAPLES25 HPE
    N25_EQI_PN_FMT = r"68-0008-0[0-9]{1} [0-9]{2}"                                                  #68-0008-xx yy    NAPLES25 EQUINIX

    N25_SWM_HPE_001_PN_FMT = r"P26968-001"                                                          #P26968-001       NAPLES25 SWM HPE
    N25_SWM_HPE_PN_FMT     = r"P26968-00[2-9]{1}"                                                   #P26968-002       NAPLES25 SWM HPE
    N25_SWM_HPE_CLD_PN_FMT = r"P41851-00[0-9]{1}"                                                   #P41851-001       NAPLES25 SWM HPE CLOUD
    N25_SWM_HPE_TAA_PN_FMT = r"P46653-00[0-9]{1}"                                                   #P46653-001       NAPLES25 SWM HPE TAA
    N25_SWM_PEN_PN_FMT     = r"68-0016-0[0-9]{1} [A-Z0-9]{2}"                                       #68-0016-01 01    NAPLES25 SWM PENSANDO
    N25_SWM_PEN_TAA_PN_FMT = r"68-0017-0[0-9]{1} [A-Z0-9]{2}"                                       #68-0017-01 01    NAPLES25 SWM PENSANDO TAA
    N25_SWM_DEL_PN_FMT = r"68-0014-0[0-9]{1} [A-Z0-9]{2}"                                           #68-0014-01 00    NAPLES25 SWM DELL
    N25_SWM_833_PN_FMT = r"68-0019-0[0-9]{1} [A-Z0-9]{2}"                                           #68-0019-01 01    NAPLES25 SWM 833 PENSANDO

    N25_OCP_PEN_PN_FMT = r"68-0023-0[0-9]{1} [A-Z0-9]{2}"                                           #68-00xx-xx       NAPLES25 OCP PENSANDO
    N25_OCP_HPE_PN_FMT = r"P37689-00[0-9]{1}"                                                       #P37689-001       NAPLES25 OCP HPE
    N25_OCP_HPE_CLD_PN_FMT = r"P41857-00[0-9]{1}"                                                   #P41857-001       NAPLES25 OCP HPE CLOUD
    N25_OCP_DEL_PN_FMT = r"68-0010-0[0-9]{1} [A-Z0-9]{2}"                                           #68-0010-01       NAPLES25 OCP DELL
    N25_OCP_ADAPTER_PN_FMT = r"73-0024-03"

    ALOM_HPE_PN_FMT = r"P26971-00[0-9]{1}"                                                          #P26971-001       NAPLES25 SWM HPE ALOM ADAPTER

    FORIO_PN_FMT = r"68-0007-0[0-9]{1} [0-9]{2}"                                                    #68-0007-01 01    FORIO
    VOMERO_PN_FMT = r"68-0009-0[0-9]{1} [0-9]{2}"                                                   #68-0009-01 01    VOMERO
    VOMERO2_PN_FMT = r"68-0011-0[0-9]{1} [A-Z0-9]{2}"                                               #68-0011-01 01    VOMERO2

    ORTANO_PN_FMT = r"68-0015-01 [A-Z0-9]{2}"                                                       #68-0015-01 01    ORTANO
    ORTANO2_ORC_PN_FMT = r"68-0015-0[2-9]{1} [A-Z0-9]{2}"                                           #68-0015-02 01    ORTANO2 ORACLE
    ORTANO2_PEN_PN_FMT= r"68-0021-0[2-9]{1} [A-Z0-9]{2}"                                            #68-0021-02 01    ORTANO2 GENERIC (PENSANDO)

    POMONTEDELL_PN_FMT = r"0PCFPC(?:X|A)[0-9]{2}"                                                   #0PCFPC X/A       POMONTE DELL
    LACONA32DELL_PN_FMT = r"(?:0X322F|0W5WGK)(?:X|A)[0-9]{2}"                                       #0X322F X/A       LACONA32 DELL
    LACONA32_PN_FMT = r"P47930-00[0-9]{1}"                                                          #P47930-001       LACONA32 HPE

    ORTANO2ADI_ORC_PN_FMT = r"68-0026-0[1-9]{1} [A-Z0-9]{2}"                                        #68-0026-01 01    ORTANO2ADI ORACLE
    ORTANO2ADI_IBM_PN_FMT = r"68-0028-0[1-9]{1} [A-Z0-9]{2}"                                        #68-0028-01 01    ORTANO2ADI IBM
    ORTANO2ADI_MSFT_PN_FMT = r"68-0034-0[1-9]{1} [A-Z0-9]{2}"                                       #68-0034-01 01    ORTANO2ADI MICROSOFT
    ORTANO2INTERP_ORC_PN_FMT = r"68-0029-0[1-9]{1} [A-Z0-9]{2}"                                     #68-0029-01 02    ORTANO2INTERP_ORC_PN_FMT ORACLE
    ORTANO2SOLO_ORC_PN_FMT = r"68-0077-0[1-9]{1} [A-Z0-9]{2}"                                       #68-0077-01 A0    ORTANO2SOLO_ORC_PN_FMT ORACLE
    ORTANO2SOLO_ORC_L_PN_FMT = r"68-0095-0[1-9]{1} [A-Z0-9]{2}"                                     #68-0095-01 A0    ORTANO2SOLO_ORC_PN_L_FMT ORACLE
    ORTANO2SOLO_ORC_THS_PN_FMT = r"68-0089-0[1-9]{1} [A-Z0-9]{2}"                                   #68-0089-01 A0    ORTANO2SOLO ORACLE Tall Heat Sink
    ORTANO2SOLO_MSFT_PN_FMT = r"68-0090-0[1-9]{1} [A-Z0-9]{2}"                                      #68-0090-01 A0    ORTANO2SOLO MICROSOFT
    ORTANO2SOLO_S4_PN_FMT = r"68-0092-0[1-9]{1} [A-Z0-9]{2}"                                        #68-0092-01 A0    ORTANO2SOLO S4
    ORTANO2ADI_CR_PN_FMT = r"68-0049-0[1-9]{1} [A-Z0-9]{2}"                                         #68-0049-03 A0    ORTANO2ADI CR
    ORTANO2ADI_CR_MSFT_PN_FMT = r"68-0091-0[1-9]{1} [A-Z0-9]{2}"                                    #68-0091-01 A0    ORTANO2ADI CR MICROSOFT
    ORTANO2ADI_CR_S4_PN_FMT = r"68-0092-0[1-9]{1} [A-Z0-9]{2}"                                      #68-0092-01 A0    ORTANO2ADI CR S4
    GINESTRA_D4_PN_FMT = r"68-0074-0[1-9]{1} [A-Z0-9]{2}"                                           #68-0074-01 01    GINESTRA_D4
    GINESTRA_D5_PN_FMT = r"68-0075-0[1-9]{1} [A-Z0-9]{2}"                                           #68-0075-01 01    GINESTRA_D5
    GINESTRA_S4_PN_FMT = r"68-0076-0[1-9]{1} [A-Z0-9]{2}"                                           #68-0076-01 01    GINESTRA_S4
    GINESTRA_CIS_PN_FMT = r"68-0094-0[1-9]{1} [A-Z0-9]{2}"                                          #68-0094-01 01    GINESTRA_CIS
    LENI_PN_FMT = r"102-P10800-0[A-Z0-9]{2}(?:\s[A-Z0-9]{1,2})?"                                    #102-P10800-00B 01  LENI
    LENI48G_PN_FMT = r"102-P10801-0[A-Z0-9]{2}(?:\s[A-Z0-9]{1,2})?"                                 #102-P10801-00B 01  LENI48G
    POLLARA_PN_FMT = r"102-P11100-0[A-Z0-9]{1,2}(?:\s[A-Z0-9]{1,2})?"                               #102-P11100-00B 01  POLLARA
    POLLARA_HPE_PN_FMT = r"102-P11101-0[A-Z0-9]{1,2}(?:\s[A-Z0-9]{1,2})?"                           #102-P11101-00B 01  POLLARA HPE
    POLLARA_DELL_PN_FMT = r"0745T9(?:X|A)[0-9]{2}"                                                  #0745T9 X/A         POLLARA DELL PN
    LINGUA_PN_FMT = r"102-P11500-0[A-Z0-9]{1,2}(?:\s[A-Z0-9]{1,2})?"                                #102-P11500-00B 01  LINGUA
    MALFA_PN_FMT = r"102-P10600-0[0-9]{1}(?:\s[A-Z0-9]{1,2})?"                                      #102-P10600-00 01   MALFA
    GELSOP_PN_FMT = r"101-P00001-0[0-9]{1}(?:\s[A-Z0-9]{1,2})?"                                     #101-P00001-00A     GELSOP

SN_FORMAT_TABLE = {
    Factory.P1: {
        PART_NUMBERS_MATCH.N25_HPE_PN_FMT:                  HPE_P1_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_PEN_PN_FMT:                 "FPF" + FLX_SN_SUFFIX_FMT + "|" + "FPN" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_NET_PN_FMT:                 "FPF" + FLX_SN_SUFFIX_FMT + "|" + "FPN" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_HPE_PN_FMT:                 HPE_P1_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_HPE_CLD_PN_FMT:             HPE_P1_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT:          HPE_P1_SN_FMT + HPE_SUFFIX_FMT + "|" + HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT:              HPE_P1_SN_FMT + HPE_SUFFIX_FMT + "|" + HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT:          HPE_P1_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_TAA_PN_FMT:          HPE_P1_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_OCP_HPE_PN_FMT:              HPE_P1_SN_FMT + HPE_SUFFIX_FMT + "|" + HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_OCP_HPE_CLD_PN_FMT:          HPE_P1_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.LACONA32_PN_FMT:                 HPE_P1_SN_FMT + HPE_SUFFIX_FMT + "|" + HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT:              "MYFLPAM" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + \
                                                            "MY" + DELL_PPID_PART_NUM_FMT + "FLPAM" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT + "|" + \
                                                            "MYFLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + \
                                                            "MY" + DELL_PPID_PART_NUM_FMT + "FLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT,
        PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT:             "MYFLPAM" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + \
                                                            "MY" + DELL_PPID_PART_NUM_FMT + "FLPAM" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT + "|" + \
                                                            "MYFLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + \
                                                            "MY" + DELL_PPID_PART_NUM_FMT + "FLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT,
        PART_NUMBERS_MATCH.N25_OCP_DEL_PN_FMT:              "FPF" + FLX_SN_SUFFIX_FMT + "|" + "FPN" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_DEL_PN_FMT:              "FPF" + FLX_SN_SUFFIX_FMT + "|" + "FPN" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2_PEN_PN_FMT:              "FPF" + FLX_SN_SUFFIX_FMT + "|" + "FPN" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2_ORC_PN_FMT:              "FPE" + FLX_SN_SUFFIX_FMT + "|" + "FPN" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2INTERP_ORC_PN_FMT:        "FPC" + FLX_SN_SUFFIX_FMT + "|" + "FPB" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT:           "FPD" + FLX_SN_SUFFIX_FMT + "|" + "FPA" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_MSFT_PN_FMT:          "FPD" + FLX_SN_SUFFIX_FMT + "|" + "FPA" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT:           "FPD" + FLX_SN_SUFFIX_FMT + "|" + "FPA" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_CR_PN_FMT:            "FPG" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_THS_PN_FMT:      "FPJ" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT:         "FPF" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_PN_FMT:          "FPF" + FLX_SN_SUFFIX_FMT + "|" + "FPJ" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_L_PN_FMT:        "FPP" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_CR_S4_PN_FMT:         "FPF" + FLX_SN_SUFFIX_FMT + "|" + "FPG" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_CR_MSFT_PN_FMT:       "FPG" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.GINESTRA_D5_PN_FMT:              "FPH" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.GINESTRA_S4_PN_FMT:              "FPH" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.GINESTRA_CIS_PN_FMT:             "AFM" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.LENI_PN_FMT:                     "FPK" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.LENI48G_PN_FMT:                  "FPK" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.MALFA_PN_FMT:                    "PFP" + FLX_SN_SUFFIX_FMT + "|" + "FPF" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.POLLARA_PN_FMT:                  "FPL" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.POLLARA_HPE_PN_FMT:              HPE_SN_FMT,
        PART_NUMBERS_MATCH.GELSOP_PN_FMT:                   "serialnumber" + r"(?:[1-9]|10)",
        PART_NUMBERS_MATCH.LINGUA_PN_FMT:                   "FPM" + FLX_SN_SUFFIX_FMT,
        "DEFAULT":                                          "FPF" + FLX_SN_SUFFIX_FMT
    },
    Factory.FSP: {
        PART_NUMBERS_MATCH.N25_HPE_PN_FMT:          HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_HPE_PN_FMT:         HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_HPE_CLD_PN_FMT:     HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT:  HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT:      HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT:  HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_TAA_PN_FMT:  HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_OCP_HPE_PN_FMT:      HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_OCP_HPE_CLD_PN_FMT:  HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.LACONA32_PN_FMT:         HPE_FSP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT:      "MYFLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + "MY" + DELL_PPID_PART_NUM_FMT + "FLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT,
        PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT:     "MYFLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + "MY" + DELL_PPID_PART_NUM_FMT + "FLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT:   "FPA" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_MSFT_PN_FMT:  "FPA" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT:   "FPA" + FLX_SN_SUFFIX_FMT,
        PART_NUMBERS_MATCH.ORTANO2INTERP_ORC_PN_FMT:"FPB" + FLX_SN_SUFFIX_FMT,
        "DEFAULT":                                  "FPN" + FLX_SN_SUFFIX_FMT
    },
    Factory.MILPITAS: {
        PART_NUMBERS_MATCH.N25_HPE_PN_FMT:          HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_HPE_PN_FMT:         HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N100_HPE_CLD_PN_FMT:     HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT:  HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT:      HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT:  HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_SWM_HPE_TAA_PN_FMT:  HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_OCP_HPE_PN_FMT:      HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.N25_OCP_HPE_CLD_PN_FMT:  HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.LACONA32_PN_FMT:         HPE_MILP_SN_FMT + HPE_SUFFIX_FMT,
        PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT:      "USFLUPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + "US" + DELL_PPID_PART_NUM_FMT + "FLUPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT,
        PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT:     "USFLUPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + "|" + "US" + DELL_PPID_PART_NUM_FMT + "FLUPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT,
        "DEFAULT":                                  "FLM" + FLX_SN_SUFFIX_FMT
    }
}

PN_FORMAT_TABLE = {
    NIC_Type.NAPLES100: [
        PART_NUMBERS_MATCH.N100_PEN_PN_FMT,                     #68-0003-01 01    NAPLES100 PENSANDO
        PART_NUMBERS_MATCH.N100_NET_PN_FMT                      #111-05363        NAPLES100 NETAPP
        ],
    NIC_Type.NAPLES100IBM: [
        PART_NUMBERS_MATCH.N100_IBM_PN_FMT                      #68-0013-01 03    NAPLES100 IBM
        ],
    NIC_Type.NAPLES100HPE: [
        PART_NUMBERS_MATCH.N100_HPE_PN_FMT,                     #P37692-001       NAPLES100 HPE
        PART_NUMBERS_MATCH.N100_HPE_CLD_PN_FMT                  #P41854-001       NAPLES100 HPE CLOUD
        ],
    NIC_Type.NAPLES100DELL: [
        PART_NUMBERS_MATCH.N100_DELL_PN_FMT                     #68-0024-01 XX    NAPLES100 DELL
        ],

    NIC_Type.NAPLES25: [
        PART_NUMBERS_MATCH.N25_PEN_PN_FMT,                      #68-0005-03 XX    NAPLES25 PENSANDO
        PART_NUMBERS_MATCH.N25_HPE_PN_FMT,                      #P18669-001       NAPLES25 HPE
        PART_NUMBERS_MATCH.N25_EQI_PN_FMT                       #68-0008-xx yy    NAPLES25 EQUINIX
        ],
    NIC_Type.NAPLES25SWM: [
        PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT,              #P26968-001       NAPLES25 SWM HPE
        PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT,                  #P26968-002       NAPLES25 SWM HPE
        PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT,              #P41851-001       NAPLES25 SWM HPE CLOUD
        PART_NUMBERS_MATCH.N25_SWM_HPE_TAA_PN_FMT,              #P46653-001       NAPLES25 SWM HPE TAA
        PART_NUMBERS_MATCH.N25_SWM_PEN_PN_FMT,                  #68-0016-01 XX    NAPLES25 SWM PENSANDO
        PART_NUMBERS_MATCH.N25_SWM_PEN_TAA_PN_FMT,              #68-0017-01 XX    NAPLES25 SWM PENSANDO TAA
        PART_NUMBERS_MATCH.ALOM_HPE_PN_FMT                      #P26971-001       NAPLES25 SWM HPE ALOM ADAPTER
        ],
    NIC_Type.NAPLES25SWMDELL: [
        PART_NUMBERS_MATCH.N25_SWM_DEL_PN_FMT                   #68-0014-01 XX    NAPLES25 SWM DELL
        ],
    NIC_Type.NAPLES25SWM833: [
        PART_NUMBERS_MATCH.N25_SWM_833_PN_FMT                   #68-0019-01 XX    NAPLES25 SWM 833
        ],

    NIC_Type.NAPLES25OCP: [
        PART_NUMBERS_MATCH.N25_OCP_PEN_PN_FMT,                  #68-00xx-xx       NAPLES25 OCP PENSANDO
        PART_NUMBERS_MATCH.N25_OCP_HPE_PN_FMT,                  #P37689-001       NAPLES25 OCP HPE
        PART_NUMBERS_MATCH.N25_OCP_HPE_CLD_PN_FMT,              #P41857-001       NAPLES25 OCP HPE CLOUD
        PART_NUMBERS_MATCH.N25_OCP_DEL_PN_FMT                   #68-0010-01       NAPLES25 OCP DELL
        ],

    NIC_Type.FORIO: [
        PART_NUMBERS_MATCH.FORIO_PN_FMT                         #68-0007-01 XX    FORIO
        ],
    NIC_Type.VOMERO: [
        PART_NUMBERS_MATCH.VOMERO_PN_FMT                        #68-0009-01 XX    VOMERO
        ],
    NIC_Type.VOMERO2: [
        PART_NUMBERS_MATCH.VOMERO2_PN_FMT                       #68-0011-01 XX    VOMERO2
        ],

    NIC_Type.ORTANO: [
        PART_NUMBERS_MATCH.ORTANO_PN_FMT                        #68-0015-01 XX    ORTANO1
        ],
    NIC_Type.ORTANO2: [
        PART_NUMBERS_MATCH.ORTANO2_ORC_PN_FMT,                  #68-0015-02 XX    ORTANO2 ORACLE
        PART_NUMBERS_MATCH.ORTANO2_PEN_PN_FMT                   #68-0021-02 XX    ORTANO2 MICROSOFT
        ],
    NIC_Type.ORTANO2ADI: [
        PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT                #68-0026-01 XX    ORTANO2ADI ORACLE
        ],
    NIC_Type.ORTANO2ADIMSFT: [
        PART_NUMBERS_MATCH.ORTANO2ADI_MSFT_PN_FMT               #68-0034-01 XX    ORTANO2ADI MICROSOFT
        ],
    NIC_Type.ORTANO2ADIIBM: [
        PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT                #68-0028-01 XX    ORTANO2ADI IBM
        ],
    NIC_Type.ORTANO2INTERP: [
        PART_NUMBERS_MATCH.ORTANO2INTERP_ORC_PN_FMT             #68-0029-01 XX    ORTANO2 Interposer
        ],
    NIC_Type.POMONTEDELL: [
        PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT                   #0PCFPC X/A       POMONTE DELL
        ],
    NIC_Type.LACONA32DELL: [
        PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT                  #0X322F X/A       LACONA32 DELL
        ],
    NIC_Type.LACONA32: [
        PART_NUMBERS_MATCH.LACONA32_PN_FMT                      #P47930-001       LACONA32 HPE
        ],
    NIC_Type.ORTANO2ADICR: [
        PART_NUMBERS_MATCH.ORTANO2ADI_CR_PN_FMT                 #68-0049-03 XX    ORTANO2ADI CR
        ],
    NIC_Type.ORTANO2ADICRMSFT: [
        PART_NUMBERS_MATCH.ORTANO2ADI_CR_MSFT_PN_FMT            #68-0091-01 XX    ORTANO2ADI CR MICROSOFT
        ],
    NIC_Type.ORTANO2SOLO: [
        PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_PN_FMT               #68-0077-01 A0    ORTANO2 SOLO
        ],
    NIC_Type.ORTANO2SOLOL: [
        PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_L_PN_FMT             #68-0095-01 A0    ORTANO2 SOLO-L
        ],
    NIC_Type.ORTANO2SOLOORCTHS: [
        PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_THS_PN_FMT           #68-0089-01 A0    ORTANO2 SOLO Oracle Tall Heat Sink
        ],
    NIC_Type.ORTANO2SOLOMSFT: [
        PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT              #68-0090-01 A0    ORTANO2 SOLO MICROSOFT
        ],
    NIC_Type.ORTANO2SOLOS4: [
        PART_NUMBERS_MATCH.ORTANO2SOLO_S4_PN_FMT                #68-0092-01 A0    ORTANO2 SOLO S4
        ],
    NIC_Type.ORTANO2ADICRS4: [
        PART_NUMBERS_MATCH.ORTANO2ADI_CR_S4_PN_FMT              #68-0092-01 A0    ORTANO2ADI CR S4
        ],
    NIC_Type.GINESTRA_D4: [
        PART_NUMBERS_MATCH.GINESTRA_D4_PN_FMT                   #68-0074-01 01    GINESTRA_D4
        ],
    NIC_Type.GINESTRA_D5: [
        PART_NUMBERS_MATCH.GINESTRA_D5_PN_FMT                   #68-0075-01 01    GINESTRA_D5
        ],
    NIC_Type.GINESTRA_S4: [
        PART_NUMBERS_MATCH.GINESTRA_S4_PN_FMT                   #68-0076-01 01    GINESTRA_S4
        ],
    NIC_Type.GINESTRA_CIS: [
        PART_NUMBERS_MATCH.GINESTRA_CIS_PN_FMT                  #68-0094-01 01    GINESTRA_CIS
        ],
    NIC_Type.LENI: [
        PART_NUMBERS_MATCH.LENI_PN_FMT                          #102-P10800-00B   LENI
        ],
    NIC_Type.LENI48G: [
        PART_NUMBERS_MATCH.LENI48G_PN_FMT                       #102-P10801-00B   LENI48G
        ],
    NIC_Type.POLLARA: [
        PART_NUMBERS_MATCH.POLLARA_PN_FMT,                      #102-P11100-00    POLLARA
        PART_NUMBERS_MATCH.POLLARA_HPE_PN_FMT,                  #102-P11101-00    POLLARA HPE
        PART_NUMBERS_MATCH.POLLARA_DELL_PN_FMT                  #0745T9 X/A       POLLARA DELL
        ],
    NIC_Type.LINGUA: [
        PART_NUMBERS_MATCH.LINGUA_PN_FMT                        #102-P11500-00    LINGUA
        ],
    NIC_Type.MALFA: [
        PART_NUMBERS_MATCH.MALFA_PN_FMT                         #102-P10600-0 01    MALFA
        ],
    NIC_Type.GELSOP: [
        PART_NUMBERS_MATCH.GELSOP_PN_FMT                        #101-P00001-001    GELSOP
        ]
}

def get_product_name_from_pn_and_sn(pn, sn=""):
    if "DSC2-2Q200-32R32F64P-R3" in pn:
        product_name = NIC_Type.ORTANO2INTERP
    elif "DSC2-2Q200-32R32F64P-M2" in pn:
        product_name = NIC_Type.ORTANO2ADIMSFT
    elif "DSC2-2Q200-32R32F64P-B" in pn:
        product_name = NIC_Type.ORTANO2ADIIBM
    elif "DSC2-2Q200-32R32F64P-R2" in pn:
        product_name = NIC_Type.ORTANO2ADI
    elif "DSC2-2Q200-32R32F64P-R4" in pn:
        product_name = NIC_Type.ORTANO2SOLO
        if "DSC2-2Q200-32R32F64P-R4-T" in pn:
            product_name = NIC_Type.ORTANO2SOLOORCTHS
        if "DSC2-2Q200-32R32F64P-R4-L" in pn:
            product_name = NIC_Type.ORTANO2SOLOL
    elif "DSC2-2Q200-32R32F64P-R5" in pn:
        product_name = NIC_Type.ORTANO2ADICR
    elif "DSC2-2Q200-32R32F64P-R" in pn:
        product_name = NIC_Type.ORTANO2
    elif "DSC2-2Q200-32R32F64P-M5" in pn:
        product_name = NIC_Type.ORTANO2ADICRMSFT
    elif "DSC2-2Q200-32R32F64P-M4" in pn:
        product_name = NIC_Type.ORTANO2SOLOMSFT
    elif "68-0092-01" in pn:
        product_name = NIC_Type.ORTANO2SOLOS4 if sn[:3].upper() == "FPF" else NIC_Type.ORTANO2ADICRS4
    elif "DSC2-2Q200-32R32F64P-S4" in pn:
        product_name = NIC_Type.ORTANO2SOLOS4 if sn[:3].upper() == "FPF" else NIC_Type.ORTANO2ADICRS4
    elif "DSC2-2Q200-32R32F64P" in pn:
        product_name = NIC_Type.ORTANO2
    elif "68-0015-02" in pn:
        product_name = NIC_Type.ORTANO2
    elif "68-0021-02" in pn:
        product_name = NIC_Type.ORTANO2
    elif "0X322F" in pn:
        product_name = NIC_Type.LACONA32DELL
    elif "0W5WGK" in pn:
        product_name = NIC_Type.LACONA32DELL
    elif "0PCFPC" in pn:
        product_name = NIC_Type.POMONTEDELL
    elif "P47928" in pn:
        product_name = NIC_Type.LACONA32
    elif "P47930" in pn:
        product_name = NIC_Type.LACONA32
    elif "68-0026-01" in pn:
        product_name = NIC_Type.ORTANO2ADI
    elif "68-0028-01" in pn:
        product_name = NIC_Type.ORTANO2ADIIBM
    elif "68-0034-01" in pn:
        product_name = NIC_Type.ORTANO2ADIMSFT
    elif "68-0049-03" in pn:
        product_name = NIC_Type.ORTANO2ADICR
    elif "68-0091-01" in pn:
        product_name = NIC_Type.ORTANO2ADICRMSFT
    elif "68-0029-01" in pn:
        product_name = NIC_Type.ORTANO2INTERP
    elif "68-0074-01" in pn:
        product_name = NIC_Type.GINESTRA_D4
    elif "DSC2A-2Q200-32R32F64P-R" in pn:
        product_name = NIC_Type.GINESTRA_D4
    elif "68-0075-01" in pn or "68-0075-02" in pn:
        product_name = NIC_Type.GINESTRA_D5
    elif "DSC2A-2Q200-32S32F64P-R" in pn:
        product_name = NIC_Type.GINESTRA_D5
    elif "68-0076-" in pn:
        product_name = NIC_Type.GINESTRA_S4
    elif "DSC2A-2Q200-32S32F64P-S4" in pn:
        product_name = NIC_Type.GINESTRA_S4
    elif "68-0094-" in pn:
        product_name = NIC_Type.GINESTRA_CIS
    elif "30-100365-" in pn:
        product_name = NIC_Type.GINESTRA_CIS
    elif "68-0077-01" in pn:
        product_name = NIC_Type.ORTANO2SOLO
    elif "68-0095-01" in pn:
        product_name = NIC_Type.ORTANO2SOLOL
    elif "68-0013-01" in pn:
        product_name = NIC_Type.NAPLES100IBM
    elif "P26968" in pn:
        product_name = NIC_Type.NAPLES25SWM
    elif "P26966-B21" in pn:
        product_name = NIC_Type.NAPLES25SWM
    elif "68-0014-01" in pn:
        product_name = NIC_Type.NAPLES25SWMDELL
    elif "P37689" in pn:
        product_name = NIC_Type.NAPLES25OCP
    elif "P37687" in pn:
        product_name = NIC_Type.NAPLES25OCP
    elif "68-0010" in pn:
        product_name = NIC_Type.NAPLES25OCP
    elif "DSC1-2S25-4P8P-DS" in pn:
        product_name = NIC_Type.NAPLES25OCP
    elif "DSC1-2S25-4H8P-DS" in pn:
        product_name = NIC_Type.NAPLES25SWMDELL
    elif "DSC1-2S25-4H8P-SL" in pn:
        product_name = NIC_Type.UNKNOWN
    elif "DSC1-2S25-4H8P-ST" in pn:
        product_name = NIC_Type.UNKNOWN
    elif "DSC1-2S25-4H8P-S" in pn:
        product_name = NIC_Type.NAPLES25SWM
    elif "111-05363" in pn:
        product_name = NIC_Type.NAPLES100
    elif "68-0003" in pn:
        product_name = NIC_Type.NAPLES100
    elif "68-0089-01" in pn:
        product_name = NIC_Type.ORTANO2SOLOORCTHS
    elif "68-0090-01" in pn:
        product_name = NIC_Type.ORTANO2SOLOMSFT
    elif "POLLARA-1Q400P-OCP" in pn:
        product_name = NIC_Type.LINGUA
    elif "102-P11500-" in pn:
        product_name = NIC_Type.LINGUA
    elif "102-P11100-" in pn:
        product_name = NIC_Type.POLLARA
    elif "102-P11101-" in pn:
        product_name = NIC_Type.POLLARA
    elif "POLLARA-1Q400P" in pn:
        product_name = NIC_Type.POLLARA
    elif "AI-NIC400-1Q400-P" in pn:
        product_name = NIC_Type.POLLARA
    elif "102-P10801" in pn:
        product_name = NIC_Type.LENI48G
    elif "DSC3-2Q400-48R64E64P" in pn:
        product_name = NIC_Type.LENI48G
    elif "102-P10800" in pn:
        product_name = NIC_Type.LENI
    elif "DSC3-2Q400-64S64E64P" in pn:
        product_name = NIC_Type.LENI
    elif "DSC3-2Q400-64R64E64P-O" in pn:
        product_name = NIC_Type.LENI
    else:
        product_name = NIC_Type.UNKNOWN

    return product_name
