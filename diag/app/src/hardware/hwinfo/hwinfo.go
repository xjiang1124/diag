package hwinfo

import (
    "os"

    "device/fanctrl/adt7462"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "device/psu/pet1600"
    "device/tempsensor/tmp42123"
)

const (
    MAX_NUM_FAN = 4
)

type DispStaFunc func(devName string)(err int)

type I2cHubInfo struct {
    hubName string
    channel byte
}

var cardName string
var uutName string

//===============================
// Naples 
// Pmbus test list
var NaplesPmbusTestList = []string {"VRM_CAPRI_DVDD", "VRM_CAPRI_AVDD", "VRM_HBM", "VRM_ARM"}
// Status display list
var naplesDispStaList map[string]DispStaFunc
// EEPROM list
var naplesEepList = []string {"FRU"}

//===============================
// MTP
// Status display list
var mtpDispStaList map[string]DispStaFunc
// EEPROM list
var mtpEepList = []string {"FRU"}
// I2C hub map
var mtpI2cHubMap map[string] I2cHubInfo

//===============================
// NIC POWER
// Status display list
var nicPwrDispStaList map[string]DispStaFunc

//===============================
// Internal lookup table
var dispMap map[string]map[string]DispStaFunc
var pmbusTestMap map[string][]string
var eepromMap map[string][]string
var i2cHubMap map[string]map[string]I2cHubInfo
var i2cHubList map[string][]string

//===============================
// Public data
// Dev display list
var DispStaList map[string]DispStaFunc
// Pmbus test device list
var PmbusTestList []string
// EEPROM  device list
var EepromList []string
// I2C hub map
var I2cHubMap map[string] I2cHubInfo
var I2cHubList []string

func init() {
    // Can only do map initialization here

    //===============================
    // NIC_POWER
    naplesDispStaList = make(map[string]DispStaFunc)
    naplesDispStaList["VRM_CAPRI_DVDD"] = tps53659.DispStatus
    naplesDispStaList["VRM_CAPRI_AVDD"] = tps53659.DispStatus
    naplesDispStaList["VRM_HBM"]        = tps549a20.DispStatus
    naplesDispStaList["VRM_ARM"]        = tps549a20.DispStatus
    naplesDispStaList["TEMP_SENSOR"]    = tmp42123.DispStatus

    //===============================
    // MTP
    mtpDispStaList = make(map[string]DispStaFunc)
    mtpDispStaList["PSU_1"] = pet1600.DispStatus
    mtpDispStaList["PSU_2"] = pet1600.DispStatus
    mtpDispStaList["DC"]    = tps549a20.DispStatus
    mtpDispStaList["FAN"]   = adt7462.DispStatus

    mtpI2cHubMap = make(map[string]I2cHubInfo)
    mtpI2cHubMap["UUT_1"]  = I2cHubInfo{"HUB_1", 0}
    mtpI2cHubMap["UUT_2"]  = I2cHubInfo{"HUB_1", 1}
    mtpI2cHubMap["UUT_3"]  = I2cHubInfo{"HUB_1", 2}
    mtpI2cHubMap["UUT_4"]  = I2cHubInfo{"HUB_1", 3}
    mtpI2cHubMap["UUT_5"]  = I2cHubInfo{"HUB_2", 0}
    mtpI2cHubMap["UUT_6"]  = I2cHubInfo{"HUB_2", 1}
    mtpI2cHubMap["UUT_7"]  = I2cHubInfo{"HUB_2", 2}
    mtpI2cHubMap["UUT_8"]  = I2cHubInfo{"HUB_2", 3}
    mtpI2cHubMap["UUT_9"]  = I2cHubInfo{"HUB_3", 0}
    mtpI2cHubMap["UUT_10"] = I2cHubInfo{"HUB_3", 1}
    //mtpI2cHubMap["PSU_1"]  = I2cHubInfo{"HUB_4", 0}
    //mtpI2cHubMap["PSU_2"]  = I2cHubInfo{"HUB_4", 1}
    //mtpI2cHubMap["FAN"]    = I2cHubInfo{"HUB_4", 2}
    //mtpI2cHubMap["FRU"]    = I2cHubInfo{"HUB_4", 2}
    //mtpI2cHubMap["DC"]     = I2cHubInfo{"HUB_4", 3}
    //mtpI2cHubMap["CLKGEN"] = I2cHubInfo{"HUB_4", 3}

    mtpI2cHubList := []string{"HUB_1", "HUB_2", "HUB_3", "HUB_4"}
    naplesMtpI2cHubList := []string{"HUB_1"}

    //===============================
    // NIC_POWER
    nicPwrDispStaList = make(map[string]DispStaFunc)
    nicPwrDispStaList["VRM_CAPRI_DVDD"] = tps53659.DispStatus
    nicPwrDispStaList["VRM_CAPRI_AVDD"] = tps53659.DispStatus
    nicPwrDispStaList["VRM_3V3"]        = tps549a20.DispStatus
    nicPwrDispStaList["VRM_1V2"]        = tps549a20.DispStatus

    //===============================
    // Dictionaries for all platforms
    // Display list
    dispMap = make(map[string]map[string]DispStaFunc)
    dispMap["NAPLES100"] = naplesDispStaList
    dispMap["NAPLES_MTP"]= naplesDispStaList
    dispMap["MTP"]       = mtpDispStaList
    dispMap["NIC_POWER"] = nicPwrDispStaList

    // Pmbus test list
    pmbusTestMap = make(map[string][]string)
    pmbusTestMap["NAPLES100"] = NaplesPmbusTestList
    pmbusTestMap["NAPLES_MTP"] = NaplesPmbusTestList

    // EEPROM list
    eepromMap = make(map[string][]string)
    eepromMap["NAPLES100"] = naplesEepList
    eepromMap["NAPLES_MTP"] = naplesEepList
    eepromMap["MTP"]    = mtpEepList

    // I2C hub map
    i2cHubMap = make(map[string]map[string]I2cHubInfo)
    i2cHubMap["MTP"] = mtpI2cHubMap

    i2cHubList = make(map[string][]string)
    i2cHubList["MTP"] = mtpI2cHubList
    i2cHubList["NAPLES_MTP"] = naplesMtpI2cHubList

    //===============================
    // Platform specified list
    cardName = os.Getenv("CARD_TYPE")
    DispStaList   = dispMap[cardName]
    PmbusTestList = pmbusTestMap[cardName]
    EepromList    = eepromMap[cardName]
    I2cHubMap     = i2cHubMap[cardName]
    I2cHubList    = i2cHubList[cardName]
}

