package i2cinfo

import (
    "fmt"
    "os"
    "strconv"
    "common/cli"
    "common/errType"
)

var CardType string
var uutType string

type I2cInfo struct {
    Name    string
    Comp    string
    Bus     uint32 // I2C controllor index
    DevAddr byte
    Page    byte   // PMBus device page number
    HubName string
    HubPort byte
}

var I2cTbl    []I2cInfo
var UutI2cTbl []I2cInfo
var CurI2cTbl []I2cInfo

//=========================================
// Naples100 PMBus table
// devAddr is 7-bit address
var Naples100Tbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName     HubPort 
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x2,   0x62,    0x0,    "HUB_NONE", 0},
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x2,   0x62,    0x1,    "HUB_NONE", 0},
    I2cInfo {"VRM_HBM",        "TPS549A20", 0x2,   0x1b,    0x0,    "HUB_NONE", 0},
    I2cInfo {"VRM_ARM",        "TPS549A20", 0x2,   0x1C,    0x0,    "HUB_NONE", 0},
    I2cInfo {"FRU",            "AT24C02C",  0x2,   0x50,    0x0,    "HUB_NONE", 0},
    I2cInfo {"RTC",            "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE", 0},
    I2cInfo {"TEMP_SENSOR",    "TMP422",    0x2,   0x4C,    0x0,    "HUB_NONE", 0},

    I2cInfo {"QSFP_1_FRU",     "QSFP",      0x1,   0xA0,    0x0,    "HUB_NONE", 0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x1,   0xA2,    0x0,    "HUB_NONE", 0},

    I2cInfo {"QSFP_2_FRU",     "QSFP",      0x0,   0xA0,    0x0,    "HUB_NONE", 0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x0,   0xA2,    0x0,    "HUB_NONE", 0},
}

//=========================================
// Naples100 PMBus table
// devAddr is 7-bit address
var NaplesMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName     HubPort 
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x0,   0x62,    0x0,    "NIC_HUB",    2},
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x0,   0x62,    0x1,    "NIC_HUB",    2},
    I2cInfo {"VRM_HBM",        "TPS549A20", 0x0,   0x1b,    0x0,    "NIC_HUB",    2},
    I2cInfo {"VRM_ARM",        "TPS549A20", 0x0,   0x1C,    0x0,    "NIC_HUB",    2},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "NIC_HUB",    2},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "NIC_HUB",    2},
    I2cInfo {"TSENSOR",        "TMP421",    0x0,   0x4C,    0x0,    "NIC_HUB",    2},
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x76,    0x0,    "NIC_HUB",    2},
    I2cInfo {"SWITCH",         "MVL6320",   0x0,   0x76,    0x0,    "NIC_HUB",    2},

    I2cInfo {"QSFP_1_A0",      "QSFP",      0x0,   0x50,    0x0,    "NIC_HUB",    1},
    I2cInfo {"QSFP_1_A2",      "QSFP",      0x0,   0x51,    0x0,    "NIC_HUB",    1},

    I2cInfo {"QSFP_2_A0",      "QSFP",      0x0,   0x50,    0x0,    "NIC_HUB",    3},
    I2cInfo {"QSFP_2_A2",      "QSFP",      0x0,   0x51,    0x0,    "NIC_HUB",    3},

    I2cInfo {"NIC_HUB",        "TCA9546A",  0x0,   0x74,    0x0,    "HUB_NONE",   0},
    I2cInfo {"PEX",            "PEX8716",   0x0,   0x38,    0x0,    "NIC_HUB",    0},
}

//=========================================
// NIC power board PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var NicPowerVrmTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName     HubPort
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x8,   0x62,    0x0,    "HUB_NONE", 0},
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x8,   0x62,    0x1,    "HUB_NONE", 0},
    I2cInfo {"VRM_3V3",        "TPS549A20", 0x8,   0x1C,    0x0,    "HUB_NONE", 0},
    I2cInfo {"VRM_1V2",        "TPS549A20", 0x8,   0x1B,    0x0,    "HUB_NONE", 0},
}

//=========================================
// MTP PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var MtpI2cTbl = []I2cInfo {
    //       name     comp         Bus  devAddr  channel HubName     HubPort
    I2cInfo {"PSU_1", "BEL_POWER", 0x0, 0x5B,    0x0,    "HUB_4",    0},
    I2cInfo {"PSU_2", "BEL_POWER", 0x0, 0x5B,    0x0,    "HUB_4",    1},
    I2cInfo {"FRU",   "AT24C02C",  0x0, 0x50,    0x0,    "HUB_4",    2},
    I2cInfo {"FAN",   "ADT7462",   0x0, 0x5C,    0x0,    "HUB_4",    2},
    I2cInfo {"DC",    "TPS549A20", 0x0, 0x1C,    0x0,    "HUB_4",    3},
    I2cInfo {"CLKGEN","SI52144",   0x0, 0x6B,    0x0,    "HUB_4",    3},
//    I2cInfo {"HUB_1", "TCA9546A",  0x0, 0x70,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"HUB_2", "TCA9546A",  0x0, 0x71,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"HUB_3", "TCA9546A",  0x0, 0x72,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"HUB_4", "TCA9546A",  0x0, 0x73,    0x0,    "HUB_NONE", 0},
}

var MtpHubI2cTbl = []I2cInfo {
    I2cInfo {"HUB_1", "TCA9546A",  0x0, 0x70,    0x0,    "HUB_NONE", 0},
    I2cInfo {"HUB_2", "TCA9546A",  0x0, 0x71,    0x0,    "HUB_NONE", 0},
    I2cInfo {"HUB_3", "TCA9546A",  0x0, 0x72,    0x0,    "HUB_NONE", 0},
    I2cInfo {"HUB_4", "TCA9546A",  0x0, 0x73,    0x0,    "HUB_NONE", 0},
}


func init() {
    CardType = os.Getenv("CARD_TYPE")

    MtpI2cTbl = append(MtpI2cTbl, MtpHubI2cTbl...)
    NaplesMtpTbl = append(NaplesMtpTbl, MtpHubI2cTbl...)
    if CardType == "NAPLES100" {
        I2cTbl = Naples100Tbl
    } else if CardType == "NIC_POWER" {
        I2cTbl = NicPowerVrmTbl
    } else if CardType == "MTP" {
        I2cTbl = MtpI2cTbl
    } else {
        cli.Println("f", "Unsupported card:", CardType)
        return
    }
    CurI2cTbl = I2cTbl

    uutType := os.Getenv("UUT_TYPE")
    if uutType == "NAPLES_MTP" {
        UutI2cTbl = NaplesMtpTbl
    } else if uutType == "UUT_NONE" {
        cli.Println("i", "No need to init UUT I2C table", CardType)
    } else {
        cli.Println("i", "UUT I2C table not intialized:", CardType, uutType)
        return
    }
}

/**
 * Find UUT type based on environment variable
 * TODO: This functionality can be implemented through redis
 */
func FindUutType(uutName string) (uutType string, err int) {
    uutType, found := os.LookupEnv(uutName)
    if found == false {
        cli.Println("e", "Cannot find uutType with uutName", uutName)
        err = errType.INVALID_PARAM
    }
    return
}

/**
 * To support Naples_MTP test card. 
 * Todo: support mix of Naples in the same MTP
 */
func SwitchI2cTbl(uutName string) (err int) {
    if uutName == "UUT_NONE" {
        CurI2cTbl = I2cTbl
        return
    }
    uutType, err := FindUutType(uutName)
    if err != errType.SUCCESS {
        return
    }
    if uutType == "NAPLES_MTP" {
        CurI2cTbl = NaplesMtpTbl
    } else {
        cli.Println("e", "uutType not supported!", uutType)
        err = errType.INVALID_PARAM
    }
    return
}

func SwitchI2cTblByIndex(uutIndex uint) (err int) {
    if uutIndex > 9 {
        cli.Println("e", "uutIndex not supported!", uutIndex)
        err = errType.INVALID_PARAM
        return
    }
    uutName := "UUT_" + strconv.FormatUint(uint64(uutIndex+1), 10)
    uutType, err := FindUutType(uutName)
    if err != errType.SUCCESS {
        return
    }
    if uutType == "NAPLES_MTP" {
        CurI2cTbl = NaplesMtpTbl
    } else {
        cli.Println("e", "uutType not supported!", uutType)
        err = errType.INVALID_PARAM
    }
    return
}

func GetI2cInfo(devName string) (i2cinfo I2cInfo, err int) {
    for _, i2cinfo = range(CurI2cTbl) {
        if devName == i2cinfo.Name {
            return
        }
    }
    cli.Println("f", "Unsupported device:", devName)
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

    for _, i2cInfo := range(CurI2cTbl) {
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

    for _, i2cInfo := range(CurI2cTbl) {
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
    for _, i2cinfo := range(CurI2cTbl) {
        if i2cinfo.Name == devName {
            page = i2cinfo.Page
            return
        }
    }
    cli.Println("f", "Unsupported card:", devName)
    err = errType.INVALID_PARAM
    return
}


