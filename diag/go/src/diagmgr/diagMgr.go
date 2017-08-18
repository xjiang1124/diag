package main

import (
    "flag"
    "os"
    "os/exec"
    "strings"

    "config"
    "common/diagEngine"
    "common/dcli"
    "common/errType"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "DIAGMGR"
)

var dspMap = make(map[string]int)

func getDspList() []string {
    cardInfo := diagEngine.GetCardInfo()
    dspList, err := diagEngine.RedisClient.SMembers("DSP:"+cardInfo.CardName).Result()
    diagEngine.CheckRedisErr(err)
    return dspList
}

func startNicDsp() int {
    dspList := getDspList()

    for _, dsp := range dspList {
        if dsp == "DIAGMGR" {
            continue
        }

        filename := config.DiagNicBinPath+strings.ToLower(dsp)
        cmd := exec.Command(filename)

        err := cmd.Start()
        if err != nil {
            dcli.Println("F", "Error starting Cmd", err)
            return errType.Fail
        }

        dspMap[dsp] = cmd.Process.Pid
    }

    return errType.Success
}

func DiagmgrDsp_StartHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    cardPtr := fs.String("card", "NIC", "Target NIC or HOST")

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    retVal := errType.Success
    if (*cardPtr == "NIC") {
        retVal = startNicDsp()
    } else {
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
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
    diagEngine.FuncMsgChan <- errType.Success
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
