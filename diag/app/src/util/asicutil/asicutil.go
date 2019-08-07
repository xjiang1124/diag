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

    prbsPtr  := flag.Bool("prbs", false, "PRBS Test")

    modePtr := flag.String("mode", "ETH",    "PRBS mode: PCIe/ETH")
    polyPtr := flag.String("poly", "PRBS31", "PRBS polynomial")
    duraPtr := flag.Int(   "dura", 60,       "PRBS duration")

    //------------------------
    flag.Parse()

    if *prbsPtr == true {
        capri.Prbs(*modePtr, *polyPtr, *duraPtr)
        return
    }

    myUsage()
}

