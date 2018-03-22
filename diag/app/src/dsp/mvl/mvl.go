package main

import (
    "flag"
	"common/spi"
    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "MVL"
)

const MVL_ID = 0x115
const MVL_ID_REG = 0x3

func Mvl_Init() {
    //in case no EEPROM
}

func Mvl_AccHdl(argList []string) {
    var data uint32

	MvlRegRead(MVL_ID_REG, &data)
	if data != MVL_ID {
	    dcli.Println(ERROR, "MVL acc test failed!")
	    diagEngine.FuncMsgChan <- errType.
	}
	else {
	    diagEngine.FuncMsgChan <- errType.Success
	}
    return
}

func Mvl_PrbsHdl(argList []string) {
    var data uint32
	//get duration, port mask
	
	//start PRBS
	
	//check error counter
	
	if data != MVL_ID {
	    dcli.Println(ERROR, "MVL acc test failed!")
	    diagEngine.FuncMsgChan <- errType.
	}
	else {
	    diagEngine.FuncMsgChan <- errType.Success
	}
    return
}

func Mvl_TrfcHdl(argList []string) {
    var data uint32

	//get packet number, port mask
	
	//start traffic
	
	//check error counter
	
	if data != MVL_ID {
	    dcli.Println(ERROR, "MVL acc test failed!")
	    diagEngine.FuncMsgChan <- errType.
	}
	else {
	    diagEngine.FuncMsgChan <- errType.Success
	}
    return
}

func Mvl_LedHdl(argList []string) {
    var data uint32

	//duration, port mask?
	
	MvlRegRead(MVL_ID_REG, &data)
	if data != MVL_ID {
	    dcli.Println(ERROR, "MVL acc test failed!")
	    diagEngine.FuncMsgChan <- errType.
	}
	else {
	    diagEngine.FuncMsgChan <- errType.Success
	}
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["ACC"]	= Mvl_AccHdl
    diagEngine.FuncMap["PRBS"]	= Mvl_PrbsHdl
    diagEngine.FuncMap["TRF"]	= Mvl_TrfHdl
    diagEngine.FuncMap["LED"]	= Mvl_LedHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
