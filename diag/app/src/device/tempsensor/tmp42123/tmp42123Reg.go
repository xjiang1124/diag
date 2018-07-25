package tmp42123

const (
    MFG_ID_V byte = 0x55
    DEV_ID_V byte = 0x22
)

const (
    LOCAL_TEMP = 0
    REMOTE_TEMP1 = 1
    REMOTE_TEMP2 = 2

    MAX_CHANNEL = 2
)

const (
    LIMIT_LOW = 5
    LIMIT_HIGH = 125
)


const (
    LOCAL_TEMP_HIGH uint64 = 0x00
    REMOTE_TEMP_HIGH1 uint64 = 0x01
    REMOTE_TEMP_HIGH2 uint64 = 0x02
    REMOTE_TEMP_HIGH3 uint64 = 0x03
    STATUS uint64 =0x08
    CONFIG1 uint64 = 0x09
    CONFIG2 uint64 = 0x0A
    CONV_RATE uint64 = 0x0B
    ONE_STOT_START uint64 = 0x0F
    LOCAL_TEMP_LOW uint64 = 0x10
    REMOTE_TEMP_LOW1 uint64 = 0x11
    REMOTE_TEMP_LOW2 uint64 = 0x12
    REMOTE_TEMP_LOW3 uint64 = 0x13
    N_CORR_1 uint64 = 0x21
    N_CORR_2 uint64 = 0x22
    N_CORR_3 uint64 = 0x23
    SOFT_RESET uint64 = 0xFC
    MFG_ID uint64 = 0xFE
    DEV_ID uint64 = 0xFF
)


