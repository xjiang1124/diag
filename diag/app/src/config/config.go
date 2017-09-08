package config

const (
    // 0: regular output; 1: JSON format
    OutputMode = 0

    // Simulation mode control; 0: no simulation; 1: simuation mode enabled
    SimMode = 1

    // Binary files location
    //DiagNicBinPath = "/home/xguo2/workspace/psdiag/diag/go/bin/"
    //DiagHostBinPath = "/home/xguo2/workspace/psdiag/diag/go/bin/host/"

    // Log file target location
    //DiagNicLogPath = "/home/xguo2/workspace/psdiag/diag/go/bin/"
    //DiagHostLogPath = "/home/xguo2/workspace/psdiag/diag/go/bin/host/"
)

var DiagNicBinPath string
var DiagHostBinPath string
var DiagNicLogPath string
var DiagHostLogPath string

func init() {
    if SimMode == 1 {
        // Binary files location
        DiagNicBinPath = "/home/xguo2/workspace/psdiag/diag/go/bin/"
        DiagHostBinPath = "/home/xguo2/workspace/psdiag/diag/go/bin/host/"

        // Log file target location
        DiagNicLogPath = "/home/xguo2/workspace/psdiag/diag/go/bin/"
        DiagHostLogPath = "/home/xguo2/workspace/psdiag/diag/go/bin/host/"
    } else {
        // Binary files location
        DiagNicBinPath = ""
        DiagHostBinPath = ""

        // Log file target location
        DiagNicLogPath = ""
        DiagHostLogPath = ""
    }
}


