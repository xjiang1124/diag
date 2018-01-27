package tca9546a

import (
    "common/errType"

    "protocol/smbus"
)

const (
)

/*
    Enble single channel 0-3
    All other channels will be disabled
 */
func EnableChan(devName string, channel byte) (err int) {
    var data byte

    if channel > 3 {
        err = errType.INVALID_PARAM
        return
    }

    data = 1 << channel
    err = smbus.SendByte(devName, data)
    return
}

/*
    Disable all channels
 */
func DisableAllChan(devName string) (err int) {
    err = smbus.SendByte(devName, 0)
    return
}

/*
    Read channel enable/disable info
 */
func ReadStatus(devName string) (data byte, err int) {
    data, err = smbus.ReceiveByte(devName)
    return
}

