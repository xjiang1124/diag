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
    "CAP0_CORE_DVDD", "CAP0_CORE_AVDD", "CAP0_HBM", "CAP0_ARM", "CAP0_3V3", "FRU",
}

var biodonaTestList = []string {
    "ELB0_CORE", "ELB0_ARM", "VDDQ_DDR", "VDD_DDR",
    "TSENSOR", "RTC",
}

var AdiTestList = []string {
    "TSENSOR", "RTC",
}

var laconaTestList = []string {
    "ELB0_CORE", "ELB0_ARM", "VDDQ_DDR",
    "TSENSOR", "RTC",
}

var ginestraTestList = []string {
    "GIG0_CORE", "GIG0_ARM", "DDR_VDDQ", "VDD_DDR",
    "TSENSOR", "RTC",
}

var i2cTestList []string

//var i2cTestMap map[string][]string

func init() {
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType

    dcli.Init("log_"+dspName+".txt", config.OutputMode)

    i2cTestMap := make(map[string][]string)
    i2cTestMap["NAPLES100"]       = naples100TestList
    i2cTestMap["NAPLES25"]        = naples100TestList
    i2cTestMap["NAPLES25SWM"]     = naples100TestList
    i2cTestMap["NAPLES25SWMDELL"] = naples100TestList
    i2cTestMap["NAPLES25SWM833"]  = naples100TestList
    i2cTestMap["NAPLES25OCP"]     = naples100TestList
    i2cTestMap["FORIO"]           = naples100TestList
    i2cTestMap["VOMERO"]          = naples100TestList
    i2cTestMap["VOMERO2"]         = naples100TestList
    i2cTestMap["NAPLES100IBM"]    = naples100TestList
    i2cTestMap["NAPLES100HPE"]    = naples100TestList
    i2cTestMap["NAPLES100DELL"]    = naples100TestList
    i2cTestMap["NAPLES25WFG"]     = naples100TestList
    i2cTestMap["BIODONA_D4"]      = biodonaTestList
    i2cTestMap["BIODONA_D5"]      = biodonaTestList
    i2cTestMap["ORTANO"]          = biodonaTestList
    i2cTestMap["ORTANO2"]         = biodonaTestList
    i2cTestMap["ORTANO2A"]        = AdiTestList
    i2cTestMap["ORTANO2AC"]       = AdiTestList
    i2cTestMap["ORTANO2I"]        = biodonaTestList
    i2cTestMap["ORTANO2S"]        = biodonaTestList
    i2cTestMap["LACONA32DELL"]    = laconaTestList
    i2cTestMap["LACONA32"]        = laconaTestList
    i2cTestMap["POMONTEDELL"]     = laconaTestList
    i2cTestMap["POMONTE"]         = laconaTestList
    i2cTestMap["GINESTRA_D4"]     = ginestraTestList
    i2cTestMap["GINESTRA_D5"]     = ginestraTestList
    //Platform TAORMINA uses it's I2C INFO Table directly in i2cTest.go to get devices.  Do not set a table here for it

    i2cTestList = i2cTestMap[cardType]
}


func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["I2C"] = I2cI2cHdl

    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
