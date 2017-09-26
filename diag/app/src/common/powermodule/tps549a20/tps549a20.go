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

func (tps549a20 *TPS549A20) ReadStatus(devName string, channel byte) (status uint16, err int) {
    status, err = pmbCmd.ReadWord(devName, tps549a20Reg.STATUS_WORD)
    return
}


func (tps549a20 *TPS549A20) ReadVout(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return integer, dec, errType.SUCCESS
}

func (tps549a20 *TPS549A20) ReadVboot(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return integer, dec, errType.SUCCESS
}
func (tps549a20 *TPS549A20) ReadIout(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadVin(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadIin(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadTemp(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadPout(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadPin(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return
}

func (tps549a20 *TPS549A20) ReadVoutLn(devName string, channel byte) (integer uint64, dec uint64, err int) {
    return
}

func (tps549a20 *TPS549A20) SetVMargin(devName string, channel byte, pct int) (err int) {
    var marginCmd byte
    var marginVal byte

    if pct > 12 || pct < -12 {
        return errType.INVALID_PARAM
    }

    if pct == 0 {
        marginCmd = tps549a20Reg.MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = tps549a20Reg.MARGIN_HIGH_CMD
        marginVal = byte(pct) << 4
    } else {
        marginCmd = tps549a20Reg.MARGIN_LOW_CMD
        marginVal = byte(-pct)
    }

    pmbCmd.WriteByte(devName, tps549a20Reg.VOUT_MARGIN, marginVal)
    pmbCmd.WriteByte(devName, tps549a20Reg.OPERATION, marginCmd)

    return

}

