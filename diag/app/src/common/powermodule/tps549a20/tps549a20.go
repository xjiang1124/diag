// Go compiler wants a .go file in package

package tps549a20

import (
    "fmt"

    "common/cli"
    "common/errType"
    "common/pmbCmd"
    "hardware/tps549a20Reg"
)

type TPS549A20 struct {
}

func (tps549a20 *TPS549A20) ReadStatus(devName string) (status uint16, err int) {
    status, err = pmbCmd.ReadWord(devName, tps549a20Reg.STATUS_WORD)
    return
}

func (tps549a20 *TPS549A20) DispStatus(devName string) (err int) {
    vrmTitle := []string {"STATUS"}
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

    status, err := tps549a20.ReadStatus(devName)
    if err != errType.SUCCESS {
        return err
    }

    outStr = fmt.Sprintf(fmtNameStr, devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    cli.Println("i", outStr)

    return

}

func (tps549a20 *TPS549A20) SetVMargin(devName string, pct int) (err int) {
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

