package mp8796

import (
    "fmt"
    "math"
    "common/cli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
)




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

    //25mV/LSB --> 0.025
    expOutFloat := float64(VIN) * 0.025 
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

    //1.25mV/LSB    0.00125
    expOutFloat := float64(VOUT) * 0.00125
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)
        
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

    //62.5mA/LSB   0.0625
    expOutFloat := float64(IOUT) *  0.0625
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)
    return
}



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


/*****************************************************************
* 
* VOUT_COMMAND and the MARGIN REGISTERS ARE 2mv per tick
*
*****************************************************************/
func SetVMargin(devName string, pct int) (err int) {
    var marginReg uint64
    var marginCmd uint8
    var marginVal int16
    var vboot uint16

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    
    vboot, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read voutcmd on device ", devName)
        smbus.Close()
        return
    }

    if (pct == 0) {
        marginCmd = MARGIN_NONE_CMD;
    } else if (pct > 0) {
        marginCmd = MARGIN_HIGH_CMD;
        marginReg = VOUT_MARGIN_HIGH
    } else {
        marginCmd = MARGIN_LOW_CMD;
        marginReg = VOUT_MARGIN_LOW
        
    }

    if (pct != 0 ) {
        marginVal = int16(vboot)
        marginVal = ( (marginVal * 2) + (((marginVal * 2) * int16(pct)) / 100) ) / 2 
        err = pmbus.WriteWord(devName, marginReg, uint16(marginVal))
        if err != errType.SUCCESS {
            cli.Println("e", "WriteWord to %s reg %d failed", devName, marginReg)
            smbus.Close()
            return
        }
    }

    err = pmbus.WriteByte(devName, OPERATION, marginCmd)
    if err != errType.SUCCESS {
        cli.Println("e", "WriteByte to %s reg %d failed", devName, OPERATION)
        smbus.Close()
        return
    }

    smbus.Close()
    return 0;
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

    //POUT
    outStrTemp = "-"
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    digIout, fracIout, err := ReadIout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, digIout, fracIout)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadVin(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    //PIN
    outStrTemp = "-"
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    //IIN
    outStrTemp = "-"
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    fmt.Println(outStr)

    return
}


func DispStatus(devName string) (err int) {

    vrmTitle := []string {"VIN", "VOUT", "IOUT", "POUT", "STATUS"}
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

    dig, frac, err := ReadVin(devName)
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

    dig, frac, _ = ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return

}




