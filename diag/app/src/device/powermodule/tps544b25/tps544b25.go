/* 
 
VOUT / IOUT / TEMP 
# i2cget -y 0 0x24 0x20 b
0x17                        2^(-9) = 0.001953125
# i2cget -y 0 0x24 0x29 w
0xf004
# i2cget -y 0 0x24 0x21 w
0x0266                      //614DEC * 1.95 = ~ 1.2V
 
# i2cget -y 0 0x24 0x8E w
0x0019
# i2cget -y 0 0x24 0x8B w
0x0263
# i2cget -y 0 0x24 0x8C w
0xe013                  2^(-4) = 0.0625 * 19 = 1.1875
#
 
 
*/ 

package tps544b25

import (
    "fmt"
    "os"
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

//Read target voltage from VOUT COMMAND
func ReadTargetVoltage(devName string) (integer uint64, dec uint64, err int) {
    var VMODE byte
    var VCMD uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    VMODE = VMODE & 0x1F  //mask exponent
    
    VCMD, err = pmbus.ReadWord(devName, VOUT_COMMAND)

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VCMD)
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

    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    VMODE = VMODE & 0x1F  //mask exponent
    
    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VOUT)

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
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) + "\n"

    cli.Println("i", outStr)

    return

}


func SetVMargin(devName string, pct int) (err int) {
    var cardType string
    var targetvoltage float64 = 0 
    var mantissa uint16 = 0
    var VMODE byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    if (pct > 10) || (pct < -10) {
        cli.Println("e", "Voltage Margin Percent Needs to be +/- 10% MAX", devName)
        err = errType.FAIL
        return
    }

    cardType = os.Getenv("CARD_TYPE")
    //Check the card type to set the target voltage... long term should go into I2C table maybe
    if cardType == "ORTANO" {
        targetvoltage = 1.20 
    } else {
        cli.Println("e", "Uknown Card Type.   Need to touch up go file and add the card type for this card", devName)
        err = errType.FAIL
        return
    }

    targetvoltage = ((targetvoltage * float64(pct))/100) + targetvoltage

    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    VMODE = VMODE & 0x1F  //mask exponent

    mantissa, err = pmbus.GetMantissa(uint16(VMODE & 0x1F), targetvoltage)

    err = pmbus.WriteWord(devName, VOUT_COMMAND, mantissa)
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    }



    return
}

