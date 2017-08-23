package main

import (
    "flag"
    //"io/ioutil"
    "os"
    "os/exec"
    "strings"

    "config"
    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/misc"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "DIAGMGR"
)

var dspMap = make(map[string]int)
var cardName string
var cardType string

func init() {
    cardName = os.Getenv("CARD_NAME")
    cardType = os.Getenv("CARD_TYPE")
}

func getDspList() []string {
    dspList, err := diagEngine.RedisClient.SMembers("DSP:"+cardName).Result()
    diagEngine.CheckRedisErr(err)

    // Remove diagmgr from the list
    dspList = misc.RmStrFromSlice(dspList, "DIAGMGR")

    return dspList
}

func startDsp(dspList []string, path string) int {
    for _, dsp := range dspList {
        dcli.Println("i", "Starting DSP:", dsp)
        filename := path+strings.ToLower(dsp)
        cmd := exec.Command(filename)

        err := cmd.Start()
        if err != nil {
            dcli.Println("F", "Error starting Cmd", err)
            return errType.Fail
        }

        dspMap[dsp] = cmd.Process.Pid
        dcli.Println("i", "Starting DSP:", dsp, "Done")
    }

    return errType.Success
}

func DiagmgrDsp_StartHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    retVal := errType.Success
    dspList := getDspList()
    if (cardName == "HOST") {
        retVal = startDsp(dspList, config.DiagHostBinPath)
    } else {
        retVal = startDsp(dspList, config.DiagNicBinPath)
    }
    diagEngine.FuncMsgChan <- retVal
    return 
}

func DiagmgrDsp_StopHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    retVal := 0
    for dsp, pid := range (dspMap) {
        dcli.Println("i", "Terminating DSP: ", dsp)
        process, err := os.FindProcess(pid)
        if err != nil {
            dcli.Println("f", "No process named is running:", pid)
            retVal += 1
            dcli.Println("i", "Terminating DSP", dsp, "failed")
            continue
        }

        err = process.Kill()
        if (err != nil) {
            dcli.Println("f", "Terminating process failed: dsp, pid")
            retVal += 1
            dcli.Println("i", "Terminating DSP", dsp, "failed")
            continue
        }
        dcli.Println("i", "Termination Done:", dsp)
        delete(dspMap, dsp)
    }

    // Inform diag engine that test handler is done// Use chan to return error code
    if (retVal != 0) {
        diagEngine.FuncMsgChan <- errType.Fail
    } else {
        diagEngine.FuncMsgChan <- errType.Success
    }
    return
}

func DiagmgrShow_DspHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    for dsp, pid := range (dspMap) {
        dcli.Println("i", "DSP:", dsp, "pid:", pid)
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.Success
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["DSP_START"] = DiagmgrDsp_StartHdl
    diagEngine.FuncMap["DSP_STOP"] = DiagmgrDsp_StopHdl
    diagEngine.FuncMap["DSP_SHOW"] = DiagmgrShow_DspHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
