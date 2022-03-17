package tps549a20

const (
    CHAN_A = 0
    CHAN_B = 1

    DAC_STEP_5MV = 0x27
    DAC_STEP_10MV = 0x24
)

// Register/Command offset
const (
    OPERATION = 0x01
    ON_OFF_CONFIG = 0x02
    CLEAR_FAULT = 0x03
    WRITE_PROTECT = 0x10
    STORE_DEFAULT_ALL = 0x11
    RESTORE_DEFAULT_ALL = 0x12
    STATUS_WORD = 0x79
    CUSTOM_REG = 0xD0
    DELAY_CONTROL = 0xD1
    MODE_SOFT_START_CONFIG = 0xD2
    FREQUENCY_CONFIG = 0xD3
    VOUT_ADJUSTMENT = 0xD4
    VOUT_MARGIN = 0xD5
    UVLO_THRESHOLD = 0xD6
)

const (
    MARGIN_NONE_CMD = 0x80
    MARGIN_HIGH_CMD = 0xA4
    MARGIN_LOW_CMD  = 0x94
    //MARGIN_NONE_CMD = 0x00
    //MARGIN_HIGH_CMD = 0x24
    //MARGIN_LOW_CMD  = 0x14
)

var opMargin = map[uint8] string {
    0x0: "MarginOff",
    0x1: "MarginOff",
    0x2: "MarginOff",
    0x3: "MarginOff",
    0x5: "MarginLow",
    0x6: "MarginLow",
    0x9: "MarginHigh",
    0xA: "MarginHigh",
}

var freqConfig = map[uint8]string {
    0: "250kHz",
    1: "300kHz",
    2: "400kHz",
    3: "500kHz",
    4: "600kHz",
    5: "750kHz",
    6: "850 kHz",
    7: "1MHz",
}

var voutAdjPct = map [uint8] float64 {
    0x1F: 9.00,
    0x1E: 9.00,
    0x1D: 9.00,
    0x1C: 9.00,
    0x1B: 8.25,
    0x1A: 7.50,
    0x19: 6.75,
    0x18: 6.00,
    0x17: 5.25,
    0x16: 4.50,
    0x15: 3.75,
    0x14: 3.00,
    0x13: 2.25,
    0x12: 1.50,
    0x11: 0.75,
    0x10: 0.00,
    0x0F: -0.00,
    0x0E: -0.75,
    0x0D: -1.50,
    0x0C: -2.25,
    0x0B: -3.00,
    0x0A: -3.75,
    0x09: -4.50,
    0x08: -5.25,
    0x07: -6.00,
    0x06: -6.75,
    0x05: -7.50,
    0x04: -8.25,
    0x03: -9.00,
    0x02: -9.00,
    0x01: -9.00,
}

var voutMarginHighPct = map [uint8] float64 {
    0xF: 12.0,
    0xE: 12.0,
    0xD: 12.0,
    0xC: 12.0,
    0xB: 10.9,
    0xA: 9.9,
    0x9: 8.8,
    0x8: 7.7,
    0x7: 6.7,
    0x6: 5.7,
    0x5: 4.7,
    0x4: 3.7,
    0x3: 2.8,
    0x2: 1.8,
    0x1: 0.9,
    0x0: 0,
}

var voutMarginLowhPct = map [uint8] float64 {
    0xF: -11.6,
    0xE: -11.6,
    0xD: -11.6,
    0xC: -11.6,
    0xB: -10.7,
    0xA: -9.9,
    0x9: -9.0,
    0x8: -8.1,
    0x7: -7.1,
    0x6: -6.2,
    0x5: -5.2,
    0x4: -4.2,
    0x3: -3.2,
    0x2: -2.1,
    0x1: -2.1,
    0x0: -0,
}
