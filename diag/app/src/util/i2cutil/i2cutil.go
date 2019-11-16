package main

import (
    //"fmt"
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
func TestI2cSpiLpbk () (err int) {
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

    spiTest := i2cspi.NewTest(i2cInfo.Bus, i2cInfo.DevAddr)

    err = spiTest.TestDpramLpbk()
    if err != errType.SUCCESS {
        return
    }

    i2cspi.Close()
    return

}

func I2cSpiReadPage (addr uint32) (err int) {
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
    err = spiTest.TestReadPage(addr)
    if err != errType.SUCCESS {
        return
    }

    return

}
func I2cSpiWritePage (addr uint32) (err int) {
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
    err = spiTest.TestWritePage(addr)
    if err != errType.SUCCESS {
        return
    }

    return

}

func I2cSpiReadId () (err int) {
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
    err = spiTest.TestReadId()
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
    dpramPtr    := flag.Bool(  "dpram",false,  "I2CSPI DPRAM loopback test")
    rdIdPtr     := flag.Bool(  "rdid", false,  "Read SPI ID")
    rdPagePtr   := flag.Bool(  "rdpage",false, "I2CSPI read page")
    wrRdPagePtr := flag.Bool(  "wrpage",false, "I2CSPI write page and read verify")
    addrPtr     := flag.Uint64("addr",  0,     "SPI address")

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
        TestI2cSpiLpbk()
        return
    }

    if *rdPagePtr == true {
        I2cSpiReadPage(uint32(*addrPtr))
        return
    }

    if *rdIdPtr == true {
        I2cSpiReadId()
        return
    }

    if *wrRdPagePtr == true {
        I2cSpiWritePage(uint32(*addrPtr))
        return
    }

    myUsage()
}

