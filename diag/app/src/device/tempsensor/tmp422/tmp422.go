package tmp422

import (
    "fmt"

    "common/cli"
    "common/dmutex"
    "common/errType"
    "protocol/i2c"
    "common/misc"
)

func ReadMfgId(devName string) (id byte, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    idBytes, err := i2c.Read(devName, MFG_ID, misc.ONE_BYTE)
    id = byte(idBytes[0])
    return
}

func ReadDevId(devName string) (id byte, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    idBytes, err := i2c.Read(devName, DEV_ID, misc.ONE_BYTE)
    id = byte(idBytes[0])
    return
}

func ReadTemp(devName string, channel byte) (integer int64, dec int64, err int) {
    var tempHighAddr uint64
    var tempLowAddr uint64

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

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

    tempHighByte, err := i2c.Read(devName, tempHighAddr, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        return
    }
    tempHigh := misc.BytesToU64(tempHighByte, misc.ONE_BYTE)

    tempLowByte, err := i2c.Read(devName, tempLowAddr, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        return
    }
    tempLow := misc.BytesToU64(tempLowByte, misc.ONE_BYTE) >> 4

    integer, err = misc.TwoCmplBits64(tempHigh, misc.BITS_8)
    integer = (integer * 10000 + 625 * int64(tempLow)) / 10000
    dec = (integer * 10000 + 625 * int64(tempLow)) % 10000
    if dec < 0 {
        dec = -dec
    }

    return
}

func DispTemp(devName string) (err int) {
    err = errType.SUCCESS

    degSym := fmt.Sprintf("(%cC)",0xB0)
    tempTitle := []string {"LOCAL", "REMOTE1", "REMOTE2",}
    var titleStr string
    for _, title := range(tempTitle) {
        tmpStr := fmt.Sprintf("%-15s", title+degSym)
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
        tmpStr = fmt.Sprintf("%-15s", tmpStr)
        outStr = outStr + tmpStr
    }
    cli.Println("i", outStr)

    return
}

