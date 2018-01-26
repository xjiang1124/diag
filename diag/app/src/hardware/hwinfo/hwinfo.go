package hwinfo

import (
    "os"
    "device/psu/pet1600"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "device/fanctrl/adt7462"
    "device/tempsensor/tmp422"
)

const (
    MAX_NUM_FAN = 4
)

type DispStaFunc func(devName string)(err int)

//===============================
// Naples 
// Pmbus test list
var NaplesPmbusTestList= []string {"VRM_CAPRI_DVDD", "VRM_CAPRI_AVDD", "VRM_HBM", "VRM_ARM"}
// Status display list
var naplesDispStaList map[string]DispStaFunc

//===============================
// MTP
// Status display list
var mtpDispStaList map[string]DispStaFunc

//===============================
// NIC POWER
// Status display list
var nicPwrDispStaList map[string]DispStaFunc

//===============================
// Internal lookup table
var dispMap map[string]map[string]DispStaFunc
var pmbusTestMap map[string][]string

//===============================
// Public data
// Dev display list
var DispStaList map[string]DispStaFunc
// Pmbus test device liest
var PmbusTestList []string

func init() {
    // Can only do map initialization here

    //===============================
    // NIC_POWER
    naplesDispStaList = make(map[string]DispStaFunc)
    naplesDispStaList["VRM_CAPRI_DVDD"] = tps53659.DispStatus
    naplesDispStaList["VRM_CAPRI_AVDD"] = tps53659.DispStatus
    naplesDispStaList["VRM_HBM"]        = tps549a20.DispStatus
    naplesDispStaList["VRM_ARM"]        = tps549a20.DispStatus
    naplesDispStaList["TEMP_SENSOR"]    = tmp422.DispStatus

    //===============================
    // MTP
    mtpDispStaList = make(map[string]DispStaFunc)
    mtpDispStaList["PSU_1"] = pet1600.DispStatus
    mtpDispStaList["PSU_2"] = pet1600.DispStatus
    mtpDispStaList["DC"]    = tps549a20.DispStatus
    mtpDispStaList["FAN"]   = adt7462.DispStatus

    //===============================
    // NIC_POWER
    nicPwrDispStaList = make(map[string]DispStaFunc)
    nicPwrDispStaList["VRM_CAPRI_DVDD"] = tps53659.DispStatus
    nicPwrDispStaList["VRM_CAPRI_AVDD"] = tps53659.DispStatus
    nicPwrDispStaList["VRM_3V3"]        = tps549a20.DispStatus
    nicPwrDispStaList["VRM_1V2"]        = tps549a20.DispStatus

    //===============================
    dispMap = make(map[string]map[string]DispStaFunc)
    dispMap["NAPLES"]    = naplesDispStaList
    dispMap["MTP"]       = mtpDispStaList
    dispMap["NIC_POWER"] = nicPwrDispStaList

    pmbusTestMap = make(map[string][]string)
    pmbusTestMap["NAPLES"] = NaplesPmbusTestList

    cardName := os.Getenv("CARD_NAME")
    DispStaList = dispMap[cardName]
    PmbusTestList = pmbusTestMap[cardName]
}

