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

func psuTest() (err int) {
    for _, psu := range(hwinfo.PsuList) {
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
