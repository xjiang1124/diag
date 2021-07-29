package tmp451

const (
    MFG_ID_V byte = 0x55
)

const (
    LOCAL_TEMP = 0
    REMOTE_TEMP = 1
)

const (
    LIMIT_LOW = 5
    LIMIT_HIGH = 125
)


/***** READ REGISTER ADDRESS **********/
const (
    LOCAL_TEMP_HIGH_RD uint64         = 0x00
    REMOTE_TEMP_HIGH_RD uint64        = 0x01
    STATUS_RD uint64                  = 0x02
    CONFIG_RD uint64                  = 0x03
        CONFIG_RANGE_BIT                  = 0x4
    CONVERSION_RATE_RD uint64         = 0x04
    LOCAL_HIGH_LIMIT_RD uint64        = 0x05
    LOCAL_LOW_LIMIT_RD uint64         = 0x06
    REMOTE_HIGH_LIMIT_RD uint64       = 0x07
    REMOTE_LOW_LIMIT_RD uint64        = 0x08
    REMOTE_TEMP_LOW_RD uint64         = 0x10
    REMOTE_TEMP_OFFSET_HIGH_RD uint64 = 0x11
    REMOTE_TEMP_OFFSET_LOW_RD uint64  = 0x12
    REMOTE_TEMP_HIGH_LIMIT_RD uint64  = 0x13
    REMOTE_TEMP_LOW_LIMIT_RD uint64   = 0x14
    LOCAL_TEMP_LOW_RD uint64          = 0x15
    REMOTE_TEMP_THERM_LIMIT_RD uint64 = 0x19
    LOCAL_TEMP_THERM_LIMIT_RD uint64  = 0x20
    THERM_HYSTERESIS_RD uint64        = 0x21
    CONSECUTIVE_ALERT_RD uint64       = 0x22
    N_FACTOR_CORRECTION_RD uint64     = 0x23
    DIGITAL_FILTER_CONTROL_RD uint64  = 0x24
    MANUFACTURING_ID_RD               = 0xFE
        MANUFACTURING_ID_VALUE            = 0x55
)


/***** WRITE REGISTER ADDRESS WHICH ARE NOT ALWAYS THE SAME AS THE READ ADDRESS **********/
const (
    CONFIG_WR uint64                  = 0x09
    CONVERSION_RATE_WR uint64         = 0x0A
    LOCAL_HIGH_LIMIT_WR uint64        = 0x0B
    LOCAL_LOW_LIMIT_WR uint64         = 0x0C
    REMOTE_HIGH_LIMIT_WR uint64       = 0x0D
    REMOTE_LOW_LIMIT_WR uint64        = 0x0E
    ONE_SHOT_START_WR uint64          = 0x0F
    REMOTE_TEMP_OFFSET_HIGH_WR uint64 = 0x11
    REMOTE_TEMP_OFFSET_LOW_WR uint64  = 0x12
    REMOTE_TEMP_HIGH_LIMIT_WR uint64  = 0x13
    REMOTE_TEMP_LOW_LIMIT_WR uint64   = 0x14
    REMOTE_TEMP_THERM_LIMIT_WR uint64 = 0x19
    LOCAL_TEMP_THERM_LIMIT_WR uint64  = 0x20
    THERM_HYSTERESIS_WR uint64        = 0x21
    CONSECUTIVE_ALERT_WR uint64       = 0x22
    N_FACTOR_CORRECTION_WR uint64     = 0x23
    DIGITAL_FILTER_CONTROL_WR uint64  = 0x24
)


