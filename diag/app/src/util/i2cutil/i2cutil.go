package main

import (
    //"fmt"
    "flag"
    "strings"
    "golang.org/x/exp/io/i2c"

    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "protocol/i2cPtcl"
)

func readWriteBytes1(rws string, devName string, data uint64, numByte uint64) (err int) {
    dataBuf := make([]byte, numByte)

    i2c, errgo := i2c.Open(&i2c.Devfs{Dev: "/dev/i2c-0"}, 0x38)
    if errgo != nil {
        panic(err)
    }
    defer i2c.Close()

    for _, vrm := range(i2cinfo.CurI2cTbl) {
        if devName != vrm.Name {
            continue
        }
        switch rws {
        case "READ":
            errgo := i2c.Read(dataBuf)
            if errgo != nil {
                cli.Println("e", "Failed to read block device", devName, "err code=", errgo)
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
            for i:=0; uint64(i) < numByte; i++ {
                dataBuf[i] = byte((data >> (8*uint64(i))) & 0xFF)
                cli.Printf("d", "data[%d]=0x%x", i, dataBuf[i])
            }
            errgo = i2c.Write(dataBuf)
            if errgo != nil {
                cli.Println("e", "Failed to write block device", devName, "err code=", errgo)
            } else {
                cli.Printf("i", "Write device %s done\n", devName)
            }
        }
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

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
    //addrPtr     := flag.Uint64("addr", 0,    "Register addr")
    dataPtr     := flag.Uint64("data", 0,    "Data value")
    numBytesPtr  := flag.Uint64("nb",   0,    "Number of bytes")
    uutPtr      := flag.String("uut",  "UUT_NONE", "Target UUT")
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

    myUsage()
}

