package sn1701022

import (
    "fmt"
    //"os"
    //"cardinfo"
    "math"
    "time"
    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "protocol/pmbus"
    "protocol/smbus"
)


func I2cTest(devname string) (err int) { 
    var data16, ot_warn_limit uint16
    err = smbus.Open(devname)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    ot_warn_limit, err = pmbus.ReadWord(devname, OT_WARN_LIMIT)
    if err != errType.SUCCESS {
        cli.Println("e", " pmbus access to", devname,"failed")
        return
    }
    err = pmbus.WriteWord(devname, OT_WARN_LIMIT, (ot_warn_limit-1))
    if err != errType.SUCCESS {
        cli.Println("e", " pmbus access to", devname,"failed")
        return
    }
    data16, err = pmbus.ReadWord(devname, OT_WARN_LIMIT)
    if err != errType.SUCCESS {
        cli.Println("e", " pmbus access to", devname,"failed")
        return
    }
    err = pmbus.WriteWord(devname, OT_WARN_LIMIT, ot_warn_limit)

    if data16 != (ot_warn_limit -1) {
        err = errType.FAIL
        cli.Printf("e", "Device-%s Register 0x%x:  Wrote 0x%.04x   Read 0x%.04x\n", devname, OT_WARN_LIMIT, (ot_warn_limit -1), data16)
        return
    }
    data16, err = pmbus.ReadWord(devname, OT_WARN_LIMIT)
    if err != errType.SUCCESS {
        cli.Println("e", " pmbus access to", devname,"failed")
        return
    }  
    if data16 != (ot_warn_limit) {
        err = errType.FAIL
        cli.Printf("e", "Device-%s Register 0x%x:  Wrote 0x%.04x   Read 0x%.04x\n", devname, OT_WARN_LIMIT, (ot_warn_limit), data16)
        return
    }

    data16, err = pmbus.ReadWord(devname, IC_DEVICE_ID)
    if err != errType.SUCCESS {
        cli.Println("e", " pmbus access to", devname,"failed")
        return
    }
    if (data16 & IC_DEVICE_ID_MASK) != IC_DEVICE_ID_VALUE {
        err = errType.FAIL
        cli.Printf("e", "Device-%s Register 0x%x: Read 0x%.04x    Expect 0x%.04x   MASK=0x%.04x\n", devname, IC_DEVICE_ID, data16, IC_DEVICE_ID_VALUE, IC_DEVICE_ID_MASK)
        return
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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    status, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}

//Read target voltage from VOUT COMMAND
func ReadTargetVoltage(devName string) (integer uint64, dec uint64, err int) {
    var VCMD uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    VCMD, err = pmbus.ReadWord(devName, VOUT_COMMAND)

    if (devName == "CPU_PVCCIN") {
        integer, dec, err =  pmbus.Convert_vr13_10mvVID(VCMD)
    } else {
        integer, dec, err =  pmbus.Convert_vr13_5mvVID(VCMD)
    }
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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    VIN, err = pmbus.ReadWord(devName, READ_VIN)

    integer, dec, err =  pmbus.Linear11(VIN)

    return
}


//Read target voltage from VOUT 
func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    //var VMODE byte
    var VOUT uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)

    
    if (devName == "CPU_PVCCIN") {
        integer, dec, err =  pmbus.Convert_vr13_10mvVID(VOUT)
    } else {
        integer, dec, err =  pmbus.Convert_vr13_5mvVID(VOUT)
    }

    return
}


func ReadVout_Linear(devName string) (integer uint64, dec uint64, err int) {
    //var VMODE byte
    var VOUT uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    VOUT, err = pmbus.ReadWord(devName, MFR_SPECIFIC_04)

    integer, dec, err =  pmbus.Linear11(VOUT)

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    //Set the phase to read max current
    if page == 0 {
        pmbus.WriteByte(devName, PHASE, 0x80)
    }

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    POUT, err = pmbus.ReadWord(devName, READ_POUT)

    integer, dec, err =  pmbus.Linear11(POUT)

    return
}

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    var TEMP uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    TEMP, err = pmbus.ReadWord(devName, READ_TEMPERATURE_1)

    integer, dec, err =  pmbus.Linear11(TEMP)

    return
}

func GetTemperature(devName string) (temperatures []float64, err int) {
    dig, frac, err := ReadTemp(devName)
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    return
}

func DispVoltWattAmp(devName string) (err int) {
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, devName)

    dig, frac, err1 := ReadTargetVoltage(devName)
    if err1 != errType.SUCCESS {
        err = err1
        cli.Println("e", "ERROR READING VOUT CMD")
        return;
    }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    fmt.Println(outStr)
    return
}


func DispStatus(devName string) (err int) {
    vrmTitle := []string {"VOUT", "POUT", "IOUT", "VIN", "PIN", "IIN", "TEMP", "STATUS"}
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

    dig, frac, err := ReadPout(devName)
    if err != 0 {
        cli.Println("e", "ERROR READING POUT")
    }
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

    dig, frac, _ = ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return
}


func SetVMargin(devName string, pct int) (err int) {
    var marginCmd byte
    var marginVal uint16
    var voutcmd uint16
    var def_volt, marg_tics float64

    if pct > 10 || pct < -10 {
        return errType.INVALID_PARAM
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    pmbus.WriteByte(devName, PAGE, page)

    voutcmd, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read voutcmd on device ", devName)
        return
    }

    fmt.Printf(" %s VOUT_COMMAND=%.04x\n", devName, voutcmd)



    //If margin back to normal 0%, we need to put SVID back in control at the end of this function, otherwise PMBUS control
    if (pct != 0) {
        var mfg_spec byte
        mfg_spec, _ = pmbus.ReadByte(devName, MFR_SPECIFIC_02)
        if mfg_spec != MFR_SPECIFIC_02_PMBUS_CTRL {
            pmbus.WriteByte(devName, MFR_SPECIFIC_02, MFR_SPECIFIC_02_PMBUS_CTRL)
            time.Sleep(time.Duration(500) * time.Millisecond)
        }
    }

    if (devName == "CPU_PVCCIN") {
        def_volt = .50 + (float64(voutcmd-1) * .01)
        marg_tics = (def_volt * float64(pct)) / 100;
        marg_tics = math.Round(marg_tics / .01)
    } else {
        def_volt = .25 + (float64(voutcmd-1) * .005)
        marg_tics = (def_volt * float64(pct)) / 100;
        marg_tics = math.Round(marg_tics / .005)
    }

    marginVal = voutcmd + uint16(marg_tics)

    fmt.Printf(" %s marginVal=%.04x\n", devName, marginVal)

    if pct == 0 {
        marginCmd = MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = MARGIN_HIGH_CMD
        
        if (devName == "CPU_PVCCIN") {  //VOUT MAX ON THIS RAIL IS SET TO THE SAME AS NOMINAL VOLTAGE.  NEED TO CHANGE IT IN ORDER TO MARGIN HIGHER
            pmbus.WriteWord(devName, VOUT_MAX, marginVal)
        }
        pmbus.WriteWord(devName, VOUT_MARGIN_HIGH, marginVal)
    } else {
        marginCmd = MARGIN_LOW_CMD
        pmbus.WriteWord(devName, VOUT_MARGIN_LOW, marginVal)
    }

    pmbus.WriteByte(devName, OPERATION, marginCmd)

    //If margin back to normal 0%, we need to put SVID back in control at the end of this function
    if (pct == 0) {
        pmbus.WriteByte(devName, MFR_SPECIFIC_02, MFR_SPECIFIC_02_SVID_CTRL)
    }

    return
}


