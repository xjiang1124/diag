package pmic

import (
    "fmt"
    "math"
    "common/cli"
    "common/errType"
    "common/misc"
    //"hardware/i2cinfo"
    "protocol/smbus"
)


func ReadStatus(devName string) (status uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    status, err = smbus.ReadByte(devName, STATUS_REG)
    return
}

func ReadAdcOutput(devName string, adc_sel byte) (data byte, err int) {
    err = smbus.WriteByte(devName, ADC_CTL_REG, ADC_ENABLE | adc_sel)
    if err != errType.SUCCESS {
        return
    }
    data, err = smbus.ReadByte(devName, ADC_CTL_REG)
    data, err = smbus.ReadByte(devName, ADC_OUT_REG)
    return
}

func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var data byte
    var adc_sel uint8
    var vout_mv uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    if devName == "DDR_VDD" || devName == "DDR_VDD_0" || devName == "DDR_VDD_1" {
        adc_sel = SWA_OUTPUT_SEL
    } else if devName == "DDR_VDDQ" || devName == "DDR_VDDQ_0" || devName == "DDR_VDDQ_1" {
        adc_sel = SWC_OUTPUT_SEL
    } else {
        adc_sel = SWD_OUTPUT_SEL
    }

    data, err = ReadAdcOutput(devName, adc_sel)

    vout_mv = 15 * uint64(data)
    integer = vout_mv / 1000
    dec = vout_mv % 1000

    return integer, dec, errType.SUCCESS
}


func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var data1, data2 byte
    var iout uint64
    var output_reg uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    // cannot write R1B in secure mode, default is read current
    /*data1, err = smbus.ReadByte(devName, OUTPUT_SELECT_REG)
    if err != errType.SUCCESS {
        return
    }
    data1 &= ADC_CURRENT_SEL
    err = smbus.WriteByte(devName, OUTPUT_SELECT_REG, data1)
    if err != errType.SUCCESS {
        return
    }*/

    if devName == "DDR_VDD" || devName == "DDR_VDD_0" || devName == "DDR_VDD_1" {
        output_reg = SWA_OUTPUT_REG
    } else if devName == "DDR_VDDQ" || devName == "DDR_VDDQ_0" || devName == "DDR_VDDQ_1" {
        output_reg = SWC_OUTPUT_REG
    } else {
        output_reg = SWD_OUTPUT_REG
    }

    data1, err = smbus.ReadByte(devName, output_reg)
    if err != errType.SUCCESS {
        return
    }
    if (output_reg == SWA_OUTPUT_REG) {
        data2, err = smbus.ReadByte(devName, output_reg + 1) //read SWB_OUTPUT
        if err != errType.SUCCESS {
            return
        }
    } else {
        data2 = 0
    }

    iout = 125 * uint64(data1 + data2)
    integer = iout / 1000
    dec = iout % 1000

    return integer, dec, errType.SUCCESS
}

func CalcPout(devName string) (integer uint64, dec uint64, err int) {
    var pout, iout, vout uint64
    var integer_i, integer_v uint64
    var dec_i, dec_v uint64

    integer_i, dec_i, err = ReadIout(devName)
    if err != errType.SUCCESS {
        return
    }
    iout = integer_i * 1000 + dec_i
    integer_v, dec_v, err = ReadVout(devName)
    if err != errType.SUCCESS {
        return
    }
    vout = integer_v * 1000 + dec_v

    pout = iout * vout / 1000
    integer = pout / 1000
    dec = pout % 1000

    return integer, dec, errType.SUCCESS
}

func ReadVinBulk(devName string) (integer uint64, dec uint64, err int) {
    var data byte
    var vout_mv uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = ReadAdcOutput(devName, VIN_BULK_SEL)

    vout_mv = 70 * uint64(data)
    integer = vout_mv / 1000
    dec = vout_mv % 1000

    return integer, dec, errType.SUCCESS
}

func ReadVinMgmt(devName string) (integer uint64, dec uint64, err int) {
    var data byte
    var vout_mv uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = ReadAdcOutput(devName, VIN_MGMT_SEL)

    vout_mv = 15 * uint64(data)
    integer = vout_mv / 1000
    dec = vout_mv % 1000

    return integer, dec, errType.SUCCESS
}

func ReadVoutBias(devName string) (integer uint64, dec uint64, err int) {
    var data byte
    var vout_mv uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = ReadAdcOutput(devName, VOUT_BIAS_SEL)

    vout_mv = 25 * uint64(data)
    integer = vout_mv / 1000
    dec = vout_mv % 1000

    return integer, dec, errType.SUCCESS
}

func ReadTempTI(devName string) (integer int64, dec uint64, err int) {
    var data byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = ReadAdcOutput(devName, TEMP_SEL)
    integer = 2 * int64(data)
    dec = 0

    return integer, dec, errType.SUCCESS
}

func ReadTemp(devName string) (temp string, err int) {
    var value byte
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    value, err = smbus.ReadByte(devName, TEMP_MEASUREMENT_REG)
    value = (value >> 5) & 0x7
    switch value {
    case 0:
        return "<=85C", errType.SUCCESS
    case 1:
        return "85C", errType.SUCCESS
    case 2:
        return "95C", errType.SUCCESS
    case 3:
        return "105C", errType.SUCCESS
    case 4:
        return "115C", errType.SUCCESS
    case 5:
        return "125C", errType.SUCCESS
    case 6:
        return "135C", errType.SUCCESS
    default:
        return ">=140C", errType.SUCCESS
    }
}

func ReadVendorID(devName string) (vendorId uint16, err int) {
    var vId_0, vId_1 byte
    var vId uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    vId_0, err = smbus.ReadByte(devName, VENDOR_ID_BYTE0_REG)
    vId_1, err = smbus.ReadByte(devName, VENDOR_ID_BYTE1_REG)
	vId = uint16(vId_1) << 8 | uint16(vId_0)
    return vId, err
}

func SetVMarginByValue(devName string, tgtVoutMv uint64) (err int) {
    var marginReg uint64
    var vmin, vmax uint64
    var voutSetting uint64
    var vStart uint64
    var data byte

    if devName == "DDR_VDD" {
        marginReg = SWA_VOL_SETTING_REG_TI
        vmin = VOUT_1P1_MIN
        vmax = VOUT_1P1_MAX
        vStart = 800
	} else if devName == "DDR_VDD_0" || devName == "DDR_VDD_1" {
        marginReg = SWA_VOL_SETTING_REG_MPS
        vmin = VOUT_1P1_MIN
        vmax = VOUT_1P1_MAX
        vStart = 800
    } else if devName == "DDR_VDDQ" {
        marginReg = SWC_VOL_SETTING_REG_TI
        vmin = VOUT_1P1_MIN
        vmax = VOUT_1P1_MAX
        vStart = 800
	} else if devName == "DDR_VDDQ_0" || devName == "DDR_VDDQ_1" {
        marginReg = SWC_VOL_SETTING_REG_MPS
        vmin = VOUT_1P1_MIN
        vmax = VOUT_1P1_MAX
        vStart = 800
    } else if devName == "DDR_VPP" {
        marginReg = SWD_VOL_SETTING_REG_TI
        vmin = VOUT_1P8_MIN
        vmax = VOUT_1P8_MAX
        vStart = 1500
    } else if devName == "DDR_VPP_0" || devName == "DDR_VPP_1" {
        marginReg = SWD_VOL_SETTING_REG_MPS
        vmin = VOUT_1P8_MIN
        vmax = VOUT_1P8_MAX
        vStart = 1500
    } else {
	    return errType.INVALID_PARAM
	}
    tgtVoutMv = uint64(math.Round(float64(tgtVoutMv) / 5)) * 5
    if (tgtVoutMv < vmin || tgtVoutMv > vmax) {
        return errType.INVALID_PARAM
    }
    voutSetting = ((tgtVoutMv - vStart) / 5) << 1

    cli.Printf("d", "tgtVoutMv(mv): %d; voutSetting: 0x%x\n", tgtVoutMv, voutSetting)

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    if marginReg >= SWA_VOL_SETTING_REG_TI && marginReg <= SWD_VOL_SETTING_REG_TI {
        // unlock vendor specific region
        err = smbus.WriteByte(devName, REG_LOCK_REG, 0x0)
        if err != errType.SUCCESS {
            return
        }
        err = smbus.WriteByte(devName, REG_LOCK_REG, 0x95)
        if err != errType.SUCCESS {
            return
        }
        err = smbus.WriteByte(devName, REG_LOCK_REG, 0x64)
        if err != errType.SUCCESS {
            return
        }

        // register R72[5] changes the dependency of the output voltage from relying on
        // R21/23/25/27 to R45/47/49/4B
        data, err = smbus.ReadByte(devName, 0x72)
        data |= 0x20
        err = smbus.WriteByte(devName, 0x72, data)
        if err != errType.SUCCESS {
            return
        }
	}

    // unlock DIMM vendor region
    err = smbus.WriteByte(devName, 0x37, 0x73)
    if err != errType.SUCCESS {
        return
    }
    err = smbus.WriteByte(devName, 0x38, 0x94)
    if err != errType.SUCCESS {
        return
    }
    err = smbus.WriteByte(devName, 0x39, 0x40)
    if err != errType.SUCCESS {
        return
    }

    if marginReg >= SWA_VOL_SETTING_REG_TI && marginReg <= SWD_VOL_SETTING_REG_TI {
        // set R5D[0] to 1, R5D[4] to 1
        data, err = smbus.ReadByte(devName, 0x5d)
        data |= 0x11
        err = smbus.WriteByte(devName, 0x5d, data)
        if err != errType.SUCCESS {
            return
        }
        // set R5E[0] to 1, R5E[4] to 1
        data, err = smbus.ReadByte(devName, 0x5e)
        data |= 0x11
        err = smbus.WriteByte(devName, 0x5e, data)
        if err != errType.SUCCESS {
            return
        }
    }
    // set voltage
    err = smbus.WriteByte(devName, marginReg, byte(voutSetting))
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    } else {
        cli.Println("i", "New vmargin enabled")
    }
    if marginReg == SWA_VOL_SETTING_REG_TI || marginReg == SWA_VOL_SETTING_REG_MPS {
        err = smbus.WriteByte(devName, marginReg + 2, byte(voutSetting))
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

/*
func SetVMarginByValue(devName string, tgtVoutMv uint64) (err int) {
    var marginReg uint64
    var vmin, vmax uint64
    var vBase uint64
    var offset int8
    var step uint64

    if devName == "DDR_VDD" {
        marginReg = SWA_OFFSET_REG
        vBase = 1100
        offset = -9 //0xF7
        vmin = 1100 - 63
        vmax = 1100 + 63
        step = 2
    } else if devName == "DDR_VDDQ" {
        marginReg = SWC_OFFSET_REG
        vBase = 1100
        offset = -22 //0xEA
        vmin = 1100 - 63
        vmax = 1100 + 63
        step = 2
    } else {
        marginReg = SWD_OFFSET_REG
        vBase = 1800
        offset = -6 //0xFA
        vmin = 1800 - 127
        vmax = 1800 + 127
        step = 1
    }

    if (tgtVoutMv < vmin || tgtVoutMv > vmax) {
        return errType.INVALID_PARAM
    }

    if tgtVoutMv < vBase {
        if offset < -127 + int8((vBase - tgtVoutMv) * step) {
            offset = -127
        } else {
            offset = offset - int8((vBase - tgtVoutMv) * step)
        }
    } else if tgtVoutMv > vBase {
        if offset  > 127 - int8((tgtVoutMv - vBase) * step) {
            offset = 127
        } else {
            offset = offset + int8((tgtVoutMv - vBase) * step)
        }
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    err = smbus.WriteByte(devName, REG_LOCK_REG, 0x0)
    if err != errType.SUCCESS {
        return
    }
    err = smbus.WriteByte(devName, REG_LOCK_REG, 0x95)
    if err != errType.SUCCESS {
        return
    }
    err = smbus.WriteByte(devName, REG_LOCK_REG, 0x64)
    if err != errType.SUCCESS {
        return
    }

    //cli.Printf("i", "new offset: %d(0x%x)\n", offset, offset)
    err = smbus.WriteByte(devName, marginReg, byte(offset))
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    } else {
        cli.Println("i", "New vmargin enabled")
    }
    //data, err = smbus.ReadByte(devName, marginReg)
    //cli.Printf("i", "read offset: %d(0x%x)\n", data, data)

    // if (marginReg == SWA_OFFSET_REG) {
    //     err = smbus.WriteByte(devName, SWB_MARGIN_REG, byte(voutSetting))
    //     if err != errType.SUCCESS {
    //         cli.Println("e", "VMargin failed!")
    //         return
    //     } else {
    //         cli.Println("i", "New vmargin enabled")
    //     }
    // }
    misc.SleepInSec(1)
    return
}
*/

func SetVMargin(devName string, pct int) (err int) {
    var vBase int
    var tgtVoutMv int

    //if (pct > 10) || (pct < -10) {
    //    return errType.INVALID_PARAM
    //}

    if devName == "DDR_VDD" || devName == "DDR_VDD_0" || devName == "DDR_VDD_1" {
        vBase = 1100
    } else if devName == "DDR_VDDQ" || devName == "DDR_VDDQ_0" || devName == "DDR_VDDQ_1" {
        vBase = 1100
    } else {
        vBase = 1800
    }
    tgtVoutMv = vBase * (100 + pct) / 100
    err = SetVMarginByValue(devName, uint64(tgtVoutMv))

    return

/*
    var data byte
    var adc_sel uint8
    var vout_mv uint64
    var marginReg uint64
    var wdata byte

    if (pct > 5) || (pct < -5) {
        return errType.INVALID_PARAM
    }

    if devName == "DDR_VDD" {
        marginReg = SWA_OFFSET_REG
        adc_sel = SWA_OUTPUT_SEL
        wdata = swaMarginPct[pct]
    } else if devName == "DDR_VDDQ" {
        marginReg = SWC_OFFSET_REG
        adc_sel = SWC_OUTPUT_SEL
        wdata = swcMarginPct[pct]
    } else {
        marginReg = SWD_OFFSET_REG
        adc_sel = SWD_OUTPUT_SEL
        wdata = swdMarginPct[pct]
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    err = smbus.WriteByte(devName, REG_LOCK_REG, 0x0)
    if err != errType.SUCCESS {
        return
    }
    err = smbus.WriteByte(devName, REG_LOCK_REG, 0x95)
    if err != errType.SUCCESS {
        return
    }
    err = smbus.WriteByte(devName, REG_LOCK_REG, 0x64)
    if err != errType.SUCCESS {
        return
    }
    //set
    err = smbus.WriteByte(devName, marginReg, byte(wdata))
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    }
    misc.SleepInSec(1)
    //read
    data, err = ReadAdcOutput(devName, adc_sel)

    vout_mv = 15 * uint64(data)
    cli.Printf("i", "write: 0x%02x(%d), read vout: %d mV\n", wdata, int8(wdata), vout_mv)

    return
*/
}

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "VINBULK", "VINMGMT", "VOUTBIAS", "TEMP", "STATUS"}
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

    dig, frac, _ := CalcPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVinBulk(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVinMgmt(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVoutBias(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    if devName == "DDR_VDD" || devName == "DDR_VDDQ" || devName == "DDR_VPP" {
        dig_signed, _, _ := ReadTempTI(devName)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig_signed, 0)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    } else {
        tempStr, _ := ReadTemp(devName)
        outStr = outStr + fmt.Sprintf(fmtStr, tempStr)
    }

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) + "\n"

    cli.Println("i", outStr)
    vid, _ := ReadVendorID(devName)
    cli.Printf("i", "vid: 0x%04x\n", vid)
    return
}
