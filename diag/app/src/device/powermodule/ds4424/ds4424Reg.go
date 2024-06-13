package ds4424

// Channels as defined in i2cInfo.page
const (
    VOUT0 byte = 0
    VOUT1 byte = 1
    VOUT2 byte = 2
    VOUT3 byte = 3
)

// Device Registers
const (
    VOUT0_REG uint64 = 0xf8
    VOUT1_REG uint64 = 0xf9
    VOUT2_REG uint64 = 0xfa
    VOUT3_REG uint64 = 0xfb
)
// Setting vout registers
const (
    MARGIN_SET_MASK byte = 0x80
    MARGIN_HIGH_SET byte = 0x00
    MARGIN_LOW_SET  byte = 0x80

    VOUT_SCALE_MAX  byte = 0x7f
    PCT_SCALE_MAX   int = 20
)

var voutChSelect = map[byte]uint64 {
    VOUT0: VOUT0_REG,
    VOUT1: VOUT1_REG,
    VOUT2: VOUT2_REG,
    VOUT3: VOUT3_REG,
}