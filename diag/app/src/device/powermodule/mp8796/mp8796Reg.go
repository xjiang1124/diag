package mp8796

// Register/Command offset
const (
    OPERATION                 = 0x01
      MARGIN_NONE_CMD         = 0x80
      MARGIN_HIGH_CMD         = 0xA4
      MARGIN_LOW_CMD          = 0x94
    ON_OFF_CONFIG             = 0x02
    CLEAR_FAULTS              = 0x03
    WRITE_PROTECT             = 0x10
    STORE_USER_ALL            = 0x15
    RESTORE_USER_ALL          = 0x16
    CAPABILITY                = 0x19
    VOUT_MODE                 = 0x20
    VOUT_COMMAND              = 0x21
    VOUT_MAX                  = 0x24
    VOUT_MARGIN_HIGH          = 0x25
    VOUT_MARGIN_LOW           = 0x26
    VOUT_SCALE_LOOP           = 0x29
    VOUT_MIN                  = 0x2B
    VIN_ON                    = 0x35
    VIN_OFF                   = 0x35
    OT_FAULT_LIMIT            = 0x4F
    OT_WARN_LIMIT             = 0x51
    VIN_OV_FAULT_LIMIT        = 0x55
    VIN_OV_WARN_LIMIT         = 0x57
    VIN_UV_WARN_LIMIT         = 0x58
    TON_DELAY                 = 0x60
    TON_RISE                  = 0x61
    TOFF_DELAY                = 0x64
    STATUS_BYTE               = 0x78
    STATUS_WORD               = 0x79
    STATUS_VOUT               = 0x7A
    STATUS_IOUT               = 0x7B
    STATUS_INPUT              = 0x7C
    STATUS_TEMPERATURE        = 0x7D
    STATUS_CML                = 0x7E
    READ_VIN                  = 0x88
    READ_VOUT                 = 0x8B
    READ_IOUT                 = 0x8C
    READ_TEMPERATURE_1        = 0x8D
    PMBUS_REVISION            = 0x98
    MFR_ID                    = 0x99
    MFR_CTRL_COMP             = 0xD0
    MFR_CTRL_VOUT             = 0xD1
    MFR_CTRL_OPS              = 0xD2
    MFR_ADDR_PMBUS            = 0xD3
    MFR_VOUT_OVP_FAULT_LIMIT  = 0xD4
    MFR_OVP_NOCP_SET          = 0xD5
    MFR_OT_OC_SET             = 0xD6
    MFG_OC_PHASE_LIMIT        = 0xD7
    MFG_HICCUP_ITV_SET        = 0xD8
    MFR_UVP_PGOOD_ON_LIMIT    = 0xD9
    MFR_VOUT_STEP             = 0xDA
    MFR_LOW_POWER             = 0xE5
    MFR_CTRL                  = 0xEA
)


