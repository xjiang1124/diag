package errType

const(
    // INFO_GENERAL
    SUCCESS              = 0
    FAIL                 = -1
    INVALID_PARAM        = 1
    SKIP                 = 2
    TIMEOUT              = 3
    INVALID_TEST         = 4
    PERM_SKIP            = 5
    INVALID_LOCK         = 6
    UNSUPPORTED_CARD     = 7
    // INFO_DIAGMGR
    DIAGMGR_SKIP         = 100
    DIAGMGR_TIMEOUT      = 101
    DIAGMGR_INVALID_TEST = 102
    DIAGMGR_PERM_SKIP    = 103
    // INFO_TEMPSENSOR
    TEMPSENSOR_INVALID_ID = 200
    TEMPSENSOR_OVER_LIMIT = 201
    // INFO_I2C
    I2C_RD_FAIL          = 300
    I2C_WR_FAIL          = 301
    // INFO_SMB
    SMB_OPEN_FAIL        = 400
    SMB_CLOSE_FAIL       = 401
    SMB_READ_FAIL        = 402
    SMB_WRITE_FAIL       = 403
    SMB_INF_BUSY         = 404
    SMB_INF_INVALID      = 405
)