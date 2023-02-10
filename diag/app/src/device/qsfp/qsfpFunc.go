package qsfp

import (
    "common/cli"
    "common/dcli"
    "common/errType"
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "protocol/smbus"
)

func ReadBytes(devName string, offset uint64, numBytes uint64) (data []byte, err int) {
    var i uint64

    data = make([]byte, numBytes)

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    if i2cinfo.CardType == "TAORMINA" {
        err = hwinfo.EnableHubChannelExclusive(devName) 
        if err != errType.SUCCESS {
            cli.Println("e", "Error:  Hub Enable Failed on device", devName)
            return
        }
    }

    for i = 0; i < numBytes; i++ {
        data[i], err = smbus.ReadByte(devName, offset+i)
        if err != errType.SUCCESS {
            return
        }
    }

    return
}

func ReadBytesUpper(devName string, offset uint64, numBytes uint64, page byte) (data []byte, err int) {
//    err = smbus.Open(devName)
//    if err != errType.SUCCESS {
//        return
//    }
//    defer smbus.Close()
//
//    err = smbus.WriteByte(devName, 127, page)
//    if err != errType.SUCCESS {
//        return
//    }

    data, err = ReadBytes(devName, offset, numBytes)
    if err != errType.SUCCESS {
        return
    }

    return
}

func ReadEepromAll(devName string) (data []byte, err int) {
    var i uint64
    
    data = make([]byte, 256)

    for i = 0; i < 256; i++ {
        data8 := []uint8{}
        data8, err = ReadBytes(devName, i, 1)
        data[i] = data8[0]
        if err != errType.SUCCESS {
            cli.Printf("e", "Error:  I2C Read failed on Device %s from byte %d", devName, i)
            return
        }
    }

    return
}

func VerifyCheckSums(devName string) (err int) {
    var computed_cc uint8  = 0
    var computed_cc_ext uint8  = 0

    dcli.Printf("i", "Testing %s Check Code and Extended Check Code\n", devName)

    rdData, erri := ReadEepromAll(devName) 
    err = erri
    if err != errType.SUCCESS {
        return
    }
    for i:=QSFP_CC_BASE_START; i < (QSFP_CC_BASE); i++ {
        computed_cc = computed_cc + rdData[i]
    }

    if computed_cc != rdData[QSFP_CC_BASE] {
        dcli.Printf("e", "Error %s:  Computer CC and Read CC Do not match.  Read CC = 0x%x.   Computer CC = 0x%x\n", devName, rdData[QSFP_CC_BASE], computed_cc)
        err = errType.FAIL
        return
    }

    for i:=int(QSFP_CC_BASE + 1); i < int(QSFP_CC_EXT_BASE); i++ {
        computed_cc_ext = computed_cc_ext + rdData[i]
    }

    if computed_cc_ext != rdData[QSFP_CC_EXT_BASE] {
        dcli.Printf("e", "Error %s:  Computer CC Extended and Read CC Extended Do not match.  Read CC = 0x%x.   Computer CC = 0x%x\n", devName, rdData[QSFP_CC_EXT_BASE], computed_cc_ext)
        err = errType.FAIL
        return
    }
    dcli.Printf("i", "Testing %s Check Code and Extended Check Code Passed\n", devName)

    return
}

func PrintQSFPvendorData(devName string) (vendor string, pn string, sn string, date string, err int) {

    vendor, err = ReadVendorName(devName)
    if err != errType.SUCCESS {
        return
    }

    pn, err = ReadPN(devName)
    if err != errType.SUCCESS {
        return
    }

    sn, err = ReadSerialNumber(devName)
    if err != errType.SUCCESS {
        return
    }

    date, err = ReadDate(devName)
    if err != errType.SUCCESS {
        return
    }

    cli.Printf("i", "%s  %s  %s  %s \n", vendor, pn, sn, date)
    return
}

func GetBitSpeed(devName string) (baudrate float64, err int) {
    data8 := []uint8{}

    data8, err = ReadBytes(devName, uint64(QSFP_BR_ADDR), 1)
    if err != errType.SUCCESS {
        return
    }
    baudrate = float64(data8[0]) * 100 
    baudrate = baudrate / 1000
    return
}


func GetFieldInfo(qsfpTbl []qsfpPage_t, field string) (fieldInfo qsfpPage_t, err int) {
    for _, fieldInfo = range(qsfpTbl) {
        if fieldInfo.name == field {
            return
        }
    }
    err = errType.INVALID_PARAM
    return
}

func ReadField(devName string, field string) (data []byte, err int) {
    fieldInfo, err := GetFieldInfo(lowerPage, field)
    if err != errType.SUCCESS {
        return
    }

    data, err = ReadBytes(devName, fieldInfo.offset, fieldInfo.numBytes)
    return
}

func ReadFieldUpper(devName string, field string, page byte) (data []byte, err int) {
    var upperTbl []qsfpPage_t

    if page == 0 {
        upperTbl = upperPage00
    } else {
        err = errType.INVALID_PARAM
        return
    }

    fieldInfo, err := GetFieldInfo(upperTbl, field)
    if err != errType.SUCCESS {
        return
    }

    data, err = ReadBytesUpper(devName, fieldInfo.offset, fieldInfo.numBytes, page)
    return
}

func ReadId(devName string) (id byte, err int) {
    data, err := ReadFieldUpper(devName, "ID", 0)
    id = data[0]
    return
}

func ReadVendorName(devName string) (vendorname string, err int) {
    data, err := ReadFieldUpper(devName, "VEND_NAME", 0)
    vendorname = string(data)
    return
}

func ReadPN(devName string) (partnumber string, err int) {
    data, err := ReadFieldUpper(devName, "VEND_PN", 0)
    partnumber = string(data)
    return
}

func ReadSerialNumber(devName string) (serialnumber string, err int) {
    data, err := ReadFieldUpper(devName, "VEND_SN", 0)
    serialnumber = string(data)
    return
}

func ReadDate(devName string) (date string, err int) {
    data, err := ReadFieldUpper(devName, "DATE_CODE", 0)
    date = string(data)
    return
}




func LaserEnDis(devName string, enDis int) (err int) {
    var data byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    if enDis == ENABLE {
        data = 0x0
    } else {
        data =0xF
    }

    if i2cinfo.CardType == "TAORMINA" {
        err = hwinfo.EnableHubChannelExclusive(devName) 
        if err != errType.SUCCESS {
            cli.Println("e", "Error:  Hub Enable Failed on device", devName)
            return
        }
    }

    err = smbus.WriteByte(devName, 0x86, data)
    if err != errType.SUCCESS {
        return
    }

    return
}

func LaserEnable(devName string) (err int) {
    err = LaserEnDis(devName, ENABLE)
    return
}

func LaserDisable(devName string) (err int) {
    err = LaserEnDis(devName, DISABLE)
    return
}
