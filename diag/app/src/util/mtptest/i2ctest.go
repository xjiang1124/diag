package main

import (
    "common/cli"
    "common/errType"
    "hardware/hwdev"
    "hardware/hwinfo"
)

func psuTest() (err int) {
    for _, psu := range(hwinfo.PsuList) {
        cli.Println("d", "Testing", psu)
        err = hwdev.DispStatus(psu, "UUT_NONE")
        if err != errType.SUCCESS {
            cli.Println("e", "#####", psu, "TEST FAILED! #####")
        }
    }
    return
}

