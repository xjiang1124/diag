package main

import (
	"common/dcli"
	"common/diagEngine"
	"common/runCmd"
	"config"
	"flag"
)

//========================================================
// Constant definition
const (
	// Each DSP should know it own name
	dspName = "SYS"
)

func SysLedHdl(argList []string) {
	fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
	var cmd string
	var err int

	errFs := fs.Parse(argList)
	if errFs != nil {
		dcli.Println("e", "Parse failed", errFs)
	}
	cmd = ""
	passSign := ""
	failSign := ""
	err = runCmd.Run(passSign, failSign, cmd)
	// Inform diag engine that test handler is done
	// Use chan to return error code
	diagEngine.FuncMsgChan <- err
	return
}

func TempAlertHdl(argList []string) {
	fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
	var cmd string
	var err int

	errFs := fs.Parse(argList)
	if errFs != nil {
		dcli.Println("e", "Parse failed", errFs)
	}
	cmd = ""
	passSign := ""
	failSign := ""
	err = runCmd.Run(passSign, failSign, cmd)
	// Inform diag engine that test handler is done
	// Use chan to return error code
	diagEngine.FuncMsgChan <- err
	return
}

func main() {
	diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
	diagEngine.FuncMap["LED"] = SysLedHdl
	diagEngine.FuncMap["TEMPALERT"] = TempAlertHdl

	dcli.Init("log_"+dspName+".txt", config.OutputMode)
	diagEngine.CardInfoInit(dspName)
	diagEngine.DspInfraInit()
	diagEngine.DspInfraMainLoop()
}
