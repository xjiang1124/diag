package tmp422

import (
    "fmt"

    "common/cli"
    "common/errType"
    "common/i2c"
    "common/misc"
    "hardware/tmp422Reg"
)

func ReadMfgId(devName string) (id byte, err int) {
    idBytes, err := i2c.Read(devName, tmp422Reg.MFG_ID, misc.ONE_BYTE)
    id = byte(idBytes[0])
    return
}

func ReadDevId(devName string) (id byte, err int) {
    idBytes, err := i2c.Read(devName, tmp422Reg.DEV_ID, misc.ONE_BYTE)
    id = byte(idBytes[0])
    return
}

func ReadTemp(devName string, channel byte) (integer int64, dec int64, err int) {
    var tempHighAddr uint64
    var tempLowAddr uint64

    err = errType.SUCCESS

    switch channel {
    case tmp422Reg.LOCAL_TEMP:
        tempHighAddr = tmp422Reg.LOCAL_TEMP_HIGH
        tempLowAddr = tmp422Reg.LOCAL_TEMP_LOW
    case tmp422Reg.REMOTE_TEMP1:
        tempHighAddr = tmp422Reg.REMOTE_TEMP_HIGH1
        tempLowAddr = tmp422Reg.REMOTE_TEMP_LOW1
    case tmp422Reg.REMOTE_TEMP2:
        tempHighAddr = tmp422Reg.REMOTE_TEMP_HIGH2
        tempLowAddr = tmp422Reg.REMOTE_TEMP_LOW2
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
    for i:=0; i<tmp422Reg.MAX_CHANNEL; i++ {
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

