// Go compiler wants a .go file in package

package tps549a20

import (
    //"fmt"

    "common/errType"
    "common/pmbCmd"
    "hardware/tps549a20Reg"
)

type TPS549A20 struct {
}

func (tps549a20 *TPS549A20) ReadStatus(i2cIdx uint32, devAddr uint32, channel uint32) (status uint32, err int) {
    pmbCmd.ReadWord(i2cIdx, devAddr, tps549a20Reg.STATUS_WORD, &status)
    return
}


func (tps549a20 *TPS549A20) ReadVout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return integer, dec, errType.SUCCESS
}

func (tps549a20 *TPS549A20) ReadVboot(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return integer, dec, errType.SUCCESS
}
func (tps549a20 *TPS549A20) ReadIout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadVin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadIin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadTemp(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadPout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadPin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadVoutLn(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int) {
    return
}

func (tps549a20 *TPS549A20) SetVMargin(i2cIdx uint32, devAddr uint32, channel uint32, pct int) (err int) {
    var marginCmd uint32
    var marginVal uint32

    if pct > 12 || pct < -12 {
        return errType.INVALID_PARAM
    }

    if pct == 0 {
        marginCmd = tps549a20Reg.MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = tps549a20Reg.MARGIN_HIGH_CMD
        marginVal = uint32(pct) << 4
    } else {
        marginCmd = tps549a20Reg.MARGIN_LOW_CMD
        marginVal = uint32(-pct)
    }

    pmbCmd.WriteByte(i2cIdx, devAddr, tps549a20Reg.VOUT_MARGIN, marginVal)
    pmbCmd.WriteByte(i2cIdx, devAddr, tps549a20Reg.OPERATION, marginCmd)

    return

}

