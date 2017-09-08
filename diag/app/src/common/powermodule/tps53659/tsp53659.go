// Go compiler wants a .go file in package

package tps53659

import (
    "fmt"

    "common/errType"
    "common/pmbCmd"
    "hardware/tps53659Reg"
)

/*
    Calculate voltage output from vid value
 */
func calcVoltFromVid (vid byte, dacStep uint32) (integer uint32, dec uint32, err uint32) {
    var volt uint32
    var base uint32

    if vid == 0 {
        return 0, 0, errType.Success
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

func ReadVout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32) {
    var data uint32
    var dacStepRegVal uint32
    var dacStep uint32

    // Write page register
    pmbCmd.WriteByte(i2cIdx, devAddr, tps53659Reg.PAGE, channel)

    pmbCmd.ReadByte(i2cIdx, devAddr, tps53659Reg.READ_VOUT, &data)
    fmt.Println(data)

    pmbCmd.ReadByte(i2cIdx, devAddr, tps53659Reg.VOUT_MODE, &dacStepRegVal)
    fmt.Println(dacStepRegVal)

    if dacStepRegVal == tps53659Reg.DAC_STEP_5MV {
        dacStep = 5
    } else {
        dacStep = 10
    }

    integer, dec, _ = calcVoltFromVid(byte(data), dacStep)

    return
}
