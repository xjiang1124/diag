package main

import (

    "config"
    "flag"
    "common/diagEngine"
    //"common/cli"
    "common/dcli"
    //"common/errType"
    "platform/taormina"
    //"device/bcm/td3"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "CPU"
)



func CpuUsbHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    filesizeMBPtr := fs.Int("filesizeMB", 16, "File Size in MegaBytes")
    NumberOfCopiesPtr := fs.Int("NumberOfCopies", 2, "How many copies of the file to make")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    filesizeMB := *filesizeMBPtr
    filecopies := * NumberOfCopiesPtr

    err = taormina.USBtest(filesizeMB, filecopies)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func CpuDramsizeHdl(argList []string) {
    var err int = 0

    err = taormina.X86_DDR_Display_Info(1)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func CpuPcieHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    skipelbaPtr := fs.Int("skipelba", 0, "Skip scanning Elbas PCI buses")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    dcli.Println("i", "CpuPcieHdl Test\n\n")

    skipelba := *skipelbaPtr
    err = taormina.Pci_scan(uint32(skipelba))

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func CpuMemoryHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    timePtr := fs.Int("testtime", 120, "Test time")
    threadsPtr := fs.Int("threads", 4, "Threads to run")
    percentPtr := fs.Int("percent", 88, "Percent of memory to test")


    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    time := *timePtr
    threads := * threadsPtr
    percent := * percentPtr

    dcli.Println("i", "CpuMemoryHdl Test")
    dcli.Println("i", "TIME=", time)
    dcli.Println("i", "threads=", threads)
    dcli.Println("i", "percent=", percent)
    err = taormina.X86_CPU_MemoryTest(uint32(threads), uint32(percent), uint32(time), 0) 

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)

    diagEngine.FuncMap["USB"] = CpuUsbHdl
    diagEngine.FuncMap["DRAMSIZE"] = CpuDramsizeHdl
    diagEngine.FuncMap["PCISCAN"] = CpuPcieHdl
    diagEngine.FuncMap["MEMORY"] = CpuMemoryHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}

