package max6657

const (
    MFG_ID_V byte = 0xA1
)

const (
    LOCAL_TEMP = 0
    REMOTE_TEMP = 1

    MAX_CHANNEL = 2
)

const (
    LIMIT_LOW = 5
    LIMIT_HIGH = 125
)

const (
    READ_INT_TEMP uint64 = 0x00
    READ_EXT_TEMP uint64 = 0x01
    READ_STATUS uint64 = 0x02
    READ_CONFIG uint64 = 0x03
    READ_CONV_RATE uint64 = 0x04
    READ_INT_H_LMT uint64 = 0x05
    READ_INT_L_LMT uint64 = 0x06
    READ_EXT_H_LMT uint64 = 0x07
    READ_EXT_L_LMT uint64 = 0x08
    WRITE_CONFIG uint64 = 0x09
    WRITE_CONV_RATE uint64 = 0x0A
    WRITE_INT_H_LMT uint64 = 0x0B
    WRITE_INT_L_LMT uint64 = 0x0C
    WRITE_EXT_H_LMT uint64 = 0x0D
    WRITE_EXT_L_LMT uint64 = 0x0E
    ONE_STOT_START uint64 = 0x0F
    READ_EXT_EXT_TEMP uint64 = 0x10
    READ_INT_EXT_TEMP uint64 = 0x11
    EXT_OVERT2_LMT_RW uint64 = 0x16
    INT_OVERT2_LMT_RW uint64 = 0x17
    EXT_OVERT1_LMT_RW uint64 = 0x19
    INT_OVERT1_LMT_RW uint64 = 0x20
    OVER_TEMP_HYST uint64 = 0x21
    MFG_ID uint64 = 0xFE
)


