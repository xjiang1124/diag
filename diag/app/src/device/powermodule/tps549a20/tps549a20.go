// Go compiler wants a .go file in package

package tps549a20

import (
    "fmt"

    "common/cli"
    "common/dcli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
    "hardware/i2cinfo"
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

func ReadOperation(devName string) (data uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    data, err = pmbus.ReadByte(devName, pmbus.OPERATION)
    return
}

func ReadFreqConfig(devName string) (data uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    data, err = pmbus.ReadByte(devName, FREQUENCY_CONFIG)
    return
}

func ReadVoutMargin(devName string) (data uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    data, err = pmbus.ReadByte(devName, VOUT_MARGIN)
    return
}

func ReadVoutAdjustment(devName string) (status uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadByte(devName, VOUT_ADJUSTMENT)
    return
}

func GetOpMargin (devName string) (data string, err int) {
    regVal, err := ReadOperation(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read Operaton", devName)
        return
    }

    regVal = (regVal >> 2) & 0xF
    data, ok := opMargin[regVal]
    if !ok {
        data = "Invalid"
        err = errType.FAIL
    }
    return
}

func GetFreqConfig (devName string) (data string, err int) {
    regVal, err := ReadFreqConfig(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read Freq Config", devName)
        return
    }
    data = freqConfig[regVal & 0x7]
    return
}

func GetVoutAdjPct (devName string) (data float64, err int) {
    regVal, err := ReadVoutAdjustment(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read Freq Config", devName)
        return
    }
    data = voutAdjPct[regVal & 0x1F]
    return
}

func GetVoutMarginPct (devName string) (data float64, err int) {
    regVal, err := ReadVoutMargin(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read VOUT Margin", devName)
        return
    }

    opMargin, err := GetOpMargin(devName)
    if err != errType.SUCCESS {
        return
    }

    if opMargin == "MarginOff" {
        data = 0.0
    } else if opMargin == "MarginLow" {
        data = voutMarginLowhPct[regVal & 0xF]
    } else {
        data = voutMarginHighPct[(regVal>>4) & 0xF]
    }

    return
}

func TestTps549a20(devName string) (err int) {
    _, err = ReadStatus(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
    }
    return
}

func DispStatus(devName string) (err int) {
    var vrmTitle []string
    var vBaseMv float64
    if i2cinfo.CardType == "GINESTRA_D5" || (i2cinfo.CardType == "GINESTRA_D4" && devName == "VDD_DDR") {
        vrmTitle = []string {"FREQ", "VOUT_ADJ", "VOUT_VMG", "STATUS", "VOUT(750mv based)"}
        vBaseMv = 750.0
    } else if i2cinfo.CardType == "GINESTRA_D4" && devName == "DDR_VDDQ" {
        vrmTitle = []string {"FREQ", "VOUT_ADJ", "VOUT_VMG", "STATUS", "VOUT(1200mv based)"}
        vBaseMv = 1200.0
    } else {
        vrmTitle = []string {"FREQ", "VOUT_ADJ", "VOUT_VMG", "STATUS", "VOUT(850mv based)"}
        vBaseMv = 850.0
    }
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    //cli.Println("i", "--------------------")
    cli.Println("i", "=================================")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)

    freq, err := GetFreqConfig(devName)
    if err != errType.SUCCESS {
        return err
    }
    outStrTemp = fmt.Sprintf("%s", freq)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    adj, err := GetVoutAdjPct(devName)
    if err != errType.SUCCESS {
        return err
    }
    outStrTemp = fmt.Sprintf("%.2f%%", adj)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    margin, err := GetVoutMarginPct(devName)
    if err != errType.SUCCESS {
        return err
    }
    outStrTemp = fmt.Sprintf("%.2f%%", margin)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, err := ReadStatus(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read status")
        return err
    }
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)//+"\n"

    vout := int(vBaseMv * (1.0 + adj/100.0) * (1.0 + margin/100.0))
    outStrTemp = fmt.Sprintf("%d", vout)
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

