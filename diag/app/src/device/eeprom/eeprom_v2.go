package eeprom

import (
    "fmt"
    "os"
    "bytes"
    "time"
    "strconv"
    "strings"
    "common/cli"
    "common/errType"
    "common/misc"
    "encoding/binary"
    "protocol/smbusNew"
    "device/fpga/materafpga"
    "device/sucuart"
    "hardware/i2cinfo"
    "hardware/hwinfo"
)

//New card PNs can be added here
const (
    //General purpose constants
    MAX_BYTES           int = 512
    MRA_HDR_LEN         int = 5
    CHDR_LEN            int = 8
    BRD_INFO_AREA_LEN   int = 6
    PROD_INFO_AREA_LEN  int = 3
    OFFSET_NORM_FACTOR  int = 8
    ZERO_START          int = 0
    DELAYED_START       int = 256
    SHORT_FORM          string = "2006-01-02"

    //Attribute constants
    MAC_LEN             int = 12
    MFG_DATE_LEN        int = 3
    DPN_LEN             int = 10

    //Profinfo data structure constants
    FIELD_NUM_NONE          int = 0xFFFF
    FIELD_NUM_SN_3          int = 3
    FIELD_NUM_SN_5          int = 5
    FIELD_NUM_PN_4          int = 4
    FIELD_NUM_PN_10         int = 10
    FIELD_NUM_MAC_9         int = 9
    FIELD_NUM_PROD_NAME_2   int = 2
    FIELD_NUM_SKU_4         int = 4
    FIELD_NUM_FRU_ID_5      int = 5
    FIELD_NUM_DPN_11        int = 11
    FIELD_NUM_PN_8          int = 8
    FIELD_NUM_SKU_3         int = 3
    FIELD_NUM_FRU_ID_7      int = 7
    FIELD_NUM_DPN_9         int = 9
    FIELD_NUM_BOARD_ID_6    int = 6


    //Field types; Area field number vs absolute byte offset
    FIELD_TYPE_NUM      int = 0
    FIELD_TYPE_BYTE     int = 1

    //FRU area definition
    AREA_TYPE_BOARD_INFO    int = 0
    AREA_TYPE_PRDT_INFO     int = 1
    AREA_TYPE_MRA_E1        int = 0xE1
    AREA_TYPE_MRA_E2        int = 0xE2
    AREA_TYPE_MRA_E6        int = 0xE6
    AREA_TYPE_MRA_C1        int = 0xC6

    //Supported board PNs
    PN_IBM           string = "68-0028"
    PN_ADI_MSFT      string = "68-0034"
    PN_SOLO_MSFT     string = "68-0090"
    PN_ADICR_MSFT    string = "68-0091"
    PN_SOLO_SSDK     string = "68-0092"
    PN_NETAPP_R2     string = "111-05363"
    PN_SOLO_ORACLE   string = "68-0077"
    PN_ADICR_ORACLE  string = "68-0049"
    PN_SR4T_ORACLE   string = "68-0089"
    PN_SR4L_ORACLE   string = "68-0095"
    PN_LIPARI_ELBA   string = "68-0032"
    PN_LIPARI        string = "68-0032-01"
    PN_LIPARI_SWITCH string = "73-0067-01"
    PN_LIPARI_CPUBRD string = "73-0068-01"
    PN_LIPARI_BMC    string = "73-0076-01"
    PN_GIN_D4_ORACLE string = "68-0074-01"
    PN_GIN_D5_ORACLE string = "68-0075"
    PN_GIN_D5_MSFT   string = "68-0087"
    PN_GIN_D5_SSDK   string = "68-0076"
    PN_GIN_D5_CISCO  string = "68-0094"
    PN_DESCHUTES     string = "73-21612-01"
    PN_MALFA         string = "102-P10600-00"
    PN_POLLARA       string = "102-P11100"
    PN_POLLARA_HPE   string = "102-P11101"
    PN_LENI          string = "102-P10800"
    PN_LENI48G       string = "102-P10801"
    PN_LINGUA        string = "102-P11500"
    PN_OCP_ADPT      string = "102-P11600"
    PN_MTP_MATERA_FRU  string = "102-P10300-00"
    PN_MTP_MATERA_MB   string = "102-P10300-00"
    PN_MTP_MATERA_IOB  string = "102-P10400-00"
    PN_MTP_MATERA_FPIC string = "102-P10500-00"
    PN_MTP_PANAREA_FRU  string = "102-P11700-00"
    PN_MTP_PANAREA_MB   string = "102-P11700-00"
    PN_MTP_PANAREA_IOB  string = "102-P11800-00"
    PN_MTP_PANAREA_FPIC string = "102-P11900-00"
    PN_GELSOP           string = "102-P12500"

    // Product name
    PROD_NAME_IBM           string = "Pensando DSC2-200 50/100/200G 2p QSFP56 Card"
    PROD_NAME_MSFT          string = "Pensando DSC2-200 50/100/200G 2p QSFP56 Card"
    PROD_NAME_SSDK          string = "Pensando DSC2-200 50/100/200G 2p QSFP56 Card"
    PROD_NAME_NETAPP_R2     string = "NAPLES 100, NetApp, R2"
    PROD_NAME_ORACLE        string = "Pensando DSC2-200 50/100/200G 2p QSFP56 Card"
    PROD_NAME_LIPARI_ELBA   string = "AMD DSS-28800"
    PROD_NAME_GIG_ORACLE    string = "Pensando DSC2A-200 50/100/200G 2p QSFP56 Card"
    PROD_NAME_GIG_MSFT      string = "Pensando DSC2A-200 50/100/200G 2p QSFP56 Card"
    PROD_NAME_GIG_SSDK      string = "Giglio 2x200G QSFP56"
    PROD_NAME_GIG_SSDK_CISCO string = "Giglio 2x200G QSFP56 SUP C"
    PROD_NAME_DESCHUTES     string = "DSS-DESCHUTES"
    PROD_NAME_MALFA         string = "Salina 2x400G QSFP112"
    PROD_NAME_POLLARA       string = "POLLARA 1x400G QSFP112"
    PROD_NAME_LENI          string = "Salina 2x400G QSFP112"
    PROD_NAME_LINGUA        string = "POLLARA, single QSFP112, OCP 3.0"
    PROD_NAME_OCP_ADPT      string = "OCP ADAPTOR"
    PROD_NAME_GELSOP        string = "VULCANO-1O800 100/200/400/800G 1p OSFP224 Card"

    // SKU 
    SKU_IBM             string = "DSC2-2Q200-32R32F64P-B"
    SKU_ADI_MSFT        string = "DSC2-2Q200-32R32F64P-M2"
    SKU_SOLO_MSFT       string = "DSC2-2Q200-32R32F64P-M4"
    SKU_ADICR_MSFT      string = "DSC2-2Q200-32R32F64P-M5"
    SKU_SOLO_SSDK       string = "DSC2-2Q200-32R32F64P-S4"
    SKU_NETAPP_R2       string = "NA"
    SKU_SOLO_ORACLE     string = "DSC2-2Q200-32R32F64P-R4"
    SKU_SR4L_ORACLE     string = "DSC2-2Q200-32R32F64P-R4-L"
    SKU_ADICR_ORACLE    string = "DSC2-2Q200-32R32F64P-R5"
    SKU_SR4T_ORACLE     string = "DSC2-2Q200-32R32F64P-R4-T"
    SKU_LIPARI_ELBA     string = "DSS-28800"
    SKU_GIN_D4_ORACLE   string = "DSC2A-2Q200-32R32F64P-R"
    SKU_GIN_D5_ORACLE   string = "DSC2A-2Q200-32S32F64P-R"
    SKU_GIN_D5_MSFT     string = "DSC2A-2Q200-32S32F64P-M"
    SKU_GIN_D5_SSDK     string = "DSC2A-2Q200-32S32F64P-S4"
    SKU_GIN_D5_SSDK_B3  string = "DSC2A-2Q200-32S32F64P-S4-B3"
    SKU_GIN_D5_SSDK_P3  string = "DSC2A-2Q200-32S32F64P-S4-P3"
    SKU_GIN_D5_SSDK_A   string = "DSC2A-2Q200-32S32F64P-S4A"
    SKU_GIN_D5_SSDK_B   string = "DSC2A-2Q200-32S32F64P-S4B"
    SKU_GIN_D5_SSDK_C   string = "DSC2A-2Q200-32S32F64P-S4C"
    SKU_GIN_D5_SSDK_CISCO  string = "DSC2A-2Q200-32S32F64P-S4-C"
    SKU_DESCHUTES       string = "DSS-DESCHUTES"
    SKU_MALFA           string = "DSC3-2Q400-128S64E256P"
    SKU_POLLARA         string = "POLLARA-1Q400P"
    SKU_POLLARA_ORACLE  string = "POLLARA-1Q400P-O"
    SKU_POLLARA_DELL    string = "POLLARA-1Q400P-D"
    SKU_POLLARA_HPE     string = "POLLARA-1Q400P-H"
    SKU_LENI            string = "DSC3-2Q400-64S64E64P"
    SKU_LENI_ORACLE     string = "DSC3-2Q400-64R64E64P-O"
    SKU_LENI48G         string = "DSC3-2Q400-48R64E64P"
    SKU_LINGUA          string = "POLLARA-1Q400P-OCP"
    SKU_OCP_ADPT        string = "DSC3-2Q400-48R64E64P"
    SKU_GELSOP          string = "100-700000001"

    // FRU ID
    FRU_ID_IBM           string = "06/28/22"
    FRU_ID_ADI_MSFT      string = "09/29/22"
    FRU_ID_SOLO_MSFT     string = "05/02/23"
    FRU_ID_ADICR_MSFT    string = "05/02/23"
    FRU_ID_SOLO_SSDK     string = "05/02/23"
    FRU_ID_NETAPP_R2     string = "09/30/22"
    FRU_ID_ADICR_ORACLE  string = "11/18/22"
    FRU_ID_SOLO_ORACLE   string = "11/18/22"
    FRU_ID_SR4T_ORACLE   string = "05/02/23"
    FRU_ID_SR4L_ORACLE   string = "09/24/25"
    FRU_ID_LIPARI_ELBA   string = "12/01/22"
    FRU_ID_GIN_D4        string = "01/24/23"
    FRU_ID_GIN_D5        string = "01/24/23"
    FRU_ID_GIN_D5_MSFT   string = "01/19/24"
    FRU_ID_GIN_D5_SSDK   string = "02/26/24"
    FRU_ID_GIN_D5_SSDK_CISCO   string = "07/11/24"
    FRU_ID_DESCHUTES     string = "07/11/24"
    FRU_ID_MALFA         string = "06/25/24"
    FRU_ID_POLLARA       string = "07/18/24"
    FRU_ID_LENI          string = "07/18/24"
    FRU_ID_LINGUA        string = "02/04/25"
    FRU_ID_OCP_ADPT      string = "02/24/25"
    FRU_ID_GELSOP        string = "09/26/25"

    // Byte offset
    BYTE_OFFSET_SN_ORACLE      int = 5
)

type progInfo struct {
    fieldType   int
    areaCode    int
    sn          int
    pn          int
    mac         int
    prodName    int
    sku         int
    fruId       int
    dpn         int
    boardID     int
}

type fieldInfo struct {
    offset  int
    value   []byte
}

type updateInfo struct {
    tbl         []entry
    prodName    string
    sku         string //PN is stored in this field for SKU type cards
    fruId       string
    info        []progInfo
    ext         []fieldInfo
}

type card struct {
    Name    string
    pn      string
}

// Ortano Solo PCIe subsystem ID
var soloOracleExt = []fieldInfo {
    fieldInfo { 94, []byte{0x0d}, },
    fieldInfo { 104, []byte{0x00, 0x5F}, },
    fieldInfo { 106, []byte{0x00, 0x64}, },
}

// Ortano ADI CR PCIe subsystem ID
var adicrOracleExt = []fieldInfo {
    fieldInfo { 94, []byte{0x0e}, },
    fieldInfo { 104, []byte{0x00, 0x5F}, },
    fieldInfo { 106, []byte{0x00, 0x64}, },
}

// Ortano Solo R4T PCIe subsystem ID
var sR4TOracleExt = []fieldInfo {
    fieldInfo { 94, []byte{0x0f}, },
    fieldInfo { 104, []byte{0x00, 0x5F}, },
    fieldInfo { 106, []byte{0x00, 0x64}, },
}

// Ginestra_D4 PCIe subsystem ID
var ginestraD4OracleExt = []fieldInfo {
    fieldInfo { 94, []byte{0x00, 0x51}, },
}

// Ginestra_D5 PCIe subsystem ID
var ginestraD5OracleExt = []fieldInfo {
    fieldInfo { 94, []byte{0x01, 0x51}, },
}

// Lipari Elba number of MAC address
var lipariElbaExt = []fieldInfo {
    fieldInfo { 125, []byte{0x10}, },
}

type entryinfo struct {
	Name     string
	DataType int
	Offset   int
	NumBytes int
}

//Part_number/SKU and data location maps
var CardDataInfo = map[string]updateInfo {
    PN_IBM: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_IBM,
        SKU_IBM,
        FRU_ID_IBM,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },
    PN_ADI_MSFT: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_MSFT,
        SKU_ADI_MSFT,
        FRU_ID_ADI_MSFT,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },
    PN_SOLO_MSFT: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_MSFT,
        SKU_SOLO_MSFT,
        FRU_ID_SOLO_MSFT,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },
    PN_ADICR_MSFT: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_MSFT,
        SKU_ADICR_MSFT,
        FRU_ID_ADICR_MSFT,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },
    PN_SOLO_SSDK: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_SSDK,
        SKU_SOLO_SSDK,
        FRU_ID_SOLO_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },
    // NetApp SKU goes alone with assembly number
    PN_NETAPP_R2: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_NETAPP_R2,
        SKU_NETAPP_R2,
        FRU_ID_NETAPP_R2,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_NONE,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_NONE,
                FIELD_NUM_SKU_4,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },

        },
        nil,
    },
    PN_SOLO_ORACLE: updateInfo {
        OrtanoOracleTbl,
        PROD_NAME_ORACLE,
        SKU_SOLO_ORACLE,
        FRU_ID_SOLO_ORACLE,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
            progInfo {
                FIELD_TYPE_BYTE,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        soloOracleExt,
    },
    PN_SR4L_ORACLE: updateInfo {
        OrtanoOracleTbl,
        PROD_NAME_ORACLE,
        SKU_SR4L_ORACLE,
        FRU_ID_SR4L_ORACLE,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
            progInfo {
                FIELD_TYPE_BYTE,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        soloOracleExt,
    },
    PN_ADICR_ORACLE: updateInfo {
        OrtanoOracleTbl,
        PROD_NAME_ORACLE,
        SKU_ADICR_ORACLE,
        FRU_ID_ADICR_ORACLE,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
            progInfo {
                FIELD_TYPE_BYTE,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        adicrOracleExt,
    },
    PN_SR4T_ORACLE: updateInfo {
        OrtanoOracleTbl,
        PROD_NAME_ORACLE,
        SKU_SR4T_ORACLE,
        FRU_ID_SR4T_ORACLE,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
            progInfo {
                FIELD_TYPE_BYTE,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        sR4TOracleExt,
    },
    PN_LIPARI_ELBA: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_LIPARI_ELBA,
        SKU_LIPARI_ELBA,
        FRU_ID_LIPARI_ELBA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        lipariElbaExt,
    },
    //keep for backward compatibility
    PN_GIN_D5_ORACLE: updateInfo {
        OrtanoOracleTbl,
        PROD_NAME_GIG_ORACLE,
        SKU_GIN_D5_ORACLE,
        FRU_ID_GIN_D5,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
            progInfo {
                FIELD_TYPE_BYTE,
                AREA_TYPE_PRDT_INFO,
                BYTE_OFFSET_SN_ORACLE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        ginestraD5OracleExt,
    },

    PN_GIN_D5_MSFT: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_GIG_MSFT,
        SKU_GIN_D5_MSFT,
        FRU_ID_GIN_D5_MSFT,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },
    //programmed before SWI
    PN_GIN_D5_SSDK: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_GIG_SSDK,
        SKU_GIN_D5_SSDK,
        FRU_ID_GIN_D5_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },
    //programmed after SWI
    /*
    SKU_GIN_D4_ORACLE: updateInfo {
        OrtanoOracleTbl,
        PROD_NAME_GIG_COMMON,
        PN_GIN_D4_ORACLE,
        FRU_ID_GIN_D4,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                },
            progInfo {
                FIELD_TYPE_BYTE,
                AREA_TYPE_PRDT_INFO,
                BYTE_OFFSET_SN_ORACLE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        ginestraD4OracleExt,
    },
    SKU_GIN_D5_ORACLE: updateInfo {
        OrtanoOracleTbl,
        PROD_NAME_GIG_ORACLE,
        PN_GIN_D5_ORACLE,
        FRU_ID_GIN_D5,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                },
            progInfo {
                FIELD_TYPE_BYTE,
                AREA_TYPE_PRDT_INFO,
                BYTE_OFFSET_SN_ORACLE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        ginestraD5OracleExt,
    },

    SKU_GIN_D5_MSFT: updateInfo {
        OrtanoPenStandardTbl,
        PROD_NAME_GIG_MSFT,
        PN_GIN_D5_MSFT,
        FRU_ID_GIN_D5_MSFT,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                },
        },
        nil,
    },
    */

    SKU_GIN_D5_SSDK: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_GIG_SSDK,
        PN_GIN_D5_SSDK,
        FRU_ID_GIN_D5_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_GIN_D5_SSDK_B3: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_GIG_SSDK,
        PN_GIN_D5_SSDK,
        FRU_ID_GIN_D5_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_GIN_D5_SSDK_P3: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_GIG_SSDK,
        PN_GIN_D5_SSDK,
        FRU_ID_GIN_D5_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_GIN_D5_SSDK_A: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_GIG_SSDK,
        PN_GIN_D5_SSDK,
        FRU_ID_GIN_D5_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_GIN_D5_SSDK_B: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_GIG_SSDK,
        PN_GIN_D5_SSDK,
        FRU_ID_GIN_D5_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_GIN_D5_SSDK_C: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_GIG_SSDK,
        PN_GIN_D5_SSDK,
        FRU_ID_GIN_D5_SSDK,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_GIN_D5_CISCO: updateInfo {
        GinestraCiscoTbl,
        PROD_NAME_GIG_SSDK_CISCO,
        SKU_GIN_D5_SSDK_CISCO,
        FRU_ID_GIN_D5_SSDK_CISCO,
        []progInfo {
            progInfo {//board info
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_NONE,//Cisco PN to be added here, fixed for now
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_NONE,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_DESCHUTES: updateInfo {
        GinestraSSDKTbl,
        PROD_NAME_DESCHUTES,
        SKU_DESCHUTES,
        FRU_ID_DESCHUTES,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_MALFA: updateInfo {
        PenStandardV2Tbl,
        PROD_NAME_MALFA,
        SKU_MALFA,
        FRU_ID_MALFA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_MALFA: updateInfo {
        PenStandardV2Tbl,
        PROD_NAME_MALFA,
        SKU_MALFA,
        FRU_ID_MALFA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_POLLARA: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_POLLARA,
        SKU_POLLARA,
        FRU_ID_POLLARA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_POLLARA_HPE: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_POLLARA,
        SKU_POLLARA,
        FRU_ID_POLLARA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_POLLARA: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_POLLARA,
        SKU_POLLARA,
        FRU_ID_POLLARA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_POLLARA_ORACLE: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_POLLARA,
        SKU_POLLARA_ORACLE,
        FRU_ID_POLLARA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_POLLARA_DELL: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_POLLARA,
        SKU_POLLARA_DELL,
        FRU_ID_POLLARA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_POLLARA_HPE: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_POLLARA,
        SKU_POLLARA_HPE,
        FRU_ID_POLLARA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_OCP_ADPT: updateInfo {
        PenStandardV2Tbl,
        PROD_NAME_OCP_ADPT,
        SKU_OCP_ADPT,
        FRU_ID_OCP_ADPT,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_LENI: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_LENI,
        SKU_LENI,
        FRU_ID_LENI,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_LENI: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_LENI,
        SKU_LENI,
        FRU_ID_LENI,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_LENI_ORACLE: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_LENI,
        SKU_LENI_ORACLE,
        FRU_ID_LENI,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_LENI48G: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_LENI,
        SKU_LENI48G,
        FRU_ID_LENI,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_LENI48G: updateInfo {
        //PenStandardV2NewTbl,
        PenStandardV2ProdInfoTbl,
        PROD_NAME_LENI,
        SKU_LENI48G,
        FRU_ID_LENI,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_LINGUA: updateInfo {
        PenStandardV2ocpProdInfoTbl,
        PROD_NAME_LINGUA,
        SKU_LINGUA,
        FRU_ID_LINGUA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_LINGUA: updateInfo {
        PenStandardV2ocpProdInfoTbl,
        PROD_NAME_LINGUA,
        SKU_LINGUA,
        FRU_ID_LINGUA,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_NONE,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    PN_GELSOP: updateInfo {
        PenStandardV2GelsoXProdInfoTbl,
        PROD_NAME_GELSOP,
        SKU_GELSOP,
        FRU_ID_GELSOP,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_BOARD_ID_6,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    SKU_GELSOP: updateInfo {
        PenStandardV2GelsoXProdInfoTbl,
        PROD_NAME_GELSOP,
        SKU_GELSOP,
        FRU_ID_GELSOP,
        []progInfo {
            progInfo {
                FIELD_TYPE_NUM,
                AREA_TYPE_BOARD_INFO,
                FIELD_NUM_SN_3,
                FIELD_NUM_PN_10,
                FIELD_NUM_MAC_9,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_4,
                FIELD_NUM_FRU_ID_5,
                FIELD_NUM_DPN_11,
                FIELD_NUM_BOARD_ID_6,
                },
            progInfo {//product info
                FIELD_TYPE_NUM,
                AREA_TYPE_PRDT_INFO,
                FIELD_NUM_SN_5,
                FIELD_NUM_PN_8,//Pensando PN
                FIELD_NUM_NONE,
                FIELD_NUM_PROD_NAME_2,
                FIELD_NUM_SKU_3,
                FIELD_NUM_FRU_ID_7,
                FIELD_NUM_NONE,
                FIELD_NUM_NONE,
                },
        },
        nil,
    },

    //PEN_PN: updateInfo{OrtanoPensandoTbl, []progInfo{progInfo{FIELD_TYPE_NUM, 
    //                                                    AREA_TYPE_BOARD_INFO, 
    //                                                    FIELD_NUM_SN_3, 
    //                                                    FIELD_NUM_PN_10, 
    //                                                    FIELD_NUM_MAC_9}}},
    // Example for multiple progInfo
    //TEST_PN:updateInfo{Lacona32DELLTbl, []progInfo{progInfo{FIELD_TYPE_NUM, 
    //    AREA_TYPE_BOARD_INFO, FIELD_NUM_SN_3, FIELD_NUM_PN_4, FIELD_NUM_MAC_9},
    //                                               progInfo{FIELD_TYPE_NUM, 
    //    AREA_TYPE_BOARD_INFO, FIELD_NUM_NONE, FIELD_NUM_PN_10, FIELD_NUM_NONE}}},
}

//Add PNs to table of accepted cards
var CardTypes = []card{
    card{"ORTANO-IBM",              PN_IBM},
    card{"ORTANO-ADI-MSFT",         PN_ADI_MSFT},
    card{"ORTANO-SOLO-MSFT",        PN_SOLO_MSFT},
    card{"ORTANO-ADICR-MSFT",       PN_ADICR_MSFT},
    card{"NETAPP-R2",               PN_NETAPP_R2},
    card{"ORTANO-SOLO_ORACLE",      PN_SOLO_ORACLE},
    card{"ORTANO-ADICR_ORACLE",     PN_ADICR_ORACLE},
    card{"ORTANO-SOLOR4T_ORACLE",   PN_SR4T_ORACLE},
    card{"ORTANO-SOLOR4T_ORACLE",   PN_SR4L_ORACLE},
    card{"ORTANO-SOLO_SSDK",        PN_SOLO_SSDK},
    //card{"ORTANO-GIN_D4_ORACLE",    PN_GIN_D4_ORACLE},
    card{"ORTANO-GIN_D5_ORACLE",    PN_GIN_D5_ORACLE},
    card{"ORTANO-GIN_D5_MSFT",      PN_GIN_D5_MSFT},
    //used in non SKU mode
    card{"ORTANO-GIN_D5_SSDK",      PN_GIN_D5_SSDK},
    card{"MALFA",                   PN_MALFA},
    card{"MALFA_SKU",               SKU_MALFA},
    card{"POLLARA",                 PN_POLLARA},
    card{"POLLARA_H",               PN_POLLARA_HPE},
    card{"POLLARA_SKU",             SKU_POLLARA},
    card{"POLLARA_ORACLE",          SKU_POLLARA_ORACLE},
    card{"POLLARA_DELL",            SKU_POLLARA_DELL},
    card{"POLLARA_HPE",             SKU_POLLARA_HPE},
    card{"LENI",                    PN_LENI},
    card{"LENI_SKU",                SKU_LENI},
    card{"LENI_SKU_ORACEL",         SKU_LENI_ORACLE},
    card{"LENI48G",                 PN_LENI48G},
    card{"LENI48G_SKU",             SKU_LENI48G},
    card{"LINGUA",                  PN_LINGUA},
    card{"LINGUA_SKU",              SKU_LINGUA},
    card{"OCP_ADPT",                PN_OCP_ADPT},
    card{"DESCHUTES",               PN_DESCHUTES},
    card{"GELSOP",                  PN_GELSOP},
    card{"GELSOP_SKU",              SKU_GELSOP},
    //SKU type cards: used in SKU mode
    //card{"GIN_D4_ORACLE",           SKU_GIN_D4_ORACLE},
    //card{"GIN_D5_ORACLE",           SKU_GIN_D5_ORACLE},
    //card{"GIN_D5_MSFT",             SKU_GIN_D5_MSFT},
    card{"GIN_D5_SSDK_CISCO",       PN_GIN_D5_CISCO},
    card{"GIN_D5_SSDK",             SKU_GIN_D5_SSDK},
    card{"GIN_D5_SSDK_B3",          SKU_GIN_D5_SSDK_B3},
    card{"GIN_D5_SSDK_P3",          SKU_GIN_D5_SSDK_P3},
    card{"GIN_D5_SSDK_A",           SKU_GIN_D5_SSDK_A},
    card{"GIN_D5_SSDK_B",           SKU_GIN_D5_SSDK_B},
    card{"GIN_D5_SSDK_C",           SKU_GIN_D5_SSDK_C},
                      }

var CardTypesAccessViaFpga = []cardDevPn{
    cardDevPn{"LIPARI",  "FRU",      PN_LIPARI_CPUBRD},
    cardDevPn{"LIPARI",  "FRU_CPU",      PN_LIPARI_CPUBRD},
    cardDevPn{"LIPARI",  "FRU_SWITCH",   PN_LIPARI_SWITCH},
}


//Data structure slices
var Data    []byte
var DataRaw []byte
var Info    []entryinfo

//==============================================================================
//                     G E N E R I C     F U N C T I O N S
//==============================================================================

func convertToByteTbl(pn string, skuMode bool) (err int){
    //Writes all entries of EepromTbl into new slices
    //Checks and sets EepromTbl based on the input part number
    found, partNum := CardInListNew(pn, skuMode)
    if found == true {
        EepromTbl = CardDataInfo[partNum].tbl
    } else {
        cli.Println("e", "ERROR: Card type not supported; failed to set EepromTbl")
        err = errType.FAIL
        return
    }
    //Writes tabl into data and info slices
    for i:=0;i<len(EepromTbl);i++ {
        Data = append(Data, EepromTbl[i].Value...)
        Info = append(Info, entryinfo{EepromTbl[i].Name, EepromTbl[i].DataType, EepromTbl[i].Offset, EepromTbl[i].NumBytes})
    }
    return
}

func checkCHdrStart() (int) {
    //Checks first 3 bytes for Oracle card . Oracle FRU has fixed starting bytes
    var OracleOrtano = []byte{0x00, 0x80, 0x02} //Oracle Ortano signature
    var chkSlice []byte
    for i:=0;i<3;i++ {
        chkSlice = append(chkSlice, Data[i])
    }
    if bytes.Equal(chkSlice, OracleOrtano) {
        return DELAYED_START
    }
    return ZERO_START
}

func getOffsetsCHdr(start int) (boardInfoOff int, productInfoOff int, multiRecordOff int, err int) {
    //Reads and returns area starting byte offsets
    if Data[start+1] != 0x00 || Data[start+2] != 0x00 {
        fmt.Printf("ERROR: common header Internal Use Area Offset and Chassis Area Offset not supported.\n")
        err = errType.FAIL
        return
    }
    boardInfoOff = (int(Data[start+3]) * OFFSET_NORM_FACTOR)
    productInfoOff = (int(Data[start+4]) * OFFSET_NORM_FACTOR)
    multiRecordOff = (int(Data[start+5]) * OFFSET_NORM_FACTOR)
    return
}

func findFieldOffset(start int, end int, fieldNum int, areaHdrLen int) (fieldOff int, fieldLen int, err int) {
    //WARNING: Function only works for board info area and product info area!
    //Multi Info Area does not have type/length field
    //Finds the offset annd length of a field based on the field offset
    if fieldNum < 1 {
        cli.Println("e", "ERROR: Invalid number of field.")
        err = errType.INVALID_PARAM
        return
    }
    //Checks if fieldNum > number of fields
    var len, totalNumberFields int
    for i:=start+areaHdrLen;i<end-1;i+=len+1 {
        len = int(Data[i] & 0x3F)
        totalNumberFields++
    }
    if totalNumberFields < fieldNum {
        cli.Printf("e", "ERROR: Field %d does not exist.", fieldNum)
        err = errType.FAIL
        return
    }
    //Finds field at offset
    var totalFields int = 0
    for i:=start+areaHdrLen;i<end-1;i+=fieldLen+1 {
        if totalFields == fieldNum {
            break
        }
        fieldOff = i+1
        fieldLen = int(Data[i] & 0x3F)
        totalFields+=1
    }
    return
}

func findPn(start int, end int, areaHdrLen int, sku_num int, pn_num int) (pn string, err int) {
    //Returns part number or assembly number and converts byte data to string
    var pnBytes []byte
    // first look for FIELD_NUM_SKU_4 which is SKU
    partNumOff, partNumLen, err := findFieldOffset(start, end, sku_num, areaHdrLen)
    if err != errType.SUCCESS {
        cli.Println("e", "ERROR: Failed to find part number offset.")
        return
    }
    pnBytes = Data[partNumOff:partNumOff+partNumLen]
    partNum := string(pnBytes) //in this case SKU is actually stored in partNum
    found, pn := CardInListNew(partNum, true)
    if (found == true) && (err == errType.SUCCESS) {
        return 
    }
    // if SKU is not found by CardInListNew, look for PN (Assembly Number)
    partNumOff, partNumLen, err = findFieldOffset(start, end, pn_num, areaHdrLen)
    pnBytes = Data[partNumOff:partNumOff+partNumLen]
    partNum = string(pnBytes)
    found, pn = CardInListNew(partNum, false)
    if (found == true) && (err == errType.SUCCESS) {
        return 
    } else {
        cli.Println("i", "Assembly number not found")
        err = errType.FAIL
        return
    }
}

func findPnBlind() (pn string, err int) {
    dataString := string(DataRaw[:])
    for _, card := range CardTypes {
        if strings.Contains(dataString, card.pn) {
            pn = card.pn
            return
        }
    }
    err = errType.PN_NOT_SUPPORT
    return
}

//unused function
func writeToTbl() {
    //Writes the values in Data back to EepromTbl
    for i:=0;i<len(EepromTbl);i++ {
        dataOffset := EepromTbl[i].Offset
        dataLen := EepromTbl[i].NumBytes
        EepromTbl[i].Value = Data[dataOffset:(dataOffset+dataLen)]
    }
}

//==============================================================================
//                  C H E C K     S U M     F U N C T I O N S
//==============================================================================

func chkSum(start int, length int) (chkSum byte) {
    //Generic Checksum function; returns checksum byte
    var sum uint
    for i:=0;i<length;i++ {
        sum += uint(Data[start+i])
    }
    chkSum = byte(0x100 - sum % 0x100)
    return
}


func mraChkSum(start int, mraOff int) {
    //Checks and returns multi-record area check sum with associated offsets
    var recordLen, recordStrt int 
    recordLen = int(Data[start+mraOff + 2])
    recordStrt = start+mraOff + 5
    Data[start+mraOff + 3] = chkSum(recordStrt, recordLen)
    Data[start+mraOff + 4] = chkSum(mraOff, (MRA_HDR_LEN - 1))
    return
}

func updateChkSum() {
    //Function to update all checksums
    //Offset and length variables
    var cHdrStrt int = checkCHdrStart()
    var boardInfoAreaOff, productInfoAreaOff, multiRecordAreaOff int 
    boardInfoAreaOff, productInfoAreaOff, multiRecordAreaOff, _ = getOffsetsCHdr(cHdrStrt)
    var boardInfoAreaLen int = int(Data[cHdrStrt+boardInfoAreaOff + 1]) * OFFSET_NORM_FACTOR
    var productInfoAreaLen int = int(Data[cHdrStrt+productInfoAreaOff + 1]) * OFFSET_NORM_FACTOR 
    //Check sum variable initialization
    var cHdrChkSum, boardInfoAreaChkSum, productInfoChkSum byte
    //Product and multi-record area Checksums calculated
    cHdrChkSum = chkSum(cHdrStrt, CHDR_LEN)
    boardInfoAreaChkSum = chkSum(cHdrStrt + boardInfoAreaOff, boardInfoAreaLen - 1)
    //Updates common header and board info area Checksums
    Data[cHdrStrt + CHDR_LEN - 1] = cHdrChkSum
    Data[cHdrStrt + boardInfoAreaOff + boardInfoAreaLen - 1] = boardInfoAreaChkSum
    //Product info area checksum and update
    if productInfoAreaOff != 0 {
        productInfoChkSum = chkSum(cHdrStrt + productInfoAreaOff, productInfoAreaLen - 1)
        Data[cHdrStrt + productInfoAreaOff + productInfoAreaLen - 1] = productInfoChkSum
    }
    //If the multi record area is present, finds and updates multi record area checksums here
    if multiRecordAreaOff != 0 {
        mraChkSum(cHdrStrt, cHdrStrt + multiRecordAreaOff)
    }
}

func updateFields(sn string, pn string, sku string, mac string, date string, dpn string, skuMode bool, boardID uint32) (err int) {
    //Updates serial number, part number, MAC address, and date in Data
    var snOff, snLen, pnOff, pnLen, macOff, macLen, dateOff, dateLen int
    var prodNameOff, prodNameLen, skuOff, skuLen, fruIdOff, fruIdLen, dpnOff, dpnLen, boardidOff, boardidLen int
    var skuField string
    var identifier string
    var areaOffset, areaLen, areaHdrLen int
    //Checks PN validity and sets card type
    if skuMode == true {
        identifier = sku
    } else {
        identifier = pn
    }
    found, minPN := CardInListNew(identifier, skuMode)
    if found != true {
        if skuMode == true {
            cli.Printf("e", "ERROR: Card SKU not supported")
        } else {
            cli.Printf("e", "ERROR: Card part number not supported")
        }
        return errType.FAIL
    }
    card := CardDataInfo[minPN]

    //Initial failure condition
    if (sn == "") || (pn == "") || ((skuMode == true) && (sku == "")) || (mac == "") || (date == "") {
        if (skuMode == true) {
            cli.Printf("e", "ERROR: Must have values for serial number, SKU, part number, MAC address, and date.\n")
        } else {
            cli.Printf("e", "ERROR: Must have values for serial number, part number, MAC address, and date.\n")
        }
        err = errType.INVALID_PARAM
        return 
    }

    //Converts MAC address to byte
    macByte := make([]byte, 6)
    data, _ := strconv.ParseUint(mac, 16, 64)
    macByte[0] = byte(data >> 40 & 0xFF)
    macByte[1] = byte(data >> 32 & 0xFF)
    macByte[2] = byte(data >> 24 & 0xFF)
    macByte[3] = byte(data >> 16 & 0xFF)
    macByte[4] = byte(data >> 8 & 0xFF)
    macByte[5] = byte(data & 0xFF)

    //Converts date into 3 hex values (month, day, year)
    var dateByte []byte
    month, day, year := date[:2], date[2:4], date[4:]
    formatDate := fmt.Sprintf("20%s-%s-%s", year, month, day)
    timeStart, _ := time.Parse(SHORT_FORM, "1996-01-01")
    timeEnd, _ := time.Parse(SHORT_FORM, formatDate)
    difference := timeEnd.Sub(timeStart)
    dateByte = append(dateByte, byte(int(difference.Minutes()) & 0xFF)) 
    dateByte = append(dateByte, byte((int(difference.Minutes()) >> 8) & 0xFF))
    dateByte = append(dateByte, byte((int(difference.Minutes()) >> 16) & 0xFF))

    //Converts SN and PN to byte & declares offset/length variables
    snByte := []byte(sn)
    pnByte := []byte(pn)

    prodNameByte:= []byte(card.prodName)
    if skuMode == true {
        //in skuMode, use the scanned SKU
        skuField = sku
    } else {
        skuField = card.sku
    }
    skuByte     := []byte(skuField)
    fruIdByte   := []byte(card.fruId)
    dpnByte     := []byte(dpn)

    //Find offset/Len of SN/PN/MAC/Date of each progInfo entry
    start := checkCHdrStart()
    boardInfoOffset, productInfoOffset, _, err := getOffsetsCHdr(start)
    if err != errType.SUCCESS {
        return
    }

    boardInfoLen := int(Data[start+boardInfoOffset+1]) * OFFSET_NORM_FACTOR
    productInfoLen := int(Data[start+productInfoOffset+1]) * OFFSET_NORM_FACTOR
    //Loops through card.info slice and updates each field
    for _, entry := range(card.info) {
        //SN, PN, MAC, and DATE offsets and locations
        //If NONE is found, provious offset and length will retain. Same field will be retained.
        //Same field will be updated.
        if entry.fieldType == FIELD_TYPE_BYTE {
            if entry.sn != FIELD_NUM_NONE {
                snOff = entry.sn
                snLen = len(sn)
            }
            if entry.pn != FIELD_NUM_NONE {
                pnOff = entry.pn
                pnLen = len(pn)
            }
            if entry.mac != FIELD_NUM_NONE {
                macOff = entry.mac
                macLen = MAC_LEN
            }
            if entry.prodName != FIELD_NUM_NONE {
                prodNameOff = entry.prodName
                prodNameLen = len(card.prodName)
            }
            if entry.sku != FIELD_NUM_NONE {
                skuOff = entry.sku
                skuLen = len(skuField)
            }
            if entry.fruId != FIELD_NUM_NONE {
                fruIdOff = entry.fruId
                fruIdLen = len(card.fruId)
            }
        } else {
            if entry.areaCode == AREA_TYPE_BOARD_INFO {
                areaOffset = boardInfoOffset
                areaLen = boardInfoLen
                areaHdrLen = BRD_INFO_AREA_LEN
            } else if entry.areaCode == AREA_TYPE_PRDT_INFO {
                areaOffset = productInfoOffset
                areaLen = productInfoLen
                areaHdrLen = PROD_INFO_AREA_LEN
            } else {
                cli.Println("e", "ERROR: Area code not supported yet.")
                return
			}
            if entry.sn != FIELD_NUM_NONE {
                snInt := entry.sn
                snOff, snLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, snInt, areaHdrLen)
            }
            if entry.pn != FIELD_NUM_NONE {
                pnInt := entry.pn
                pnOff, pnLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, pnInt, areaHdrLen)
            }
            if entry.mac != FIELD_NUM_NONE {
                macInt := entry.mac
                macOff, macLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, macInt, areaHdrLen)
            }
            if entry.prodName != FIELD_NUM_NONE {
                prodNameInt := entry.prodName
                prodNameOff, prodNameLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, prodNameInt, areaHdrLen)
            }
            if entry.sku != FIELD_NUM_NONE {
                skuInt := entry.sku
                skuOff, skuLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, skuInt, areaHdrLen)
            }
            if entry.fruId != FIELD_NUM_NONE {
                fruIdInt := entry.fruId
                fruIdOff, fruIdLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, fruIdInt, areaHdrLen)
            }
            if entry.dpn != FIELD_NUM_NONE {
                dpnInt := entry.dpn
                dpnOff, dpnLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, dpnInt, areaHdrLen)
            }
            if entry.boardID != FIELD_NUM_NONE {
                boardidInt := entry.boardID
                boardidOff, boardidLen, err = findFieldOffset(start+areaOffset, start+areaOffset+areaLen, boardidInt, areaHdrLen)
            }
        }

        //Sets date offset and length
        dateOff, dateLen = start+areaOffset+MFG_DATE_LEN, MFG_DATE_LEN

        //Returns error if previous step for finding offset and lengths fail
        if err != errType.SUCCESS {
            cli.Println("e", "ERROR: Failed to find correct offsets and field lengths.")
            return
        }

        //Error return if any of the update fields are empty
        var errField string
        if snOff == 0 {
            errField = "Serial Number"
            err = errType.FAIL
            cli.Printf("e", "ERROR: Specified update field empty; check card info slice/field: %s", errField)
            return
        } else if entry.fieldType == FIELD_TYPE_NUM && entry.areaCode != AREA_TYPE_BOARD_INFO && pnOff == 0 {
            errField = "Part Number"
            err = errType.FAIL
            cli.Printf("e", "ERROR: Specified update field empty; check card info slice/field: %s", errField)
            return
        } else if entry.fieldType == FIELD_TYPE_NUM && entry.areaCode != AREA_TYPE_BOARD_INFO && macOff == 0 {
            errField = "MAC Address"
            err= errType.FAIL
            cli.Printf("e", "ERROR: Specified update field empty; check card info slice/field: %s", errField)
            return
        }

        //Returns error if string longer than specified value
        if (
            (entry.sn != FIELD_NUM_NONE && len(sn) > snLen)                   ||
            (entry.pn != FIELD_NUM_NONE && len(pn) > pnLen)                   ||
            (entry.mac != FIELD_NUM_NONE && len(mac) != MAC_LEN)               ||
            (len(date) != (MFG_DATE_LEN*2))     ||
            (entry.prodName != FIELD_NUM_NONE && len(prodNameByte) > prodNameLen)   ||
            (entry.sku != FIELD_NUM_NONE && len(skuByte) > skuLen) ||
            (entry.dpn != FIELD_NUM_NONE && len(dpnByte) > dpnLen) ||
            (entry.fruId != FIELD_NUM_NONE && fruIdLen != 0 && len(fruIdByte) > fruIdLen) ) {
            err = errType.INVALID_PARAM
            var errorOutput string
            var maxLen, realLen int

            if len(date) != (2*MFG_DATE_LEN) {
                errorOutput = "Date"
                maxLen = 2*MFG_DATE_LEN
                realLen = len(date)
            } else if entry.sn != FIELD_NUM_NONE && len(sn) > snLen {
                errorOutput = "Serial Number"
                maxLen = snLen
                realLen = len(sn)
            } else if entry.pn != FIELD_NUM_NONE && len(pn) > pnLen {
                errorOutput = "Assembly Number"
                maxLen = pnLen
                realLen = len(pn)
            } else if entry.mac != FIELD_NUM_NONE && len(mac) != MAC_LEN {
                errorOutput = "MAC Address"
                maxLen = MAC_LEN
                realLen = len(mac)
            } else if entry.prodName != FIELD_NUM_NONE && len(prodNameByte) > prodNameLen {
                errorOutput = " Product Name"
                maxLen = prodNameLen
                realLen = len(prodNameByte)
            } else if entry.sku != FIELD_NUM_NONE && len(skuByte) > skuLen {
                errorOutput = "SKU"
                maxLen = skuLen
                realLen = len(skuByte)
            } else if entry.fruId != FIELD_NUM_NONE && fruIdLen != 0 && len(fruIdByte) > fruIdLen {
                errorOutput = "FRU ID"
                maxLen = fruIdLen
                realLen = len(fruIdByte)
            } else if entry.dpn != FIELD_NUM_NONE && len(dpnByte) > dpnLen {
                errorOutput = "Diagnostic Product Name"
                maxLen = dpnLen
                realLen = len(dpnByte)
            }
            cli.Printf("e", "ERROR: Input fields differ from specified lengths. Affected field(s): %s; expected: %d; got: %d", 
                errorOutput, maxLen, realLen)
            return
        }

        //Pads values if less than FRU specified length
        if entry.fieldType != FIELD_TYPE_BYTE {
            if (len(sn) < snLen) {
                for i:=len(snByte);i<snLen;i++ {
                    snByte=append(snByte, 0x20)
                }
            }
            if (len(pnByte) < pnLen) {
                for i:=len(pnByte);i<pnLen;i++ {
                    pnByte=append(pnByte, 0x20)
                }
            }
            if (len(prodNameByte) < prodNameLen) {
                for i:=len(prodNameByte);i<prodNameLen;i++ {
                    prodNameByte=append(prodNameByte, 0x20)
                }
            }
            if (len(skuByte) < skuLen) {
                for i:=len(skuByte);i<skuLen;i++ {
                    skuByte=append(skuByte, 0x20)
                }
            }
            if (len(fruIdByte) < fruIdLen) {
                for i:=len(fruIdByte);i<fruIdLen;i++ {
                    fruIdByte=append(fruIdByte, 0x20)
                }
            }
            if (len(dpnByte) < dpnLen) {
                for i:=len(dpnByte);i<dpnLen;i++ {
                    dpnByte=append(dpnByte, 0x20)
                }
            }
        }

        //Update Data slice (byte)
        var incrementVar int = 0
        for offset:=0;offset<len(Data);offset++ {
            if entry.areaCode == AREA_TYPE_BOARD_INFO {
                if offset == dateOff {
                    for i:=offset;i<offset+dateLen;i++ {
                        Data[i]=dateByte[incrementVar]
                        incrementVar++
                    }
                    incrementVar = 0
                }
            }
            if (offset == snOff) && (entry.sn != FIELD_NUM_NONE) {
                for i:=offset;i<offset+snLen;i++ {
                    Data[i]=snByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
            if (offset == pnOff) && (entry.pn != FIELD_NUM_NONE) {
                for i:=offset;i<offset+pnLen;i++ {
                    Data[i]=pnByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
            if (offset == macOff) && (entry.mac != FIELD_NUM_NONE) {
                for i:=offset;i<offset+macLen;i++ {
                    Data[i]=macByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
            if (offset == prodNameOff) && (entry.prodName != FIELD_NUM_NONE) {
                for i:=offset;i<offset+prodNameLen;i++ {
                    Data[i]=prodNameByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
            if (offset == skuOff) && (entry.sku != FIELD_NUM_NONE) {
                for i:=offset;i<offset+skuLen;i++ {
                    Data[i]=skuByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
            if (offset == fruIdOff) && (entry.fruId != FIELD_NUM_NONE) {
                for i:=offset;i<offset+fruIdLen;i++ {
                    Data[i]=fruIdByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
            if (offset == dpnOff) && (entry.dpn != FIELD_NUM_NONE) {
                for i:=offset;i<offset+dpnLen;i++ {
                    Data[i]=dpnByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
            if (offset == boardidOff) && (entry.boardID != FIELD_NUM_NONE) {
                var start int = offset
                var end int  = offset + boardidLen + 1
                binary.BigEndian.PutUint32(Data[start:end], boardID)
            }
        }
    }

    // update card extra field
    extTbl := card.ext
    if extTbl != nil {
         for i:= 0; i < len(extTbl); i++ {
            copy(Data[(extTbl[i].offset):], extTbl[i].value)
            copy(Data[(extTbl[i].offset + len(extTbl[i].value)):], Data[(extTbl[i].offset + len(extTbl[i].value)):])
        }
    }
    return
}

//==============================================================================
//                  F R U    A C T I O N    F U N C T I O N S
//==============================================================================

func writeToFRU(devName string, bus uint32, devAddr byte) (err int) {
    //var wrtoCPLD bool
    //Writes values in Data directly to FRU
    
    //Checks Data length vs Max number of bytes
    if len(Data) > MAX_BYTES {
        err = errType.FAIL
        cli.Printf("e", "ERROR: Data larger than Maximum Bytes by %d offsets", MAX_BYTES-len(Data))
        return
    }

    if devName == "CPLD_FRU" {
        //Writes FRU data to CPLD UFM2 FLASH
        fmt.Printf("WRITE TO UFM2\n");
        i2cinfo.SwitchI2cTbl("UUT_NONE")
        errGo := materafpga.Spi_cpldXO3_program_flash(uint32(bus-3), "ufm2", false, "", Data)
        if errGo != nil {
            return errType.FAIL 
        }
    } else if devName == "SUCFRU" {
        //Writes FRU data to SUC Microcontroller via it's console
        fmt.Printf("WRITE TO SUC Microcontroller  Bus=%d  Len=%d\n", bus, len(Data));
        i2cinfo.SwitchI2cTbl("UUT_NONE")
        for i:=0; i<len(Data); i++ {
            command := fmt.Sprintf("fru write %d hex %x", i, Data[i])
            fmt.Printf("%s\n", command);
            sucuart.Suc_exec_cmds(int(bus-2), command)
        }
        sucuart.Suc_exec_cmds(int(bus-2), "fru save")
    } else {
        var lockName string
        if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
            lockName, _, err = hwinfo.LockDev(devName)
            if err != errType.SUCCESS {
                return
            }
        }
        //Writes FRU data to EEPROM
        err = smbusNew.Open(devName, bus, devAddr)
        if err != errType.SUCCESS {
            if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                hwinfo.UnlockDev(lockName)
            }
            return
        }
        for i:=0;i<len(Data);i++ {
            misc.SleepInUSec(5000) //delay for writing
            if I2cAddr16 == true {
                err = smbusNew.I2C16WriteByte(devName, uint16(i), Data[i])
            } else {
                err = smbusNew.WriteByte(devName, uint64(i), Data[i])
            }
            if err != errType.SUCCESS {
                cli.Printf("e", "ERROR: Failed to write to FRU at offset %d", i)
                smbusNew.Close()
                if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                    hwinfo.UnlockDev(lockName)
                }
                return err
            }
        }
        smbusNew.Close()
        if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
            hwinfo.UnlockDev(lockName)
        }
    }
    return
}

func readFromFruBlind(devName string, bus uint32, devAddr byte) (err int) {
    var fruData byte

    if devName == "CPLD_FRU" {
        //Read FRU data from CPLD UFM2 FLASH
        var errGo error
        fmt.Printf(" Read from CPLD UFM2\n")
        i2cinfo.SwitchI2cTbl("UUT_NONE")
        DataRaw, errGo = materafpga.Spi_cpldX03_read_flash(uint32(bus-3), "ufm2", 0x00, uint32(MAX_BYTES))
        if errGo != nil {
            return errType.FAIL 
        }
    } else {
        var lockName string
        if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
            lockName, _, err = hwinfo.LockDev(devName)
            if err != errType.SUCCESS {
                return
            }
        }
        err = smbusNew.Open(devName, bus, devAddr)
        if err != errType.SUCCESS {
            if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                hwinfo.UnlockDev(lockName)
            }
            return
        }
        //Read FRU data from EEPROM
        for i:=0;i<MAX_BYTES;i++ {
            fruData, err =readOffset(devName, bus, devAddr, i)
            DataRaw = append(DataRaw, fruData)
            if err != errType.SUCCESS {
                smbusNew.Close()
                if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                    hwinfo.UnlockDev(lockName)
                }
                return
            }
        }
        smbusNew.Close()
        if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
            hwinfo.UnlockDev(lockName)
        }
    }
    return
}

func readFromFru(devName string, bus uint32, devAddr byte) (err int) {
    //Reads values from FRU and uploads into Data slice
    var sliceLen int
    var fruData byte
    var lockName string
    //Fills Data slice with 0xFF temporarily
    for i:=0;i<MAX_BYTES;i++ {
        Data = append(Data, 0xFF)
    }

    //Read FRU data from CPLD UFM2 FLASH and return out
    if devName == "CPLD_FRU" {
        var errGo error
        fmt.Printf(" Read from CPLD UFM2\n")
        i2cinfo.SwitchI2cTbl("UUT_NONE")
        Data, errGo = materafpga.Spi_cpldX03_read_flash(uint32(bus-3), "ufm2", 0x00, uint32(MAX_BYTES))
        if errGo != nil {
            return errType.FAIL 
        }
        return
    } 

    if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
        lockName, _, err = hwinfo.LockDev(devName)
        if err != errType.SUCCESS {
            return
        }
    }
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
            hwinfo.UnlockDev(lockName)
        }
        return
    }
    //Read FRU data from EEPROM
    // Calculate FRU table size based on IPMI headers
    //Checks header for variables
    for i:=0;i<6;i++ {
        fruData, err = readOffset(devName, bus, devAddr, i)
        Data[i] = fruData
    }
    start := checkCHdrStart()
    for i:=start;i<start+6;i++ {
        fruData, err =readOffset(devName, bus, devAddr, i)
        Data[i] = fruData
    }
    boardInfoOff, productInfoOff, mraInfoOff, err := getOffsetsCHdr(start)
    if err != errType.SUCCESS {
        smbusNew.Close()
        if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
            hwinfo.UnlockDev(lockName)
        }
        return
    }

    boardInfoByte, _ := readOffset(devName, bus, devAddr, start+boardInfoOff + 1)
    boardInfoLen := int(boardInfoByte) * OFFSET_NORM_FACTOR

    productInfoByte, _ := readOffset(devName, bus, devAddr, start+productInfoOff + 1)
    productInfoLen := int(productInfoByte) * OFFSET_NORM_FACTOR

    //Checks and sets the slice length
    if mraInfoOff != 0 {
        sliceLen += start+mraInfoOff
        for i:=start+mraInfoOff;i<MAX_BYTES;i++ {
            endOfList, _ := readOffset(devName, bus, devAddr, start+mraInfoOff + 1)
            recordLen, _ := readOffset(devName, bus, devAddr, start+mraInfoOff + 2)
            sliceLen += MRA_HDR_LEN + int(recordLen)
            mraInfoOff += MRA_HDR_LEN + int(recordLen)
            if endOfList == 0x82 {
                break
            }
        }
    } else if productInfoOff != 0 {
        sliceLen = start+productInfoOff + productInfoLen
    } else if boardInfoOff != 0 {
        sliceLen = start+boardInfoOff + boardInfoLen
    }
    //Clears Data slice
    Data = nil

    if strings.Contains(devName, "CPLD_FRU")==true {
        if sliceLen == 0 {
            sliceLen = MAX_BYTES
        }
    }

    //Reads data from FRU and fills the Data slice
    for i:=0;i<sliceLen;i++ {
        fruData, err = readOffset(devName, bus, devAddr, i)
        Data = append(Data, fruData)
        if err != errType.SUCCESS {
            cli.Printf("e", "ERROR: Failed to read from FRU at offset %s", i)
            smbusNew.Close()
            if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                hwinfo.UnlockDev(lockName)
            }
            return
        }
    }
    smbusNew.Close()
    if os.Getenv("CARD_TYPE") == "MTP_MATERA" || os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
        hwinfo.UnlockDev(lockName)
    }
    return
}

func readOffset(devName string, bus uint32, devAddr byte, offset int) (data byte, err int) {
    //Generic FRU reading function
    if I2cAddr16 == true {
        data, err = smbusNew.I2C16ReadByte(devName, uint16(offset))
    } else {
        data, err = smbusNew.ReadByte(devName, uint64(offset))
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to read from FRU at offset %d\n", offset)
    }
    return
}

//==============================================================================
//                      P U B L I C     F U N C T I O N S
//==============================================================================

func CardInListNew(partNum string, skuMode bool) (found bool, minPN string) {
    found = false
    //Looks through supported card slice and returns true if card number is present
    for _, card := range(CardTypes) {
        // In the case of fru display, partNum is the whole string read from EEPROM containing trailing spaces
        partNum = strings.TrimSpace(partNum)
        if (skuMode == true && partNum == card.pn) ||// for SKU card types, this is to find the exactly matching SKU
           (skuMode == false && strings.Contains(partNum, card.pn)) {
            found = true
            minPN = card.pn //for SKU card types, SKU is actually returned in minPN
            return
        }
    }
    return
}

func CardInListAccessViaFpga(dev string) (found bool, minPN string) {
    found = false

    //return true if card type in the list of cards access eeprom via FPGA
    var cardtyp string = os.Getenv("CARD_TYPE")
    for _, card := range(CardTypesAccessViaFpga) {
        if (cardtyp == card.cardTyp) {
            found = true
            if (dev == card.devName) {
                minPN = card.partNum
                return
            }
        }
    }

    return
}

func DisplayData(devName string, bus uint32, devAddr byte, field string, fpo bool) (err int){
    //Displays data of EEPROM
    //Formatting
    var outputString string
    var cardPN string
    var dataValue []byte

    fmtStr  := "%-45s%-20s"
    fmtDate := "%-45s0x%02X%02X%02X  %s"
    fmtMac  := "%-45s%02X-%02X-%02X-%02X-%02X-%02X"
    fmtHex  := "%-45s0x%-20X"

    //Reads data from FRU and puts into Data slice
    if fpo == true {
        err = readFromFruBlind(devName, bus, devAddr)
        if err != errType.SUCCESS {
            return
        }

        cardPN, err = findPnBlind()
        if err != errType.SUCCESS {
            return
        }

    } else {
        err = readFromFru(devName, bus, devAddr)
        if err != errType.SUCCESS {
            return
        }

        //Finds PN on card and sets EepromTbl
        start := checkCHdrStart()
        boardInfoOffset, productInfoOff, _, err1 := getOffsetsCHdr(start)
        if err1 != errType.SUCCESS {
            err = err1
            return
        }
        boardInfoLen := int(Data[start+boardInfoOffset+1]) * OFFSET_NORM_FACTOR
        productInfoLen := int(Data[start+productInfoOff+1]) * OFFSET_NORM_FACTOR
        //SKU takes priority over PN
        if productInfoOff != 0 {
            cardPN, err = findPn(start+productInfoOff, start+productInfoOff+productInfoLen, PROD_INFO_AREA_LEN, FIELD_NUM_SKU_3, FIELD_NUM_PN_8)
        } else {
            cardPN, err = findPn(start+boardInfoOffset, start+boardInfoOffset+boardInfoLen, BRD_INFO_AREA_LEN, FIELD_NUM_SKU_4, FIELD_NUM_PN_10)
        }
    }
    if (err == errType.SUCCESS) {
        EepromTbl=CardDataInfo[cardPN].tbl
    } else {
        // If using Salina CPLD FRU and no part number is found, set a different error type
        // If err = PN_NOT_SUPPORT, eeutil will fall back to checking Legacy cards which we don't want to do for CPLD Salina FRU 
        if strings.Contains(devName, "CPLD_FRU")==true {
            err = errType.FAIL
        } else {
            err = errType.PN_NOT_SUPPORT
        }
        return
    }

    //Displays info
    for i:=0;i<len(EepromTbl);i++ {
        dataName := EepromTbl[i].Name
        dataOffset := EepromTbl[i].Offset
        dataLen := EepromTbl[i].NumBytes
        dataType := EepromTbl[i].DataType
        if fpo == true {
            dataValue = DataRaw[dataOffset:(dataOffset+dataLen)]
        } else {
            dataValue = Data[dataOffset:(dataOffset+dataLen)]
        }
        //Checks for the field
        if field != "ALL" {
            if field == "SN" {
                if dataName != "Serial Number" {
                    continue
                }
            } else if field == "MAC" {
                if dataName != "MAC Address Base" {
                    continue
                }
            } else if field == "PN" {
                if dataName != "Assembly Number" {
                    continue
                }
            } else if field == "DATE" {
                if dataName != "Manufacturing Date/Time" {
                    continue
                }
            } else if field == "DPN" {
                if dataName != "DPN (Diagnostic Part Number)" {
                    continue
                }
            } else if field == "BOARDID" {
                if dataName != "Board ID" {
                    continue
                }
            }
        }
        //Formats and displays FRU value
        if dataType == STRING {
            dataString := string(dataValue)
            outputString = fmt.Sprintf(fmtStr, dataName, dataString)
        } else {
            if dataName == "Manufacturing Date/Time" {
                start := time.Date(1996, 1, 1, 0, 0, 0, 0, time.UTC)
                minutes := int((int(dataValue[2]) * 0x10000) + 
                    (int(dataValue[1]) * 0x100) + int(dataValue[0]))
                now := start.Add(time.Minute * time.Duration(minutes))
                year, month, day := now.Date()
                date := fmt.Sprintf("%02d/%02d/%02d", 
                    int(month), 
                    int(day), 
                    (int(year) % 100))
                outputString = fmt.Sprintf(fmtDate, dataName, 
                    dataValue[2], dataValue[1], dataValue[0], 
                    date)
            } else if dataName == "MAC Address Base" {
                outputString = fmt.Sprintf(fmtMac, dataName, 
                    dataValue[0],
                    dataValue[1],
                    dataValue[2],
                    dataValue[3],
                    dataValue[4],
                    dataValue[5],)
            } else if dataName == "Class Code" {
                outputString = fmt.Sprintf("%-45s0x%02X%02X%02X", dataName,
                dataValue[2], dataValue[1], dataValue[0]) 
            } else if dataName == "PCI-SIG Vendor ID" {
                outputString = fmt.Sprintf("%-45s0x%02X%02X", dataName, 
                dataValue[1], dataValue[0])
            } else if dataName == "Cap List Pointer" {
                outputString = fmt.Sprintf("%-45s0x%02X%02X", dataName, dataValue[1], dataValue[0])
            } else if dataName == "Manufacturer" {
                outputString = fmt.Sprintf("%-45s", dataName)
                str, _ := misc.Asc6ToStr(dataValue)
                outputString += str
            } else {
                outputString = fmt.Sprintf(fmtHex, dataName, dataValue)
            }
        }
        cli.Println("i", outputString)
    }
    return
}

func ProgData(devName string, bus uint32, devAddr byte, sn string, pn string, sku string, mac string, date string, dpn string, skuMode bool, boardID uint32) (err int){
    //Creates data slice of EEPROM table, updates data and checksums, and writes to FRU
    //Opens connections

    //Initiates the entries
    var identifier string
    if skuMode == true {
        identifier = sku
    } else {
        identifier = pn
    }
    err = convertToByteTbl(identifier, skuMode)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Card not supported.")
        err = errType.FAIL
        return 
    }
    //Updates the byte data slice with specified data
    err = updateFields(sn, pn, sku, mac, date, dpn, skuMode, boardID)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Update failed.")
        err = errType.FAIL
        return 
    }
    //Updates check sums
    updateChkSum()
    //Writes data table to FRU
    err = writeToFRU(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Write failed.")
        err = errType.FAIL
        return 
    }
    cli.Println("i", "EEPROM updated.")
    return
}
