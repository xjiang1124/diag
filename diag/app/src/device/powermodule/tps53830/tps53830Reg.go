package tps53830

// Register offset
const (
    STATUS_REG = 0x08
    SWA_OUTPUT_REG = 0x0C
    SWB_OUTPUT_REG = 0x0D
    SWC_OUTPUT_REG = 0x0E
    SWD_OUTPUT_REG = 0x0F
    OUTPUT_SELECT_REG = 0x1B
    SWA_OFFSET_REG = 0x7C
    SWB_OFFSET_REG = 0x7D
    SWC_OFFSET_REG = 0x7E
    SWD_OFFSET_REG = 0x7F
    SECURE_MODE_REG = 0x2F
    ADC_CTL_REG = 0x30
    ADC_OUT_REG = 0x31
    VENDOR_ID_REG = 0x3D
    REG_LOCK_REG = 0xA2
)

const (
    VENDOR_ID = 0x97
    ADC_ENABLE = 0x80
    SWA_OUTPUT_SEL = 0
    SWB_OUTPUT_SEL = 0x8
    SWC_OUTPUT_SEL = 0x10
    SWD_OUTPUT_SEL = 0x18
    VIN_BULK_SEL = 0x28
    VIN_MGMT_SEL = 0x30
    VIN_BIAS_SEL = 0x38
    TEMP_SEL = 0x50
    ADC_CURRENT_SEL = 0xBF
    ADC_POWER_SEL = 0x40
    PROGRAMMABLE_MODE = 0x6
    VOUT_1P1_MAX = 1210
    VOUT_1P1_MIN = 990
    VOUT_1P8_MAX = 1980
    VOUT_1P8_MIN = 1620
)

var swaMarginPct = map [int] uint8 {
    5 : 0x65,
    4 : 0x4F,
    3 : 0x2A,
    2 : 0x20,
    1 : 0x06,
    0 : 0xF7,
    -1: 0xDD,
    -2: 0xC5,
    -3: 0xAA,
    -4: 0x9F,
    -5: 0x89,
}

var swcMarginPct = map [int] uint8 {
    5 : 0x58,
    4 : 0x42,
    3 : 0x2A,
    2 : 0x20,
    1 : 0x06,
    0 : 0xEA,
    -1: 0xDD,
    -2: 0xC5,
    -3: 0xAA,
    -4: 0x92,
    -5: 0x81,
}

var swdMarginPct = map [int] uint8 {
    5 : 0x54,
    4 : 0x42,
    3 : 0x2A,
    2 : 0x20,
    1 : 0x06,
    0 : 0xFA,
    -1: 0xDD,
    -2: 0xC5,
    -3: 0xBA,
    -4: 0xB2,
    -5: 0xA0,
}
