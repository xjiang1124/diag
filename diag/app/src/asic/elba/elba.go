package elba

import (
    "strings"
    "strconv"

    "common/errType"
    "common/runCmd"
    "common/dcli"
)

func Prbs(mode string, poly string, duration int) (err int) {
    var cmd string

    err = errType.SUCCESS

    mode = strings.ToUpper(mode)
    poly = strings.ToUpper(poly)

    if (poly != "PRBS7"  &&
        poly != "PRBS9"  &&
        poly != "PRBS15" &&
        poly != "PRBS31") {
        dcli.Println("e", "Invalid POLY:", poly)
        err = errType.INVALID_PARAM
        return
    }

    dcli.Println("i", mode, strconv.Itoa(duration))
    cmd = "/data/nic_arm/elba/asic_src/ip/cosim/tclsh/nic_prbs.sh"
    if mode == "PCIE" {
        passSign := "PCIE PRBS PASSED"
        failSign := "PCIE PRBS FAILED"
        // err = runCmd.Run(passSign, failSign, cmd, "PCIE", strconv.Itoa(duration))
        err = runCmd.Run(passSign, failSign, cmd, "PCIE", "10")
    } else if mode == "ETH" {
        passSign := "MX PRBS PASSED"
        failSign := "MX PRBS FAILED"
        err = runCmd.Run(passSign, failSign, cmd, "ETH", strconv.Itoa(duration))
    } else {
        dcli.Println("e", "Invalid mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    if err != errType.SUCCESS {
        dcli.Println("e", mode, "PRBS Test Failed!")
    } else {
        dcli.Println("i", mode, "PRBS PASSED")
    }

    return err
}

