package main

import (
    "flag"
    "os"

    "common/cli"
    //"common/errType"
    "asic/capri"
    "asic/elba"

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

    duraPtr := flag.Int("dura", 120, "PRBS duration")
    intLpbkPtr := flag.Bool("int_lpbk", false, "Internal loopback")

    verbosePtr    := flag.Bool("verbose", false, "Turn on verbose")
    //------------------------
    flag.Parse()

    var intLpbk int
    var asicType = os.Getenv("ASIC_TYPE")

    if *intLpbkPtr == true {
        intLpbk = 1
    } else {
        intLpbk = 0
    }

    if *prbsPtr == true {
        if asicType == "ELBA" {
            cli.Println("d", "No PRBS test for Elba cards")
        } else if asicType == "CAPRI"{
            capri.Prbs(*modePtr, *polyPtr, *duraPtr)
        } else {
            cli.Println("e", "Unsupported ASIC type", asicType)
        }
        return
    }

    if *snakePtr == true {
        if asicType == "ELBA" {
            cli.Println("d", "intLpbk:", intLpbk)
            elba.Snake(*modePtr, *duraPtr, intLpbk, *verbosePtr)
        } else if asicType == "CAPRI"{
            capri.Snake(*modePtr, *duraPtr, *verbosePtr)
        } else {
            cli.Println("e", "Unsupported ASIC type", asicType)
        }
        return
    }

    if *snakeChkPtr == true {
        if asicType == "ELBA" {
            elba.SnakeCheck()
        } else if asicType == "CAPRI"{
            capri.SnakeCheck()
        } else {
            cli.Println("e", "Unsupported ASIC type", asicType)
        }
        return
    }

    if *snakePostPtr == true {
        if asicType == "ELBA" {
            elba.SnakePost()
        } else if asicType == "CAPRI"{
            capri.SnakePost(*modePtr)
        } else {
            cli.Println("e", "Unsupported ASIC type", asicType)
        }
        return
    }

    myUsage()
}

