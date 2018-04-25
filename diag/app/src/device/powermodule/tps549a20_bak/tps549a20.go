// Go compiler wants a .go file in package

package tps549a20

import (
    "fmt"

    "common/cli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
)

type TPS549A20 struct {
}

func (tps549a20 *TPS549A20) ReadStatus(devName string) (status uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}

func (tps549a20 *TPS549A20) DispStatus(devName string) (err int) {
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

    status, err := tps549a20.ReadStatus(devName)
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

func (tps549a20 *TPS549A20) SetVMargin(devName string, pct int) (err int) {
    var marginCmd byte
    var marginVal byte

    if pct > 12 || pct < -12 {
        return errType.INVALID_PARAM
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

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

func (tps549a20 *TPS549A20) ReadByte(devName string, regAddr uint64) (data byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    data, err = pmbus.ReadByte(devName, regAddr)
    return
}

func (tps549a20 *TPS549A20) ReadWord(devName string, regAddr uint64) (data uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    data, err = pmbus.ReadWord(devName, regAddr)
    return
}

func (tps549a20 *TPS549A20) WriteByte(devName string, regAddr uint64, data byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    err = pmbus.WriteByte(devName, regAddr, data)
    return
}

func (tps549a20 *TPS549A20) WriteWord(devName string, regAddr uint64, data uint16) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    err = pmbus.WriteWord(devName, regAddr, data)
    return
}

func (tps549a20 *TPS549A20) SendByte(devName string, data byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    err = pmbus.SendByte(devName, data)
    return
}

func (tps549a20 *TPS549A20) ReadBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    cli.Println("i", "Read block is not supported!")
    return
}

func (tps549a20 *TPS549A20) WriteBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    cli.Println("i", "Write block is not supported!")
    return
}

func (tps549a20 *TPS549A20) ProgramVerifyNvm(devName string, fileName string, mode string, verbose bool) (err int) {
    cli.Println("i", "Function not supported!")
    return
}

func (tps549a20 *TPS549A20) Info(devName string) (err int) {
    cli.Println("i", "Function not supported!")
    return
}
