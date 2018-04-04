package pet1600

import (
    "fmt"

    "common/cli"
    "common/errType"

	"hardware/pmbusCmd"
)

const (
    // 2's complementary of -11
    VOUT_MODE_N = 0x15

    // CMD data length in bytes
    MFR_ID_LEN    = 19
    MFR_MODEL_LEN = 20
)

func DispStatus(devName string) (err int) {
    var fmtDig string = "%d.%03d"
    var fmtStr = "%-10s"
    var fmtNameStr = "%-20s"
    var outStr string
    var outStrTemp string
    var dig uint64
    var frac uint64
    var dataByte byte

    err = pmbusCmd.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbusCmd.Close()
    // MFR info
    //cli.Println("i", "--------------------")
    cli.Println("i", "=================================")
    dataBuf, err := pmbusCmd.ReadMfrId(devName, MFR_ID_LEN)
    outStr = string(dataBuf[:MFR_ID_LEN])
    cli.Println("i", "MFR_ID:", outStr)
    if err != errType.SUCCESS {
        return
    }

    dataBuf, err = pmbusCmd.ReadMfrModel(devName, MFR_MODEL_LEN)
    outStr = string(dataBuf[:MFR_MODEL_LEN])
    cli.Println("i", "MFR_MODEL:", outStr)
    if err != errType.SUCCESS {
        return
    }

    // Status
    stsTitle := []string {"STATUS", "STS_VOUT", "STS_IOUT", "STS_INPUT",
                          "STS_TEMP", "STS_CML", "STS_MFR", "STS_FAN"}
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(stsTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)

    data, err := pmbusCmd.ReadStatusWord(devName, pmbusCmd.PAGE_0)
    outStr = fmt.Sprintf(fmtNameStr, devName)
    outStrTemp = fmt.Sprintf("0x%X", data)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    if err != errType.SUCCESS {
        return
    }

    stsList := []byte {pmbusCmd.STATUS_VOUT,
                         pmbusCmd.STATUS_IOUT,
                         pmbusCmd.STATUS_INPUT,
                         pmbusCmd.STATUS_TEMPERATURE,
                         pmbusCmd.STATUS_CML,
                         pmbusCmd.STATUS_MFR_SPECIFIC,
                         pmbusCmd.STATUS_FANS_1_2,
                     }

    for _, cmd := range(stsList) {
        dataByte, err = pmbusCmd.ReadByte(devName, cmd)
        outStrTemp = fmt.Sprintf("0x%X", dataByte)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        if err != errType.SUCCESS {
            return
        }
    }
    cli.Println("i", outStr)

    // Power outputs
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN"}
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)

    funcs := make([]func(string, byte)(uint64, uint64, int), 6)
    funcs[0] = pmbusCmd.ReadPoutLnr
    funcs[1] = pmbusCmd.ReadVoutLnr
    funcs[2] = pmbusCmd.ReadIoutLnr
    funcs[3] = pmbusCmd.ReadPinLnr
    funcs[4] = pmbusCmd.ReadVinLnr
    funcs[5] = pmbusCmd.ReadIinLnr

    for _, rfunc := range(funcs) {
        dig, frac, err = rfunc(devName, pmbusCmd.PAGE_0)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDig, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        if err != errType.SUCCESS {
            return
        }
    }
    cli.Println("i", outStr)

    // Temp and fan speed
    vrmTitle = []string {"TEMP-1", "TEMP-2", "TEMP-3", "FAN-1", "FAN-2"}
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)

    funcs = make([]func(string, byte)(uint64, uint64, int), 5)
    funcs[0] = pmbusCmd.ReadTemp1Lnr
    funcs[1] = pmbusCmd.ReadTemp2Lnr
    funcs[2] = pmbusCmd.ReadTemp3Lnr
    funcs[3] = pmbusCmd.ReadFanSpd1Lnr
    funcs[4] = pmbusCmd.ReadFanSpd2Lnr

    for _, rfunc := range(funcs) {
        dig, frac, err = rfunc(devName, pmbusCmd.PAGE_NONE)
        if err != errType.SUCCESS {
            return
        }

        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDig, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    }
    cli.Println("i", outStr+"\n")

    return
}

