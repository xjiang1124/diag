package main

import (
    //"bufio"
	"bytes"
    "flag"
    "io"
    "os"
    "os/exec"
    "path/filepath"
    "strconv"
    //"sync"

    //"common/cli"
    "common/diagEngine"
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
    err := runCmd.Run("PCIE PRBS PASSED", "PCIE PRBS FAILED", "stdbuf_tclsh.sh", "/home/diag/diag/scripts/asic/ext_pcie_prbs.tcl", sn, strconv.Itoa(slot), strconv.Itoa(duration), poly)

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
    //err := runCmd.Run("ETH PRBS PASSED", "ETH PRBS FAILED", "tclsh", "/home/diag/diag/scripts/asic/ext_eth_prbs.tcl", sn, strconv.Itoa(slot), strconv.Itoa(duration), poly)
    err := runCmd.Run("ETH PRBS PASSED", "ETH PRBS FAILED", "stdbuf_tclsh.sh", "/home/diag/diag/scripts/asic/ext_eth_prbs.tcl", sn, strconv.Itoa(slot), strconv.Itoa(duration), poly)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func AsicL1_TestHdl(argList []string) {
    var err int

    fs         := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    snPtr      := fs.String("sn",       "SN000001", "Serial number")
    slotPtr    := fs.Uint64("slot",     1,          "Slot number")
    intLpbkPtr := fs.Uint64("int_lpbk", 0,          "Enable internal loopback")
    vmargPtr   := fs.String("vmarg",    "normal",   "Vmargin normal/high/low")
    zmqEnPtr   := fs.Uint64("zmq_en",   0,          "ZMQ enable flag")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    sn := *snPtr
    slot := *slotPtr
    intLpbk := *intLpbkPtr
    vmarg := *vmargPtr
    zmqEn := *zmqEnPtr

    dcli.Println("i", "sn:", sn, "; slot:", strconv.Itoa(int(slot)), "int_lpbk:", strconv.Itoa(int(intLpbk)), "vmarg:", vmarg, "zmqEn:", zmqEn)

    // Diable time stamp since there are too much asic output
    dcli.TimeStampEnable(misc.DISABLE)
    defer dcli.TimeStampEnable(misc.ENABLE)

    dcli.Println("i", "RunVerbose")
    err = runCmd.RunVerbose("L1 TEST PASSED", "L1 TEST FAILED", false, "==>", "stdbuf_tclsh.sh", "/home/diag/diag/scripts/asic/l1_test.tcl", sn, strconv.Itoa(int(slot)), strconv.Itoa(int(intLpbk)), vmarg, strconv.Itoa(int(zmqEn)))

    diagEngine.FuncMsgChan <- err
    return
}


func AsicStop_ZmqHdl(argList []string) {
    var err int

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errGo := fs.Parse(argList)
    if errGo != nil {
        dcli.Println("e", "Parse failed", errGo)
        err = errType.FAIL
        diagEngine.FuncMsgChan <- errType.SUCCESS
        return
    }

    cmd := exec.Command("killall", "diag_zmq_server.exe")
    errGo = cmd.Run()
    if errGo != nil {
        dcli.Println("F", "Failed to kill zmq server", errGo)
        err = errType.FAIL
        diagEngine.FuncMsgChan <- err
        return
    }

    // Check if zmq is running
    c1 := exec.Command("ps", "-elf")
    c2 := exec.Command("grep", "zmq")

    r, w := io.Pipe()
    c1.Stdout = w
    c2.Stdin = r

    var b2 bytes.Buffer
    c2.Stdout = &b2

    c1.Start()
    c2.Start()
    c1.Wait()
    w.Close()
    c2.Wait()
    dcli.Println("i", b2.String())

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func AsicStart_ZmqHdl(argList []string) {
    var err int

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errGo := fs.Parse(argList)
    if errGo != nil {
        dcli.Println("e", "Parse failed", errGo)
        err = errType.FAIL
        diagEngine.FuncMsgChan <- errType.SUCCESS
        return
    }

    cmd := exec.Command("/bin/bash", "/home/diag/diag/scripts/asic/start_zmq.sh")
    errGo = cmd.Start()
    if errGo != nil {
        dcli.Println("F", "Error starting Cmd", errGo)
        err = errType.FAIL
        diagEngine.FuncMsgChan <- err
        return
    }

    misc.SleepInSec(1)

    // Check if zmq is running
    c1 := exec.Command("ps", "-elf")
    c2 := exec.Command("grep", "zmq")

    r, w := io.Pipe()
    c1.Stdout = w
    c2.Stdin = r

    var b2 bytes.Buffer
    c2.Stdout = &b2

    c1.Start()
    c2.Start()
    c1.Wait()
    w.Close()
    c2.Wait()
    dcli.Println("i", b2.String())

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func main() {
    pName := filepath.Base(os.Args[0])
    dcli.Init("log_"+pName+".txt", config.OutputMode)

    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PCIE_PRBS"] = AsicPcie_PrbsHdl
    diagEngine.FuncMap["ETH_PRBS"] = AsicEth_PrbsHdl
    diagEngine.FuncMap["L1"] = AsicL1_TestHdl
    diagEngine.FuncMap["start_zmq"] = AsicStart_ZmqHdl
    diagEngine.FuncMap["stop_zmq"] = AsicStop_ZmqHdl

    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
