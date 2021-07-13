package qsfp

type qsfpPage_t struct {
    name     string
    offset   uint64
    numBytes uint64
}

// Laser enable/disable
const (
    ENABLE  = 1
    DISABLE = 0
)

// QSFP Identifier
// SFF-8024
const (
    ID_QSFP_P byte = 0xD
    ID_QSFP28 byte = 0x11

    QSFP_BR_ADDR           byte = 140

    QSFP_CC_BASE_START     byte = 128
    QSFP_CC_BASE           byte = 191

    QSFP_CC_EXT_BASE       byte = 223
)


var lowerPage = []qsfpPage_t {
    qsfpPage_t {"ID",       0,   1,},
    qsfpPage_t {"STA",      1,   2,},
    qsfpPage_t {"INTR",     3,   19,},
    qsfpPage_t {"MDL_MNTR", 22,  12,},
    qsfpPage_t {"CHN_MNTR", 34,  48,},
    qsfpPage_t {"RSVD_01",  82,  4,},
    qsfpPage_t {"CTRL",     86,  12,},
    qsfpPage_t {"RSVD_02",  98,  2,},
    qsfpPage_t {"MASKS",    100, 7,},
    qsfpPage_t {"RSVD_03",  107, 12,},
    qsfpPage_t {"PWD_CHG",  119, 4,},
    qsfpPage_t {"PWD",      123, 4,},
    qsfpPage_t {"PG_SEL",   127, 1,},
}

var upperPage00 = []qsfpPage_t {
    qsfpPage_t {"ID",       128, 1,},
    qsfpPage_t {"EXT_ID",   129, 1,},
    qsfpPage_t {"CONN",     130, 1,},
    qsfpPage_t {"TCVR",     131, 8,},
    qsfpPage_t {"ENCODING", 139, 1,},
    qsfpPage_t {"BR",       140, 1,},
    qsfpPage_t {"RATE_SEL", 141, 1,},
    qsfpPage_t {"LEN_SMF",  142, 1,},
    qsfpPage_t {"LEN_EBW",  143, 1,},
    qsfpPage_t {"LEN_50UM", 144, 1,},
    qsfpPage_t {"LEN_625UM",145, 1,},
    qsfpPage_t {"LEN_COP",  146, 1,},
    qsfpPage_t {"DEV_TECH", 147, 1,},
    qsfpPage_t {"VEND_NAME",148, 16,},
    qsfpPage_t {"EXT_TCVR", 164, 1,},
    qsfpPage_t {"VEND_OUI", 165, 3,},
    qsfpPage_t {"VEND_PN",  168, 16,},
    qsfpPage_t {"VEND_REV", 184, 2,},
    qsfpPage_t {"LZER_WLEN",186, 2,},
    qsfpPage_t {"WLEN",     188, 2,},
    qsfpPage_t {"MAX_TEMP", 190, 1,},
    qsfpPage_t {"CC_BASE",  191, 1,},
    qsfpPage_t {"OPTIONS",  192, 4,},
    qsfpPage_t {"VEND_SN",  196, 16,},
    qsfpPage_t {"DATE_CODE",212, 8,},
    qsfpPage_t {"DIAG_TYPE",220, 1,},
    qsfpPage_t {"ENH_OPT",  221, 1,},
    qsfpPage_t {"RSVD",     222, 1,},
    qsfpPage_t {"CC_EXT",   223, 1,},
    qsfpPage_t {"VEND_SPEC",224, 32,},
}


