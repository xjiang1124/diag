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
    // INFO_DIAGMGR
    DIAGMGR_SKIP         = 100
    DIAGMGR_TIMEOUT      = 101
    DIAGMGR_INVALID_TEST = 102
    DIAGMGR_PERM_SKIP    = 103
)