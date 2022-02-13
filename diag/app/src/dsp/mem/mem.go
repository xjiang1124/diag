package main

import (
    "os"
    "os/exec"
    "flag"
    "strings"
    "strconv"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/runCmd"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "MEM"
)

func MemDdr_StressHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    secondsPtr := fs.Int("seconds", 60, "number of seconds to run")
    copy_threadsPtr := fs.Int("copy_threads", 16, "number of memory copy threads to run")
    logfilePtr := fs.String("logfile", "stressapptest.log", "log output to file 'logfile'")
    var cmd string
    var err int

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    out, errGo := exec.Command("grep", "MemAvailable", "/proc/meminfo").Output()
    if errGo != nil {
        dcli.Println("e", "Failed to get MemAvailable", errGo)
        err = errType.FAIL
        diagEngine.FuncMsgChan <- err
        return
    }
    availMemStr := string(out)
    availMemStrArr := strings.Fields(availMemStr)
    availMemInKb := availMemStrArr[1]
    availMemSize, _ := strconv.Atoi(availMemInKb)
    dcli.Println("i", "Available memory in Kbytes: ", availMemSize)
    availMemSize = (availMemSize / 1024 / 100) * 100;
    dcli.Println("i", "Available memory in Mbytes: ", availMemSize)

    cmd = "/data/nic_util/stressapptest_arm"
    passSign := "Status: PASS - please verify no corrected errors"
    failSign := "Status: FAIL - test discovered HW problems"
    err = runCmd.Run(passSign, failSign, cmd, "-M", strconv.Itoa(availMemSize), "-s", strconv.Itoa(*secondsPtr), "-m", strconv.Itoa(*copy_threadsPtr), "-l", "/data/nic_util/" + *logfilePtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func MemEdmaHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    cmdStr := "/data/nic_util/run_edma.sh"
    passSign := "EDMA TEST PASSED"
    failSign := "EDMA TEST FAILED"
    _, errOs := os.Stat("/nic/bin/ddr_test.sh")
    if errOs == nil {
        dcli.Println("i", "ddr_test.sh exists")
        cmdStr = "/nic/bin/ddr_test.sh"
        passSign = "Test PASSED"
        failSign = "Test FAILED"
    }

    err := runCmd.Run(passSign, failSign, cmdStr)

    if err != errType.SUCCESS {
         dcli.Println("e", "EDMA Test Failed!")
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["DDR_STRESS"] = MemDdr_StressHdl
    diagEngine.FuncMap["EDMA"] = MemEdmaHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
