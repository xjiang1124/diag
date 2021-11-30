package ltc3888

import (
    "bufio"
    "encoding/hex"
    "fmt"
    //"math"
    "os"
    "reflect"
    "sort"
    "strings"

    "common/cli"
    "common/errType"
    "common/misc"
    "hardware/i2cinfo"
    "protocol/pmbus"
    "device/powermodule/ltc2301"
)

const (
    MFG_ID = "LTC"
    MFG_SPECIAL_ID = 0x4880
    DEVICE_ID = "LTC3888-1"
    VERIFY_FLAG = "=== READ VERIFY ==="
)

type DEV_INFO struct {
    addr uint64
    numByte int
    access string
}

var devInfoMap map[string]DEV_INFO

func init() {
    devInfoMap = make(map[string]DEV_INFO)
    devInfoMap["MFR_ID"]        = DEV_INFO{MFR_ID, 3, "BLOCK"}
    devInfoMap["MFR_SPECIAL_ID"] = DEV_INFO{MFR_SPECIAL_ID, 2, "BLOCK"}
    devInfoMap["IC_DEVICE_ID"]  = DEV_INFO{IC_DEVICE_ID, 9, "BLOCK"}
}

/*
    Calculate voltage output from vid value
    Formula comes from TPS53659 data sheet
 */
func calcVoltFromVid (vid uint16) (integer uint64, dec uint64, err int) {
    var volt uint64
    err = errType.SUCCESS

    if vid == 0 {
        return 0, 0, err
    }

    // if (dacStep != 85 && dacStep != 75) {
    //     return 0, 0, errType.INVALID_PARAM
    // }

    // volt = (uint64)(vid) * 10 * dacStep
    volt = (uint64)(vid) * 1000
    volt = volt >> 12
    return volt/1000, volt%1000, errType.SUCCESS
}

/*
    Calculate vid from given voltage (in mv unit)
 */
func calcVidFromVolt (tgtVoltMv uint64) (vid uint16, err int) {
    err = errType.SUCCESS

    if tgtVoltMv == 0 {
        return 0, err
    }

    // if (dacStep != 85 && dacStep != 75) {
    //     return 0, errType.INVALID_PARAM
    // }

    // tgtVoltMv = tgtVoltMv << 12
    // tgtVoltMv = tgtVoltMv / (dacStep * 10)
    tgtVoltMv = (tgtVoltMv << 12 ) / 1000
    vid = (uint16)(tgtVoltMv & 0xffff)
    return vid, err
}

func ReadStatus(devName string) (status uint16, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    status, err = pmbus.ReadStatusWord(devName, page)
    return
}

func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)

    data, err = pmbus.ReadWord(devName, READ_VOUT)

    integer, dec, _ = calcVoltFromVid(data)

    return integer, dec, errType.SUCCESS
}

func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)

    data, err = pmbus.ReadWord(devName, MFR_TOTAL_IOUT)
    integer, dec, err = pmbus.Linear11(data)
    return
}

/*
    Read register with linear 11 format and calculate output
 */
func ReadRegLnr11(devName string, cmd uint64) (integer uint64, dec uint64, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err = pmbus.ReadLnr11(devName, page, cmd)

    return
}

func ReadVin(devName string) (integer uint64, dec uint64, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    integer, dec, err = pmbus.ReadLnr11(devName, pmbus.PAGE_NONE, READ_VIN)

    return
}

func ReadIin(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = ltc2301.ReadIin(devName)
    return
}

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadRegLnr11(devName, READ_TEMPERATURE_1)
    return
}

func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    var vout_int uint64
    var vout_dec uint64
    var iout_int uint64
    var iout_dec uint64
    var pout uint64
    err = errType.SUCCESS 

    vout_int, vout_dec, err = ReadVout(devName)
    if err != errType.SUCCESS {
        return
    }
    iout_int, iout_dec, err = ReadIout(devName)
    if err != errType.SUCCESS {
        return
    }
    pout = (vout_int * 1000 + vout_dec) * (iout_int * 1000 + iout_dec)
     
    return pout/1000000, pout%1000000/1000, errType.SUCCESS
}

func ReadPin(devName string) (integer uint64, dec uint64, err int) {
    var vin_int uint64
    var vin_dec uint64
    var iin_int uint64
    var iin_dec uint64
    var pin uint64
    err = errType.SUCCESS 

    vin_int, vin_dec, err = ReadVin(devName)
    if err != errType.SUCCESS {
        return
    }

    iin_int, iin_dec, err = ReadIin(devName)
    if err != errType.SUCCESS {
        return
    }
    pin = (vin_int * 1000 + vin_dec) * (iin_int * 1000 + iin_dec)
     
    return pin/1000000, pin%1000000/1000, errType.SUCCESS
}

func ReadDeviceID(devName string) (devID string, err int) {
    var byteCnt int
    readData :=make([]byte, 10)

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    byteCnt, err = pmbus.ReadBlock(devName, IC_DEVICE_ID, readData)
    readData[byteCnt] = 0
    devID = string(readData) 
    return devID, err
}

func FindVid(voutMv uint64) (vid uint16, err int) {
    vid, err = calcVidFromVolt(voutMv)

    return
}

func SetVMarginByValue(devName string, tgtVoutMv uint64) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Get current VOUT
    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)

    data, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    integer, dec, _ := calcVoltFromVid(data)

    curVoutMv := integer * 1000 + dec
    cli.Println("d", "curVoutMv:", curVoutMv)

    if tgtVoutMv > curVoutMv {
        marginCmd = MARGIN_HIGH_CMD
        marginReg = VOUT_MARGIN_HIGH
    } else if tgtVoutMv < curVoutMv {
        marginCmd = MARGIN_LOW_CMD
        marginReg = VOUT_MARGIN_LOW
    } else {
        marginCmd = MARGIN_NONE_CMD
    }

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(tgtVoutMv)

    if marginCmd != MARGIN_NONE_CMD {
        // Disable Vmargin
        err = pmbus.WriteByte(devName, OPERATION, MARGIN_NONE_CMD)
        if err != errType.SUCCESS {
            cli.Println("e", "Disable VMargin failed!")
            return
        }

        err = pmbus.WriteWord(devName, marginReg, uint16(vidTgt))
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        }

        // Enable Vmargin
        err = pmbus.WriteByte(devName, OPERATION, marginCmd)
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        }
    }

    return
}

func SetVMargin(devName string, pct int) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16
    //var sign int
    //pctList := make([]int, 0, 2)

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)

    if pct != 0 {
        // Disable Vmargin
        err = pmbus.WriteByte(devName, OPERATION, MARGIN_NONE_CMD)
        if err != errType.SUCCESS {
            cli.Println("e", "Disable VMargin failed!")
            return
        }
    }

    if pct == 0 {
        marginCmd = MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = MARGIN_HIGH_CMD
        marginReg = pmbus.VOUT_MARGIN_HIGH
    } else {
        marginCmd = MARGIN_LOW_CMD
        marginReg = pmbus.VOUT_MARGIN_LOW
    }

    data, err = pmbus.ReadWord(devName, VOUT_COMMAND)

    integer, dec, _ := calcVoltFromVid(data)
    voltMv := integer * 1000 + dec
    voltMvTemp := voltMv * uint64(100+pct)
    voltMvTgt := voltMvTemp / 100

    cli.Printf("d", "VOUT(mv): %d; TargetVolt(mv): %d\n", voltMv, voltMvTgt)
    if (voltMv < 650 || voltMv > 1000) {
        cli.Printf("e", "Invalid VOUT!! VOUT(mv): %d; TargetVolt(mv): %d\n", voltMv, voltMvTgt)
        err = errType.FAIL
        return
    }

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(voltMvTgt)
    cli.Printf("i", "Target VID: 0x%x\n", vidTgt)

    if pct != 0 {
        err = pmbus.WriteWord(devName, marginReg, uint16(vidTgt))
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        }
        // Enable Vmargin
        err = pmbus.WriteByte(devName, pmbus.OPERATION, marginCmd)
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        } else {
            cli.Println("i", "New vmargin enabled")
        }
    }
    misc.SleepInSec(1)

    return
}


func DispStatus(devName string) (err int) {
    vrmTitle := []string {"VOUT", "IOUT", "POUT", "VIN", "IIN", "PIN", "TEMP", "STATUS"}
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

    dig, frac, _ := ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) + "\n"

    cli.Println("i", outStr)

    return
}

func ProgramVerifyNvm(devName string, fileName string, mode string, verbose bool) (err int) {
    verifyStart := false
    var errCnt int

    if mode != "VERIFY" && mode != "PROGRAM" {
        cli.Println("e", "Invalid mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    file, errgo := os.Open(fileName)
    if errgo != nil {
        cli.Println("e", "Failed to open file:", fileName, errgo)
        err = errType.FAIL
        return
    }
    defer file.Close()

    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        if mode == "VERIFY" {
            // Image after this flag is form read verification
            // Start to verify after the flag
            if strings.Contains(scanner.Text(), VERIFY_FLAG) {
                verifyStart = true
                continue
            }

            if verifyStart == false {
                continue
            }
        } else { // Program
            // Image after this flag is form read verification
            if strings.Contains(scanner.Text(), VERIFY_FLAG) {
                break
            }
        }

        cmd := strings.Split(scanner.Text(), ",")
        if verbose == true { cli.Println("i", cmd) }
        // Remove prefix "0x". regAddr is always a byte
        regAddr, _ := hex.DecodeString(cmd[1][2:4])

        // WriteByte and WriteWord: remove first "0x" and last two char (PEC)
        // BlockWrite: remove first "0x" and next two char (byte count), and last two char (PEC)
        switch cmd[0] {
        case "ReadByte":
            var readData byte
            dataStr := cmd[2][2:len(cmd[2])]
            data, errgo := hex.DecodeString(dataStr)
            if errgo != nil {
                cli.Println("e", "Failed to DEcodeString", err)
                err = errType.FAIL
                return
            }
            if verbose == true {
                cli.Printf("i", "%s; addr=0x%x, data=0x%x", dataStr, regAddr[0], data[0])
            }
            readData, err = pmbus.ReadByte(devName, uint64(regAddr[0]))
            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to read byte data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
                return
            }

            if readData != data[0] {
                cli.Printf("e", "Data mismatch! addr=0x%x, expected 0x%x, read back 0x%x", regAddr[0], data[0], readData)
                errCnt = errCnt + 1
            }
        case "ReadWord":
            var readData uint16
            dataStr := cmd[2][2:len(cmd[2])]
            dataArr, _ := hex.DecodeString(dataStr)
            data := uint16(dataArr[0]) | uint16(dataArr[1] << 8)
            if verbose == true {
                cli.Printf("i", "%s; addr=0x%x; data=0x%x", dataStr, regAddr[0], data)
            }

            readData, err = pmbus.ReadWord(devName, uint64(regAddr[0]))
            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to read word data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
                return
            }

            if readData != data {
                cli.Printf("e", "Data mismatch! addr=0x%x, expected 0x%x, read back 0x%x", regAddr[0], data, readData)
                errCnt = errCnt + 1
            }

        case "BlockRead":
            dataStr := cmd[2][4:len(cmd[2])]
            dataLenStr := cmd[2][2:4]
            data, _ := hex.DecodeString(dataStr)
            dataLenArr, _ := hex.DecodeString(dataLenStr)
            dataLen := dataLenArr[0]

            readData := make([]byte, dataLen)
            var byteCnt int
            byteCnt, err = pmbus.ReadBlock(devName, uint64(regAddr[0]), readData)
            if verbose == true {
                cli.Printf("i", "Expected 0x%x; received 0x%x", data, readData)
            }
            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to read block data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
                return
            }
            if byteCnt != int(dataLen) {
                cli.Println("e", "Read block data length mismatch! expected", dataLen, "received", byteCnt)
                errCnt = errCnt + 1
            }
            if reflect.DeepEqual(data, readData) != true {
                cli.Printf("e", "Read block data mismatch! addr=0x%x, expected 0x%x, received 0x%x", regAddr[0], data, readData)
                errCnt = errCnt + 1
            }

        case "WriteByte":
            dataStr := cmd[2][2:len(cmd[2])]
            data, _ := hex.DecodeString(dataStr)

            if verbose == true {
                cli.Printf("i", "%s; addr=0x%x, data=0x%x", dataStr, regAddr[0], data[0])
            }

            err = pmbus.WriteByte(devName, uint64(regAddr[0]), data[0])
            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to write byte data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
                return
            }

        case "WriteWord":
            dataStr := cmd[2][2:len(cmd[2])]
            dataArr, _ := hex.DecodeString(dataStr)
            data := uint16(dataArr[0]) | uint16(dataArr[1] << 8)

            if verbose == true {
                cli.Printf("i", "%s; addr=0x%x; data=0x%x", dataStr, regAddr[0], data)
            }
            err = pmbus.WriteWord(devName, uint64(regAddr[0]), data)
            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to write word data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
                return
            }

        case "BlockWrite":
            // Do not check number of byte written. API always return 0
            dataStr := cmd[2][4:len(cmd[2])]
            data, _ := hex.DecodeString(dataStr)

            if verbose == true {
                cli.Printf("i", "0x%x", data)
            }
            _, err = pmbus.WriteBlock(devName, uint64(regAddr[0]), data)

            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to write block data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
                return
            }

        case "SendByte":
            if verbose == true {
                cli.Println("i", "SendByte", cmd[1])
            }
            err = pmbus.SendByte(devName, regAddr[0])

            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to send byte data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
                return
            }

        default:
            cli.Println("e", "Unsupported cmd", cmd[0])
            errCnt = errCnt + 1
            break
        }
        misc.SleepInUSec(50000)
    }

    if errgo = scanner.Err(); errgo != nil {
        cli.Println("e", "Failed to read file:", fileName, errgo)
        err = errType.FAIL
    }

    if errCnt != 0 {
        err = errType.FAIL
        cli.Println("i", mode, "failed!", err)
    } else {
        cli.Println("i", mode, "Done")
    }

    return
}

func Info(devName string) (err int) {
    var outKey string
    var outValue string
    var dataBuf []byte
    //var numByte int

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    // Sort keys; otherwise the sequence will be random
    keys := make([]string, 0)
    for k, _ := range(devInfoMap) {
        keys = append(keys, k)
    }
    sort.Strings(keys)

    cli.Println("i", "0.00.00.00.00.00.0--")
    outKey = fmt.Sprintf("%-14s ", "Device")
    outValue = fmt.Sprintf("%-14s ", devName)
    for _, k := range(keys) {
        v := devInfoMap[k]
        if v.access == "BLOCK" {
            dataBuf = make([]byte, v.numByte)
            //numByte, err = pmbus.ReadBlock(devName, v.addr, dataBuf)
            _, err = pmbus.ReadBlock(devName, v.addr, dataBuf)
        }
        outKey = outKey + fmt.Sprintf("%-14s", k)
        outValue = outValue + fmt.Sprintf("0x%-11x ", dataBuf)
    }
    cli.Println("i", outKey)
    cli.Println("i", outValue)

    return
}


