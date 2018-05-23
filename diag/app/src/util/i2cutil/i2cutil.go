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

    err = i2cPtcl.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer i2cPtcl.Close()

    for _, vrm := range(i2cinfo.CurI2cTbl) {
        if devName != vrm.Name {
            continue
        }
        switch rws {
        case "READ":
            dataBuf, err = i2cPtcl.Read(numByte)
            if err != errType.SUCCESS {
                return
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
            if err != errType.SUCCESS {
                return
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
    //addr := *addrPtr
    data := *dataPtr
    numBytes := *numBytesPtr

    if *uutPtr != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(*uutPtr)
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

