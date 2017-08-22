package main

import (
    "flag"
    "io/ioutil"
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
var cardName string
var cardType string

func init() {
    cardName = os.Getenv("CARD_NAME")
    cardType = os.Getenv("CARD_TYPE")
}

func getDspListDev() []string {
    dspList, err := diagEngine.RedisClient.SMembers("DSP:"+cardName+":DEV").Result()
    diagEngine.CheckRedisErr(err)
    return dspList
}

//func getFilesFromPath(path string) []string {
func getFilesFromPath(path string) []string{
    files, err := ioutil.ReadDir(path)
    if err != nil {
        dcli.Println("f", "Failed to read file list")
    }

    fileList := make([]string, len(files))
    for idx, file := range files {
        dcli.Println("i", file.Name())
        fileList[idx] = file.Name()
    }
    return fileList
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
    cardPtr := fs.String("card", "NIC", "Target NIC or HOST")

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    retVal := errType.Success
    if (*cardPtr == "NIC") {
        dspList := getDspListDev()
        retVal = startDsp(dspList, config.DiagNicBinPath)
    } else {
        dspList := getFilesFromPath(config.DiagHostBinPath)
        retVal = startDsp(dspList, config.DiagHostBinPath)
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
