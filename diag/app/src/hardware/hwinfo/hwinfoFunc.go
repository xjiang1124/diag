package hwinfo

import (
    "common/cli"
    "common/errType"
    "device/i2chub/tca9546a"
    "hardware/i2cinfo"
)

/**
 * To support NAPlES_MTP test card
 * Todo: support mix of Naples on the same MTP
 */
func SwitchHwInfo(uutName string) (err int) {
    if uutName == "UUT_NONE" {
        DispStaList   = dispMap[cardName]
        PmbusTestList = pmbusTestMap[cardName]
        EepromList    = eepromMap[cardName]
    } else {
        DispStaList   = dispMap[uutName]
        PmbusTestList = pmbusTestMap[uutName]
        EepromList    = eepromMap[uutName]
        I2cHubList    = eepromMap[uutName]
    }
    return
}

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
    for _, hubName := range I2cHubList {
        err = tca9546a.DisableAllChan(hubName)
        if err != errType.SUCCESS {
            cli.Println("d", "Failed: ", err)
            return
        }
    }

    i2cInfo, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed: ", err)
        return
    }

    if i2cInfo.HubName != "HUB_NONE" {
        err = tca9546a.EnableChan(i2cInfo.HubName, i2cInfo.HubPort)
    }
    return
}

/**
 * Exclusively enable hub channel specified
 * All other Channels will be disabled
 */
func EnableHubChannelUut(uutName string) (err int) {
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

    hubInfo, ok := I2cHubMap[uutName]
    if ok != true {
        cli.Println("d", "Failed: ", err)
        err = errType.INVALID_PARAM
        return
    }
    err = tca9546a.EnableChan(hubInfo.hubName, hubInfo.channel)
    return
}

