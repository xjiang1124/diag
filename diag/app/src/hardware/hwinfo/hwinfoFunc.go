package hwinfo

import (
    "common/errType"
    "device/i2chub/tca9546a"
)

func SelectHubChannel(devName string) (err int) {
    // for MTP only for now
    if cardName != "MTP" {
        return
    }

    i2chubInfo, ok := I2cHubMap[devName]
    if ok != true {
        err = errType.INVALID_PARAM
        return
    }

    err = tca9546a.EnableChan(i2chubInfo.hubName, i2chubInfo.channel)
    return
}

