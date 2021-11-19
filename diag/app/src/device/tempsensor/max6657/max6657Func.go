package max6657

import (
    "fmt"

    "common/cli"
    "common/errType"
    "protocol/smbus"
    "common/misc"
)

func ReadTemp(devName string, channel byte) (integer int64, dec int64, err int) {
    var tempHighAddr uint64
    var tempLowAddr uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    switch channel {
    case LOCAL_TEMP:
        tempHighAddr = READ_INT_EXT_TEMP
        tempLowAddr = READ_INT_TEMP
    case REMOTE_TEMP:
        tempHighAddr = READ_EXT_EXT_TEMP
        tempLowAddr = READ_EXT_TEMP
    default:
        err = errType.INVALID_PARAM
        return
    }

    config, err := smbus.ReadByte(devName, READ_CONFIG)
    cli.Println("i", "config value", config)
    rate, err := smbus.ReadByte(devName, READ_CONV_RATE)
    cli.Println("i", "conversion rate", rate)

    tempHighByte, err := smbus.ReadByte(devName, tempHighAddr)
    if err != errType.SUCCESS {
        return
    }

    tempLowByte, err := smbus.ReadByte(devName, tempLowAddr)
    if err != errType.SUCCESS {
        return
    }

    integer, err = misc.TwoCmplBits64(uint64(tempHighByte), misc.BITS_8)
    // integer = (integer * 10000 + 625 * int64(tempLowByte)) / 10000
    // dec = (integer * 10000 + 625 * int64(tempLowByte)) % 10000
    dec = int64(tempLowByte) * 125
    if dec < 0 {
        dec = -dec
    }

    return
}

func DispStatus(devName string) (err int) {
    err = errType.SUCCESS

    degSym := fmt.Sprintf("(%cC)",0xB0)
    tempTitle := []string {"LOCAL", "REMOTE",}
    var titleStr string
    for _, title := range(tempTitle) {
        tmpStr := fmt.Sprintf("%-20s", title+degSym)
        titleStr = titleStr + tmpStr
    }
    cli.Println("i", titleStr)

    var outStr string
    for i:=0; i<MAX_CHANNEL; i++ {
        integer, dec, err := ReadTemp(devName, byte(i))
        if err != errType.SUCCESS {
            return err
        }
        tmpStr := fmt.Sprintf("%d.%04d", integer, dec)
        tmpStr = fmt.Sprintf("%-20s", tmpStr)
        outStr = outStr + tmpStr
    }
    cli.Println("i", outStr)

    return
}

