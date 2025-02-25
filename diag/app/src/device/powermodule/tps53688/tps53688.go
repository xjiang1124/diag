package tps53688

import (
    "fmt"
    "math"
    "common/cli"
    "common/errType"
    "common/misc"
    "hardware/i2cinfo"
    "protocol/pmbus"
)

func calcVoltFromVid (vid byte, dacStep uint64) (integer uint64, dec uint64, err int) {
    var volt uint64
    var base uint64
    err = errType.SUCCESS

    if vid == 0 {
        return 0, 0, err
    }

    if (dacStep != 5 && dacStep != 10) {
        return 0, 0, errType.INVALID_PARAM
    }

    if dacStep == 5 {
        base = 250
    } else {
        base = 500
    }

    volt = (uint64(vid) - 1) * dacStep + base

    return volt/1000, volt%1000, errType.SUCCESS
}

func calcVidFromVolt (tgtVoltMv uint64, dacStep uint64) (vid byte, err int) {
    var volt uint64
    var voltNext uint64
    var base uint64
    var vidMax uint64
    var vidStep uint64

    err = errType.SUCCESS

    if tgtVoltMv == 0 {
        return 0, err
    }

    if (dacStep != 5 && dacStep != 10) {
        return 0, errType.INVALID_PARAM
    }

    if dacStep == 5 {
        base = 250
        vidMax = 0xFF
    } else {
        base = 500
        vidMax = 0xC9
    }

    for vidStep = 1; vidStep < vidMax; vidStep++ {
        volt = (vidStep - 1) * dacStep + base
        voltNext = vidStep * dacStep + base
        if (volt <= tgtVoltMv) && (voltNext > tgtVoltMv) {
            //cli.Println("tgtVoltMv", tgtVoltMv, "vidStep", vidStep, "volt", volt, "voltNext", voltNext)
            if tgtVoltMv - volt < voltNext - tgtVoltMv {
                return byte(vidStep), err
            } else {
                return byte(vidStep + 1), err
            }
        }
    }
    return 0, errType.FAIL
}


func ReadStatus(devName string) (status uint16, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

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
    fmt.Printf(" DEBUG: devID=%x\n", devID)
    return devID, err
}

func ReadPmbusRev(devName string) (rev uint8, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    rev, err = pmbus.ReadByte(devName, PMBUS_REVISION)
    return rev, err
}

//Read target voltage from VOUT COMMAND
func ReadTargetVoltage(devName string) (integer uint64, dec uint64, err int) {
    var VCMD uint16
    var dacStepRegVal uint8
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    dacStepRegVal, err = pmbus.ReadByte(devName, VOUT_MODE);
    if err != errType.SUCCESS {
        return
    }

    VCMD, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        return
    }

    if (dacStepRegVal == DAC_STEP_10MV) {
        integer, dec, err =  pmbus.Convert_vr13_10mvVID(VCMD)
    } else if (dacStepRegVal == DAC_STEP_5MV) {
        integer, dec, err =  pmbus.Convert_vr13_5mvVID(VCMD)
    } else {
        //Linear16
        integer, dec, err =  pmbus.Linear16(uint64(dacStepRegVal), VCMD)
    }
    return
}


func ReadVin(devName string) (integer uint64, dec uint64, err int) {
    var VIN uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    VIN, err = pmbus.ReadWord(devName, READ_VIN)
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf(" DEBUG: VIN READ_VIN=%x\n", VIN)

    integer, dec, err =  pmbus.Linear11(VIN)

    return

}


//Read target voltage from VOUT 
func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var VOUT uint16
    var dacStepRegVal uint8
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    dacStepRegVal, err = pmbus.ReadByte(devName, VOUT_MODE);
    if err != errType.SUCCESS {
        return
    }

    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)
    if err != errType.SUCCESS {
        return
    }

    if (dacStepRegVal == DAC_STEP_10MV) {
        integer, dec, err =  pmbus.Convert_vr13_10mvVID(VOUT)
    } else if (dacStepRegVal == DAC_STEP_5MV) {
        integer, dec, err =  pmbus.Convert_vr13_5mvVID(VOUT)
    } else {
        //Linear16
        integer, dec, err =  pmbus.Linear16(uint64(dacStepRegVal), VOUT)
    }

    return
}


func ReadVout_Linear(devName string) (integer uint64, dec uint64, err int) {
    //var VMODE byte
    var VOUT uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    VOUT, err = pmbus.ReadWord(devName, MFR_SPECIFIC_D4)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(VOUT)

    return
}


func ReadVboot(devName string) (integer uint64, dec uint64, err int) {
    var voutcmd uint16
    var dacStepRegVal uint8

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }
    dacStepRegVal, err = pmbus.ReadByte(devName, VOUT_MODE);
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf(" DEBUG: VBOOT VOUT_MODE=%x\n", dacStepRegVal)

    voutcmd, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf(" DEBUG: VBOOT VOUT_COMMAND=%x\n", voutcmd)

    if (dacStepRegVal == DAC_STEP_5MV) {
        integer, dec, err =  pmbus.Convert_vr13_5mvVID(voutcmd)
    } else if (dacStepRegVal == DAC_STEP_10MV) {
        integer, dec, err =  pmbus.Convert_vr13_10mvVID(voutcmd)
    } else {
        //Linear16
        integer, dec, err =  pmbus.Linear16(uint64(dacStepRegVal), voutcmd)
    }

    return
}


func ReadVoutCmd(devName string) (voutcmd uint16, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    voutcmd, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        return
    }

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    IIN, err = pmbus.ReadWord(devName, READ_IIN)
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf(" DEBUG: IIN READ_IIN=%x\n", IIN)

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    IOUT, err = pmbus.ReadWord(devName, READ_IOUT)
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf(" DEBUG: IOUT READ_IOUT=%x\n", IOUT)

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    PIN, err = pmbus.ReadWord(devName, READ_PIN)
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf(" DEBUG: PIN READ_PIN=%x\n", PIN)

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

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    POUT, err = pmbus.ReadWord(devName, READ_POUT)
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf(" DEBUG: POUT READ_POUT=%x\n", POUT)

    integer, dec, err =  pmbus.Linear11(POUT)

    return
}

func findVid(devName string, voutMv uint64) (vid byte, err int) {
    var dacStepRegVal byte
    var dacStep uint64

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Get current VOUT
    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)
    // Write phase register
    pmbus.WriteByte(devName, PHASE, 0xFF)
    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)
    if err != errType.SUCCESS {
        return
    }

    if dacStepRegVal == DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }
    vid, err = calcVidFromVolt(voutMv, dacStep)
    return
}

func UpdateVboot(devName string, tgtVoutMv uint64) (err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)
    // Write phase register
    pmbus.WriteByte(devName, PHASE, 0xFF)

    // Set VOUT_MAX
    voutMaxVid, err := findVid(devName, VOUT_MAX_MV)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to find vid")
        return
    }
    err = pmbus.WriteWord(devName, pmbus.VOUT_MAX, uint16(voutMaxVid))
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to update VOUT_MAX")
        return
    }

    // Set VOUT_MIN
    voutMinVid, err := findVid(devName, VOUT_MIN_MV)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to find vid")
        return
    }
    err = pmbus.WriteWord(devName, pmbus.VOUT_MIN, uint16(voutMinVid))
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to update VOUT_MIN")
        return
    }

    // Set OPERATION to On, Margin None
    err = pmbus.WriteByte(devName, pmbus.OPERATION, 0x80)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to set OPERATION")
        return
    }

    // Update VBoot
    vbootVid, err := findVid(devName, tgtVoutMv)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to find vid")
        return
    }

    err = pmbus.WriteWord(devName, pmbus.VOUT_COMMAND, uint16(vbootVid))
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to update VBOOT")
        return
    }

    // Store to NVM
    err = pmbus.SendByte(devName, pmbus.STORE_USER_ALL)

    return
}

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    var TEMP uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }
    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    TEMP, err = pmbus.ReadWord(devName, READ_TEMPERATURE_1)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(TEMP)

    return
}

func GetTemperature(devName string) (temperatures []float64, err int) {
    dig, frac, err := ReadTemp(devName)
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
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

    digIout, fracIout, err := ReadIout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, digIout, fracIout)
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
    vrmTitle := []string {"VBOOT", "POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
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

    dig, frac, _ := ReadVboot(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPout(devName)
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
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) + "\n"

    cli.Println("i", outStr)

    return
}

func DispStatusSalina(devName string) (err int) {
    // Salina boards doesnt use Vboot, and the VIN/IIN/PIN measured here is invalid when no aux cable present
    vrmTitle := []string {"VOUT", "IOUT", "POUT", "TEMP", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "=================================")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)
    var dig uint64
    var frac uint64
    for _, title := range(vrmTitle) {
        switch title {
        case "VOUT":
            dig, frac, _ = ReadVout(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "IOUT":
            dig, frac, _ = ReadIout(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "POUT":
            dig, frac, _ = ReadPout(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "TEMP":
            dig, frac, _ = ReadTemp(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "STATUS":
            status, _ := ReadStatus(devName)
            outStrTemp = fmt.Sprintf("0x%X", status)
        default:
            outStrTemp = "N/A"
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    }
    cli.Println("i", outStr)

    return
}

func DispStatusVsense(devName string) (err int) {
    /* Read from a sense resistor at input line. */
    vrmTitle := []string {"VOUT", "IOUT", "POUT", "TEMP", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "=================================")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)
    var dig uint64
    var frac uint64
    for _, title := range(vrmTitle) {
        switch title {
        case "VOUT":
            dig, frac, _ = ReadVin(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "IOUT":
            dig, frac, _ = ReadIin(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "POUT":
            dig, frac, _ = ReadPin(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "TEMP":
            dig, frac, _ = ReadTemp(devName)
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        case "STATUS":
            status, _ := ReadStatus(devName)
            outStrTemp = fmt.Sprintf("0x%X", status)
        default:
            outStrTemp = "N/A"
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    }

    cli.Println("i", outStr)

    return
}

func SetVMargin(devName string, pct int) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64
    var voutcmd uint16

    //if pct > 10 || pct < -10 {
    //    return errType.INVALID_PARAM
    //}

    voutcmd, err = ReadVoutCmd(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read voutcmd on device ", devName)
        return
    }

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }
    // Write phase register
    if i2cinfo.CardType != "LIPARI" {
        pmbus.WriteByte(devName, PHASE, 0xFF)
    }

    // Disable Vmargin
    err = pmbus.WriteByte(devName, pmbus.OPERATION, MARGIN_NONE_CMD)
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    }

    if pct == 0 {
        marginCmd = MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = MARGIN_HIGH_IGN_FLT
        marginReg = pmbus.VOUT_MARGIN_HIGH
    } else {
        marginCmd = MARGIN_LOW_IGN_FLT
        marginReg = pmbus.VOUT_MARGIN_LOW
    }

    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)


    //LINEAR16 FORMAT FOR LIPARI
    if dacStepRegVal == LINEAR {
        var integer, dec uint64
        var expval int = int(dacStepRegVal & 0x1F)

        //Get Default Target Voltage for Part
        integer, dec, err =  pmbus.Linear16(uint64(expval), voutcmd)
        def_volt := float64(integer) + (float64(dec)/1000)



        //Get Exponent Portion
        if expval > 0xF {
            expval = 0x20 - expval
            expval = 0 - expval
        }
        exponentF := math.Pow(2, float64(expval))

        //Calculate what to set Margin High or Low Reg to
        marginVal := uint64( (def_volt + (def_volt * (float64(pct) / 100))) / exponentF)

        fmt.Printf(" voutcmd=%x  marginVal=%x float64(pct)=%f  def_volt=%f\n", voutcmd, (marginVal & 0xFFFF), float64(pct), def_volt)

        if pct != 0 {
            err = pmbus.WriteWord(devName, marginReg, uint16(marginVal))
            if err != errType.SUCCESS {
                cli.Println("e", "WriteWord to %s reg %d failed", devName, marginReg)
                return
            }
        }
        err = pmbus.WriteByte(devName, pmbus.OPERATION, marginCmd)
        if err != errType.SUCCESS {
            cli.Println("e", "WriteByte to %s reg %d failed", devName, pmbus.OPERATION)
            return
        }

    } else {
        if dacStepRegVal == DAC_STEP_5MV {
            dacStep = 5
        } else {
            dacStep = 10
        }

        data, err = pmbus.ReadWord(devName, pmbus.VOUT_COMMAND)

        integer, dec, _ := calcVoltFromVid(byte(data), dacStep)
        voltMv := integer *1000 + dec
        voltMvTemp := voltMv * uint64(100+pct)
        voltMvTgt := voltMvTemp / 100
        if (voltMvTgt < 700) {
            voltMvTgt = 700
        }
        cli.Printf("d", "VOUT(mv): %d; TargetVolt(mv): %d\n", voltMv, voltMvTgt)
        // Update VOUT_MARGIN_HIGH/HOW with target VID
        vidTgt, _ := calcVidFromVolt(voltMvTgt, dacStep)
        cli.Printf("i", "Target VID: 0x%x\n", vidTgt)
        if pct != 0 {
            err = pmbus.WriteWord(devName, marginReg, uint16(vidTgt))
            if err != errType.SUCCESS {
                cli.Println("e", "VMargin failed!")
                return
            }
        }

        // Enable Vmargin
        err = pmbus.WriteByte(devName, pmbus.OPERATION, marginCmd)
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        } else {
            cli.Println("i", "New vmargin enabled")
        }
        misc.SleepInSec(1)
    }
    return
}

func SetVMarginByValue(devName string, tgtVoutMv uint64) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64
    if (tgtVoutMv < 700) {
        tgtVoutMv = 700
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Get current VOUT
    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)
    // Write phase register
    pmbus.WriteByte(devName, PHASE, 0xFF)
    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)

    if dacStepRegVal == DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    data, err = pmbus.ReadWord(devName, pmbus.VOUT_COMMAND)
    integer, dec, _ := calcVoltFromVid(byte(data), dacStep)

    curVoutMv := integer *1000 + dec
    cli.Println("d", "curVoutMv:", curVoutMv)

    if tgtVoutMv == curVoutMv {
        marginCmd = MARGIN_NONE_CMD
    } else if tgtVoutMv > curVoutMv {
        marginCmd = MARGIN_HIGH_IGN_FLT
        marginReg = pmbus.VOUT_MARGIN_HIGH
    } else {
        marginCmd = MARGIN_LOW_IGN_FLT
        marginReg = pmbus.VOUT_MARGIN_LOW
    }

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(tgtVoutMv, dacStep)

    if marginCmd != MARGIN_NONE_CMD {
        err = pmbus.WriteWord(devName, marginReg, uint16(vidTgt))
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        }
    }
    // Enable Vmargin
    err = pmbus.WriteByte(devName, pmbus.OPERATION, marginCmd)
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    }

    return
}
