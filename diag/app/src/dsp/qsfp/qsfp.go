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
var taorminaQsfpList = []string {"QSFP_1", "QSFP_2", "QSFP_3", "QSFP_4", "QSFP_5", "QSFP_6"}
var qsfpTestList []string

//var qsfpTestMap map[string][]string

func init() {
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType

    dcli.Init("log_"+dspName+".txt", config.OutputMode)

    qsfpTestMap := make(map[string][]string)
    qsfpTestMap["NAPLES100"] = naples100QsfpList
    qsfpTestMap["FORIO"] = naples100QsfpList
    qsfpTestMap["VOMERO"] = naples100QsfpList
    qsfpTestMap["VOMERO2"] = naples100QsfpList
    qsfpTestMap["ORTANO"] = naples100QsfpList
    qsfpTestMap["ORTANO2"] = naples100QsfpList
    qsfpTestMap["ORTANO2A"] = naples100QsfpList
    qsfpTestMap["ORTANO2I"] = naples100QsfpList
    qsfpTestMap["POMONTEDELL"] = naples100QsfpList
    qsfpTestMap["POMONTE"] = naples100QsfpList
    qsfpTestMap["NAPLES100_IBM"] = naples100QsfpList
    qsfpTestMap["NAPLES100DELL"] = naples100QsfpList
    qsfpTestMap["TAORMINA"] = taorminaQsfpList

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
