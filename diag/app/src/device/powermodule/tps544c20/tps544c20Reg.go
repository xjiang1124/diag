package tps544c20

// Register/Command offset
const (
    OPERATION                 = 0x01
    ON_OFF_CONFIG             = 0x02
    CLEAR_FAULTS              = 0x03
    WRITE_PROTECT             = 0x10
    STORE_USER_ALL            = 0x15
    RESTORE_USER_ALL          = 0x16
    CAPABILITY                = 0x19
    VOUT_MODE                 = 0x20
    VIN_ON                    = 0x35
    VIN_OFF                   = 0x36
    IOUT_CAL_OFFSET           = 0x39
    IOUT_OC_FAULT_LIMIT       = 0x46
    IOUT_OC_FAULT_RESPONSE    = 0x47
    IOUT_OC_WARN_LIMIT        = 0x4A
    OT_FAULT_LIMIT            = 0x4F
    OT_WARN_LIMIT             = 0x51
    TON_RISE                  = 0x61
    STATUS_BYTE               = 0x78
    STATUS_WORD               = 0x79
    STATUS_VOUT               = 0x7A
    STATUS_IOUT               = 0x7B
    STATUS_TEMPERATURE        = 0x7D
    STATUS_CML                = 0x7E
    STATUS_MFR_SPECIFIC       = 0x80
    READ_VOUT                 = 0x8B
    READ_IOUT                 = 0x8C
    READ_TEMPERATURE_2        = 0x8E
    PMBUS_REVISION            = 0x98
    MFR_SPECIFIC_D0           = 0xD0
    VREF_TRIM                 = 0xD4
    STEP_VREF_MARGIN_HIGH     = 0xD5
    STEP_VREF_MARGIN_LOW      = 0xD6
    PCT_VOUT_FAULT_PG_LIMIT   = 0xD7
    SEQUENCE_TON_TOFF_DELAY   = 0xD8
    OPTIONS                   = 0xE5
    MASK_SMBALERT             = 0xE7
    DEVICE_CODE               = 0xFC
)

const (
    MARGIN_NONE_CMD = 0x80
    MARGIN_HIGH_CMD = 0xA4
    MARGIN_LOW_CMD  = 0x94
    //MARGIN_NONE_CMD = 0x00
    //MARGIN_HIGH_CMD = 0x24
    //MARGIN_LOW_CMD  = 0x14

)
