package main

import (
    "common/cli"
    "common/misc"
    "common/errType"

    "device/cpld/mtpCpld"
    "device/fanctrl/adt7462"

    "hardware/hwdev"
    "hardware/hwinfo"

    "protocol/smbus"
)

type FanSpeedConfig struct {
    pct int
    rpmMin uint64
    rpmMax uint64
}

type FanTempConfig struct {
    tempMin int
    tempMax int
}

func psuTest(psumask uint) (err int) {
    for i, psu := range(hwinfo.PsuList) {
        if (1<<uint(i)) & psumask == 0 {
            cli.Printf("i", "%s bypassed\n", psu)
            continue
        }
        err = hwdev.DispStatus(psu, "UUT_NONE")
        if err != errType.SUCCESS {
            cli.Println("e", "#####", psu, "TEST FAILED! #####")
        } else {
            cli.Println("i", "#####", psu, "TEST PASSED! #####")
        }
    }
    return
}

func fanTest() (err int) {
    fan := "FAN"
    err = hwdev.DispStatus(fan, "UUT_NONE")
    if err != errType.SUCCESS {
        cli.Println("e", "#####", fan, "TEST FAILED! #####")
    } else {
        cli.Println("i", "#####", fan, "TEST PASSED! #####")
    }
    return
}

func fanSpeedTest() (err int) {
    var rpm uint64
    var err1 int
    fan := "FAN"

    var fanSpeedList = []FanSpeedConfig {
        FanSpeedConfig{
            pct: 50,
            rpmMin: 2000,
            rpmMax: 4000,
        },
    }
    for _, fanSpeed := range(fanSpeedList) {
        err1 = hwdev.FanSpeedSet(fan, fanSpeed.pct, 7)
        if err != errType.SUCCESS {
            err = err1
            cli.Println("e", fan, "access failed")
        }

        // Wait for speed to settle down
        misc.SleepInSec(10)

        for i := 0; i < 6; i++ {
            rpm, err1 = hwdev.FanSpeedGet(fan, uint64(i))
            if err1 != errType.SUCCESS {
                err = err1
                cli.Println("e", fan, "access failed")
            }
            if rpm < fanSpeed.rpmMin || rpm > fanSpeed.rpmMax {
                cli.Printf("e", "Speed out of range, idx=%d, pct=%d, min=%d, max=%d, read rpm=%d\n",
                    i, fanSpeed.pct, fanSpeed.rpmMin, fanSpeed.rpmMax, rpm)
                err = errType.FAIL
            }
        }
    }
    if (err == errType.SUCCESS) {
        cli.Println("i", "#####", "Fan Speed", "TEST PASSED! #####")
    } else {
        cli.Println("i", "#####", "Fan Speed", "TEST FAILED! #####")
    }
    return
}

func fanTempTest(mode string) (err int) {
    fan := "FAN"
    var temp int
    fanTempTbl := make(map[string]FanTempConfig)
    fanTempTbl["AMB"] = FanTempConfig{20, 30}

    fanTemp, ok := fanTempTbl[mode]
    if ok != true {
        cli.Println("e", "Invalid mode:", mode)
        err = errType.SUCCESS
        cli.Println("e", "##### Fan Temp TEST FAILED! #####")
        return
    }

    for i:=0; i<4; i++ {
        temp, err = hwdev.FanGetTemp(fan, uint64(i))
        if err != errType.SUCCESS {
            cli.Println("e", "#####", fan, "TEST FAILED! #####")
            return
        }
        if temp < fanTemp.tempMin || temp > fanTemp.tempMax {
            cli.Printf("e", "Fan temp out of range! idx=%d, min=%d, max=%d, read=%d\n",
                i, fanTemp.tempMin, fanTemp.tempMax, temp)
        }
        cli.Printf("i", "Fan Temp Sensor idx%d passed; read=%d\n", i, temp)
    }
    cli.Println("i", "#####", "Fan Temp Sensor", "TEST PASSED! #####")
    return
}

func fanAlertTest() (err int) {
    fan := "FAN"

    // Read Fan controller alert status
    value, err := mtpCpld.CpldRead(0x5)
    if err != errType.SUCCESS {
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }
    if (value & 0x4) != 0 {
        cli.Printf("e", "CPLD interrupt is already set! value=0x%x\n", value)
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }
    cli.Println("d", "P0")

    // Lower Local Temp High Limit to trigger interrupt
    err = hwinfo.EnableHubChannelExclusive(fan)
    if err != errType.SUCCESS {
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }

    cli.Println("d", "P1")
    err = smbus.Open(fan)
    if err != errType.SUCCESS {
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }
    defer smbus.Close()
    err = smbus.WriteByte(fan, adt7462.LOCAL_HIGH_LIMIT, 0x50)
    if err != errType.SUCCESS {
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }
    cli.Println("d", "P2")

    misc.SleepInSec(1)

    value, err = mtpCpld.CpldRead(0x5)
    if err != errType.SUCCESS {
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }
    if (value & 0x4) == 0 {
        cli.Printf("e", "CPLD interrupt is not set after trigerring! value=0x%x\n", value)
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }

    // Restore Local Temp High Limit
    err = smbus.WriteByte(fan, adt7462.LOCAL_HIGH_LIMIT, 0x95)
    if err != errType.SUCCESS {
        cli.Println("i", "#####", "Fan Alert", "TEST FAILED! #####")
        return
    }
    cli.Println("i", "#####", "Fan Temp Sensor", "TEST PASSED! #####")
    return
}


func vrmTest() (err int) {
    vrm := "DC_1"
    err = hwdev.DispStatus(vrm, "UUT_NONE")
    if err != errType.SUCCESS {
        cli.Println("e", "#####", vrm, "TEST FAILED! #####")
        return
    }    
    vrm = "DC_2"
    err = hwdev.DispStatus(vrm, "UUT_NONE")
    if err != errType.SUCCESS {
        cli.Println("e", "#####", vrm, "TEST FAILED! #####")
    } else {
        cli.Println("i", "#####", vrm, "TEST PASSED! #####")
    }

    return
}

func stsCheck(psumask uint) (err int) {
    value, err := mtpCpld.CpldRead(0x3)
    if err != errType.SUCCESS {
        cli.Println("e", "#####", "Status Check", "TEST FAILED! #####")
        return
    }
    if value & 0x7 != 0x7 {
        cli.Printf("e", "Fan present bit missing! read 0x%x\n", value)
        cli.Println("e", "#####", "Status Check", "TEST FAILED! #####")
        err = errType.FAIL
        return
    }

    for i:=0; i<2; i++ {
        bit := uint(1 << uint(i))
        if bit & psumask == 0 {
            continue
        }
        if (value >> 3) & uint8(bit) == 0 {
            cli.Printf("e", "PSU DC ok not set! read 0x%x\n", value)
            cli.Println("e", "#####", "Status Check", "TEST FAILED! #####")
            err = errType.FAIL
            return
        }
    }
    cli.Println("i", "#####", "Status Check", "TEST PASSED! #####")
    return
}


