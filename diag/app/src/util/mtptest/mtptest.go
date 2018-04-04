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

    psutestPtr  := flag.Bool("psu",     false, "PSU test")
    flag.Parse()

    if *psutestPtr == true {
        psuTest()
        return
    }


    myUsage()
}

