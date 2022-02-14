package main

import (
    "flag"
    "strconv"

    "common/dcli"
    "common/diagEngine"
    //"common/errType"
    "config"
    "common/runCmd"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "I2CSPI"
)

func I2CspiI2CspiHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    slotPtr := fs.Int("slot", 1, "NIC slot number")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    slot := *slotPtr
    err := runCmd.Run("I2CSPI TEST PASSED", "I2CSPI TEST FAILED", "/home/diag/diag/scripts/i2cspi_test.sh", strconv.Itoa(slot))

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["I2CSPI"] = I2CspiI2CspiHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
