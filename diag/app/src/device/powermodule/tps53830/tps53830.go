package tps53830

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
    data, err = smbus.ReadByte(devName, ADC_CTL_REG)
    if err != errType.SUCCESS {
        return
    }
    data &= ^adc_sel
    err = smbus.WriteByte(devName, ADC_CTL_REG, data | ADC_ENABLE | adc_sel)
    if err != errType.SUCCESS {
        return
    }
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

    if devName == "DDR_VDD" {
        adc_sel = SWA_OUTPUT_SEL
    } else if devName == "DDR_VDDQ" {
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

    data1, err = smbus.ReadByte(devName, OUTPUT_SELECT_REG)
    if err != errType.SUCCESS {
        return
    }
    data1 &= ADC_CURRENT_SEL
    err = smbus.WriteByte(devName, ADC_CTL_REG, data1)
    if err != errType.SUCCESS {
        return
    }

    if devName == "DDR_VDD" {
        output_reg = SWA_OUTPUT_SEL
    } else if devName == "DDR_VDDQ" {
        output_reg = SWC_OUTPUT_SEL
    } else {
        output_reg = SWD_OUTPUT_SEL
    }

    data1, err = smbus.ReadByte(devName, output_reg)
    if err != errType.SUCCESS {
        return
    }
    if (output_reg == SWA_OUTPUT_SEL) {
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

func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    var data1, data2 byte
    var pout uint64
    var output_reg uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data1, err = smbus.ReadByte(devName, OUTPUT_SELECT_REG)
    if err != errType.SUCCESS {
        return
    }
    data1 |= ADC_POWER_SEL
    err = smbus.WriteByte(devName, ADC_CTL_REG, data1)
    if err != errType.SUCCESS {
        return
    }
    if devName == "DDR_VDD" {
        output_reg = SWA_OUTPUT_SEL
    } else if devName == "DDR_VDDQ" {
        output_reg = SWC_OUTPUT_SEL
    } else {
        output_reg = SWD_OUTPUT_SEL
    }

    data1, err = smbus.ReadByte(devName, output_reg)
    if err != errType.SUCCESS {
        return
    }
    if (output_reg == SWA_OUTPUT_SEL) {
        data2, err = smbus.ReadByte(devName, output_reg + 1) //read SWB_OUTPUT
        if err != errType.SUCCESS {
            return
        }
    } else {
        data2 = 0
    }

    pout = 125 * uint64(data1 + data2)
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

func ReadVinBias(devName string) (integer uint64, dec uint64, err int) {
    var data byte
    var vout_mv uint64

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = ReadAdcOutput(devName, VIN_BIAS_SEL)

    vout_mv = 25 * uint64(data)
    integer = vout_mv / 1000
    dec = vout_mv % 1000

    return integer, dec, errType.SUCCESS
}

func ReadTemp(devName string) (integer int64, dec uint64, err int) {
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

func ReadVendorID(devName string) (devID byte, err int) {
    var vendorId byte
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    vendorId, err = smbus.ReadByte(devName, VENDOR_ID)
    return vendorId, err
}

func SetVMarginByValue(devName string, tgtVoutMv uint64) (err int) {
    var marginReg uint64
    var vmin, vmax uint64
    var voutSetting uint64

    if devName == "DDR_VDD" {
        marginReg = SWA_MARGIN_REG
        vmin = VOUT_1P1_MIN
        vmax = VOUT_1P1_MAX
    } else if devName == "DDR_VDDQ" {
        marginReg = SWC_MARGIN_REG
        vmin = VOUT_1P1_MIN
        vmax = VOUT_1P1_MAX
    } else {
        marginReg = SWD_MARGIN_REG
        vmin = VOUT_1P8_MIN
        vmax = VOUT_1P8_MAX
    }

    tgtVoutMv = uint64(math.Round(float64(tgtVoutMv) / 5)) * 5
    if (tgtVoutMv < vmin || tgtVoutMv > vmax) {
        return errType.INVALID_PARAM
    }
    voutSetting = ((tgtVoutMv - 800) / 5) << 1

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    err = smbus.WriteByte(devName, SECURE_MODE_REG, PROGRAMMABLE_MODE)
    if err != errType.SUCCESS {
        return
    }
    err = smbus.WriteByte(devName, marginReg, byte(voutSetting))
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    } else {
        cli.Println("i", "New vmargin enabled")
    }
    if (marginReg == SWA_MARGIN_REG) {
        err = smbus.WriteByte(devName, SWB_MARGIN_REG, byte(voutSetting))
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

func SetVMargin(devName string, pct int) (err int) {
    var vBase int
    var tgtVoutMv int

    if (pct > 10) || (pct < -10) {
        return errType.INVALID_PARAM
    }

    if devName == "DDR_VDD" {
        vBase = 1100
    } else if devName == "DDR_VDDQ" {
        vBase = 1100
    } else {
        vBase = 1800
    }
    tgtVoutMv = vBase * (100 + pct) / 100
    err = SetVMarginByValue(devName, uint64(tgtVoutMv))

    return
}


func DispStatus(devName string) (err int) {
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "VINBUIK", "VINMGMT", "VINBIAS", "TEMP", "STATUS"}
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

    dig, frac, _ := ReadPout(devName)
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

    dig, frac, _ = ReadVinBias(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig_signed, _, _ := ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig_signed, 0)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) + "\n"

    cli.Println("i", outStr)

    return
}
