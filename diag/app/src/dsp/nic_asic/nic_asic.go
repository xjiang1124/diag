package main

import (
    "flag"
    "os"

    "asic/capri"
    "asic/elba"
    "common/diagEngine"
    "common/dcli"
    //"common/errType"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "NIC_ASIC"
)

func Nic_AsicPcie_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    durationPtr := fs.Int("duration", 60, "test time")
    polyPtr := fs.String("poly", "PRBS31", "PRBS polynomial")
    var cardType string
    var err int

    cardType = os.Getenv("CARD_TYPE")
    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    if ( cardType == "ORTANO"  || cardType == "ORTANO2" ) {
        err = elba.Prbs("PCIE", *polyPtr, *durationPtr)
    } else {
        err = capri.Prbs("PCIE", *polyPtr, *durationPtr)
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func Nic_AsicEth_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    durationPtr := fs.Int("duration", 60, "test time")
    polyPtr := fs.String("poly", "PRBS31", "PRBS polynomial")
    var cardType string
    var err int

    cardType = os.Getenv("CARD_TYPE")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    if ( cardType == "ORTANO"  || cardType == "ORTANO2" ) {
        err = elba.Prbs("ETH", *polyPtr, *durationPtr)
    } else {
        err = capri.Prbs("ETH", *polyPtr, *durationPtr)
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PCIE_PRBS"] = Nic_AsicPcie_PrbsHdl
    diagEngine.FuncMap["ETH_PRBS"] = Nic_AsicEth_PrbsHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
