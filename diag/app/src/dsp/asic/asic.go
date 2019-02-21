package main

import (
    //"bufio"
    "flag"
    //"io"
    //"os/exec"
    "strconv"
    //"sync"

    "common/diagEngine"
    //"common/cli"
    "common/dcli"
    //"common/errType"
    "common/misc"
    "common/runCmd"
    "config"
    //"bytes"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "ASIC"
)

func AsicPcie_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    snPtr       := fs.String("sn", "SN000001", "Serial number")
    slotPtr     := fs.Int("slot", 1, "Slot number")
    durationPtr := fs.Int("duration", 30, "test time")
    polyPtr     := fs.String("poly", "prbs31", "PRBS polynomial")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    sn := *snPtr
    slot := *slotPtr
    duration := *durationPtr
    poly := *polyPtr

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "duration", duration, "poly", poly)
    err := runCmd.Run("PCIE PRBS PASSED", "PCIE PRBS FAILED", "tclsh", "/home/diag/diag/scripts/asic/ext_pcie_prbs.tcl", sn, strconv.Itoa(slot), strconv.Itoa(duration), poly)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}
func AsicEth_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    snPtr       := fs.String("sn", "SN000001", "Serial number")
    slotPtr     := fs.Int("slot", 1, "Slot number")
    durationPtr := fs.Int("duration", 30, "test time")
    polyPtr     := fs.String("poly", "prbs31", "PRBS polynomial")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    sn := *snPtr
    slot := *slotPtr
    duration := *durationPtr
    poly := *polyPtr

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "duration", duration, "poly", poly)
    err := runCmd.Run("ETH PRBS PASSED", "ETH PRBS FAILED", "tclsh", "/home/diag/diag/scripts/asic/ext_eth_prbs.tcl", sn, strconv.Itoa(slot), strconv.Itoa(duration), poly)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func AsicL1_TestHdl(argList []string) {
    var err int

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    snPtr := fs.String("sn", "SN000001", "Serial number")
    slotPtr := fs.Uint64("slot", 1, "Slot number")
    intLpbkPtr := fs.Uint64("int_lpbk", 0, "Enable internal loopback")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    sn := *snPtr
    slot := *slotPtr
    intLpbk := *intLpbkPtr

    dcli.Println("i", "sn:", sn, "; slot:", strconv.Itoa(int(slot)), "int_lpbk:", strconv.Itoa(int(intLpbk)))

    // Diable time stamp since there are too much asic output
    dcli.TimeStampEnable(misc.DISABLE)
    defer dcli.TimeStampEnable(misc.ENABLE)

    err = runCmd.Run("L1 TEST PASSED", "L1 TEST FAILED", "tclsh", "/home/diag/diag/scripts/asic/l1_test.tcl", sn, strconv.Itoa(int(slot)), strconv.Itoa(int(intLpbk)))

    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PCIE_PRBS"] = AsicPcie_PrbsHdl
    diagEngine.FuncMap["ETH_PRBS"] = AsicEth_PrbsHdl
    //diagEngine.FuncMap["TRF"] = AsicTrfHdl
    diagEngine.FuncMap["L1"] = AsicL1_TestHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
