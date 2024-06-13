package vrminfo

import (
    "os"
)

var SensorTbl map[string]float64

func init() {
    // MALFA
    malfaSensorTbl := make(map[string]float64)
    malfaSensorTbl = map[string]float64 {
        "P12V": 0.002,
        "P3V3": 0.02,
        "VDD_DDR": 0.005,
        "P1V8": 0.02,
        "VDDQ": 0.1,
        "VDD_075_MX": 0.005,
        "VDD_075_PCIE": 0.005,
        "VDD_12_MX": 0.005,
        "VDD_12_PCIE": 0.005,
    }

    CardType := os.Getenv("CARD_TYPE")
    if CardType == "MALFA" {
        SensorTbl = malfaSensorTbl
    }
}

func GetAllSensorInfo() (sensorTbl map[string]float64) {
    return SensorTbl
}

func GetSenseResistance(devName string) (senseResistance float64) {
    return SensorTbl[devName]
}
