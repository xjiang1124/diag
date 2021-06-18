package sn1701022

import (
    "fmt"
    //"os"
    //"cardinfo"
    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
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

    integer, dec, err =  pmbus.Convert_vr13_5mvVID(VCMD)
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

    integer, dec, err =  pmbus.Convert_vr13_5mvVID(VOUT)

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


/*
func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    voutInt, voutFrac, err := ReadVout(devName)
    if err != errType.SUCCESS {
        return
    }
    ioutInt, ioutFrac, err := ReadIout(devName)
    if err != errType.SUCCESS {
        return
    }

    voutFloat := float64(voutInt) + float64(voutFrac)/1000
    ioutFloat := float64(ioutInt) + float64(ioutFrac)/1000
    poutFloat := voutFloat * ioutFloat

    integer = uint64(poutFloat)
    dec = uint64((poutFloat - float64(uint64(poutFloat)))*1000)

    return
}


func DispStatus(devName string) (err int) {

    vrmTitle := []string {"POUT", "VOUT_TGT", "VOUT", "IOUT", "STATUS"}
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

    dig, frac, _ := ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTargetVoltage(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return

}
*/

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
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

    dig, frac, _ = ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return
}


