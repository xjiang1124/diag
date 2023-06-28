package dps2100

import (
    "fmt"
    "os"
    "unicode"
    "common/cli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
    "device/fpga/liparifpga"
)


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
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err = pmbus.Linear11(VIN)
    return
}


//Read target voltage from VOUT 
func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var VOUT uint16
    var VMODE uint8
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE);
    if err != errType.SUCCESS {
        return
    }

    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VOUT)
        
    return
}


func ReadIin(devName string) (integer uint64, dec uint64, err int) {
    var IIN uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    IIN, err = pmbus.ReadWord(devName, READ_IIN)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(IIN)



    return
}


func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var IOUT uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    IOUT, err = pmbus.ReadWord(devName, READ_IOUT)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(IOUT)

    return
}


func ReadPin(devName string) (integer uint64, dec uint64, err int) {
    var PIN uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    PIN, err = pmbus.ReadWord(devName, READ_PIN)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(PIN)

    return
}


func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    var POUT uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    POUT, err = pmbus.ReadWord(devName, READ_POUT)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(POUT)

    return

}


/************************************************************************
* 
* Return 0 if no warning of fault.  Non zero if warning of fault is set
* 
* 
*************************************************************************/ 
func ReadFanWarnFault(devName string) (WarnFault uint32, err int) {
    var FanStatus uint8
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    FanStatus, err = pmbus.ReadByte(devName, STATUS_FANS_1_2)
    if err != errType.SUCCESS {
        return
    }

    if (FanStatus & STATUS_FAN_FAULT) == STATUS_FAN_FAULT {
        WarnFault = 1
    }
    if (FanStatus & STATUS_FAN_WARN) == STATUS_FAN_WARN {
        WarnFault = 1
    }

    return


}


func ReadFanSpeed(devName string) (rpm uint32, err int) {
    var FanConfig uint8
    var FanSpeed uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    FanConfig, err = pmbus.ReadByte(devName, FAN_CONFIG_1_2)
    if err != errType.SUCCESS {
        return
    }

    FanSpeed, err = pmbus.ReadWord(devName, READ_FAN_SPEED_1)
    if err != errType.SUCCESS {
        return
    }

    rpm =  uint32(FanSpeed)
    //Check if it's 2 pulses per revolution
    if FanConfig & 0x30 == 0x01 { 
        rpm = rpm / 2
    }

    return
}



/********************************************************************** 
* 
* Read a single temperature
* 
* 
**********************************************************************/
func ReadTemp(devName string, sensorNumber uint32) (integer uint64, dec uint64, err int) {
    var TEMP uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    switch sensorNumber {
        case 0: TEMP, err = pmbus.ReadWord(devName, READ_TEMPERATURE_1)
        case 1: TEMP, err = pmbus.ReadWord(devName, READ_TEMPERATURE_2)
        case 2: TEMP, err = pmbus.ReadWord(devName, READ_TEMPERATURE_3)
    }
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(TEMP)
    return
}


/********************************************************************** 
* 
* Return all 3 temperatures in a slice 
* 
* 
**********************************************************************/ 
func GetTemperature(devName string) (temperatures []float64, err int) {

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "LIPARI" {
        var PSUnumber uint32
        if devName == "PSU_1" {
            PSUnumber = liparifpga.PSU0
        } else {
            PSUnumber = liparifpga.PSU1
        }
        present, _ := liparifpga.PSU_present(PSUnumber)
        pwrok, _ := liparifpga.PSU_pwrok(PSUnumber)
        if present == false || pwrok == false{
               return
        }
    }

    dig, frac, err := ReadTemp(devName, 0)
    if err != errType.SUCCESS {
        return;
    }
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    dig, frac, err = ReadTemp(devName, 1)
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    dig, frac, err = ReadTemp(devName, 2)
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    return
}


func StrIsAscii(s string ) bool {

    if len(s) == 0 {
        return false
    }
    for i := 0; i < len(s); i++ {
        if s[i] > unicode.MaxASCII {
            return false
        }
    }
    return true
}


func DisplayManufacturingInfo(devName string, useCLI int) (err int) {
    /*
    var psuNumber uint32 = 0
    var i byte = 0
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

    present, errGo := liparifpga.PSU_present(psuNumber)
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
    mfgId, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_ID_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgId) != MFG_ID_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MfgID is wrong.   Len=%d.  Expect=%d", devName, len(mfgId), MFG_ID_BLK_SIZE + 1)
    }

    wrData[0] = MFR_MODEL
    mfgModel, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_MODEL_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgModel) != MFG_MODEL_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, len(mfgModel), MFG_MODEL_BLK_SIZE + 1)
    }

    wrData[0] = MFR_REVISION
    mfgRev, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_REVISION_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgRev) != MFG_REVISION_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, len(mfgRev), MFG_REVISION_BLK_SIZE + 1)
    }

    wrData[0] = MFR_SERIAL
    mfgSerial, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFR_SERIAL_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    i = mfgSerial[0]
    if i < (MFR_SERIAL_BLK_SIZE-6) || i > MFR_SERIAL_BLK_SIZE {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect %d - Expect=%d for the length", devName, i, (MFR_SERIAL_BLK_SIZE-6), MFR_SERIAL_BLK_SIZE + 1)
    }
    //s/n might be less than total block size.. truncate it if it is 
    if i != MFR_SERIAL_BLK_SIZE {
        i=i+1
        mfgSerial = mfgSerial[:i]
    }

    wrData[0] = MFR_FW_REVISION
    mfgFWrev, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFR_FW_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }


    //PSU_1: DELTA DPS-800AB-40    Rev: 00F   S/N: JBMD2047000089   F/W REV: S00.S01
    //SSD MODEL: W6EN064G1TA-S91AA3-2D2.A5   S/N: 62901-0152 Capacity: 64.0 GB    Smart Health PASSED 
    wrData[0] = USER_CODE_00
    usercode00, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if uint32(usercode00[0]) == 0xFF {  //Not programmed at all
        //err = errType.FAIL
    } else if uint32(usercode00[0]) > 32 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of USER_CODE_00 seem to high > 32.  Read %d", devName, uint32(usercode00[0]))
    } else {
        wrData[0] = USER_CODE_00
        usercode00, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, uint32(usercode00[0]) + 1)
        if errGo != nil {
            err = errType.FAIL
            return
        }
    }

    wrData[0] = USER_CODE_01
    usercode01, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if uint32(usercode01[0]) == 0xFF {  //Not programmed at all
        //err = errType.FAIL
    } else if uint32(usercode01[0]) > 32 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of USER_CODE_00 seem to high > 32.  Read %d", devName, uint32(usercode01[0]))
    } else {
        wrData[0] = USER_CODE_01
        usercode01, errGo = liparifpga.I2c_access( uint32(iInfo.Bus), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, uint32(usercode01[0]) + 1 )
        if errGo != nil {
            err = errType.FAIL
            return
        }
    }


    if useCLI > 0 {
        cli.Printf("i", "%s: %s %s  H/W Rev: %s    S/N: %s  F/W REV: %s\n", devName, string(mfgId[1:]), string(mfgModel[1:]), string(mfgRev[1:]), string(mfgSerial[1:]), string(mfgFWrev[1:]) )
    } else { fmt.Printf("%s: %s %s  H/W Rev: %s    S/N: %s  F/W REV: %s\n", devName, string(mfgId[1:]), string(mfgModel[1:]), string(mfgRev[1:]), string(mfgSerial[1:]), string(mfgFWrev[1:]) ) }

    if StrIsAscii(string(usercode00[1:])) == true {
        if useCLI > 0 { cli.Printf("i", "%s: %s %s  \n", devName, string(usercode00[1:]), string(usercode01[1:]) )
        } else {             fmt.Printf("%s: %s %s  \n", devName, string(usercode00[1:]), string(usercode01[1:]) ) }
    } else {
        if useCLI > 0 { cli.Printf("i", "%s: ...... ........................\n", devName)
        } else {             fmt.Printf("%s: ...... ........................\n", devName) }
        
    }
    */
    return
}



// vrmTitle := []string {"VBOOT", "VOUT", "POUT", "IOUT", "VIN", "PIN", "IIN"}
func DispVoltWattAmp(devName string) (err int) {
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, devName)

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "LIPARI" {
        var PSUnumber uint32
        if devName == "PSU_1" {
            PSUnumber = liparifpga.PSU0
        } else {
            PSUnumber = liparifpga.PSU1
        }
        present, _ := liparifpga.PSU_present(PSUnumber)
        pwrok, _ := liparifpga.PSU_pwrok(PSUnumber)

        if pwrok == false || present == false {
            for i:=0;i<7;i++ {
                outStrTemp = "-"
                outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
            }
            fmt.Println(outStr)
            return
        }
    }


    outStrTemp = "-"
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err := ReadVout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadPout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadIout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadVin(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadPin(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadIin(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    fmt.Println(outStr)

    return
}


func DispStatus(devName string) (err int) {
    /*
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP1", "TEMP2", "TEMP3", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "LIPARI" {
        var PSUnumber uint32
        if devName == "PSU_1" {
            PSUnumber = liparifpga.PSU0
        } else {
            PSUnumber = liparifpga.PSU1
        }
        present, _ := liparifpga.PSU_present(PSUnumber)
        if present == false {
               cli.Printf("i", "=================================\n")
               cli.Printf("i", "%-20s IS NOT PRESENT\n", devName)
               return
        }
        pwrok, _ := liparifpga.PSU_pwrok(PSUnumber)
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

    dig, frac, err := ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    if err != errType.SUCCESS {
        return;
    }

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
    */
    return
}


