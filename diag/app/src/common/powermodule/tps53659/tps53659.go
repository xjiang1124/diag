package tps53659

import (
    "bufio"
    "encoding/hex"
    "fmt"
    "math"
    "os"
    "reflect"
    "sort"
    "strings"

    "common/cli"
    "common/dmutex"
    "common/errType"
    "common/misc"
    "protocol/pmbus"
    "hardware/tps53659Reg"
)

const (
    DEVICE_ID = 0x59
    VERIFY_FLAG = "=== READ VERIFY ==="
)

type TPS53659 struct {
    numPhases int
}

type DEV_INFO struct {
    addr uint64
    numByte int
    access string
}

var channelMap map[string]byte
var devInfoMap map[string]DEV_INFO

func init() {
    channelMap = make(map[string]byte)
    channelMap["VRM_CAPRI_DVDD"] = 0
    channelMap["VRM_CAPRI_AVDD"] = 1

    devInfoMap = make(map[string]DEV_INFO)
    devInfoMap["MFR_ID"] = DEV_INFO{tps53659Reg.MFR_ID, 2, "BLOCK"}
    devInfoMap["MFR_MODEL"] = DEV_INFO{tps53659Reg.MFR_MODEL, 2, "BLOCK"}
    devInfoMap["MFR_REVISION"] = DEV_INFO{tps53659Reg.MFR_REVISION, 2, "BLOCK"}
    devInfoMap["MFR_DATE"] = DEV_INFO{tps53659Reg.MFR_DATE, 2, "BLOCK"}
    devInfoMap["MFR_SERIAL"] = DEV_INFO{tps53659Reg.MFR_SERIAL, 4, "BLOCK"}
    devInfoMap["IC_DEVICE_ID"] = DEV_INFO{tps53659Reg.IC_DEVICE_ID, 1, "BLOCK"}
    devInfoMap["IC_DEVICE_REV"] = DEV_INFO{tps53659Reg.IC_DEVICE_REV, 1, "BLOCK"}
}

/*
    Calculate voltage output from vid value
    Formula comes from TPS53659 data sheet
 */
func calcVoltFromVid (vid byte, dacStep uint64) (integer uint64, dec uint64, err int) {
    var volt uint64
    var base uint64
    err = errType.SUCCESS

    if vid == 0 {
        return 0, 0, err
    }

    if (dacStep != 5 && dacStep != 10) {
        return 0, 0, errType.INVALID_PARAM
    }

    if dacStep == 5 {
        base = 250
    } else {
        base = 500
    }

    volt = (uint64(vid) - 1) * dacStep + base

    return volt/1000, volt%1000, errType.SUCCESS
}

/*
    Calculate vid from given voltage (in mv unit)
 */
func calcVidFromVolt (tgtVoltMv uint64, dacStep uint64) (vid byte, err int) {
    var volt uint64
    var voltNext uint64
    var base uint64
    var vidMax uint64
    var vidStep uint64

    err = errType.SUCCESS

    if tgtVoltMv == 0 {
        return 0, err
    }

    if (dacStep != 5 && dacStep != 10) {
        return 0, errType.INVALID_PARAM
    }

    if dacStep == 5 {
        base = 250
        vidMax = 0xFF
    } else {
        base = 500
        vidMax = 0xC9
    }

    for vidStep = 1; vidStep < vidMax; vidStep++ {
        volt = (vidStep - 1) * dacStep + base
        voltNext = vidStep * dacStep + base
        if (volt <= tgtVoltMv) && (voltNext > tgtVoltMv) {
            //cli.Println("tgtVoltMv", tgtVoltMv, "vidStep", vidStep, "volt", volt, "voltNext", voltNext)
            return byte(vidStep), err
        }
    }
    return 0, errType.FAIL
}

/*
    3659 has many register using EXP format.
    16-bit value, 
    upper 5 bits: Linear two's complement format exponent.
    lower 11 bits: Linear two's complement format mantissa.
 */
func getExpOutput(input uint16) (integer uint64, dec uint64, err int) {
    var expUint uint64
    var expInt int64
    var expFloat float64
    var manFloat float64
    var expOutFloat float64

    expUint = uint64(input >> 11)
    manFloat = float64(input & 0x7FF)

    expInt, err = misc.TwoCmplBits64(expUint, 5)
    if err != errType.SUCCESS {
        return 0, 0, err
    }

    expFloat = float64(expInt)
    expOutFloat = math.Pow(2, expFloat) * manFloat
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return integer, dec, errType.SUCCESS
}

func (tps53659 *TPS53659) ReadStatus(devName string) (status uint16, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]

    // Write page register
    pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)

    status, err = pmbus.ReadWord(devName, tps53659Reg.STATUS_WORD)

    return
}


func (tps53659 *TPS53659) ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]

    // Write page register
    pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)

    data, err = pmbus.ReadWord(devName, tps53659Reg.READ_VOUT)

    dacStepRegVal, err = pmbus.ReadByte(devName, tps53659Reg.VOUT_MODE)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return integer, dec, errType.SUCCESS
}

func (tps53659 *TPS53659) ReadVboot(devName string) (integer uint64, dec uint64, err int) {
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]

    // Write page register
    pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)

    // Read Vboot
    data, err = pmbus.ReadWord(devName, tps53659Reg.MFR_SPECIFIC_11)

    dacStepRegVal, err = pmbus.ReadByte(devName, tps53659Reg.VOUT_MODE)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return integer, dec, errType.SUCCESS
}

func (tps53659 *TPS53659) ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]

    // Write page register
    pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)

    // Write phase register: all phases
    pmbus.WriteByte(devName, tps53659Reg.PHASE, 0x80)

    data, err = pmbus.ReadWord(devName, tps53659Reg.READ_IOUT)
    integer, dec, err = getExpOutput(data)
    return
}

func (tps53659 *TPS53659) ReadIoutPhase(devName string, phase byte) (integer uint64, dec uint64, err int) {
    var data uint16

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]

    // Write page register
    pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)

    // Write phase register: all phases
    pmbus.WriteByte(devName, tps53659Reg.PHASE, phase)

    data, err = pmbus.ReadWord(devName, tps53659Reg.READ_IOUT)
    integer, dec, err = getExpOutput(data)
    return
}

/*
    Read register with EXP format and calculate output
 */
func (tps53659 *TPS53659) ReadRegExp(devName string, addrAddr uint64) (integer uint64, dec uint64, err int) {
    var data uint16

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    defer dmutex.Unlock(devName)

    channel := channelMap[devName]

    // Write page register
    pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)

    data, err = pmbus.ReadWord(devName, addrAddr)
    integer, dec, err = getExpOutput(data)

    return
}

func (tps53659 *TPS53659) ReadVin(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, tps53659Reg.READ_VIN)
    return
}

func (tps53659 *TPS53659) ReadIin(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, tps53659Reg.READ_IIN)
    return
}

func (tps53659 *TPS53659) ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, tps53659Reg.READ_TEMPERATURE_1)
    return
}

func (tps53659 *TPS53659) ReadPout(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, tps53659Reg.READ_POUT)
    return
}

func (tps53659 *TPS53659) ReadPin(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, tps53659Reg.READ_PIN)
    return
}

func (tps53659 *TPS53659) ReadVoutLn(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, tps53659Reg.MFR_SPECIFIC_04)
    return
}

func (tps53659 *TPS53659) ReadDeviceID(devName string) (devID byte, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    defer dmutex.Unlock(devName)

    devID, err = pmbus.ReadByte(devName, tps53659Reg.IC_DEVICE_ID)
    return devID, err
}

func (tps53659 *TPS53659) SetVMargin(devName string, pct int) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]

    if pct == 0 {
        marginCmd = tps53659Reg.MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = tps53659Reg.MARGIN_HIGH_CMD
        marginReg = tps53659Reg.VOUT_MARGIN_HIGH
    } else {
        marginCmd = tps53659Reg.MARGIN_LOW_CMD
        marginReg = tps53659Reg.VOUT_MARGIN_LOW
    }

    // Write page register
    pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)

    dacStepRegVal, err = pmbus.ReadByte(devName, tps53659Reg.VOUT_MODE)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    data, err = pmbus.ReadWord(devName, tps53659Reg.VOUT_COMMAND)

    integer, dec, _ := calcVoltFromVid(byte(data), dacStep)
    voltMv := integer *1000 + dec
    voltMvTemp := voltMv * uint64(100+pct)
    voltMvTgt := voltMvTemp / 100

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(voltMvTgt, dacStep)
    //cli.Println("d", "voltMvTgt:", voltMvTgt, "vidTgt:", vidTgt, "reg:", marginReg)
    pmbus.WriteWord(devName, marginReg, uint16(vidTgt))

    // Set to PMBus control
    pmbus.WriteByte(devName, tps53659Reg.MFR_SPECIFIC_02, tps53659Reg.CTRL_PMBUS)

    // Enable Vmargin
    pmbus.WriteByte(devName, tps53659Reg.OPERATION, marginCmd)

    return
}


func (tps53659 *TPS53659) DispStatus(devName string) (err int) {
    vrmTitle := []string {"VBOOT", "POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
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

    outStr = fmt.Sprintf(fmtNameStr, devName)

    dig, frac, _ := tps53659.ReadVboot(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = tps53659.ReadPout(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = tps53659.ReadVout(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = tps53659.ReadIout(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = tps53659.ReadPin(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = tps53659.ReadVin(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = tps53659.ReadIin(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = tps53659.ReadTemp(devName)
    if dig == 0 && frac == 0 {
        outStrTemp = "-.-"
    } else {
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    }
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := tps53659.ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    cli.Println("i", outStr)

    return
}

func (tps53659 *TPS53659) ReadByte(devName string, regAddr uint64) (data byte, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]
    err = pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)
    if err != errType.SUCCESS {
        return
    }
    data, err = pmbus.ReadByte(devName, regAddr)
    return
}

func (tps53659 *TPS53659) ReadWord(devName string, regAddr uint64) (data uint16, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]
    err = pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)
    if err != errType.SUCCESS {
        return
    }
    data, err = pmbus.ReadWord(devName, regAddr)
    return
}

func (tps53659 *TPS53659) WriteByte(devName string, regAddr uint64, data byte) (err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]
    err = pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.WriteByte(devName, regAddr, data)
    return
}

func (tps53659 *TPS53659) WriteWord(devName string, regAddr uint64, data uint16) (err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]
    err = pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.WriteWord(devName, regAddr, data)
    return
}

func (tps53659 *TPS53659) SendByte(devName string, data byte) (err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    channel := channelMap[devName]
    err = pmbus.WriteByte(devName, tps53659Reg.PAGE, channel)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.SendByte(devName, data)
    return
}

func (tps53659 *TPS53659) ReadBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    byteCnt, err = pmbus.ReadBlock(devName, regAddr, dataBuf)
    return
}

func (tps53659 *TPS53659) WriteBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    byteCnt, err = pmbus.WriteBlock(devName, regAddr, dataBuf)
    return
}

func (tps53659 *TPS53659) ProgramVerifyNvm(devName string, fileName string, mode string, verbose bool) (err int) {
    verifyStart := false
    var errCnt int

    if mode != "VERIFY" && mode != "PROGRAM" {
        cli.Println("e", "Invalid mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    defer dmutex.Unlock(devName)

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
            }

        case "SendByte":
            if verbose == true {
                cli.Println("i", "SendByte", cmd[1])
            }
            err = pmbus.SendByte(devName, regAddr[0])

            if err != errType.SUCCESS {
                cli.Printf("e", "Failed to send byte data! addr=0x%x", regAddr[0])
                errCnt = errCnt + 1
            }

        default:
            cli.Println("e", "Unsupported cmd", cmd[0])
            errCnt = errCnt + 1
            break
        }
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

func (tps53659 *TPS53659) Info(devName string) (err int) {
    var outKey string
    var outValue string
    var dataBuf []byte
    //var numByte int

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()
    defer dmutex.Unlock(devName)

    // Sort keys; otherwise the sequence will be random
    keys := make([]string, 0)
    for k, _ := range(devInfoMap) {
        keys = append(keys, k)
    }
    sort.Strings(keys)

    cli.Println("i", "--------------------")
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


