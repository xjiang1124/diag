package main

import (
    "common/diagEngine"
    "common/dcli"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "I2C"
)

var naples100TestList = []string {
    "CAP0_CORE_DVDD", "CAP0_CORE_AVDD", "CAP0_HBM", "CAP0_ARM", "CAP0_3V3",
    "TSENSOR", "RTC",
}

var naples25TestList = []string {
    "CAP0_CORE_DVDD", "CAP0_CORE_AVDD", "CAP0_HBM", "CAP0_ARM", "CAP0_3V3",
    "TSENSOR", "RTC",
}
var i2cTestList []string

//var i2cTestMap map[string][]string

func init() {
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType

    dcli.Init("log_"+dspName+".txt", config.OutputMode)

    i2cTestMap := make(map[string][]string)
    i2cTestMap["NAPLES100"] = naples100TestList
    i2cTestMap["NAPLES25"]  = naples100TestList

    i2cTestList = i2cTestMap[cardType]
}


func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["I2C"] = I2cI2cHdl

    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
