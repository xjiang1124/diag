package main

import (
    "flag"
    //"io/ioutil"
    "os"
    "os/exec"
    "strings"
    //"syscall"

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

//var dspMap = make(map[string]int)
var dspMap = make(map[string] *exec.Cmd)
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
        //cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}

        err := cmd.Start()
        if err != nil {
            dcli.Println("F", "Error starting Cmd", err)
            return errType.FAIL
        }
        //cmd.Wait()

        //dspMap[dsp] = cmd.Process.Pid
        dspMap[dsp] = cmd
        dcli.Println("i", "Starting DSP:", dsp, "Done")
    }

    return errType.SUCCESS
}

func stopDsp() int {
    retVal := 0
    //for dsp, pid := range (dspMap) {
    for dsp, cmd := range (dspMap) {
        dcli.Println("i", "Terminating DSP: ", dsp)

        err := cmd.Process.Kill()
        if (err != nil) {
            dcli.Println("f", "Terminating process failed: dsp, pid")
            retVal += 1
            dcli.Println("i", "Terminating DSP", dsp, "failed")
            continue
        }

        dcli.Println("i", "Termination Done:", dsp)
        delete(dspMap, dsp)
    }

    if retVal == 0 {
        return errType.SUCCESS
    } else {
        return errType.FAIL
    }

}

func DiagmgrDsp_StartHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }
    retVal := errType.SUCCESS

    // Stop all DSPs first
    retVal = stopDsp()
    if retVal != errType.SUCCESS {
        diagEngine.FuncMsgChan <- retVal
        return 
    }

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

    retVal := stopDsp()
    diagEngine.FuncMsgChan <- retVal
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
    diagEngine.FuncMsgChan <- errType.SUCCESS
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
