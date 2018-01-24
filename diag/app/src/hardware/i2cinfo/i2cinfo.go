package i2cinfo

import (
    "fmt"
    "os"

    "common/cli"
    "common/errType"

    //"device/psu/pet1600"
)

type I2cInfo struct {
    Name    string
    Comp    string
    Bus     uint32 // I2C controllor index
    DevAddr byte
    Channel byte // TPS53659 only
}

//=========================================
// Naples PMBus table
// devAddr is 7-bit address
var NaplesVrmTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel 
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x2,   0xC4,    0x0 },
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x2,   0xC4,    0x1 },
    I2cInfo {"VRM_HBM",        "TPS549A20", 0x2,   0x36,    0x0 },
    I2cInfo {"VRM_ARM",        "TPS549A20", 0x2,   0x38,    0x0 },
}

var Tps53659TblNaples= []string {"VRM_CAPRI_DVDD", "VRM_CAPRI_AVDD" }
var Tps546a20TblNaples = []string {"VRM_HBM", "VRM_ARMD" }

//=========================================
// NIC power board PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var NicPowerVrmTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel 
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x0,   0x62,    0x0 },
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x0,   0x62,    0x1 },
    I2cInfo {"VRM_3V3",        "TPS549A20", 0x0,   0x1C,    0x0 },
    I2cInfo {"VRM_1V2",        "TPS549A20", 0x0,   0x1B,    0x0 },
}

//=========================================
// MTP PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var MtpI2cTbl = []I2cInfo {
    //       name     comp         Bus  devAddr  channel 
    I2cInfo {"PSU_1", "BEL_POWER", 0x0, 0xB0,    0x0 },
    I2cInfo {"PSU_2", "BEL_POWER", 0x0, 0xB0,    0x0 },
    I2cInfo {"DC",    "TPS549A20", 0x0, 0x38,    0x0 },
    I2cInfo {"FAN",   "ADT7462",   0x0, 0x5C,    0x0 },
    I2cInfo {"CLKGEN","SI52144",   0x0, 0xD6,    0x0 },
    I2cInfo {"HUB_1", "TCA9546A",  0x0, 0xE0,    0x0 },
    I2cInfo {"HUB_2", "TCA9546A",  0x0, 0xE2,    0x0 },
    I2cInfo {"HUB_3", "TCA9546A",  0x0, 0xE4,    0x0 },
    I2cInfo {"HUB_4", "TCA9546A",  0x0, 0xE6,    0x0 },
}

// Dev status list
// Device name must match I2C table
var MtpStaDevList = []string{"PSU_1", "PSU_2", "DC", "FAN"}

func GetI2cInfoByName(name string) (vrmInfo I2cInfo, err int) {
    var vrmTbl []I2cInfo
    cardName := os.Getenv("CARD_NAME")
    if cardName == "NAPLES" {
        vrmTbl = NaplesVrmTbl
    } else {
        cli.Println("f", "Unsupported card:", cardName)
        err = errType.FAIL
        return
    }

    for _, vrmInf := range(vrmTbl) {
        if name == vrmInf.Name {
            return vrmInf, errType.SUCCESS
        }
    }
    return vrmInfo, errType.FAIL

}

func GetI2cTable(cardName string) (vrmTbl []I2cInfo, err int) {
    if cardName == "NAPLES" {
        vrmTbl = NaplesVrmTbl
        return
    } else if cardName == "NIC_POWER" {
        vrmTbl = NicPowerVrmTbl
        return
    } else if cardName == "MTP" {
        vrmTbl = MtpI2cTbl
        return
    } else {
        cli.Println("f", "Unsupported card:", cardName)
        err = errType.UNSUPPORTED_CARD
        return
    }
}

func GetI2cInfoByNameTbl(tblName string, devName string) (vrmInfo I2cInfo, err int) {
    var vrmTbl []I2cInfo
    if  tblName == "NAPLES" {
        vrmTbl = NaplesVrmTbl
    } else if tblName == "NIC_POWER" {
        vrmTbl = NicPowerVrmTbl
    }else if tblName == "MTP" {
        vrmTbl = MtpI2cTbl
    } else {
        cli.Println("f", "Unsupported card:", tblName)
        err = errType.FAIL
        return
    }

    for _, vrmInf := range(vrmTbl) {
        if devName == vrmInf.Name {
            return vrmInf, errType.SUCCESS
        }
    }
    return vrmInfo, errType.FAIL

}

func DispI2cInfoAll(cardName string) (err int) {
    var fmtDig string = "%d"
    var fmtStr = "%-10s"
    var outStr string
    var outStrTemp string

    var i2cTbl []I2cInfo

    // Titles
    i2cTitle := []string {"DEV_NAME", "COMP", "BUS", "DEV_ADDR", "PAGE(PMBus)"}
    outStr = fmt.Sprintf(fmtStr, "NAME")
    for _, title := range(i2cTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)

    outStr = ""
    i2cTbl, err = GetI2cTable(cardName)
    for _, i2cInfo := range(i2cTbl) {
        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Name)
        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Comp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Bus)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.DevAddr)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Channel)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    }
    cli.Println("i", outStr)

    return
}


