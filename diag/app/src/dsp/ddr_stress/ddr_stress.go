package main

import (
    "flag"
    "strconv"

    "common/diagEngine"
    "common/dcli"
    "common/runCmd"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "DDR_STRESS"
)

func Ddr_StressDdr_StressHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    secondsPtr := fs.Int("seconds", 60, "number of seconds to run")
    mbytesPtr := fs.Int("mbytes", 20000, "megabytes of ram to test")
    copy_threadsPtr := fs.Int("copy_threads", 16, "number of memory copy threads to run")
    logfilePtr := fs.String("logfile", "stressapptest.log", "log output to file 'logfile'")
    var cmd string
    var err int

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    cmd = "/data/nic_util/stressapptest_arm"
    passSign := "Status: PASS - please verify no corrected errors"
    failSign := "Status: FAIL - test discovered HW problems"
    err = runCmd.Run(passSign, failSign, cmd, "-M", strconv.Itoa(*mbytesPtr), "-s", strconv.Itoa(*secondsPtr), "-m", strconv.Itoa(*copy_threadsPtr), "-l", "/data/nic_util/" + *logfilePtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["DDR_STRESS"] = Ddr_StressDdr_StressHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
