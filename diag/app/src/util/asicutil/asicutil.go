package main

import (
    "flag"

    //"common/cli"
    //"common/errType"
    "asic/capri"

)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
}

func main() {
    flag.Usage = myUsage

    chkLogPtr  := flag.Bool("chklog", false, "Check test log")
    //------------------------
    flag.Parse()

    if *chkLogPtr == true {
        capri.PciePrbs("PRBS31", 5)
        return
    }

    myUsage()
}

