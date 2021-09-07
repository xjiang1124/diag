package dps800

import (
    "fmt"
    "os"
    "strconv"
    //"cardinfo"
    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "protocol/pmbus"
    "protocol/smbus"
    "device/fpga/taorfpga"
)



func I2cTest(devname string) (err int) { 
    var psuNumber uint32 = 0
    wrData := []byte{}
    mfgId := []byte{}
    expected := []byte{0x05, 0x44, 0x45, 0x4c, 0x54, 0x41}

    if devname == "PSU_1" {
        psuNumber = 0
    } else {
        psuNumber = 1
    }

    present, errGo := taorfpga.PSU_present(psuNumber)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    if present != true {
        cli.Printf("e", "%s: is not present", devname)
        err = errType.FAIL
        return
    }


    iInfo, err := i2cinfo.GetI2cInfo(devname)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain I2C info of", devname)
        return
    }
    wrData = append(wrData, MFR_ID)
    mfgId, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_ID_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgId) != MFG_ID_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MfgID is wrong.   Len=%d.  Expect=%d", devname, len(mfgId), MFG_ID_BLK_SIZE + 1)
    }
    for i:=0; i<(MFG_ID_BLK_SIZE + 1); i++ {
        if expected[i] != mfgId[i] {
            err = errType.FAIL
            cli.Printf("e", "%s: MFG ID is wrong.  Expected[%d]=%.02x     Read[%d]=%.02x", devname, i, expected[i], mfgId[i])
        }
    }
    return
}



func ReadStatus(devName string) (status uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}



//Read target voltage from VOUT 
func ReadVin(devName string) (integer uint64, dec uint64, err int) {
    var VIN uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    VIN, err = pmbus.ReadWord(devName, READ_VIN)

    integer, dec, err =  pmbus.Linear11(VIN)

    return
}


//Read target voltage from VOUT 
func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var VMODE byte
    var VOUT uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)

    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    VMODE = VMODE & 0x1F  //mask exponent

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VOUT)//pmbus.Convert_vr13_5mvVID(VOUT)

    return
}


func ReadIin(devName string) (integer uint64, dec uint64, err int) {
    var IIN uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    IIN, err = pmbus.ReadWord(devName, READ_IIN)

    integer, dec, err =  pmbus.Linear11(IIN)

    return
}


func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var IOUT uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    IOUT, err = pmbus.ReadWord(devName, READ_IOUT)

    integer, dec, err =  pmbus.Linear11(IOUT)

    return
}


func ReadPin(devName string) (integer uint64, dec uint64, err int) {
    var PIN uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    PIN, err = pmbus.ReadWord(devName, READ_PIN)

    integer, dec, err =  pmbus.Linear11(PIN)

    return
}


func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    var POUT uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    POUT, err = pmbus.ReadWord(devName, READ_POUT)

    integer, dec, err =  pmbus.Linear11(POUT)

    return
}


func ReadTemp(devName string, sensorNumber uint32) (integer uint64, dec uint64, err int) {
    var TEMP uint16
    var reg uint32
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    switch sensorNumber {
        case 0: reg = READ_TEMPERATURE_1
        case 1: reg = READ_TEMPERATURE_2
        case 2: reg = READ_TEMPERATURE_3

    }

    TEMP, err = pmbus.ReadWord(devName, uint64(reg))

    integer, dec, err =  pmbus.Linear11(TEMP)

    return
}

func DisplayManufacturingInfo(devName string) (err int) {
    var psuNumber uint32 = 0
    wrData := []byte{}
    mfgId := []byte{}
    mfgRev := []byte{}
    mfgModel := []byte{}
    mfgSerial := []byte{}
    mfgFWrev := []byte{}
    usercode00 := []byte{}
    usercode01 := []byte{}

    if devName == "PSU_1" {
        psuNumber = 0
    } else {
        psuNumber = 1
    }

    present, errGo := taorfpga.PSU_present(psuNumber)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    if present != true {
        cli.Printf("e", "%s: is not present", devName)
        err = errType.FAIL
        return
    }


    iInfo, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain I2C info of", devName)
        return
    }
    wrData = append(wrData, MFR_ID)
    mfgId, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_ID_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgId) != MFG_ID_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MfgID is wrong.   Len=%d.  Expect=%d", devName, len(mfgId), MFG_ID_BLK_SIZE + 1)
    }

    wrData[0] = MFR_MODEL
    mfgModel, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_MODEL_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgModel) != MFG_MODEL_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, len(mfgModel), MFG_MODEL_BLK_SIZE + 1)
    }

    wrData[0] = MFR_REVISION
    mfgRev, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_REVISION_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgRev) != MFG_REVISION_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, len(mfgRev), MFG_REVISION_BLK_SIZE + 1)
    }

    wrData[0] = MFR_SERIAL
    mfgSerial, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFR_SERIAL_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgSerial) != MFR_SERIAL_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, len(mfgSerial), MFR_SERIAL_BLK_SIZE + 1)
    }

    wrData[0] = MFR_FW_REVISION
    mfgFWrev, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFR_FW_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }

    fw_rev_major, _ := strconv.Atoi(string(mfgFWrev[2:4]))
    fw_rev_minor, _ := strconv.Atoi(string(mfgFWrev[6:8]))
    

    if (fw_rev_major > 0) || (fw_rev_minor > 0) {
        wrData[0] = USER_CODE_00
        usercode00, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, USER_CODE_00_BLK_SIZE + 1 )
        if errGo != nil {
            err = errType.FAIL
            return
        }
        if len(usercode00) != USER_CODE_00_BLK_SIZE + 1 {
            err = errType.FAIL
            cli.Printf("e", "%s Length of USER_CODE_00_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, len(mfgSerial), USER_CODE_00_BLK_SIZE + 1)
        }

        wrData[0] = USER_CODE_01
        usercode01, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, USER_CODE_01_BLK_SIZE + 1 )
        if errGo != nil {
            err = errType.FAIL
            return
        }
        if len(usercode01) != USER_CODE_01_BLK_SIZE + 1 {
            err = errType.FAIL
            cli.Printf("e", "%s Length of USER_CODE_01_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, len(mfgSerial), USER_CODE_01_BLK_SIZE + 1)
        }
    }

    /*
    DPS-800AB-40 A:
    USER_CODE_00 : “R8R51A” (total 6bytes)
    USER_CODE_01 : “CX 10000-48Y6C FB AC PSU” (total 24 bytes)
    DPS-800AB-65 A:
    USER_CODE_00 : “R8R52A” (total 6bytes)
    USER_CODE_01 : “CX 10000-48Y6C BF AC PSU” (total 24 bytes)
    */
    //PSU_1: DELTA DPS-800AB-40    Rev: 00F   S/N: JBMD2047000089   F/W REV: S00.S01
    //SSD MODEL: W6EN064G1TA-S91AA3-2D2.A5   S/N: 62901-0152 Capacity: 64.0 GB    Smart Health PASSED 

    fmt.Printf("%s: %s %s  H/W Rev: %s    S/N: %s  F/W REV: %s\n", devName, string(mfgId[1:]), string(mfgModel[1:]), string(mfgRev[1:]), string(mfgSerial[1:]), string(mfgFWrev[1:]) )
    if (fw_rev_major > 0) || (fw_rev_minor > 0) {
        fmt.Printf("%s: %s %s  \n", devName, string(usercode00[1:]), string(usercode01[1:]) )
    }
    return
}


func DispStatus(devName string) (err int) {
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP1", "TEMP2", "TEMP3", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "TAORMINA" {
        var PSUnumber uint32
        if devName == "PSU_1" {
            PSUnumber = taorfpga.PSU0
        } else {
            PSUnumber = taorfpga.PSU1
        }
        present, _ := taorfpga.PSU_present(PSUnumber)
        if present == false {
               cli.Printf("i", "=================================\n")
               cli.Printf("i", "%-20s IS NOT PRESENT\n", devName)
               return
        }
        pwrok, _ := taorfpga.PSU_pwrok(PSUnumber)
        if pwrok == false {
               cli.Printf("i", "=================================\n")
               cli.Printf("i", "%-20s IS REPORTING POWER NOT OK AT THE FPGA\n", devName)
               return
        }
    }

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    //cli.Println("i", "0.00.00.00.00.00.0--")
    cli.Println("i", "=================================")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)

    //dig, frac, _ := ReadVboot(devName)
    //outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    //outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ := ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTemp(devName, 0)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    dig, frac, _ = ReadTemp(devName, 1)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    dig, frac, _ = ReadTemp(devName, 2)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return
}


