package main

import (
    "flag"
//    "strings"
    "common/cli"
//    "common/errType"
    "hardware/i2cinfo"
    "common/misc"
    "device/pciesw/pex8716"
)

const (
    DEVNAME string = "PCIE_SMB"
    NUMBYTE uint = 4
    
    PORTCONTROL uint64 = 0x208
    TESTPATTERN0 uint64 = 0x20c
    TESTPATTERN1 uint64 = 0x210
    TESTPATTERN2 uint64 = 0x214
    TESTPATTERN3 uint64 = 0x218
    PHYSICALTEST0 uint64 = 0x224
    PHYSICALTEST1 uint64 = 0x228
    PORTCOMMAND uint64 = 0x230
    DIAGDATAQUAD0 uint64 = 0x238
    DIAGDATAQUAD1 uint64 = 0x23C
    DIAGDATAQUAD2 uint64 = 0x240
    DIAGDATAQUAD3 uint64 = 0x244
)

func pexLpbkConfig() (err int) {
    dataBuf := make([]byte, NUMBYTE)
    pattern0 := []byte{0x11, 0x22, 0x33, 0x44}
    pattern1 := []byte{0x55, 0x66, 0x77, 0x88}
    pattern2 := []byte{0x11, 0x22, 0x33, 0x44}
    pattern3 := []byte{0x55, 0x66, 0x77, 0x88}
    
    //clear 0x224 bit10
    err = pex8716.PexRegRead(DEVNAME, PHYSICALTEST0, dataBuf)
    dataBuf[1] &= 0xFB
    err = pex8716.PexRegWrite(DEVNAME, PHYSICALTEST0, dataBuf)
    
    //write pattern to register
    err = pex8716.PexRegWrite(DEVNAME, TESTPATTERN0, pattern0)
    err = pex8716.PexRegWrite(DEVNAME, TESTPATTERN1, pattern1)
    err = pex8716.PexRegWrite(DEVNAME, TESTPATTERN2, pattern2)
    err = pex8716.PexRegWrite(DEVNAME, TESTPATTERN3, pattern3)
    
    //write reg 0x208, set bit[24, 25] 0x10, clear [28, 29]
    err = pex8716.PexRegRead(DEVNAME, PORTCONTROL, dataBuf)
    dataBuf[3] &= 0xCE
    dataBuf[3] |= 0x2
    err = pex8716.PexRegWrite(DEVNAME, PORTCONTROL, dataBuf)

    //set reg 0x230 port 0 master lpbk
    err = pex8716.PexRegRead(DEVNAME, PORTCOMMAND, dataBuf)
    dataBuf[0] = 0
    dataBuf[0] |= 1
    dataBuf[1] = 0
    dataBuf[2] = 0
    dataBuf[3] = 0
    err = pex8716.PexRegWrite(DEVNAME, PORTCOMMAND, dataBuf)
    
    //read back to make sure lpbk is ready
    var i uint = 0
    for ; i < 10; i++ {
        err = pex8716.PexRegRead(DEVNAME, PORTCOMMAND, dataBuf)
        if dataBuf[0] & 0x8 == 0 {
            break
        }
    }
    if i == 10 {
        cli.Println("Port lpbk master state is not ready")
    }
    return
}

func pexTestStart() (err int) {
    dataBuf := make([]byte, NUMBYTE)
    //write reg 0x228 to set parallel lpbk, enable generator
    dataBuf[2] = 0x2
    dataBuf[3] = 0xFF
    err = pex8716.PexRegWrite(DEVNAME, PHYSICALTEST1, dataBuf)
    
    return
}

func pexTestStop() (err int) {
    dataBuf := make([]byte, NUMBYTE)
    //clear reg 0x228
    err = pex8716.PexRegWrite(DEVNAME, PHYSICALTEST1, dataBuf)
    
    return
}

func pexTestCheck() (err int) {
    dataBuf := make([]byte, NUMBYTE)
//    err = pex8716.PexRegRead(DEVNAME, DIAGDATAQUAD0, dataBuf)
    for i:=0; i< 8; i++ {
        dataBuf[3] = (byte)(i % 4)
        err = pex8716.PexRegWrite(DEVNAME, DIAGDATAQUAD0 + (uint64)((i/4)*4), dataBuf)
        err = pex8716.PexRegRead(DEVNAME, DIAGDATAQUAD0 + (uint64)((i/4)*4), dataBuf)
        if dataBuf[3] & 0x80 == 0 {
            cli.Println("Serdes", i, "UTP is not sync")
            continue
        }
        if dataBuf[2] != 0 {
            cli.Println("Serdes", i, "error, expected", dataBuf[0], "actual", dataBuf[1])
        } else {
            cli.Println("Serdes", i, "UTP passed!")
        }
    }
    
    return
}

func pexTestCleanup() (err int) {
    dataBuf := make([]byte, NUMBYTE)
    err = pex8716.PexRegWrite(DEVNAME, PHYSICALTEST1, dataBuf)
    
    return
}

func myUsage() {
    flag.PrintDefaults()
    i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage

    durationPtr     := flag.Int(  "dura", 10, "Test duration")
    flag.Parse()

    //cli.Println("devNamePtr:", *devNamePtr, "statusPtr:", *statusPtr, "marginPtr:", *marginPtr, "pctPtr:", *pctPtr)
    //cli.Println("i", *readPtr, *writePtr, *sendPtr, *addrPtr, *dataPtr)
    duration := *durationPtr

    pexLpbkConfig()
    pexTestStart()
    misc.SleepInSec(duration)
    pexTestStop()
    pexTestCheck()
    pexTestCleanup()

    myUsage()
}

