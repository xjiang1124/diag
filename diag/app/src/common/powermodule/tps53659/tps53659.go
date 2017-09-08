// Go compiler wants a .go file in package

package tps53659

import (
    //"fmt"
    "math"

    "common/errType"
    "common/misc"
    "common/pmbCmd"
    "hardware/tps53659Reg"
)

/*
    Calculate voltage output from vid value
    Formula comes from TPS53659 data sheet
 */
func calcVoltFromVid (vid byte, dacStep uint32) (integer uint32, dec uint32, err int) {
    var volt uint32
    var base uint32
    err = errType.Success

    if vid == 0 {
        return 0, 0, err
    }

    if (dacStep != 5 && dacStep != 10) {
        return 0, 0, errType.Invalidparam
    }

    if dacStep == 5 {
        base = 250
    } else {
        base = 500
    }

    volt = (uint32(vid) - 1) * dacStep + base

    return volt/1000, volt%1000, errType.Success
}

/*
    tps53659 has many register using EXP format.
    16-bit value, 
    upper 5 bits: Linear two's complement format exponent.
    lower 11 bits: Linear two's complement format mantissa.
 */
func getExpOutput(input uint16) (integer uint32, dec uint32, err int) {
    var expUint uint32
    var expInt int
    var expFloat float64
    var manFloat float64
    var expOutFloat float64

    expUint = uint32(input >> 11)
    manFloat = float64(input & 0x7FF)

    expInt, err = misc.TwoCmplBits(expUint, 5)
    if err != errType.Success {
        return 0, 0, err
    }

    expFloat = float64(expInt)
    expOutFloat = math.Pow(2, expFloat) * manFloat
    intpart, div := math.Modf(expOutFloat)

    integer = uint32(intpart)
    dec = uint32(div*1000)

    return integer, dec, errType.Success
}


func ReadVout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    var data uint32
    var dacStepRegVal uint32
    var dacStep uint32

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    pmbCmd.ReadByte(i2cIdx, devAddr, tps53659Reg.READ_VOUT, &data)

    pmbCmd.ReadByte(i2cIdx, devAddr, tps53659Reg.VOUT_MODE, &dacStepRegVal)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return integer, dec, errType.Success
}

func ReadIout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    var data uint32

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    // Write phase register: all phases
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PHASE, 0x80)

    pmbCmd.ReadWord(i2cIdx, devAddr, tps53659Reg.READ_IOUT, &data)

    // Only lower 16-bit
    data = data & 0xFFFF
    integer, dec, err = getExpOutput(uint16(data))
    return
}

func ReadIoutPhase(i2cIdx uint32, devAddr uint32, channel uint32, phase uint32) (integer uint32, dec uint32, err int) {
    var data uint32

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    // Write phase register: all phases
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PHASE, phase)

    pmbCmd.ReadWord(i2cIdx, devAddr, tps53659Reg.READ_IOUT, &data)

    // Only lower 16-bit
    data = data & 0xFFFF
    integer, dec, err = getExpOutput(uint16(data))
    return
}

/*
    Read register with EXP format and calculate output
 */
func ReadRegExp(i2cIdx uint32, devAddr uint32, channel uint32, addrAddr uint32) (integer uint32, dec uint32, err int) {
    var data uint32

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    pmbCmd.ReadWord(i2cIdx, devAddr, addrAddr, &data)

    // Only lower 16-bit
    data = data & 0xFFFF
    integer, dec, err = getExpOutput(uint16(data))

    return
}

func ReadVin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_VIN)
    return
}

func ReadIin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_IIN)
    return
}

func ReadTemp(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_TEMPERATURE_1)
    return
}

func ReadPout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_POUT)
    return
}

func ReadPin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_PIN)
    return
}

func ReadVoutLn(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.MFR_SPECIFIC_04)
    return
}

