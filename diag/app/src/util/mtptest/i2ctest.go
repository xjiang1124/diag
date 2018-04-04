package main

import (
    "common/cli"
    "common/misc"
    "common/errType"

    "hardware/hwdev"
    "hardware/hwinfo"
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

func psuTest(psumask int) (err int) {
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
    fan := "FAN"

    var fanSpeedList = []FanSpeedConfig {
        FanSpeedConfig{
            pct: 50,
            rpmMin: 4000,
            rpmMax: 6000,
        },
    }
    for _, fanSpeed := range(fanSpeedList) {
        err = hwdev.FanSpeedSet(fan, fanSpeed.pct, 7)
        if err != errType.SUCCESS {
            cli.Println("e", "#####", fan, "TEST FAILED! #####")
            return
        }

        // Wait for speed to settle down
        misc.SleepInSec(10)

        for i := 0; i < 6; i++ {
            rpm, err = hwdev.FanSpeedGet(fan, uint64(i))
            if err != errType.SUCCESS {
                cli.Println("e", "#####", fan, "TEST FAILED! #####")
                return
            }
            if rpm < fanSpeed.rpmMin || rpm > fanSpeed.rpmMax {
                cli.Printf("e", "Speed out of range, idx=%d, pct=%d, min=%d, max=%d, read rpm=%d\n",
                    i, fanSpeed.pct, fanSpeed.rpmMin, fanSpeed.rpmMax, rpm)
                cli.Println("e", "#####", "Fan Speed", "TEST FAILED! #####")
                err = errType.FAIL
                return
            }
        }
    }
    cli.Println("i", "#####", fan, "TEST PASSED! #####")
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


func vrmTest() (err int) {
    vrm := "DC"
    err = hwdev.DispStatus(vrm, "UUT_NONE")
    if err != errType.SUCCESS {
        cli.Println("e", "#####", vrm, "TEST FAILED! #####")
    } else {
        cli.Println("i", "#####", vrm, "TEST PASSED! #####")
    }
    return
}
