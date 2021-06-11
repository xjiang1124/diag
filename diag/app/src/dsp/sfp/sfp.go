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
var taorminaSfpList = []string {"SFP_1", "SFP_2","SFP_2", "SFP_3","SFP_5", "SFP_6","SFP_7", "SFP_8",
                                "SFP_9", "SFP_10","SFP_11", "SFP_12","SFP_13", "SFP_14","SFP_15", "SFP_16",
                                "SFP_17", "SFP_18","SFP_19", "SFP_20","SFP_21", "SFP_22","SFP_23", "SFP_24",
                                "SFP_25", "SFP_26","SFP_27", "SFP_28","SFP_29", "SFP_30","SFP_31", "SFP_32",
                                "SFP_33", "SFP_34","SFP_35", "SFP_36","SFP_37", "SFP_38","SFP_39", "SFP_40",
                                "SFP_41", "SFP_42","SFP_43", "SFP_44","SFP_45", "SFP_46","SFP_47", "SFP_48"}
var sfpTestList []string

//var sfpTestMap map[string][]string

func init() {
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType

    dcli.Init("log_"+dspName+".txt", config.OutputMode)

    sfpTestMap := make(map[string][]string)
    sfpTestMap["NAPLES25"] = naples25SfpList
    sfpTestMap["NAPLES25SWM"] = naples25SfpList
    sfpTestMap["NAPLES25SWMDELL"] = naples25SfpList
    sfpTestMap["NAPLES25SWM833"] = naples25SfpList
    sfpTestMap["NAPLES25OCP"] = naples25SfpList
    sfpTestMap["TAORMINA"] = taorminaSfpList

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
