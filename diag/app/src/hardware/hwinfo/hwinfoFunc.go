package hwinfo

import (
    "common/cli"
    "common/errType"
    "device/i2chub/tca9546a"
)

func EnableHubChannel(devName string) (err int) {
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

/**
 * Exclusively enable hub channel specified
 * All other Channels will be disabled
 */
func EnableHubChannelExclusive(devName string) (err int) {
    // for MTP only for now
    if cardName != "MTP" {
        return
    }

    for _, hubName := range I2cHubList {
        err = tca9546a.DisableAllChan(hubName)
        if err != errType.SUCCESS {
            cli.Println("d", "Failed: ", err)
            return
        }
    }

    i2chubInfo, ok := I2cHubMap[devName]
    if ok != true {
        cli.Println("d", "Failed: ", err)
        err = errType.INVALID_PARAM
        return
    }

    err = tca9546a.EnableChan(i2chubInfo.hubName, i2chubInfo.channel)
    return
}

