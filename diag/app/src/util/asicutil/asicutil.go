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

    prbsPtr     := flag.Bool("prbs",       false, "PRBS Test")
    snakePtr    := flag.Bool("snake",      false, "SNAKE Test")
    snakePostPtr:= flag.Bool("snake_post", false, "SNAKE Test post check")
    snakeChkPtr := flag.Bool("snake_chk",  false, "SNAKE Test status check")

    modePtr := flag.String("mode", "ETH",    "PRBS mode: PCIe/ETH; Snake mode: PCIE_LB/HBM_LB")
    polyPtr := flag.String("poly", "PRBS31", "PRBS polynomial")

    duraPtr := flag.Int(   "dura", 60,       "PRBS duration")

    verbosePtr    := flag.Bool("verbose", false, "Turn on verbose")
    //------------------------
    flag.Parse()

    if *prbsPtr == true {
        capri.Prbs(*modePtr, *polyPtr, *duraPtr)
        return
    }

    if *snakePtr == true {
        capri.Snake(*modePtr, *duraPtr, *verbosePtr)
        return
    }

   if *snakeChkPtr == true {
       capri.SnakeCheck()
       return
   }

   if *snakePostPtr == true {
       capri.SnakePost(*modePtr)
       return
   }

    myUsage()
}

