package ina3221a

// Channels as defined in i2cInfo.page
const (
    CHAN_1 byte = 0x1
    CHAN_2 byte = 0x2
    CHAN_3 byte = 0x3
)

// SMBus Registers
const (
    CONFIG uint64 = 0x0
    CHAN_1_IOUT uint64 = 0x1
    CHAN_1_VOUT uint64 = 0x2
    CHAN_2_IOUT uint64 = 0x3
    CHAN_2_VOUT uint64 = 0x4
    CHAN_3_IOUT uint64 = 0x5
    CHAN_3_VOUT uint64 = 0x6
    CHAN_1_CRIT_LIMIT uint64 = 0x7
    CHAN_1_WARN_LIMIT uint64 = 0x8
    CHAN_2_CRIT_LIMIT uint64 = 0x9
    CHAN_2_WARN_LIMIT uint64 = 0xA
    CHAN_3_CRIT_LIMIT uint64 = 0xB
    CHAN_3_WARN_LIMIT uint64 = 0xC
    CHAN_IOUT_SUM uint64 = 0xD
    CHAN_IOUT_SUM_LIMIT uint64 = 0xE
    STATUS uint64 = 0xF
    POUT_MAX_LIMIT uint64 = 0x10
    POUT_MIN_LIMIT uint64 = 0x11
    MFR_ID uint64 = 0xFE
    DIE_ID uint64 = 0xFF
)

// Fixed values
const (
    MFR_ID_VALUE = 0x5449
    DIE_ID_VALUE = 0x3220
)

// Reading VOUT/IOUT registers
const (
    RESERVED_BITS = 3
    RESULT_BITS = 0x7ff8
    SIGN_BIT = 0x8000

    IOUT_SCALE = 0.00004 // LSB = 40 uohm
    VOUT_SCALE = 0.008   // LSB = 8 mohm
)

var voutRegAddr = map[byte]uint64 {
    CHAN_1: CHAN_1_VOUT,
    CHAN_2: CHAN_2_VOUT,
    CHAN_3: CHAN_3_VOUT,
}

var ioutRegAddr = map[byte]uint64 {
    CHAN_1: CHAN_1_IOUT,
    CHAN_2: CHAN_2_IOUT,
    CHAN_3: CHAN_3_IOUT,
}