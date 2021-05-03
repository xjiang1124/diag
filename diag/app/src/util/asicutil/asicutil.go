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

    duraPtr := flag.Int("dura", 60, "PRBS duration")
    intLpbkPtr := flag.Bool("int_lpbk", false, "Internal loopback")

    verbosePtr    := flag.Bool("verbose", false, "Turn on verbose")
    //------------------------
    flag.Parse()

    var intLpbk int
    var cardType = os.Getenv("CARD_TYPE")

    if *intLpbkPtr == true {
        intLpbk = 1
    } else {
        intLpbk = 0
    }

    if *prbsPtr == true {
        if cardType == "ORTANO2" {
            cli.Println("d", "No PRBS test for Elba cards")
        } else {
            capri.Prbs(*modePtr, *polyPtr, *duraPtr)
        }
        return
    }

    if *snakePtr == true {
        if cardType == "ORTANO2" {
            cli.Println("d", "intLpbk:", intLpbk)
            elba.Snake(*modePtr, *duraPtr, intLpbk, *verbosePtr)
        } else {
            capri.Snake(*modePtr, *duraPtr, *verbosePtr)
        }
        return
    }

    if *snakeChkPtr == true {
        if cardType == "ORTANO2" {
            elba.SnakeCheck()
        } else {
            capri.SnakeCheck()
        }
        return
    }

    if *snakePostPtr == true {
        if cardType == "ORTANO2" {
            elba.SnakePost()
        } else {
            capri.SnakePost(*modePtr)
        }
        return
    }

    myUsage()
}

