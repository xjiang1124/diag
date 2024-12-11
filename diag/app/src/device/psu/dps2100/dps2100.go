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


func ReadStatusWord(devName string) (status uint16, err int) {

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}


func ReadStatusVout(devName string) (status uint8, err int) {

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadByte(devName, STATUS_VOUT)
    return
}


func ReadStatusIout(devName string) (status uint8, err int) {

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadByte(devName, STATUS_IOUT)
    return
}


func ReadStatusInput(devName string) (status uint8, err int) {

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadByte(devName, STATUS_INPUT)
    return
}


func ReadStatusTemp(devName string) (status uint8, err int) {

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadByte(devName, STATUS_TEMPERATURE)
    return
}


func ReadStatusFan(devName string) (status uint8, err int) {

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadByte(devName, STATUS_FANS_1_2)
    return
}


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
    mfgId := make([]byte, 32)
    mfgRev := make([]byte, 32)
    mfgModel := make([]byte, 32)
    mfgSerial := make([]byte, 32)
    fwrevision := make([]byte, 32)
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    _, err = pmbus.Readi2cBlock(devName, MFR_ID, mfgId)
    if err != errType.SUCCESS {
        return
    }
    if mfgId[0] != MFG_ID_BLK_SIZE {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MfgID is wrong.   Len=%d.  Expect=%d", devName, mfgId[0], MFG_ID_BLK_SIZE)
        return
    }


    _, err = pmbus.Readi2cBlock(devName, MFR_MODEL, mfgModel)
    if err != errType.SUCCESS {
        return
    }
    if mfgModel[0] != MFG_MODEL_BLK_SIZE {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, mfgModel[0], MFG_MODEL_BLK_SIZE)
        return
    }

    _, err = pmbus.Readi2cBlock(devName, MFR_REVISION, mfgRev)
    if err != errType.SUCCESS {
        return
    }
    if mfgRev[0] != MFG_REVISION_BLK_SIZE {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_MODEL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, mfgRev[0], MFG_REVISION_BLK_SIZE)
        return
    }

    _, err = pmbus.Readi2cBlock(devName, MFR_SERIAL, mfgSerial)
    if err != errType.SUCCESS {
        return
    }
    if mfgSerial[0] != MFR_SERIAL_BLK_SIZE {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_SERIAL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, mfgSerial[0], MFR_SERIAL_BLK_SIZE)
        return
    }

    _, err = pmbus.Readi2cBlock(devName, MFR_FW_REVISION, fwrevision)
    if err != errType.SUCCESS {
        return
    }
    if fwrevision[0] != MFR_FW_REVISION_BLK_SIZE {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MFG_SERIAL_BLK_SIZE is wrong.   Len=%d.  Expect=%d", devName, fwrevision[0], MFR_FW_REVISION_BLK_SIZE)
        return
    }


    fmt.Printf("%s: %s %s    H/W Rev: %s    S/N: %s\n", devName, string(mfgId[1:(MFG_ID_BLK_SIZE+1)]), string(mfgModel[1:(MFG_MODEL_BLK_SIZE+1)]), string(mfgRev[1:(MFG_REVISION_BLK_SIZE+1)]), string(mfgSerial[1:(MFR_SERIAL_BLK_SIZE+1)]) )
    fmt.Printf("%s: FW Rev:  Primary:%.02x  Secondary:%.02x  Major:%.02x  Downgrade:%.02x \n", devName, fwrevision[2], fwrevision[1], (fwrevision[3]&0x7f),  (fwrevision[3]&0x80))
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
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP1", "TEMP2", "TEMP3"}
    vrmTitle1 := []string {"FAN-RPM", "STS_WORD", "STS_VOUT", "STS_IOUT", "STS_INP", "STS_TEMP", "STS_FAN"}
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
    cli.Println("i", "=================================")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)

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

    cli.Println("i", outStr)
    
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle1) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "------------")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)

    fanRPM, _ := ReadFanSpeed(devName)
    outStrTemp = fmt.Sprintf("%d", fanRPM)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    statusWord, _ := ReadStatusWord(devName)
    outStrTemp = fmt.Sprintf("0x%X", statusWord)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    statusVout, _ := ReadStatusVout(devName)
    outStrTemp = fmt.Sprintf("0x%X", statusVout)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    statusIout, _ := ReadStatusIout(devName)
    outStrTemp = fmt.Sprintf("0x%X", statusIout)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    statusInput, _ := ReadStatusInput(devName)
    outStrTemp = fmt.Sprintf("0x%X", statusInput)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    statusTemperature, _ := ReadStatusTemp(devName)
    outStrTemp = fmt.Sprintf("0x%X", statusTemperature)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    statusFan, _ := ReadStatusFan(devName)
    outStrTemp = fmt.Sprintf("0x%X", statusFan)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    cli.Println("i", outStr)

    return
}


