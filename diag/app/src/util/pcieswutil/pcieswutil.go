package main

import (
    "flag"
    "strings"

    "common/cli"
    "common/errType"
    "device/pciesw/pex8716"

    "hardware/i2cinfo"
)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage
    //------------------------
    infoPtr     := flag.Bool(  "info",  false, "Show I2C info table")
    devNamePtr  := flag.String("dev",   "",    "Device name")
    //------------------------
    readPtr     := flag.Bool(  "rd",    false, "Read register value")
    writePtr    := flag.Bool(  "wr",    false, "Write register value")
    erdPtr      := flag.Bool(  "erd",   false, "Read PEX EEPROM")
    ewrPtr      := flag.Bool(  "ewr",   false, "Write PEX EEPROM")
    progPtr     := flag.Bool(  "prog",  false, "Program PEX eeprom")
    verifPtr    := flag.Bool(  "verif", false, "Verify PEX eeprom")
    //------------------------
    addrPtr     := flag.Uint64("addr",  0,    "Register addr")
    dataPtr     := flag.Uint64("data",  0,    "Data value")
    //numBytesPtr := flag.Uint64("nb",   0,    "Number of bytes")
    accModePtr  := flag.Uint64("am",    0, "Access mod, default 0: transparent ports")
    portPtr     := flag.Uint64("p",     0, "Port")
    byteEnPtr   := flag.Uint64("be",    0xF, "Byte Enable: default: 0xF")
    //------------------------
    mtpTestPtr  := flag.Bool(  "mtest", false, "MTP PCIe test")
    durationPtr := flag.Int(   "dura",  10, "Test duration")
    modePtr     := flag.Int(   "mode",  1, "Test mode: 0 - master lpbk on port 0; 1 - master lpbk on port 1")
    //------------------------
    uutPtr      := flag.String("uut",   "UUT_NONE", "Target UUT")
    //------------------------
    fnPtr       := flag.String("fn",    "", "File name")
    //------------------------
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    addr := uint32(*addrPtr)
    data := uint32(*dataPtr)
    port := byte(*portPtr)
    accMode := byte(*accModePtr)
    byteEn := byte(*byteEnPtr)
    uut  := strings.ToUpper(*uutPtr)
    fn   := *fnPtr

    if uut != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(uut)
    }

    if *readPtr == true {
        err := pex8716.Open(devName)
        if err != errType.SUCCESS {
            return
        }
        defer pex8716.Close()
        data, err := pex8716.ReadReg(addr, accMode, port, byteEn)
        if err == errType.SUCCESS {
            cli.Printf("i", "PEX read at addr=0x%x with data=0x%x\n", addr, data)
        }
        return
    }

    if *writePtr == true {
        err := pex8716.Open(devName)
        if err != errType.SUCCESS {
            return
        }
        defer pex8716.Close()
        err = pex8716.WriteReg(addr, data, accMode, port, byteEn)
        if err == errType.SUCCESS {
            cli.Printf("i", "PEX write at addr=0x%x with data=0x%x done\n", addr, data)
        }
        return
    }

    if *erdPtr == true {
        err := pex8716.Open(devName)
        if err != errType.SUCCESS {
            return
        }
        defer pex8716.Close()
        data, err := pex8716.ReadEepDw(addr, port)
        if err == errType.SUCCESS {
            cli.Printf("i", "PEX read EEPROM at addr=0x%x with data=0x%x\n", addr, data)
        }
        return
    }

    if *ewrPtr == true {
        err := pex8716.Open(devName)
        if err != errType.SUCCESS {
            return
        }
        defer pex8716.Close()
        err = pex8716.WriteEepDw(addr, port, data)
        if err == errType.SUCCESS {
            cli.Printf("i", "PEX write EEPROM at addr=0x%x with data=0x%x - done\n", addr, data)
        }
        return
    }

    if *infoPtr == true {
        i2cinfo.DispI2cInfoAll()
        return
    }

    if *mtpTestPtr == true {
        pex8716.UTPTest(devName, *durationPtr, *modePtr)
        return
    }

    if *progPtr == true {
        pex8716.Program(devName, fn)
        return
    }

    if *verifPtr == true {
        pex8716.Verify(devName, fn)
        return
    }

    myUsage()
}

