package main

import (
    "os"
    "os/exec"
    "flag"
    "strings"
    "strconv"
    "regexp"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/runCmd"
    "common/misc"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "MEM"
)

func check_mcc_interrupts() (err int) {
    dcli.Println("i", "check mcc interrupts")
    err = errType.SUCCESS
    out, errGo := exec.Command("halctl", "show", "interrupts").Output()
    if errGo != nil {
        dcli.Println("e", "Failed to show interrupts", errGo)
        err = errType.FAIL
        return
    }
    regexMCC := regexp.MustCompile(`.*int_mcc_(ecc.*|controller\s+)`)
    outStr := string(out)
    matches := regexMCC.FindAllString(outStr, -1)
    if matches != nil {
        dcli.Println("e", "Got mcc interrupts")
        err = errType.FAIL
        for _, mccInt := range matches {
            dcli.Println("e", mccInt)
        }
    }
    return
}

func MemDdr_StressHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    secondsPtr := fs.Int("seconds", 900, "number of seconds to run")
    copy_threadsPtr := fs.Int("copy_threads", 16, "number of memory copy threads to run")
    logfilePtr := fs.String("logfile", "stressapptest.log", "log output to file 'logfile'")
    var cmd string
    var err int

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }
    // clear old interrupts before starting test
    dcli.Println("i", "clear old interrupts")
    _, errGo := exec.Command("halctl", "clear", "interrupts").Output()
    if errGo != nil {
        dcli.Println("e", "Failed to clear interrupts", errGo)
        err = errType.FAIL
        return
    }
    misc.SleepInSec(10)
    // check new interrupts before running stress test
    err = check_mcc_interrupts()
    if err != errType.SUCCESS {
        diagEngine.FuncMsgChan <- err
        return
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
    availMemSize = (availMemSize / 1024 / 100) * 100 - 1000;//use available memory - 1G
    dcli.Println("i", "Available memory in Mbytes: ", availMemSize)

    cmd = "/data/nic_util/stressapptest_arm"
    passSign := "Status: PASS - please verify no corrected errors"
    failSign := "Status: FAIL - test discovered HW problems"
    err = runCmd.Run(passSign, failSign, cmd, "-M", strconv.Itoa(availMemSize), "-s", strconv.Itoa(*secondsPtr), "-m", strconv.Itoa(*copy_threadsPtr), "-l", "/data/nic_util/" + *logfilePtr)
    // check interrupts after stress test
    misc.SleepInSec(3)
    err_intr := check_mcc_interrupts()
    if err_intr != errType.SUCCESS {
        diagEngine.FuncMsgChan <- err_intr
        return
    }
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
