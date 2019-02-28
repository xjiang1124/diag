package main

import (
    //"flag"

    "common/diagEngine"
    "common/dcli"
    //"common/errType"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "SFP"
)

// FIXME: SFP list should move to hwinfo module
var naples25SfpList = []string {"SFP_1", "SFP_2"}
var sfpTestList []string

//var sfpTestMap map[string][]string

func init() {
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType

    dcli.Init("log_"+dspName+".txt", config.OutputMode)

    sfpTestMap := make(map[string][]string)
    sfpTestMap["NAPLES25"] = naples25SfpList

    sfpTestList = sfpTestMap[cardType]
}
func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["I2C"] = SfpI2CHdl
    diagEngine.FuncMap["LASER"] = SfpLaserHdl
    diagEngine.FuncMap["present"] = SfpPresentHdl

    //dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
