package tps544b25

const (
    CHAN_A = 0
    CHAN_B = 1

    DAC_STEP_5MV = 0x27
    DAC_STEP_10MV = 0x24
)

// Register/Command offset
const (
    OPERATION                 = 0x01
    ON_OFF_CONFIG             = 0x02
    CLEAR_FAULTS              = 0x03
    PHASE                     = 0x04
    WRITE_PROTECT             = 0x10
    STORE_DEFAULT_ALL         = 0x11
    RESTORE_DEFAULT_ALL       = 0x12
    CAPABILITY                = 0x19
    SMBALERT_MASK             = 0x1B
    VOUT_MODE                 = 0x20
    VOUT_COMMAND              = 0x21
    VOUT_TRIM                 = 0x22
    VOUT_CAL_OFFSET           = 0x23
    VOUT_MAX                  = 0x24
    VOUT_TRANSITION_RATE      = 0x27
    VOUT_SCALE_LOOP           = 0x29
    VIN_ON                    = 0x35
    VIN_OFF                   = 0x36
    IOUT_CAL_OFFSET           = 0x39
    VOUT_OV_FAULT_LIMIT       = 0x40
    VOUT_OV_FAULT_RESPONSE    = 0x41
    VOUT_OV_WARN_LIMIT        = 0x42
    VOUT_UV_WARN_LIMIT        = 0x43
    VOUT_UV_FAULT_LIMIT       = 0x44
    VOUT_UV_FAULT_RESPONSE    = 0x45
    IOUT_OC_FAULT_LIMIT       = 0x46
    IOUT_OC_FAULT_RESPONSE    = 0x47
    IOUT_OC_WARN_LIMIT        = 0x4A
    OT_FAULT_LIMIT            = 0x4F
    OT_FAULT_RESPONSE         = 0x50
    OT_WARN_LIMIT             = 0x51
    TON_DELAY                 = 0x60
    TON_RISE                  = 0x61
    TON_MAX_FAULT_LIMIT       = 0x62
    TON_MAX_FAULT_RESPONSE    = 0x63
    TOFF_DELAY                = 0x64
    TOFF_FALL                 = 0x65
    STATUS_BYTE               = 0x78
    STATUS_WORD               = 0x79
    STATUS_VOUT               = 0x7A
    STATUS_IOUT               = 0x7B
    STATUS_INPUT              = 0x7C
    STATUS_TEMPERATURE        = 0x7D
    STATUS_CML                = 0x7E
    STATUS_MFR_SPECIFIC       = 0x80
    READ_VOUT                 = 0x8B
    READ_IOUT                 = 0x8C
    READ_TEMPERATURE_2        = 0x8E
    PMBUS_REVISION            = 0x98
    MFR_VOUT_MIN              = 0xA4
    IC_DEVICE_ID              = 0xAD
    IC_DEVICE_REV             = 0xAE
    MFR_SPECIFIC_D0           = 0xD0
    MFR_SPECIFIC_E5           = 0xE5
    MFR_SPECIFIC_F0           = 0xF0
)

const (
    MARGIN_NONE_CMD = 0x80
    MARGIN_HIGH_CMD = 0xA4
    MARGIN_LOW_CMD  = 0x94
    //MARGIN_NONE_CMD = 0x00
    //MARGIN_HIGH_CMD = 0x24
    //MARGIN_LOW_CMD  = 0x14

)
