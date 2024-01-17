package mp2975

// Register/Command offset
const (
    PAGE                      = 0x00
    OPERATION                 = 0x01
    MFR_PWD_USER              = 0x02
    CLEAR_FAULTS              = 0x03
    WRITE_PROTECT             = 0x10
    STORE_USER_ALL            = 0x17
    RESTORE_USER_ALL          = 0x18
    CAPABILITY                = 0x19
    VOUT_MODE                 = 0x20
    VOUT_COMMAND              = 0x21
    VOUT_MAX                  = 0x24
    VOUT_MARGIN_HIGH          = 0x25
    VOUT_MARGIN_LOW           = 0x26
    VOUT_TRANSISTION_RATE     = 0x27
    VOUT_SENSE_SET            = 0x29
    VOUT_MIN                  = 0x2B
    VIN_ON                    = 0x35
    VIN_OFF                   = 0x36
    OT_WARN_LIMIT             = 0x51
    IOUT_CAL_OFFSET           = 0x54
    VIN_OV_FAULT_LIMIT        = 0x55
    TON_DELAY                 = 0x60
    TOFF_DELAY                = 0x64
    STATUS_BYTE               = 0x78
    STATUS_WORD               = 0x79
    STATUS_VOUT               = 0x7A
    STATUS_IOUT               = 0x7B
    STATUS_INPUT              = 0x7C
    STATUS_TEMPERATURE        = 0x7D
    STATUS_CML                = 0x7E
    READ_VIN                  = 0x88
    READ_IIN                  = 0x89
    READ_VOUT                 = 0x8B
    READ_IOUT                 = 0x8C
    READ_TEMPERATURE_1        = 0x8D
    READ_POUT                 = 0x96
    READ_PIN                  = 0x97
    PMBUS_REVISION            = 0x98
    MFR_ID                    = 0x99
)


