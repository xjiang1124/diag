package main

import (
    //"fmt"
    "flag"
    "strings"
    "hardware/i2cinfo"
    "util/utillib"
)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage

    infoPtr     := flag.Bool(  "info", false, "Show I2C info table")
    devNamePtr  := flag.String("dev",  "",    "Device name")
    readPtr     := flag.Bool(  "rd",   false, "Read register value")
    readBlkPtr  := flag.Bool(  "rdb",  false, "Read register block value")
    writePtr    := flag.Bool(  "wr",   false, "Write register value")
    writeBlkPtr := flag.Bool(  "wrb",  false, "Write register block value")
    sendPtr     := flag.Bool(  "sd",   false, "Send byte")
    recvPtr     := flag.Bool(  "rb",   false, "Receive byte")
    modePtr     := flag.String("mode", "b",   "r/w mode: byte(b) or word(w)")
    addrPtr     := flag.Uint64("addr", 0,    "Register addr")
    dataPtr     := flag.Uint64("data", 0,    "Data value")
    numBytePtr  := flag.Uint64("nb",   0,    "Number of bytes")
    uutPtr      := flag.String("uut",  "UUT_NONE", "Target UUT")
    phyPtr      := flag.Uint64("phy", 0,    "Phy addr")
    smiPtr     	:= flag.Bool(  "smi", false, "Switch smi access")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    addr := *addrPtr
    data := *dataPtr
    mode := strings.ToUpper(*modePtr)
    numByte := *numBytePtr
    phyAddr := *phyPtr
    uut := strings.ToUpper(*uutPtr)

    if uut != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(uut)
    }

    if *readPtr == true {
        if devName == "SWITCH" {
            if *smiPtr == true {
                utillib.ReadWriteSmi("READ", phyAddr, addr, uint16(data), mode)
            } else {
                utillib.ReadWriteMdio("READ", phyAddr, addr, uint16(data), mode)
            }
        } else {
            utillib.ReadWriteSend("READ", devName, addr, uint16(data), mode)
        }
        return
    }

    if *writePtr == true {
        if devName == "SWITCH" {
            if *smiPtr == true {
                utillib.ReadWriteSmi("WRITE", phyAddr, addr, uint16(data), mode)
            } else {
                utillib.ReadWriteMdio("WRITE", phyAddr, addr, uint16(data), mode)
            }
        } else {
            utillib.ReadWriteSend("WRITE", devName, addr, uint16(data), mode)
        }
        return
    }

    if *sendPtr == true {
        utillib.ReadWriteSend("SEND", devName, addr, uint16(data), mode)
        return
    }

    if *recvPtr == true {
        utillib.ReadWriteSend("RECEIVE", devName, addr, uint16(data), mode)
        return
    }

    if *readBlkPtr == true {
        utillib.ReadWriteBlk("READ_BLK", devName, addr, data, numByte)
        return
    }

    if *writeBlkPtr == true {
        utillib.ReadWriteBlk("WRITE_BLK", devName, addr, data, numByte)
        return
    }

    if *infoPtr == true {
        i2cinfo.DispI2cInfoAll()
        return
    }

    myUsage()
}

