package tps53659

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
    "common/dcli"
    "common/errType"
    "common/misc"
    "hardware/i2cinfo"
    //"hardware/pmbus"
    "protocol/pmbus"
)

const (
    DEVICE_ID = 0x59
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
    devInfoMap["MFR_ID"]        = DEV_INFO{pmbus.MFR_ID, 2, "BLOCK"}
    devInfoMap["MFR_MODEL"]     = DEV_INFO{pmbus.MFR_MODEL, 2, "BLOCK"}
    devInfoMap["MFR_REVISION"]  = DEV_INFO{pmbus.MFR_REVISION, 2, "BLOCK"}
    devInfoMap["MFR_DATE"]      = DEV_INFO{pmbus.MFR_DATE, 2, "BLOCK"}
    devInfoMap["MFR_SERIAL"]    = DEV_INFO{pmbus.MFR_SERIAL, 4, "BLOCK"}
    devInfoMap["IC_DEVICE_ID"]  = DEV_INFO{pmbus.IC_DEVICE_ID, 1, "BLOCK"}
    devInfoMap["IC_DEVICE_REV"] = DEV_INFO{pmbus.IC_DEVICE_REV, 1, "BLOCK"}
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
    var dacStepRegVal byte
    var dacStep uint64

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

    data, err = pmbus.ReadWord(devName, pmbus.READ_VOUT)

    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)

    if dacStepRegVal == DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return integer, dec, errType.SUCCESS
}

func ReadVboot(devName string) (integer uint64, dec uint64, err int) {
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

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

    // Read Vboot
    data, err = pmbus.ReadWord(devName, MFR_SPECIFIC_11)

    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)

    if dacStepRegVal == DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

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

    // Write phase register: all phases
    pmbus.WriteByte(devName, pmbus.PHASE, 0x80)

    data, err = pmbus.ReadWord(devName, pmbus.READ_IOUT)
    integer, dec, err = pmbus.Linear11(data)
    return
}

func ReadIoutPhase(devName string, phase byte) (integer uint64, dec uint64, err int) {
    var data uint16

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)

    // Write phase register: all phases
    pmbus.WriteByte(devName, pmbus.PHASE, phase)

    data, err = pmbus.ReadWord(devName, pmbus.READ_IOUT)
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
    integer, dec, err = ReadRegLnr11(devName, pmbus.READ_VIN)
    return
}

func ReadIin(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadRegLnr11(devName, pmbus.READ_IIN)
    return
}

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadRegLnr11(devName, pmbus.READ_TEMPERATURE_1)
    return
}

func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadRegLnr11(devName, pmbus.READ_POUT)
    return
}

func ReadPin(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadRegLnr11(devName, pmbus.READ_PIN)
    return
}

func ReadPinMax10(devName string) (integer uint64, dec uint64, err int) {
    integer = 0
    dec = 0
    for i := 0; i < 10; i++ {
        integer1, dec1, _ := ReadRegLnr11(devName, pmbus.READ_PIN)
        if integer1 > integer {
            integer = integer1
            dec = dec1
        } else if integer1 == integer {
            if dec1 > dec {
                dec = dec1
            }
        }
    }
    return
}

func ReadVoutLn(devName string) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadRegLnr11(devName, MFR_SPECIFIC_04)
    return
}

func ReadDeviceID(devName string) (devID byte, err int) {
    var readData uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    readData, err = pmbus.ReadWord(devName, pmbus.IC_DEVICE_ID)
    devID = (uint8)(readData & 0xff00 >> 8)
    return devID, err
}

func ReadMfrRevision(devName string) (MfrRevision uint16, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    MfrRevision, err = pmbus.ReadWord(devName, pmbus.MFR_REVISION)
    return
}

func findVid(devName string, voutMv uint64) (vid byte, err int) {
    var dacStepRegVal byte
    var dacStep uint64

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Get current VOUT
    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)
    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)
    if err != errType.SUCCESS {
        return
    }

    if dacStepRegVal == DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }
    vid, err = calcVidFromVolt(voutMv, dacStep)
    return
}

func FindVid(devName string, voutMv uint64) (vid byte, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    vid, err = findVid(devName, voutMv)
    return
}

func UpdateVboot(devName string, tgtVoutMv uint64) (err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write Page")
        return
    }

    // Get current VOUT
    // Write page register
    pmbus.WriteByte(devName, pmbus.PAGE, page)

    // Set to PMBus control
    err = pmbus.WriteByte(devName, MFR_SPECIFIC_02, CTRL_PMBUS)
    if err != errType.SUCCESS {
        cli.Println("e", "Can not set to PMBus control!")
        return
    }

    // Set VOUT_MAX
    voutMaxVid, err := findVid(devName, VOUT_MAX_MV)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to find vid")
        return
    }
    err = pmbus.WriteWord(devName, pmbus.VOUT_MAX, uint16(voutMaxVid))
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to update VOUT_MAX")
        return
    }

    // Update VBoot
    vbootVid, err := findVid(devName, tgtVoutMv)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to find vid")
        return
    }

    err = pmbus.WriteByte(devName, pmbus.VOUT_COMMAND, vbootVid)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to update VBOOT")
        return
    }

    err = pmbus.WriteByte(devName, MFR_SPECIFIC_11, vbootVid)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to update VBOOT")
        return
    }

    // Store to NVM
    err = pmbus.SendByte(devName, pmbus.STORE_DEFAULT_ALL)

    return
}
func SetVMarginByValue(devName string, tgtVoutMv uint64) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

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
    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)

    if dacStepRegVal == DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    data, err = pmbus.ReadWord(devName, pmbus.VOUT_COMMAND)
    integer, dec, _ := calcVoltFromVid(byte(data), dacStep)

    curVoutMv := integer *1000 + dec
    cli.Println("d", "curVoutMv:", curVoutMv)

    if tgtVoutMv == curVoutMv {
        marginCmd = MARGIN_NONE_CMD
    } else if tgtVoutMv > curVoutMv {
        marginCmd = MARGIN_HIGH_CMD
        marginReg = pmbus.VOUT_MARGIN_HIGH
    } else {
        marginCmd = MARGIN_LOW_CMD
        marginReg = pmbus.VOUT_MARGIN_LOW
    }

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(tgtVoutMv, dacStep)

    if marginCmd != MARGIN_NONE_CMD {
        err = pmbus.WriteWord(devName, marginReg, uint16(vidTgt))
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        }
    }
    // Set to PMBus control
    err = pmbus.WriteByte(devName, MFR_SPECIFIC_02, CTRL_PMBUS)
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    }

    // Enable Vmargin
    err = pmbus.WriteByte(devName, pmbus.OPERATION, marginCmd)
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    }

    return
}

func SetVMargin(devName string, pct int) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64
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

    // Disable Vmargin
    err = pmbus.WriteByte(devName, pmbus.OPERATION, MARGIN_NONE_CMD)
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
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

    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)

    if dacStepRegVal == DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    data, err = pmbus.ReadWord(devName, pmbus.VOUT_COMMAND)

    integer, dec, _ := calcVoltFromVid(byte(data), dacStep)
    voltMv := integer *1000 + dec
    voltMvTemp := voltMv * uint64(100+pct)
    voltMvTgt := voltMvTemp / 100

    cli.Printf("d", "VOUT(mv): %d; TargetVolt(mv): %d\n", voltMv, voltMvTgt)
    if (devName=="ELB0_CORE" || devName=="ELB0_ARM") { 
        if (voltMv < 650 || voltMv > 1000) {
            cli.Printf("e", "Invalid VOUT!! VOUT(mv): %d; TargetVolt(mv): %d\n", voltMv, voltMvTgt)
            err = errType.FAIL
            return
        }
    }

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(voltMvTgt, dacStep)
    cli.Printf("i", "Target VID: 0x%x\n", vidTgt)

    if pct != 0 {
        err = pmbus.WriteWord(devName, marginReg, uint16(vidTgt))
        if err != errType.SUCCESS {
            cli.Println("e", "VMargin failed!")
            return
        }
    }
    // Set to PMBus control
    err = pmbus.WriteByte(devName, MFR_SPECIFIC_02, CTRL_PMBUS)
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
    misc.SleepInSec(1)

    return
}

func TriggerVrFault(devName string) (err int) {
    var limit uint16
    var data uint16
    var integer uint64

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write Page")
        return
    }

    pmbus.WriteByte(devName, pmbus.PAGE, page)
    // read Input Current
    integer, _, err = pmbus.ReadLnr11(devName, page, pmbus.READ_IIN)

   // Update IIN_OC_FAULT_LIMIT
    data, err = pmbus.ReadWord(devName, pmbus.IIN_OC_FAULT_LIMIT)
    // IIN_OCF_EXP field is read-only, with the reset value being 11111b (2 ^-1 = 0.5A)
    // just modify IIN_OC_MAN to be lower than the Input Current reading
    limit = uint16((float64(integer) * 0.9) / 0.5)
    limit = (data & 0xF800) | (limit & 0x7FF);
    cli.Printf("i", "limit: 0x%04x\n", limit)
    // sleep 1s to allow the above message to be printed
    misc.SleepInSec(1)
    err = pmbus.WriteWord(devName, pmbus.IIN_OC_FAULT_LIMIT, limit)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to set IIN OC fault limit")
        return
    }
    return
}

/*
    Read Device ID and compare with expected one
 */
func TestTps53659(devName string) (err int) {
    devID, err := ReadDeviceID(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }

    /* hack for now. Probably need to based on device rev */
    if ((devID != DEVICE_ID) && (devID != DEVICE_ID)) {
        dcli.Println("F", devName, " Invalid Device ID: expected", DEVICE_ID, "read", devID)
        return errType.FAIL
    }
    return
}

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"VBOOT", "POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    //For cisco MtFuji, they want to display their firmware revision as well which is stored in the mfg revision register 9Bh
    if i2cinfo.CardType == "MTFUJI" {
        vrmTitle = append(vrmTitle, "FW REV")
    }

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

    dig, frac, _ := ReadVboot(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    if i2cinfo.CardType == "MTFUJI" {
        MfrRev, _ := ReadMfrRevision(devName)
        outStrTemp = fmt.Sprintf("0x%X", MfrRev)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) + "\n"
    } else {
        outStr = outStr + fmt.Sprintf("\n")
    }

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


