package ad7997

// Channels as defined in i2cInfo.page
const (
    CHAN_1 byte = 1
    CHAN_2 byte = 2
    CHAN_3 byte = 3
    CHAN_4 byte = 4
)

// Device Registers
const (
    RESULT = 0x0
    ALERT_STATUS = 0x1
    CONFIG = 0x2
    CYCLE_TIMER = 0x3
    CHAN_1_MIN_ALERT = 0x4
    CHAN_1_MAX_ALERT = 0x5
    CHAN_1_HYSTERESIS = 0x6
    CHAN_2_MIN_ALERT = 0x7
    CHAN_2_MAX_ALERT = 0x8
    CHAN_2_HYSTERESIS = 0x9
    CHAN_3_MIN_ALERT = 0xA
    CHAN_3_MAX_ALERT = 0xB
    CHAN_3_HYSTERESIS = 0xC
    CHAN_4_MIN_ALERT = 0xD
    CHAN_4_MAX_ALERT = 0xE
    CHAN_4_HYSTERESIS = 0xF
)

// Channel selection by address pointer
const (
    CHAN_1_SELECT byte = 0x80
    CHAN_2_SELECT byte = 0x90
    CHAN_3_SELECT byte = 0xa0
    CHAN_4_SELECT byte = 0xb0
)

// Reading RESULT register
const (
    RESULT_MASK = 0x0fff
    CHANNEL_MASK = 0x7000
    ALERT_MASK = 0x8000

    VOUT_SCALE = 1.2 / 0xfff
)

var voutChSelect = map[byte]byte {
    CHAN_1: CHAN_1_SELECT,
    CHAN_2: CHAN_2_SELECT,
    CHAN_3: CHAN_3_SELECT,
    CHAN_4: CHAN_4_SELECT,
}