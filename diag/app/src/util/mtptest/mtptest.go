package main

import (
    //"fmt"
    "flag"
    //"os"
    //"strings"

    //"common/cli"
    //"common/errType"
    //"config"
    //"hardware/i2cinfo"
    //"hardware/hwdev"
)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
}

func main() {
    //var err int
    flag.Usage = myUsage

    psuPtr  := flag.Bool("psu",     false, "PSU test")
    fanPtr  := flag.Bool("fan",     false, "Fan test")
    fanSpdPtr  := flag.Bool("fanspd",     false, "Fan speed test")
    flag.Parse()

    if *psuPtr == true {
        psuTest()
        return
    }

    if *fanPtr == true {
        fanTest()
        return
    }

    if *fanSpdPtr == true {
        fanSpeedTest()
        return
    }


    myUsage()
}

