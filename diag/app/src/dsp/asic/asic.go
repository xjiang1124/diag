package main

import (
    "bufio"
    "flag"
    "io"
    "os/exec"
    "strconv"
    "sync"

    "common/diagEngine"
    //"common/cli"
    "common/dcli"
    "common/errType"
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

func print(stdout io.ReadCloser) {
    r := bufio.NewReader(stdout)
    //for {
    //    line, _, _ := r.ReadLine()
    //    //cli.Println("i", string(line))
    //    dcli.Println("i", string(line))
    //}
    line, _, _ := r.ReadLine()
    dcli.Println("i", string(line))
}

func copyLogs(r io.Reader) {
    buf := make([]byte, 80)
    for {
        misc.SleepInUSec(1000)
        n, err := r.Read(buf)
        if n > 0 {
            dcli.Printf("NO_INFO", "%s", string(buf[0:n]))
        }
        if err != nil {
            break
        }
    }
}


func Mtp_AsicPcie_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    durationPtr := fs.Int("duration", 30, "test time")
    polyPtr := fs.String("poly", "prbs31", "PRBS polynomial")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "duration", *durationPtr, "poly", *polyPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func Mtp_AsicEth_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    durationPtr := fs.Int("duration", 30, "test time")
    polyPtr := fs.String("poly", "prbs31", "PRBS polynomial")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "duration", *durationPtr, "poly", *polyPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func AsicL1_TestHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    snPtr := fs.String("sn", "SN000001", "Serial number")
    slotPtr := fs.Uint64("slot", 1, "Slot number")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    sn := *snPtr
    slot := *slotPtr

    dcli.Println("i", "sn:", sn, "; slot:", strconv.Itoa(int(slot)))

    // Diable time stamp since there are too much asic output
    dcli.TimeStampEnable(misc.DISABLE)
    defer dcli.TimeStampEnable(misc.ENABLE)

    cmd := exec.Command("tclsh", "/home/diag/diag/scripts/asic/l1_test.tcl", sn, strconv.Itoa(int(slot)))
    //cmd := exec.Command("tclsh", "/home/diag/diag/scripts/asic/test.tcl", sn, strconv.Itoa(int(slot)))
    stdout, _ := cmd.StdoutPipe()
    stderr, _ := cmd.StderrPipe()
    var wg sync.WaitGroup

    cmd.Start()
    wg.Add(2)
    go func() {
        defer wg.Done()
        copyLogs(stdout)
    }()

    go func() {
        defer wg.Done()
        copyLogs(stderr)
    }()
    wg.Wait()
    //go print(stdout)
    cmd.Wait()

    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func AsicL11_TestHdl(argList []string) {
    var err int

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    snPtr := fs.String("sn", "SN000001", "Serial number")
    slotPtr := fs.Uint64("slot", 1, "Slot number")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    sn := *snPtr
    slot := *slotPtr

    dcli.Println("i", "sn:", sn, "; slot:", strconv.Itoa(int(slot)))

    // Diable time stamp since there are too much asic output
    dcli.TimeStampEnable(misc.DISABLE)
    defer dcli.TimeStampEnable(misc.ENABLE)

    err = runCmd.Run("L1 Test Passed", "L1 Test Failed", "tclsh", "/home/diag/diag/scripts/asic/l1_test.tcl", sn, strconv.Itoa(int(slot)))
    //err = runCmd.Run("L1 Test Passed", "L1 Test Failed", "tclsh", "/home/diag/diag/scripts/asic/test.tcl", sn, strconv.Itoa(int(slot)))

    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    //diagEngine.FuncMap["PCIE_PRBS"] = AsicPcie_PrbsHdl
    //diagEngine.FuncMap["ETH_PRBS"] = AsicEth_PrbsHdl
    //diagEngine.FuncMap["TRF"] = AsicTrfHdl
    diagEngine.FuncMap["L1"] = AsicL1_TestHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
