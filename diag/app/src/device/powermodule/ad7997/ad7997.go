package ad7997

import (
    "fmt"
    "common/cli"
    "common/dcli"
    "common/errType"
    "common/misc"
    "protocol/smbus"
    "hardware/i2cinfo"
    "hardware/vrminfo"
)

func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var channel byte
    var data uint16

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    // page variable is used to store the channel # for this component, not actual page in memory
    channel, err = i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        dcli.Printf("e", "No channel (page) defined for %s", devName)
        return
    }
    // send address pointer without any data in a write cycle
    err = smbus.SendByte(devName, voutChSelect[channel])
    if err != errType.SUCCESS {
        dcli.Printf("e", "Failed to write %s address pointer", devName)
        return
    }
    data, err = smbus.ReadWord(devName, RESULT)
    if err != errType.SUCCESS {
        dcli.Printf("e", "Failed to read %s result register", devName)
        return
    }
    data = misc.SwapUint16(data)
    curBin := (float64)(data & RESULT_MASK) * VOUT_SCALE
    integer = uint64(curBin)
    dec = uint64(curBin * 1000) % 1000
    return
}

func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    vout_int, vout_dec, vout_err := ReadVout(devName)
    if vout_err != errType.SUCCESS {
        return
    }
    senseResistance := vrminfo.GetSenseResistance(devName)
    vout := (float64)((vout_int * 1000) + vout_dec) / 1000
    iout := vout / senseResistance
    integer = uint64(iout)
    dec = uint64(iout * 1000) % 1000
    return
}

func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    vout_int, vout_dec, vout_err := ReadVout(devName)
    if vout_err != errType.SUCCESS {
        err = vout_err
        return
    }
    iout_int, iout_dec, iout_err := ReadIout(devName)
    if iout_err != errType.SUCCESS {
        err = iout_err
        return
    }
    vout := (float64)((vout_int * 1000) + vout_dec) / 1000
    iout := (float64)((iout_int * 1000) + iout_dec) / 1000
    pout := vout * iout
    integer = uint64(pout)
    dec = uint64(pout * 1000) % 1000
    return
}

func dispStatusSelective(devName string, vrmTitle []string) (err int) {
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
    var dig uint64
    var frac uint64
    for _, title := range(vrmTitle) {
        switch title {
        case "VOUT":
            dig, frac, _ = ReadVout(devName)
        case "IOUT":
            dig, frac, _ = ReadIout(devName)
        case "POUT":
            dig, frac, _ = ReadPout(devName)
        default:
            dig = 0
            frac = 0
        }
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    }
    cli.Println("i", outStr)

    return
}

func DispStatusVout(devName string) (err int) {
    /* use this func when voltage line is connected to ad7997 */
    var vrmTitle []string
    vrmTitle = []string {"VOUT"}
    err = dispStatusSelective(devName, vrmTitle)
    return
}

func DispStatusIout(devName string) (err int){
    /* use this func when current monitor line is connected to ad7997 */
    var vrmTitle []string
    vrmTitle = []string {"IOUT"}
    err = dispStatusSelective(devName, vrmTitle)
    return
}