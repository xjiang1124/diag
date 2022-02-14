package tmp42123

import (
    "fmt"

    "common/cli"
    "common/errType"
    "protocol/smbus"
    "common/misc"
)

func ReadMfgId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, MFG_ID)
    return
}

func ReadDevId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, DEV_ID)
    return
}

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
        tempHighAddr = LOCAL_TEMP_HIGH
        tempLowAddr = LOCAL_TEMP_LOW
    case REMOTE_TEMP1:
        tempHighAddr = REMOTE_TEMP_HIGH1
        tempLowAddr = REMOTE_TEMP_LOW1
    case REMOTE_TEMP2:
        tempHighAddr = REMOTE_TEMP_HIGH2
        tempLowAddr = REMOTE_TEMP_LOW2
    default:
        err = errType.INVALID_PARAM
        return
    }

    tempHighByte, err := smbus.ReadByte(devName, tempHighAddr)
    if err != errType.SUCCESS {
        return
    }

    tempLowByte, err := smbus.ReadByte(devName, tempLowAddr)
    if err != errType.SUCCESS {
        return
    }

    integer, err = misc.TwoCmplBits64(uint64(tempHighByte), misc.BITS_8)
    integer = (integer * 10000 + 625 * int64(tempLowByte)) / 10000
    dec = (integer * 10000 + 625 * int64(tempLowByte)) % 10000
    if dec < 0 {
        dec = -dec
    }

    return
}

func DispStatus(devName string) (err int) {
    err = errType.SUCCESS

    degSym := fmt.Sprintf("(%cC)",0xB0)
    tempTitle := []string {"LOCAL", "REMOTE1",}
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

