package hwdev

import (
    "sort"

    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "device/powermodule/tps53659"
    //"device/powermodule/tps549a20"
    //"device/fanctrl/adt7462"
)

func DevInfo(devName string) {
    for _, i2cInfo := range(i2cinfo.CurI2cTbl) {
        if devName != i2cInfo.Name {
            continue
        }
        if i2cInfo.Comp == "TPS53659" {
            tps53659.Info(devName)
            return
        }
    }
    cli.Println("e", "Unsupported device: ", devName)
}

func DispStatus(devName string, uutName string) (err int){
    if uutName == "UUT_NONE" {
        err = dispStatus(devName)
    } else {
        err = dispStatusUut(devName, uutName)
    }
    return
}

func dispStatus(devName string) (err int){
    if devName == "ALL" {
        // golang range(map) sequence is random
        // Sorted output
        keys := make([]string, 0)
        for k, _ := range(hwinfo.DispStaList) {
            keys = append(keys, k)
        }
        sort.Strings(keys)
        for _, dev := range(keys) {
            dispFunc := hwinfo.DispStaList[dev]
            hwinfo.EnableHubChannelExclusive(dev)
            dispFunc(dev)
        }
    } else {
        hwinfo.EnableHubChannelExclusive(devName)
        dispFunc, ok := hwinfo.DispStaList[devName]
        if ok == false {
            cli.Println("f", "Invalde device: ", devName)
            err = errType.INVALID_PARAM
            return
        }
        dispFunc(devName)
    }
    return
}

func dispStatusUut(devName string, uutName string) (err int){
    if devName == "ALL" {
        cli.Println("e", "\"ALL\" does not support by UUT!")
        err = errType.INVALID_PARAM
        return
    }

    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    hwinfo.SwitchHwInfo(uutName)
    i2cinfo.SwitchI2cTbl(uutName)
    dispFunc, ok := hwinfo.DispStaList[devName]
    if ok == false {
        cli.Println("f", "Invalde device: ", devName)
        err = errType.INVALID_PARAM
        return
    }
    dispFunc(devName)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    hwinfo.SwitchHwInfo("UUT_NONE")

    return
}
