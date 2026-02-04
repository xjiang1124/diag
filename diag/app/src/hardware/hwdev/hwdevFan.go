package hwdev

import (
    "fmt"
    "strconv"
    "common/cli"
    "common/dmutex"
    "common/errType"

    "device/fanctrl/adt7462"
    "device/fpga/liparifpga"
    "device/fpga/materafpga"
    "device/fpga/panareafpga"

    "hardware/hwinfo"
    "hardware/i2cinfo"

)


func FanReadReg(devName string, addr uint32) (data byte, err int) {
    var i2cif i2cinfo.I2cInfo

    if i2cinfo.CardType == "MTP_MATERA" || i2cinfo.CardType == "MTP_PANAREA" || i2cinfo.CardType == "MTP_PONZA" {
        cli.Println("i", "Use fpgautil to read the fan registers for this platform  ")
        return
    }

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    hwinfo.EnableHubChannelExclusive(devName)
    data, err = adt7462.ReadReg(devName, addr) 
    return
}


func FanWriteReg(devName string, addr uint32, data byte) (err int) {
    var i2cif i2cinfo.I2cInfo

    if i2cinfo.CardType == "MTP_MATERA" || i2cinfo.CardType == "MTP_PANAREA" || i2cinfo.CardType == "MTP_PONZA" {
        cli.Println("i", "Use fpgautil to write the fan registers for this platform  ")
        return
    }

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    hwinfo.EnableHubChannelExclusive(devName)
    err = adt7462.WriteReg(devName, addr, data)
    return
}

func FanDumpReg(devName string) (err int) {
    var i2cif i2cinfo.I2cInfo

    if i2cinfo.CardType == "MTP_MATERA" || i2cinfo.CardType == "MTP_PANAREA" || i2cinfo.CardType == "MTP_PONZA" {
        cli.Println("i", "Use fpgautil to dump the fpga registers for this functionality  ")
        return
    }

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    hwinfo.EnableHubChannelExclusive(devName)
    err = adt7462.DumpReg(devName) 
    return
}


func FanSpeedSet(devName string, pct int, mask uint64) (err int) {
    var i uint32
    var i2cif i2cinfo.I2cInfo
    var num_fans int = hwinfo.MAX_NUM_FAN
    if i2cinfo.CardType == "TAORMINA" {
        num_fans = 8
    }

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "FanSpeedSet get i2c info failed for dev  ", devName)
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        cli.Println("e", "FanSpeedSet mutex lock failed for dev  ", devName)
        return
    }
    defer dmutex.Unlock(lockName)

    hwinfo.EnableHubChannelExclusive(devName)
    if i2cif.Comp == "ADT7462" {
        for i = 0; i < uint32(num_fans); i++ {
            if (mask & (1 << i)) != 0 {
                adt7462.SetFanSpeed(devName, uint64(i), uint64(pct))
            }
        }
    } else if i2cif.Comp == "FPGA" {
        if i2cinfo.CardType == "LIPARI" {
            for i = 0; i < liparifpga.MAXFAN; i++ {
                if (mask & (1 << i)) != 0 {
                    liparifpga.FAN_Set_PWM(i, uint32(pct))
                }
            }
        } else if i2cinfo.CardType == "MTP_MATERA" {
            for i = 0; i < materafpga.MAXFAN; i++ {
                if (mask & (1 << i)) != 0 {
                    materafpga.FAN_Set_PWM(i, uint32(pct))
                }
            }
        } else if i2cinfo.CardType == "MTP_PANAREA"  {
            for i = 0; i < panareafpga.MAXFAN; i++ {
                if (mask & (1 << i)) != 0 {
                    panareafpga.FAN_Set_PWM(i, uint32(pct))
                }
            }
        } else if i2cinfo.CardType == "MTP_PONZA"{
            for i = 0; i < panareafpga.PONZA_MAXFAN; i++ {
                if (mask & (1 << i)) != 0 {
                    panareafpga.FAN_Set_PWM(i, uint32(pct))
                }
            }
        } else {
            cli.Println("e", "Unsupported component: ", i2cif.Comp," for cardtype: ", i2cinfo.CardType)
            err = errType.INVALID_PARAM
        }
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

/************************************************************************************************** 
*  
* rpm  = Main fan, or in the case with fan modules that have two fans, it will report the inner fan
* rpm2 = on fan modules with 2 fans, this will report the outer fan 
*  
**************************************************************************************************/
func FanSpeedGet(devName string, fanIdx uint64) (rpm uint64, rpm2 uint64, err int) {
    var i2cif i2cinfo.I2cInfo

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to enable hub channel", i2cif.Comp)
        return
    }
    if i2cif.Comp == "ADT7462" {
        rpm, err = adt7462.GetFanSpeed(devName, fanIdx)
    } else if i2cif.Comp == "FPGA" {
        var inner_fan, outer_fan uint32
        if i2cinfo.CardType == "LIPARI" {
            inner_fan, outer_fan, err = liparifpga.FAN_Get_RPM(uint32(fanIdx)) 
        } else if i2cinfo.CardType == "MTP_MATERA"  {
            inner_fan, outer_fan, err = materafpga.FAN_Get_RPM(uint32(fanIdx)) 
        } else if i2cinfo.CardType == "MTP_PANAREA" || i2cinfo.CardType == "MTP_PONZA" {
            inner_fan, outer_fan, err = panareafpga.FAN_Get_RPM(uint32(fanIdx)) 
        } else {
            cli.Println("e", "Unsupported component: ", i2cif.Comp," for cardtype: ", i2cinfo.CardType)
            err = errType.INVALID_PARAM
        }
        rpm = uint64(inner_fan)
        rpm2 = uint64(outer_fan)
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func FanGetTemp(devName string, tempIdx uint64) (temp int, err int) {
    var i2cif i2cinfo.I2cInfo

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    hwinfo.EnableHubChannelExclusive(devName)
    if i2cif.Comp == "ADT7462" {
        temp, _, err = adt7462.GetTemp(devName, tempIdx)
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func FanSetup(devName string) (err int) {
    var i2cif i2cinfo.I2cInfo

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    hwinfo.EnableHubChannelExclusive(devName)
    if i2cif.Comp == "ADT7462" {
        adt7462.Setup(devName)
    } else if i2cif.Comp == "FPGA" {
        if i2cinfo.CardType == "LIPARI" {
            err = liparifpga.Fan_Init() 
        } else if i2cinfo.CardType == "MTP_MATERA" {
            err = materafpga.Fan_Init() 
        } else if i2cinfo.CardType == "MTP_PANAREA" || i2cinfo.CardType == "MTP_PONZA" {
            err = panareafpga.Fan_Init() 
        } else {
            cli.Println("e", "Unsupported component: ", i2cif.Comp," for cardtype: ", i2cinfo.CardType)
            err = errType.INVALID_PARAM
        }
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func FanGetDeviceName(devNumber int) (device string, err int) {
    if i2cinfo.CardType == "MTP" {
        device = "FAN"
    } else if i2cinfo.CardType == "TAORMINA" {
        device = fmt.Sprintf("FAN_%d", devNumber+1)
    } else if i2cinfo.CardType == "LIPARI" {
        device = fmt.Sprintf("FAN")
    } else if i2cinfo.CardType == "MTP_MATERA" || i2cinfo.CardType == "MTP_PANAREA" || i2cinfo.CardType == "MTP_PONZA" {
        device = fmt.Sprintf("FAN")
    } else {
        cli.Printf("e", "INVALID CARD_TYPE.  Make sure card type is set in the environment\n")
        err = errType.FAIL
    }
    return
}
