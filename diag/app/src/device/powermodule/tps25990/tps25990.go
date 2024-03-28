package tps25990

import (
    "fmt"
    "math"
    "common/cli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
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

func ReadDeviceID(devName string) (devID uint64, err int) {
    var byteCnt int
    readData :=make([]byte, 6)

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    byteCnt, err = pmbus.ReadBlock(devName, pmbus.IC_DEVICE_ID, readData)
    if byteCnt != 6 {
        cli.Println("e", "read IC_DEVICE_ID length mismatch, expected 6, received ", byteCnt)
        return
    }
    devID = uint64(readData[0]) << 40 | uint64(readData[1]) << 32 | uint64(readData[2]) << 24 |
            uint64(readData[3]) << 16 | uint64(readData[4]) << 8 | uint64(readData[5])
    return devID, err
}

//Read target voltage from VOUT COMMAND
func ReadTargetVoltage(devName string) (integer uint64, dec uint64, err int) {
    /*
    var VCMD uint16
    var dacStepRegVal uint8
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    dacStepRegVal, err = pmbus.ReadByte(devName, VOUT_MODE);
    if err != errType.SUCCESS {
        return
    }

    VCMD, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        return
    }

    if (dacStepRegVal == DAC_STEP_5MV) {
        integer, dec, err =  pmbus.Convert_vr13_5mvVID(VCMD)
    } else {
        integer, dec, err =  pmbus.Convert_vr13_10mvVID(VCMD)
    }
    */
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

    //Y = (m * X + b) * 10R
    //X = (y/(10R * m)) - (b/m)

    expOutFloat := float64(VIN) / (math.Pow(10, (-2)) * 5251)
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return
}


//Read target voltage from VOUT 
func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var VOUT uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)
    if err != errType.SUCCESS {
        return
    }

    //Y = (m * X + b) * 10R
    //X = (y/(10R * m)) - (b/m)

    expOutFloat := float64(VOUT) / (math.Pow(10, (-2)) * 5251)
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)
        
    return
}




func ReadVboot(devName string) (integer uint64, dec uint64, err int) {
    /*
    var voutcmd uint16
    var dacStepRegVal uint8

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    dacStepRegVal, err = pmbus.ReadByte(devName, VOUT_MODE);
    if err != errType.SUCCESS {
        return
    }

    voutcmd, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        return
    }

    if (dacStepRegVal == DAC_STEP_5MV) {
        integer, dec, err =  pmbus.Convert_vr13_5mvVID(voutcmd)
    } else if (dacStepRegVal == DAC_STEP_10MV) {
        integer, dec, err =  pmbus.Convert_vr13_10mvVID(voutcmd)
    } else {
        cli.Println("i", "Unexpected vout_mode", dacStepRegVal)
        return
    }
    */
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

    expOutFloat := float64(IIN) / ((math.Pow(10, (-3))) * (9.538 * 309))
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)
    return
}

/*
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

    //Y = (m * X + b) * 10R

    //X = (y/(10R * m)) - (b/m)

    expOutFloat := float64(IOUT) / ( (math.Pow(10, (-3)) * (9.538 * 309)) )
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return


}
*/


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

    //Y = (m * X + b) * 10R

    //X = (y/(10R * m)) - (b/m)

    expOutFloat := float64(PIN) / ((math.Pow(10, (-4))) * (4.901 * 309))
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return
}

/*
func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    var f float64
    dig, frac, _ := ReadVout(devName)
    if err != errType.SUCCESS {
        return;
    }

    digIout, fracIout, _ := ReadIout(devName)

    f = float64(dig) + (float64(frac)/1000)
    f = f * (float64(digIout) + (float64(fracIout)/1000))

    intpart, div := math.Modf(f)
    integer = uint64(intpart)
    dec = uint64(div*1000)

    return
}
*/

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    var TEMP uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    TEMP, err = pmbus.ReadWord(devName, READ_TEMPERATURE_1)

    expOutFloat := (float64(TEMP) * math.Pow(10, 2) - 32100) / 140
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return
}

func GetTemperature(devName string) (temperatures []float64, err int) {
    dig, frac, err := ReadTemp(devName)
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    return
}


// vrmTitle := []string {"VOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
func DispVoltWattAmp(devName string) (err int) {
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, devName)

    outStrTemp = "-"
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err := ReadVout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

   /* dig, frac, err = ReadPout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    digIout, fracIout, err := ReadIout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, digIout, fracIout)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)*/

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

    dig, frac, err = ReadTemp(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    outStrTemp = "-"
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    fmt.Println(outStr)

    return
}

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"VOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

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

  /*  dig, frac, _ := ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)*/

    dig, frac, _ := ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

 /*   dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)*/

    dig, frac, _ = ReadPin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return
}




