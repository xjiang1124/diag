package main

import (
    "fmt"
    "flag"
    "strings"

    "common/cli"
    "common/errType"
    //"common/misc"
    "hardware/i2cinfo"
    "protocol/i2cPtcl"
    "protocol/i2cspi"
)

func readWriteBytes(rws string, devName string, data uint64, numByte uint64) (err int) {
    var dataBuf []byte

	i2cInfo, err := i2cinfo.GetI2cInfo(devName)
	if err != errType.SUCCESS {
	    cli.Println("e", "Fail to open I2C device:", devName)
	    return
	}

    err = i2cPtcl.Open(devName, i2cInfo.Bus, i2cInfo.DevAddr)
    if err != errType.SUCCESS {
        return
    }
    defer i2cPtcl.Close()

    switch rws {
    case "READ":
        dataBuf, err = i2cPtcl.Read(numByte)
        if err != errType.SUCCESS {
            cli.Println("i", "Faied to read I2C device")
        } else {
            cli.Printf("i", "Read device %s done\n", devName)
            cli.Printf("i", "0x%x\n", dataBuf)
            for i:=0; i<len(dataBuf); i++ {
                cli.Printf("i", "data[%d] = 0x%x\n", i, dataBuf[i])
            }
        }
    case "WRITE":
        if numByte > 8 {
            cli.Println("f", "Maximun 8 bytes of i2c write is allowed! Reveived request of ", numByte, "bytes")
            return errType.FAIL
        }
        dataBuf = make([]byte, numByte)
        for i:=0; uint64(i) < numByte; i++ {
            dataBuf[i] = byte((data >> (8*uint64(i))) & 0xFF)
            cli.Printf("d", "data[%d]=0x%x", i, dataBuf[i])
        }
        err = i2cPtcl.Write(dataBuf)
        if err == errType.SUCCESS {
            cli.Printf("i", "Write device %s done\n", devName)
        } else {
            cli.Println("i", "Failed to write I2C device")
        }
    }
    return
}

func I2cSpiExecCmd (cmd string, addr uint32, numBytes int) (err int) {
    devName := "I2CSPI"

	i2cInfo, err := i2cinfo.GetI2cInfo(devName)
	if err != errType.SUCCESS {
	    cli.Println("e", "Fail to open I2C device:", devName)
	    return
	}

    err = i2cspi.Open(devName, i2cInfo.Bus, i2cInfo.DevAddr)
    if err != errType.SUCCESS {
        return
    }
    defer i2cspi.Close()

    spiTest := i2cspi.NewTest(i2cInfo.Bus, i2cInfo.DevAddr)
    switch cmd {
    case "ERASE_BLOCK":
        err = spiTest.TestEraseSector(addr)
    case "READ_ID":
        err = spiTest.TestReadId()
    case "WRITE_PAGE":
        err = spiTest.TestWritePage(addr)
    case "READ_PAGE":
        err = spiTest.TestReadPage(addr)
    case "DPRAM":
        err = spiTest.TestDpramLpbk()
    case "DPRAM_RD":
        err = spiTest.TestDpramLpbkRead(numBytes)
    case "DPRAM_WR":
        err = spiTest.TestDpramLpbkWrite(numBytes)
    case "READ_STS":
        err = spiTest.TestShowSts()
    default:
        cli.Println("e", "Invalid cmd:", cmd)
    }
    if err != errType.SUCCESS {
        return
    }

    return
}

func I2cSpiProgram (imgType string, filename string, startAddr uint32) (err int) {
    devName := "I2CSPI"
    imgType = strings.ToUpper(imgType)

	i2cInfo, err := i2cinfo.GetI2cInfo(devName)
	if err != errType.SUCCESS {
	    cli.Println("e", "Fail to open I2C device:", devName)
	    return
	}

    err = i2cspi.Open(devName, i2cInfo.Bus, i2cInfo.DevAddr)
    if err != errType.SUCCESS {
        return
    }
    defer i2cspi.Close()

    i2cspi.SpiProgram(imgType, filename, startAddr)

    if err != errType.SUCCESS {
        return
    }

    return
}

func I2cSpiDump (imgType string, filename string, startAddr uint32, sizeInByte uint32) (err int) {
    devName := "I2CSPI"
    imgType = strings.ToUpper(imgType)

	i2cInfo, err := i2cinfo.GetI2cInfo(devName)
	if err != errType.SUCCESS {
	    cli.Println("e", "Fail to open I2C device:", devName)
	    return
	}

    err = i2cspi.Open(devName, i2cInfo.Bus, i2cInfo.DevAddr)
    if err != errType.SUCCESS {
        return
    }
    defer i2cspi.Close()

    i2cspi.SpiDump(imgType, filename, startAddr, sizeInByte)

    if err != errType.SUCCESS {
        return
    }

    return
}

func I2cSpiSendCmd (data uint64, numBytes int) (err int) {
    devName := "I2CSPI"

	i2cInfo, err := i2cinfo.GetI2cInfo(devName)
	if err != errType.SUCCESS {
	    cli.Println("e", "Fail to open I2C device:", devName)
	    return
	}

    err = i2cspi.Open(devName, i2cInfo.Bus, i2cInfo.DevAddr)
    if err != errType.SUCCESS {
        return
    }
    defer i2cspi.Close()

    cmd := make([]byte, numBytes)
    for i:=0; i<numBytes; i++ {
        cmd[numBytes-1-i] = byte(data & 0xFF)
        data = data >> 8
    }

    for i:=0; i<numBytes; i++ {
        fmt.Printf("[%d]=0x%02x ", i, cmd[i])
    }
    fmt.Printf("\n")

    err = i2cspi.BusWrite(cmd)
    if err != errType.SUCCESS {
        return
    }

    return
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
    writePtr    := flag.Bool(  "wr",   false, "Write register value")
    dataPtr     := flag.Uint64("data", 0,     "Data value")
    numBytesPtr := flag.Uint64("nb",   0,     "Number of bytes")
    uutPtr      := flag.String("uut",  "UUT_NONE", "Target UUT")
    //======================
    // i2cspi options
    dpramPtr    := flag.Bool(  "dpram",     false,  "I2CSPI DPRAM loopback test")
    dpramWrPtr  := flag.Bool(  "dpram_wr",  false,  "I2CSPI DPRAM loopback write test")
    dpramRdPtr  := flag.Bool(  "dpram_rd",  false,  "I2CSPI DPRAM loopback read test")
    rdIdPtr     := flag.Bool(  "rdid",      false,  "Read SPI ID")
    rdPagePtr   := flag.Bool(  "rdpage",    false,  "I2CSPI read page")
    wrPagePtr   := flag.Bool(  "wrpage",    false,  "I2CSPI write page and read verify")
    erasePtr    := flag.Bool(  "erase",     false,  "I2CSPI erase block")
    rdStsPtr    := flag.Bool(  "rdsts",     false,  "I2CSPI read status")
    sendCmdPtr  := flag.Bool(  "sdcmd",     false,  "I2CSPI send command")
    addrPtr     := flag.Uint64("addr",      0,      "SPI address")
    // Image program
    progPtr     := flag.Bool(  "prog",      false,  "Program image to SPI flash")
    dumpPtr     := flag.Bool(  "dump",      false,  "Dump SPI flash to file")
    imgTypePtr  := flag.String("img_type",  "TESTFW", "Image type: TESTFW/GOLDFW")
    filenamePtr := flag.String("fn",        "",     "Image file name")

    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    data := *dataPtr
    numBytes := *numBytesPtr
    uut := strings.ToUpper(*uutPtr)

    if uut != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(uut)
    }

    if *readPtr == true {
        readWriteBytes("READ", devName, data, numBytes)
        return
    }

    if *writePtr == true {
        readWriteBytes("WRITE", devName, data, numBytes)
        return
    }

    if *infoPtr == true {
        i2cinfo.DispI2cInfoAll()
        return
    }

    if *dpramPtr == true {
        I2cSpiExecCmd("DPRAM", uint32(*addrPtr), int(*numBytesPtr))
        return
    }

    if *dpramWrPtr == true {
        I2cSpiExecCmd("DPRAM_WR", uint32(*addrPtr), int(*numBytesPtr))
        return
    }
    if *dpramRdPtr == true {
        I2cSpiExecCmd("DPRAM_RD", uint32(*addrPtr), int(*numBytesPtr))
        return
    }

    if *rdPagePtr == true {
        I2cSpiExecCmd("READ_PAGE", uint32(*addrPtr), int(*numBytesPtr))
        return
    }

    if *rdIdPtr == true {
        I2cSpiExecCmd("READ_ID", uint32(*addrPtr), int(*numBytesPtr))
        return
    }

    if *wrPagePtr == true {
        I2cSpiExecCmd("WRITE_PAGE", uint32(*addrPtr), int(*numBytesPtr))
        return
    }

    if *erasePtr == true {
        I2cSpiExecCmd("ERASE_BLOCK", uint32(*addrPtr), int(*numBytesPtr))
        return
    }

    if *rdStsPtr == true {
        I2cSpiExecCmd("READ_STS", uint32(*addrPtr), int(*numBytesPtr))
        return
    }

    if *progPtr == true {
        I2cSpiProgram(*imgTypePtr, *filenamePtr, uint32(*addrPtr))
        return
    }

    if *dumpPtr == true {
        I2cSpiDump(*imgTypePtr, *filenamePtr, uint32(*addrPtr), uint32(*numBytesPtr))
        return
    }

    if *sendCmdPtr == true {
        I2cSpiSendCmd(*dataPtr, int(*numBytesPtr))
        return
    }

    myUsage()
}

