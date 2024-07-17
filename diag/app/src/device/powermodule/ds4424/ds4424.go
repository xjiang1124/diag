package ds4424

import (
    "common/dcli"
    "common/errType"
    "protocol/smbus"
    "hardware/i2cinfo"
)

func SetVMargin(devName string, pct int) (err int) {
    var channel byte
    var pctBin byte
    var data byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    // page variable is used to store the channel # for this component, not actual page in memory
    channel, err = i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        dcli.Printf("e", "No channel (page) defined for %s", devName)
        return
    }

    if (pct > 20 || pct < -20) {
        dcli.Println("e", "Margin percentage cannot be more than +/-20%% for this device")
        err = errType.FAIL
        return
    }

    pctScaled := pct * (int)(VOUT_SCALE_MAX)
    pctScaled = pctScaled / PCT_SCALE_MAX
    // add sign bit
    if pct < 0 {
        pctScaled = pctScaled * -1
        pctBin = (byte)(pctScaled) | (MARGIN_SET_MASK & MARGIN_LOW_SET)
    } else {
        pctBin = (byte)(pctScaled) | MARGIN_SET_MASK & MARGIN_HIGH_SET
    }

    err = smbus.WriteByte(devName, voutChSelect[channel], pctBin)
    if err != errType.SUCCESS {
        dcli.Printf("e", "Failed to write %s margin setting", devName)
        return
    }

    // read back to verify
    data, err = smbus.ReadByte(devName, voutChSelect[channel])
    if err != errType.SUCCESS {
        dcli.Printf("e", "Failed to read back %s margin setting", devName)
        return
    }
    if data != (pctBin) {
        dcli.Printf("e", "Data mismatch; register %x expected %x, got %x", voutChSelect[channel], pctBin, data)
        err = errType.FAIL
        return
    }
    return
}