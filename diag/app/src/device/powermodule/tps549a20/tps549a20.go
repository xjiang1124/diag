// Go compiler wants a .go file in package

package tps549a20

import (
    "fmt"

    "common/cli"
    "common/dmutex"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
)

func ReadStatus(devName string) (status uint16, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to lock device", devName)
        return
    }
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

    status, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"STATUS"}
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)

    status, err := ReadStatus(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read status")
        return err
    }

    outStr = fmt.Sprintf(fmtNameStr, devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    cli.Println("i", outStr)

    return

}

func SetVMargin(devName string, pct int) (err int) {
    var marginCmd byte
    var marginVal byte

    if pct > 12 || pct < -12 {
        return errType.INVALID_PARAM
    }
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to lock device", devName)
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

    if pct == 0 {
        marginCmd = MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = MARGIN_HIGH_CMD
        marginVal = byte(pct) << 4
    } else {
        marginCmd = MARGIN_LOW_CMD
        marginVal = byte(-pct)
    }

    pmbus.WriteByte(devName, VOUT_MARGIN, marginVal)
    pmbus.WriteByte(devName, OPERATION, marginCmd)

    return
}

