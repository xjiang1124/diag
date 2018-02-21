package i2cinfo

import (
    "fmt"
    "os"

    "common/cli"
    "common/errType"
)

var cardName string

type I2cInfo struct {
    Name    string
    Comp    string
    Bus     uint32 // I2C controllor index
    DevAddr byte
    Page    byte   // PMBus device page number
}

var I2cTbl []I2cInfo

//=========================================
// Naples PMBus table
// devAddr is 7-bit address
var NaplesVrmTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel 
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x2,   0xC4,    0x0 },
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x2,   0xC4,    0x1 },
    I2cInfo {"VRM_HBM",        "TPS549A20", 0x2,   0x36,    0x0 },
    I2cInfo {"VRM_ARM",        "TPS549A20", 0x2,   0x38,    0x0 },
    I2cInfo {"FRU",            "AT24C02C",  0x2,   0xA0,    0x0 },
    I2cInfo {"RTC",            "PCF85263A", 0x2,   0xA2,    0x0 },
    I2cInfo {"TEMP_SENSOR",    "TMP422",    0x2,   0x98,    0x0 },

    I2cInfo {"QSFP_1_FRU",     "QSFP",      0x1,   0xA0,    0x0 },
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x1,   0xA2,    0x0 },

    I2cInfo {"QSFP_2_FRU",     "QSFP",      0x0,   0xA0,    0x0 },
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x0,   0xA2,    0x0 },
}

//=========================================
// NIC power board PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var NicPowerVrmTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel 
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x8,   0x62,    0x0 },
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x8,   0x62,    0x1 },
    I2cInfo {"VRM_3V3",        "TPS549A20", 0x8,   0x1C,    0x0 },
    I2cInfo {"VRM_1V2",        "TPS549A20", 0x8,   0x1B,    0x0 },
}

//=========================================
// MTP PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var MtpI2cTbl = []I2cInfo {
    //       name     comp         Bus  devAddr  channel 
    I2cInfo {"PSU_1", "BEL_POWER", 0x8, 0x5B,    0x0 },
    I2cInfo {"PSU_2", "BEL_POWER", 0x8, 0x5B,    0x0 },
    I2cInfo {"DC",    "TPS549A20", 0x8, 0x1C,    0x0 },
    I2cInfo {"FAN",   "ADT7462",   0x8, 0x5C,    0x0 },
    I2cInfo {"CLKGEN","SI52144",   0x8, 0x6B,    0x0 },
    I2cInfo {"HUB_1", "TCA9546A",  0x8, 0x70,    0x0 },
    I2cInfo {"HUB_2", "TCA9546A",  0x8, 0x71,    0x0 },
    I2cInfo {"HUB_3", "TCA9546A",  0x8, 0x72,    0x0 },
    I2cInfo {"HUB_4", "TCA9546A",  0x8, 0x73,    0x0 },
    I2cInfo {"FRU",   "AT24C02C",  0x8, 0x50,    0x0 },
}

func init() {
    cardName = os.Getenv("CARD_NAME")

    if cardName == "NAPLES" {
        I2cTbl = NaplesVrmTbl
        return
    } else if cardName == "NIC_POWER" {
        I2cTbl = NicPowerVrmTbl
        return
    } else if cardName == "MTP" {
        I2cTbl = MtpI2cTbl
        return
    } else {
        cli.Println("f", "Unsupported card:", cardName)
        return
    }
}

func GetI2cInfo(devName string) (i2cInfo I2cInfo, err int) {
    for _, i2cInf := range(I2cTbl) {
        if devName == i2cInf.Name {
            return i2cInf, errType.SUCCESS
        }
    }
    err = errType.INVALID_PARAM
    return

}

func DispI2cInfo(devName string) (err int) {
    var fmtDig string = "%d"
    var fmtHex string = "0x%x"
    var fmtStr = "%-15s"
    var outStr string
    var outStrTemp string

    // Titles
    i2cTitle := []string {"DEV_NAME", "COMP", "BUS", "DEV_ADDR", "PAGE(PMBus)"}
    for _, title := range(i2cTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)

    for _, i2cInfo := range(I2cTbl) {
        if i2cInfo.Name != devName {
            continue
        }
        outStr = ""

        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Name)
        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Comp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Bus)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtHex, i2cInfo.DevAddr)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Page)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        cli.Println("i", outStr)
        return
    }
    err = errType.SUCCESS
    cli.Println("f", "Unsupported device:", devName)
    return
}

func DispI2cInfoAll() (err int) {
    var fmtDig string = "%d"
    var fmtHex string = "0x%x"
    var fmtStr = "%-15s"
    var outStr string
    var outStrTemp string

    // Titles
    i2cTitle := []string {"DEV_NAME", "COMP", "BUS", "DEV_ADDR", "PAGE(PMBus)"}
    for _, title := range(i2cTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)

    for _, i2cInfo := range(I2cTbl) {
        outStr = ""

        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Name)
        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Comp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Bus)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtHex, i2cInfo.DevAddr)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Page)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        cli.Println("i", outStr)
    }

    return
}

func GetPage(devName string) (page byte, err int) {
    for _, i2cinfo := range(I2cTbl) {
        if i2cinfo.Name == devName {
            page = i2cinfo.Page
            return
        }
    }
    cli.Println("f", "Unsupported card:", devName)
    err = errType.INVALID_PARAM
    return

}

