package sfp

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

func ReadEepromAll(devName string) (data []byte, err int) {
    var i uint64
    //var bytecnt int

    data = make([]byte, 128)

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    //func ReadBlock(devName string, regAddr uint64, buf []byte) (byteCnt int, err int) {

    //for i = 0; i < 128; i=i+16 {
    //    bytecnt, err = smbus.ReadBlock(devName, i, buf)
    //    if err != errType.SUCCESS {
    //        return
    //    }
    //    fmt.Printf(" Bytecnt=%d\n", bytecnt);
    //    data = append(data, buf...)
    //}
    for i = 0; i < 128; i++ {
        data[i], err = smbus.ReadByte(devName, i)
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
    for i:=0; i < int(SFP_CC_BASE); i++ {
        computed_cc = computed_cc + rdData[i]
    }

    if computed_cc != rdData[SFP_CC_BASE] {
        dcli.Printf("e", "Error %s:  Computer CC and Read CC Do not match.  Read CC = 0x%x.   Computer CC = 0x%x\n", devName, rdData[SFP_CC_BASE], computed_cc)
        err = errType.FAIL
        return
    }

    for i:=int(SFP_CC_BASE + 1); i < int(SFP_CC_EXT_BASE); i++ {
        computed_cc_ext = computed_cc_ext + rdData[i]
    }

    if computed_cc_ext != rdData[SFP_CC_EXT_BASE] {
        dcli.Printf("e", "Error %s:  Computer CC Extended and Read CC Extended Do not match.  Read CC = 0x%x.   Computer CC = 0x%x\n", devName, rdData[SFP_CC_EXT_BASE], computed_cc_ext)
        err = errType.FAIL
        return
    }
    dcli.Printf("i", "Testing %s Check Code and Extended Check Code Passed\n", devName)

    return
}

func GetBitSpeed(devName string) (baudrate float64, err int) {
    reg12 := []uint8{}
    reg66 := []uint8{}

    reg12, err = ReadBytes(devName, uint64(SFP_BITRATE_NOM), 1)
    if err != errType.SUCCESS {
        return
    }
    reg66, err = ReadBytes(devName, uint64(SFP_BITRATE_MAX), 1)
    if err != errType.SUCCESS {
        return
    }

    if reg12[0] == uint8(0xFF) {
        baudrate = float64(reg12[0]) * 100 
    } else {
        baudrate = float64(reg66[0]) * 250
    }
    baudrate = baudrate / 1000
    return
}


func PrintSFPvendorData(devName string) (vendor string, pn string, sn string, date string, err int) {
    var bitspeed float64
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

    bitspeed, err = GetBitSpeed(devName)
    if err != errType.SUCCESS {
        return
    }
    dcli.Printf("i", "%s VENDOR: %s PN: %s SN: %s DATE: %s SPD: %.01fGb/s\n", devName, vendor, pn, sn, date, bitspeed)
    return
}

func GetFieldInfo(sfpTbl []sfpPage_t, field string) (fieldInfo sfpPage_t, err int) {
    for _, fieldInfo = range(sfpTbl) {
        if fieldInfo.name == field {
            return
        }
    }
    err = errType.INVALID_PARAM
    return
}

func ReadField(devName string, field string) (data []byte, err int) {
    fieldInfo, err := GetFieldInfo(regTblA0, field)
    if err != errType.SUCCESS {
        return
    }

    data, err = ReadBytes(devName, fieldInfo.offset, fieldInfo.numBytes)
    return
}

func ReadId(devName string) (id byte, err int) {
    data, err := ReadField(devName, "ID")
    id = data[0]
    return
}

func ReadPN(devName string) (pn string, err int) {
    data, err := ReadField(devName, "PN")
    pn = string(data)
    return
}

func ReadVendorName(devName string) (vendorname string, err int) {
    data, err := ReadField(devName, "VENDORNAME")
    vendorname = string(data)
    return
}

func ReadSerialNumber(devName string) (sn string, err int) {
    data, err := ReadField(devName, "SERIALNUMBER")
    sn = string(data)
    return
}

func ReadDate(devName string) (date string, err int) {
    data, err := ReadField(devName, "DATE")
    date = string(data)
    return
}


