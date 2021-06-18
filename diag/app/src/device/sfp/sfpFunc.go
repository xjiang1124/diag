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

    dcli.Printf("i", "Testing %s Check Code and Extended Check Code", devName)

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
    dcli.Printf("i", "Testing %s Check Code and Extended Check Code Passed", devName)

    return
}

func PrintSFPvendorData(devName string) (vendor string, pn string, sn string, date string, err int) {

    rdData, erri := ReadEepromAll(devName) 
    err = erri
    if err != errType.SUCCESS {
        return
    }

    sfp_vendor_name := rdData[int(SFP_VENDOR_NAME_START):int(SFP_VENDOR_NAME_END + 1)]
    vendor = string(sfp_vendor_name)

    sfp_part_num := rdData[int(SFP_PART_NUM_START):int(SFP_PART_NUM_END + 1)]
    pn = string(sfp_part_num)

    sfp_serial_num := rdData[int(SFP_SREIAL_NUM_START):int(SFP_SREIAL_NUM_END + 1)]
    sn = string(sfp_serial_num)

    sfp_date_code := rdData[int(SFP_DATE_CODE_START):int(SFP_DATE_CODE_END + 1)]
    date = string(sfp_date_code)

    dcli.Printf("i", "%s  %s  %s  %s \n", vendor, string(pn), string(sn), string(date))
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

