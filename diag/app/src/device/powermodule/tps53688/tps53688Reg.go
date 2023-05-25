package tps53688

// Register/Command offset
const (
    PAGE                      = 0x00
    OPERATION                 = 0x01
    ON_OFF_CONFIG             = 0x02
    CLEAR_FAULTS              = 0x03
    PHASE                     = 0x04
    STORE_USER_ALL            = 0x15
    RESTORE_USER_ALL          = 0x16
    CAPABILITY                = 0x19
    SMBALERT_MASK             = 0x1B
    VOUT_MODE                 = 0x20
    VOUT_COMMAND              = 0x21
    VOUT_MAX                  = 0x24
    VOUT_MARGIN_HIGH          = 0x25
    VOUT_MARGIN_LOW           = 0x26
    VOUT_TRANSITION_RATE      = 0x27
    VOUT_DROOP                = 0x28
    VOUT_SCALE_LOOP           = 0x29
    VOUT_MIN                  = 0x2B
    FREQUENCY_SWITCH          = 0x33
    VIN_ON                    = 0x35
    IOUT_CAL_GAIN             = 0x38
    IOUT_CAL_OFFSET           = 0x39
    VOUT_OV_FAULT_LIMIT       = 0x40
    VOUT_OV_FAULT_RESPONSE    = 0x41
    VOUT_UV_FAULT_LIMIT       = 0x44
    VOUT_UV_FAULT_RESPONSE    = 0x45
    IOUT_OC_FAULT_LIMIT       = 0x46
    IOUT_OC_FAULT_RESPONSE    = 0x47
    IOUT_OC_WARN_LIMIT        = 0x4A
    OT_FAULT_LIMIT            = 0x4F
    OT_FAULT_RESPONSE         = 0x50
    OT_WARN_LIMIT             = 0x51
    VIN_OV_FAULT_LIMIT        = 0x55
    VIN_OV_FAULT_RESPONSE     = 0x56
    VIN_UV_FAULT_LIMIT        = 0x59
    VIN_UV_FAULT_RESPONSE     = 0x5A
    IIN_OC_FAULT_LIMIT        = 0x5B
    IIN_OC_FAULT_RESPONSE     = 0x5C
    IIN_OC_WARN_LIMIT         = 0x5D
    TON_DELAY                 = 0x60
    STATUS_BYTE               = 0x78
    STATUS_WORD               = 0x79
    STATUS_VOUT               = 0x7A
    STATUS_IOUT               = 0x7B
    STATUS_INPUT              = 0x7C
    STATUS_TEMPERATURE        = 0x7D
    STATUS_CML                = 0x7E
    STATUS_MFR_SPECIFIC       = 0x80
    READ_VIN                  = 0x88
    READ_IIN                  = 0x89
    READ_VOUT                 = 0x8B
    READ_IOUT                 = 0x8C
    READ_TEMPERATURE_1        = 0x8D
    READ_POUT                 = 0x96
    READ_PIN                  = 0x97
    PMBUS_REVISION            = 0x98
        PMBUS_REV_VALUE           = 0x33
    MFR_ID                    = 0x99
    MFR_MODEL                 = 0x9A
    MFR_REVISION              = 0x9B
    MFR_DATE                  = 0x9D
    IC_DEVICE_ID              = 0xAD
        IC_DEVICE_ID_VALUE        = 0x544953688000
    IC_DEVICE_REV             = 0xAE
        IC_DEVICE_REV_VALUE       = 0x3
    USER_DATA_01              = 0xB1
    USER_DATA_02              = 0xB2
    USER_DATA_03              = 0xB3
    USER_DATA_04              = 0xB4
    USER_DATA_07              = 0xB7
    USER_DATA_08              = 0xB8
    USER_DATA_10              = 0xBA
    USER_DATA_11              = 0xBB
    USER_DATA_13              = 0xBD

    MFR_SPECIFIC_D1           = 0xD1
    MFR_SPECIFIC_D2           = 0xD2
    MFR_SPECIFIC_D3           = 0xD3
    MFR_SPECIFIC_D4           = 0xD4
    MFR_SPECIFIC_D5           = 0xD5
    MFR_SPECIFIC_D6           = 0xD6
    MFR_SPECIFIC_D7           = 0xD7
    MFR_SPECIFIC_D8           = 0xD8
    MFR_SPECIFIC_DA           = 0xDA
    MFR_SPECIFIC_DB           = 0xDB
    MFR_SPECIFIC_DC           = 0xDC
    MFR_SPECIFIC_DD           = 0xDD

    SYNC_CONFIG               = 0xE4
)

const (
    MARGIN_NONE_CMD = 0x80
    MARGIN_LOW_IGN_FLT = 0x94
    MARGIN_LOW_ACT_FLT = 0x98
    MARGIN_HIGH_IGN_FLT = 0xA4
    MARGIN_HIGH_ACT_FLT = 0xA8
)

const (
    DAC_STEP_10MV = 0x24
    DAC_STEP_5MV = 0x27
)
