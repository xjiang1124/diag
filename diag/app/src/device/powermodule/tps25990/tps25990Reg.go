package tps25990

// Register/Command offset
const (
    OPERATION                 = 0x01
    CLEAR_FAULTS              = 0x03
    WRITE_PROTECT             = 0x10
    RESTORE_FACT_DEF          = 0x12
    STORE_USER_ALL            = 0x15
    RESTORE_USER_ALL          = 0x16

    EEPROM_DET_CMD            = 0xF4
    BB_ERASE                  = 0xF5
    FEATCH_BB_EEPROM          = 0xF6
    POWER_CYCLE               = 0xD9

    CAPABILITY                = 0x19

    STATUS_BYTE               = 0x78
    STATUS_WORD               = 0x79
    STATUS_VOUT               = 0x7A
    STATUS_IOUT               = 0x7B
    STATUS_INPUT              = 0x7C
    STATUS_TEMPERATURE        = 0x7D
    STATUS_CML                = 0x7E

    STATUS_MFR_SPECIFIC_2     = 0x7F
    STATUS_MFR_SPECIFIC       = 0x80

    PMBUS_REVISION            = 0x98
    MFR_ID                    = 0x99
    MFR_MODEL                 = 0x9A
    MFR_REVISION              = 0x9B
    READ_VIN                  = 0x88
    READ_VOUT                 = 0x8B
    READ_IIN                  = 0x89
    READ_TEMPERATURE_1        = 0x8D
    READ_VAUX                 = 0xD0

    READ_PIN                  = 0x97
    READ_EIN                  = 0x86

    READ_VIN_AVG              = 0xDC
    READ_VIN_MIN              = 0xD1
    READ_VIN_PEAK             = 0xD2
    READ_VOUT_AVG             = 0xDD
    READ_VOUT_MIN             = 0xDA
    READ_IOUT_AVG             = 0xDE
    READ_IOUT_PEAK            = 0xD4
    READ_TEMP_AVG             = 0xD6
    READ_TEMP_PEAK            = 0xD7
    READ_PIN_AVG              = 0xDF
    READ_PIN_PEAK             = 0xD5
    READ_SAMPLE_BUF           = 0xD8
    READ_BB_RAM               = 0xFD
    BB_TIMER                  = 0xFA
    PMBUS_DEV_ADDR            = 0xFB
    VIN_UV_WARN               = 0x58
    VIN_UV_FAULT              = 0x59
    VIN_OV_WARN               = 0x57
    VIN_OV_FAULT              = 0x55
    VOUT_UV_WARN              = 0x43
    VOUT_PWR_GOOD_THRESHOLD   = 0x5F
    OT_WARN                   = 0x51
    OT_FAULT                  = 0x4F
    PIN_OP_WARN               = 0x6B
    IOUT_OC_WARN              = 0x5D
    VIREF                     = 0xE0
    GPIO_CONFIG_12            = 0xE1
    GPIO_CONFIG_34            = 0xE2
    ALERT_MASK                = 0xDB
    FAULT_MASK                = 0xE3
    DEVICE_CONFIG             = 0xE4
    BB_CONFIG                 = 0xE5
    OC_TIMER                  = 0xE6
    RETRY_CONFIG              = 0xE7
    ADD_CONFIG_1              = 0xE8
    ADD_CONFIG_2              = 0xE9
    PK_MIN_AVG                = 0xEA
    VCMPXREF                  = 0xEB
    PSU_VOLTAGE               = 0xEC
    CABLE_RESISTANCE          = 0xED
    GPDAC1                    = 0xF0
    GPDAC2                    = 0xF1
    INS_DLY                   = 0xF9


)


