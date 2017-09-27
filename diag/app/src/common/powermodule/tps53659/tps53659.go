package tps53659

import (
    //"fmt"
    "math"

    "common/dmutex"
    "common/errType"
    "common/misc"
    "common/pmbCmd"
    "hardware/tps53659Reg"
)

type TPS53659 struct {
    numPhases int
}

const (
    DEVICE_ID = 0x59
)

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
        if volt < tgtVoltMv && voltNext > tgtVoltMv {
            return byte(vidStep), err
        }
    }
    return 0, errType.FAIL
}

/*
    tps53659 has many register using EXP format.
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

func (tps53659 *TPS53659) ReadStatus(devName string, channel byte) (status uint16, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    // Write page register
    pmbCmd.WriteByte(devName, tps53659Reg.PAGE, channel)

    status, err = pmbCmd.ReadWord(devName, tps53659Reg.STATUS_WORD)

    return
}


func (tps53659 *TPS53659) ReadVout(devName string, channel byte) (integer uint64, dec uint64, err int) {
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    // Write page register
    pmbCmd.WriteByte(devName, tps53659Reg.PAGE, channel)

    data, err = pmbCmd.ReadWord(devName, tps53659Reg.READ_VOUT)

    dacStepRegVal, err = pmbCmd.ReadByte(devName, tps53659Reg.VOUT_MODE)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return integer, dec, errType.SUCCESS
}

func (tps53659 *TPS53659) ReadVboot(devName string, channel byte) (integer uint64, dec uint64, err int) {
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    // Write page register
    pmbCmd.WriteByte(devName, tps53659Reg.PAGE, channel)

    // Read Vboot
    data, err = pmbCmd.ReadWord(devName, tps53659Reg.MFR_SPECIFIC_11)

    dacStepRegVal, err = pmbCmd.ReadByte(devName, tps53659Reg.VOUT_MODE)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return integer, dec, errType.SUCCESS
}

func (tps53659 *TPS53659) ReadIout(devName string, channel byte) (integer uint64, dec uint64, err int) {
    var data uint16

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    // Write page register
    pmbCmd.WriteByte(devName, tps53659Reg.PAGE, channel)

    // Write phase register: all phases
    pmbCmd.WriteByte(devName, tps53659Reg.PHASE, 0x80)

    data, err = pmbCmd.ReadWord(devName, tps53659Reg.READ_IOUT)
    integer, dec, err = getExpOutput(data)
    return
}

func (tps53659 *TPS53659) ReadIoutPhase(devName string, channel byte, phase byte) (integer uint64, dec uint64, err int) {
    var data uint16

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    // Write page register
    pmbCmd.WriteByte(devName, tps53659Reg.PAGE, channel)

    // Write phase register: all phases
    pmbCmd.WriteByte(devName, tps53659Reg.PHASE, phase)

    data, err = pmbCmd.ReadWord(devName, tps53659Reg.READ_IOUT)
    integer, dec, err = getExpOutput(data)
    return
}

/*
    Read register with EXP format and calculate output
 */
func (tps53659 *TPS53659) ReadRegExp(devName string, channel byte, addrAddr uint64) (integer uint64, dec uint64, err int) {
    var data uint16

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    // Write page register
    pmbCmd.WriteByte(devName, tps53659Reg.PAGE, channel)

    data, err = pmbCmd.ReadWord(devName, addrAddr)
    integer, dec, err = getExpOutput(data)

    return
}

func (tps53659 *TPS53659) ReadVin(devName string, channel byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, channel, tps53659Reg.READ_VIN)
    return
}

func (tps53659 *TPS53659) ReadIin(devName string, channel byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, channel, tps53659Reg.READ_IIN)
    return
}

func (tps53659 *TPS53659) ReadTemp(devName string, channel byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, channel, tps53659Reg.READ_TEMPERATURE_1)
    return
}

func (tps53659 *TPS53659) ReadPout(devName string, channel byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, channel, tps53659Reg.READ_POUT)
    return
}

func (tps53659 *TPS53659) ReadPin(devName string, channel byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, channel, tps53659Reg.READ_PIN)
    return
}

func (tps53659 *TPS53659) ReadVoutLn(devName string, channel byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = tps53659.ReadRegExp(devName, channel, tps53659Reg.MFR_SPECIFIC_04)
    return
}

func (tps53659 *TPS53659) ReadDeviceID(devName string) (devID byte, err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

    devID, err = pmbCmd.ReadByte(devName, tps53659Reg.IC_DEVICE_ID)
    return devID, err
}

func (tps53659 *TPS53659) SetVMargin(devName string, channel byte, pct int) (err int) {
    var marginReg uint64
    var marginCmd byte
    var data uint16
    var dacStepRegVal byte
    var dacStep uint64

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(devName)

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
    pmbCmd.WriteByte(devName, tps53659Reg.PAGE, channel)

    dacStepRegVal, err = pmbCmd.ReadByte(devName, tps53659Reg.VOUT_MODE)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    data, err = pmbCmd.ReadWord(devName, tps53659Reg.VOUT_COMMAND)

    integer, dec, _ := calcVoltFromVid(byte(data), dacStep)
    voltMv := integer *1000 + dec
    voltMvTemp := voltMv * uint64(100+pct)
    voltMvTgt := voltMvTemp / 100

    // Update VOUT_MARGIN_HIGH/HOW with target VID
    vidTgt, _ := calcVidFromVolt(voltMvTgt, dacStep)
    pmbCmd.WriteWord(devName, marginReg, uint16(vidTgt))

    // Set to PMBus control
    pmbCmd.WriteByte(devName, tps53659Reg.MFR_SPECIFIC_02, tps53659Reg.CTRL_PMBUS)

    // Enable Vmargin
    pmbCmd.WriteByte(devName, tps53659Reg.OPERATION, marginCmd)

    return

}

