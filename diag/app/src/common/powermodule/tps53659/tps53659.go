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

type TPS53659 struct {
    numPhases int
}


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
    Calculate vid from given voltage (in mv unit)
 */
func calcVidFromVolt (tgtVoltMv uint32, dacStep uint32) (vid byte, err int) {
    var volt uint32
    var voltNext uint32
    var base uint32
    var vidMax uint32
    var vidStep uint32

    err = errType.Success

    if tgtVoltMv == 0 {
        return 0, err
    }

    if (dacStep != 5 && dacStep != 10) {
        return 0, errType.Invalidparam
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
        if volt < tgtVoltMv && voltNext > tgtVoltMv {
            return byte(vidStep), err
        }
    }
    return 0, errType.Fail
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


func (tps53659 *TPS53659) ReadVout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    var data uint32
    var dacStepRegVal uint32
    var dacStep uint32

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    pmbCmd.ReadWord(i2cIdx, devAddr, tps53659Reg.READ_VOUT, &data)

    pmbCmd.ReadByte(i2cIdx, devAddr, tps53659Reg.VOUT_MODE, &dacStepRegVal)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return integer, dec, errType.Success
}

func (tps53659 *TPS53659) ReadIout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
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

func (tps53659 *TPS53659) ReadIoutPhase(i2cIdx uint32, devAddr uint32, channel uint32, phase uint32) (integer uint32, dec uint32, err int) {
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
func (tps53659 *TPS53659) ReadRegExp(i2cIdx uint32, devAddr uint32, channel uint32, addrAddr uint32) (integer uint32, dec uint32, err int) {
    var data uint32

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    pmbCmd.ReadWord(i2cIdx, devAddr, addrAddr, &data)

    // Only lower 16-bit
    data = data & 0xFFFF
    integer, dec, err = getExpOutput(uint16(data))

    return
}

func (tps53659 *TPS53659) ReadVin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = tps53659.ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_VIN)
    return
}

func (tps53659 *TPS53659) ReadIin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = tps53659.ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_IIN)
    return
}

func (tps53659 *TPS53659) ReadTemp(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = tps53659.ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_TEMPERATURE_1)
    return
}

func (tps53659 *TPS53659) ReadPout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = tps53659.ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_POUT)
    return
}

func (tps53659 *TPS53659) ReadPin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = tps53659.ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.READ_PIN)
    return
}

func (tps53659 *TPS53659) ReadVoutLn(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    integer, dec, err = tps53659.ReadRegExp(i2cIdx, devAddr, channel, tps53659Reg.MFR_SPECIFIC_04)
    return
}

const (
    MARGIN_NONE = 0
    MARGIN_HIGH = 1
    MARGIN_LOW  = 2

    MARGIN_NONE_CMD = 0x80
    MARGIN_HIGH_CMD = 0xA4
    MARGIN_LOW_CMD  = 0x94

    CTRL_SVID  = 0x2
    CTRL_PMBUS = 0x1
)


func (tps53659 *TPS53659) SetVMargin(i2cIdx uint32, devAddr uint32, channel uint32, pct int) (err int) {
    var marginReg uint32
    var marginCmd uint32
    var data uint32
    var dacStepRegVal uint32
    var dacStep uint32

    if pct == 0 {
        marginCmd = MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = MARGIN_HIGH_CMD
        marginReg = tps53659Reg.VOUT_MARGIN_HIGH
    } else {
        marginCmd = MARGIN_LOW_CMD
        marginReg = tps53659Reg.VOUT_MARGIN_LOW
    }

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    pmbCmd.ReadByte(i2cIdx, devAddr, tps53659Reg.VOUT_MODE, &dacStepRegVal)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    pmbCmd.ReadWord(i2cIdx, devAddr, tps53659Reg.VOUT_COMMAND, &data)

    integer, dec, _ := calcVoltFromVid(byte(data), dacStep)
    voltMv := integer *1000 + dec
    voltMvTemp := voltMv * uint32(100+pct)
    voltMvTgt := voltMvTemp / 100

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(voltMvTgt, dacStep)
    pmbCmd.WriteWord(i2cIdx, devAddr, marginReg, uint32(vidTgt))

    // Set to PMBus control
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.MFR_SPECIFIC_02, CTRL_PMBUS)

    // Enable Vmargin
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.OPERATION, marginCmd)

    return

}

