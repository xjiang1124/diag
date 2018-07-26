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
    dspName = "QSFP"
)

var naples100QsfpList = []string {"QSFP_1", "QSFP_2"}
var qsfpTestList []string

//var qsfpTestMap map[string][]string

func init() {
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType

    dcli.Init("log_"+dspName+".txt", config.OutputMode)

    qsfpTestMap := make(map[string][]string)
    qsfpTestMap["NAPLES100"] = naples100QsfpList

    qsfpTestList = qsfpTestMap[cardType]
}
func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["I2C"] = QsfpI2CHdl
    diagEngine.FuncMap["laser_en"] = QsfpLaser_EnHdl
    diagEngine.FuncMap["laser_dis"] = QsfpLaser_DisHdl
    diagEngine.FuncMap["present"] = QsfpPresentHdl

    //dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
