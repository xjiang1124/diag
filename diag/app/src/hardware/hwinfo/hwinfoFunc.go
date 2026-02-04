package hwinfo

import (
    "os"
    "strconv"

    "common/cli"
    "common/dmutex"
    "common/errType"
    "device/i2chub/tca9546a"
    "device/fpga/taorfpga"
    "device/fpga/liparifpga"
    "hardware/i2cinfo"
)

/**
 * To support NAPlES_MTP test card
 * Todo: support mix of Naples on the same MTP
 */
func SwitchHwInfo(uutName string) (err int) {
    var uutType string
    if uutName == "UUT_NONE" || uutName == "UUT_BLIND" {
        DispStaList   = dispMap[cardType]
        PmbusTestList = pmbusTestMap[cardType]
        EepromList    = eepromMap[cardType]
        I2cHubList    = i2cHubListMap[cardType]
    } else {
        uutType, err = i2cinfo.FindUutTypeMtp(uutName)
        if err != errType.SUCCESS {
            return
        }

        DispStaList   = dispMap[uutType]
        PmbusTestList = pmbusTestMap[uutType]
        EepromList    = eepromMap[uutType]
        I2cHubList    = i2cHubListMap[uutType]
    }
    return
}

/**
 * Find UUT I2C root device
 */
func FindUutI2cDev(uutName string) (i2cDevIdx int, err int) {
    // This function is only useful on MTP
    cardType, found := os.LookupEnv("CARD_TYPE")
    if found == false {
        cli.Println("e", "Cannot find CARD_TYPE")
        err = errType.INVALID_PARAM
        return
    }

    if (cardType != "MTP" && cardType != "MTPS" && cardType != "MTP_MATERA" && cardType != "MTP_PANAREA" && cardType != "MTP_PONZA") {
        err = errType.INVALID_PARAM
        return
    }

    cardType = i2cinfo.CardType
    hubMap, ok := i2cHubMap[cardType]
    if ok != true {
        cli.Println("e", "Invalid card name:", cardType)
        err = errType.INVALID_PARAM
        return
    }

    hubInfo, ok := hubMap[uutName]
    if ok != true {
        if uutName != "UUT_NONE" {
            cli.Println("e", "Invalid UUT name:", uutName)
        }
        err = errType.INVALID_PARAM
        return
    }

    hubI2cInfo, err := i2cinfo.GetI2cInfo(hubInfo.hubName)
    if err != errType.SUCCESS {
        return
    }
    i2cDevIdx = int(hubI2cInfo.Bus)
    return
}

func EnableHubChannel(devName string) (err int) {

    if cardType == "TAORMINA" {
        var i2cInfo i2cinfo.I2cInfo
        i2cInfo, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed: ", err)
            return
        }
        //On taormina, /dev/ic2-# starts at 1 instead of 0. 
        //So first bus is 1.  On the fpga it's zero based so 
        //we subtract 1 below from the bus number to make it zero based
        taorfpga.SetI2Cmux((i2cInfo.Bus - 1), uint32(i2cInfo.HubPort))
        return
    }
    if cardType == "LIPARI" || cardType == "MTP_MATERA" || cardType == "MTP_PANAREA" || cardType == "MTP_PONZA" {
        var i2cInfo i2cinfo.I2cInfo
        i2cInfo, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed: ", err)
            return
        }
        liparifpga.SetI2Cmux((i2cInfo.Bus), uint32(i2cInfo.HubPort))
        return
    }

    // for MTP only for now
    if cardType != "MTP" {
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

    if cardType == "TAORMINA" {
        var i2cInfo i2cinfo.I2cInfo
        i2cInfo, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed: ", err)
            return
        }
        //On taormina, /dev/ic2-# starts at 1 instead of 0 (1-17). 
        //So first bus is 1.  On the fpga the bus is zero based (0-16) 
        //we subtract 1 below from the bus number to make it zero based to match the fpga
        taorfpga.SetI2Cmux((i2cInfo.Bus - 1), uint32(i2cInfo.HubPort))
        return
    }
    if cardType == "LIPARI" {
        var i2cInfo i2cinfo.I2cInfo
        i2cInfo, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed: ", err)
            return
        }
        liparifpga.SetI2Cmux((i2cInfo.Bus), uint32(i2cInfo.HubPort))
        return
    }

    i2cInfo, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed: ", err)
        return
    }

    if i2cInfo.HubName == "HUB_NONE" {
        // Device is not under any hub
        return
    }

    for _, hubName := range I2cHubList {
        if hubName == "HUB_NONE" {
            continue
        }
        err = tca9546a.DisableAllChan(hubName)
        if err != errType.SUCCESS {
            cli.Println("e", " tca9546a.DisableAllChan Failed: ", err)
            return
        }
    }

    err = tca9546a.EnableChan(i2cInfo.HubName, i2cInfo.HubPort)
    return
}

/**
 * Exclusively enable hub channel specified
 * All other Channels will be disabled
 */
func EnableHubChannelUut(uutName string) (err int) {
    // for MTP only for now
    if cardType != "MTP" {
        cli.Println("e", "Unsupported platform!", cardType)
        err = errType.INVALID_PARAM
        return
    }

    for _, hubName := range I2cHubList {
        err = tca9546a.DisableAllChan(hubName)
        if err != errType.SUCCESS {
            cli.Println("e", " tca9546a.DisableAllChanFailed: ", err)
            return
        }
    }

    hubInfo, ok := I2cHubMap[uutName]
    if ok != true {
        cli.Println("e", " Getting hubInfo from I2cHubMap Failed: ", err)
        err = errType.INVALID_PARAM
        return
    }
    err = tca9546a.EnableChan(hubInfo.hubName, hubInfo.channel)
    return
}

/**
 * Lock I2C device
 */
func LockDev(devName string) (lockName string, i2cif i2cinfo.I2cInfo, err int) {
    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Getting I2C Info Failed: ", err)
        return
    }

    lockName = "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    return
}

/**
 * Unlock I2C device
 */
func UnlockDev(lockName string) {
    dmutex.Unlock(lockName)
}

/** 
 * Lock UUT I2C root device
 */
func PreUutSetup(uutName string) (lockName string, err int) {
    lockName = "i2c-"
    var i2cDevIdx int = 0

    //Matera does not lock dmutex, neither EnableHubChannelUut
    if cardType != "MTP_MATERA" && cardType != "MTP_PANAREA" && cardType != "MTP_PONZA" {
        i2cDevIdx, err = FindUutI2cDev(uutName)
        if err != errType.SUCCESS {
            return
        }

        lockName = "i2c-"+strconv.Itoa(i2cDevIdx)
        err = dmutex.Lock(lockName)
        if err != errType.SUCCESS {
            return
        }

        err = EnableHubChannelUut(uutName)
        if err != errType.SUCCESS {
            return
        }
    }

    err = i2cinfo.SwitchI2cTbl(uutName)
    if err != errType.SUCCESS {
        return
    }
    if cardType == "MTP_MATERA" || cardType == "MTP_PANAREA" {
        i2cinfo.UpdateNicI2cBus(uutName)
    }

    err = SwitchHwInfo(uutName)
    if err != errType.SUCCESS {
        return
    }

    return
}

/** 
 * Lock UUT I2C root device
 */
func PreUutSetupBlind(uutName string) (lockName string, err int) {
    lockName = "i2c-"
    var i2cDevIdx int = 0

    //Matera does not lock dmutex, neither EnableHubChannelUut
    if cardType != "MTP_MATERA" && cardType != "MTP_PANAREA" && cardType != "MTP_PONZA" {
        i2cDevIdx, err = FindUutI2cDev(uutName)
        if err != errType.SUCCESS {
            return
        }

        lockName = "i2c-"+strconv.Itoa(i2cDevIdx)
        err = dmutex.Lock(lockName)
        if err != errType.SUCCESS {
            return
        }

        err = EnableHubChannelUut(uutName)
        if err != errType.SUCCESS {
            return
        }
    }

    err = i2cinfo.SwitchI2cTbl("UUT_BLIND")
    if err != errType.SUCCESS {
        return
    }
    if cardType == "MTP_MATERA" || cardType == "MTP_PANAREA" || cardType == "MTP_PONZA" {
        i2cinfo.UpdateNicI2cBus(uutName)
    }

    err = SwitchHwInfo("UUT_BLIND")
    if err != errType.SUCCESS {
        return
    }

    return
}

/**
 * Unlock UUT I2C device
 */
func PostUutClean(lockName string) {
    //Matera does not lock/unlock dmutex
    if cardType != "MTP_MATERA" && cardType != "MTP_PANAREA" && cardType != "MTP_PONZA" {
        dmutex.Unlock(lockName)
    }
    SwitchHwInfo("UUT_NONE")
    i2cinfo.SwitchI2cTbl("UUT_NONE")
}

