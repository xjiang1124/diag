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
    //var bytecnt int

    data = make([]byte, 256)

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
    for i = 0; i < 256; i++ {
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

    dcli.Printf("i", "Testing %s Check Code and Extended Check Code", devName)

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
    dcli.Printf("i", "Testing %s Check Code and Extended Check Code Passed", devName)

    return
}

func PrintQSFPvendorData(devName string) (vendor string, pn string, sn string, date string, err int) {

    rdData, erri := ReadEepromAll(devName) 
    err = erri
    if err != errType.SUCCESS {
        return
    }

    qsfp_vendor_name := rdData[int(QSFP_VENDOR_NAME_START):int(QSFP_VENDOR_NAME_END + 1)]
    vendor = string(qsfp_vendor_name)

    qsfp_part_num := rdData[int(QSFP_PART_NUM_START):int(QSFP_PART_NUM_END + 1)]
    pn = string(qsfp_part_num)

    qsfp_serial_num := rdData[int(QSFP_SREIAL_NUM_START):int(QSFP_SREIAL_NUM_END + 1)]
    sn = string(qsfp_serial_num)

    qsfp_date_code := rdData[int(QSFP_DATE_CODE_START):int(QSFP_DATE_CODE_END + 1)]
    date = string(qsfp_date_code)

    dcli.Printf("i", "%s  %s  %s  %s \n", vendor, pn, sn, date)
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
