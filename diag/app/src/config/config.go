package config

const (
    MODE_REGULAR = 0
    MODE_JSON = 1

    DISABLE = 0
    ENABLE = 1
)

const (
    // 0: regular output; 1: JSON format
    OutputMode = DISABLE

    // Simulation mode control; 0: no simulation; 1: simuation mode enabled
    SimMode = DISABLE

    // PAL simuation mode select; 0: diable; 1: enable
    PalSimEnable = ENABLE

    // SMB mode: 0: disable, 1: enable
    SmbusMode = DISABLE
)

var DiagNicBinPath string
var DiagHostBinPath string
var DiagNicLogPath string
var DiagHostLogPath string

func init() {
    if SimMode == ENABLE {
        // Binary files location
        DiagNicBinPath = "/home/xguo2/workspace/psdiag/diag/app/bin/linux_amd64/"
        DiagHostBinPath = "/home/xguo2/workspace/psdiag/diag/app/bin/host/"

        // Log file target location
        DiagNicLogPath = "/home/xguo2/workspace/psdiag/log/"
        DiagHostLogPath = "/home/xguo2/workspace/psdiag/log/host/"
    } else {
        // Binary files location
        DiagNicBinPath = "/home/diag/diag/"
        DiagHostBinPath = ""

        // Log file target location
        DiagNicLogPath = "/home/diag/diag/log/"
        DiagHostLogPath = ""
    }
}


