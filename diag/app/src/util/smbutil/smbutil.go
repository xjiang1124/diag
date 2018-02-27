package main

import (
    "flag"
    "strings"

    "common/cli"
    "common/dmutex"
    "common/errType"

    "hardware/i2cinfo"

    "protocol/smbus"
)

func init() {
}

func readWriteSend(rws string, devName string, regAddr uint64, data uint16, mode string) (err int) {
    var dataB byte

    mode = strings.ToUpper(mode)
    if (mode != "B" && mode != "W") {
        cli.Println("e", "Unsupported mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

    for _, vrm := range(i2cinfo.I2cTbl) {
        if devName != vrm.Name {
            continue
        }
        switch rws {
        case "READ":
            if mode == "B" {
                dataB, err = smbus.ReadByte(devName, regAddr)
                data = uint16(dataB)
            } else {
                data, err = smbus.ReadWord(devName, regAddr)
                cli.Printf("d", "data=0x%x\n", data)
            }
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device", devName, "at", regAddr)
            } else {
                cli.Printf("i", "Read device %s at addr 0x%x; data=0x%x\n", devName, regAddr, data)
            }
        case "WRITE":
            if mode == "B" {
                err = smbus.WriteByte(devName, regAddr, byte(data))
            } else {
                err = smbus.WriteWord(devName, regAddr, data)
            }
            if err != errType.SUCCESS {
                cli.Printf("i", "Write device %s at addr 0x%x with data=0x%x failed: 0x%x\n", devName, regAddr, data, err)
            } else {
               cli.Printf("i", "Write device %s at addr 0x%x with data=0x%x - Done\n", devName, regAddr, data)
            }
        case "SEND":
            err = smbus.SendByte(devName, byte(regAddr))
            if err != errType.SUCCESS {
                cli.Printf("i", "Send byte device %s of data=0x%x failed: 0x%x\n", devName, regAddr, err)
            } else {
                cli.Printf("i", "Send byte device %s of data=0x%x - Done\n", devName, regAddr)
            }
        case "RECEIVE":
            dataB, err = smbus.ReceiveByte(devName)
            if err != errType.SUCCESS {
                cli.Printf("i", "Receive byte device %s failed: 0x%x\n", devName, err)
            } else {
                cli.Printf("i", "Receive byte device %s of data=0x%x - Done\n", devName, dataB)
            }
        }
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func readWriteBlk(rws string, devName string, regAddr uint64, data uint64, numByte uint64) (err int) {
    dataBuf := make([]byte, numByte)
    var byteCnt int

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

    for _, vrm := range(i2cinfo.I2cTbl) {
        if devName != vrm.Name {
            continue
        }
        switch rws {
        case "READ_BLK":
            byteCnt, err = smbus.ReadBlock(devName, regAddr, dataBuf)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read block device", devName, "at addr=", regAddr, "err code=", err)
            } else {
                cli.Printf("i", "Read block device %s at addr 0x%x with %d bytes\n", devName, regAddr, byteCnt)
                cli.Printf("i", "0x%x\n", dataBuf)
                for i:=0; i<len(dataBuf); i++ {
                    cli.Printf("i", "data[%d] = 0x%x\n", i, dataBuf[i])
                }
            }
        case "WRITE_BLK":
            if numByte > 4 {
                cli.Println("f", "Maximun 8 bytes of block write is allowed! Reveived request of ", numByte, "bytes")
                return errType.FAIL
            }
            for i:=0; uint64(i) < numByte; i++ {
                dataBuf[i] = byte((data >> (8*uint64(i))) & 0xFF)
            }
            byteCnt, err = smbus.WriteBlock(devName, regAddr, dataBuf)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to write block device", devName, "at", regAddr)
            } else {
                cli.Printf("i", "Write block device %s at addr 0x%x with %d bytes\n", devName, regAddr, byteCnt)
            }
        }
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func main() {
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
    flag.Parse()

    //cli.Println("devNamePtr:", *devNamePtr, "statusPtr:", *statusPtr, "marginPtr:", *marginPtr, "pctPtr:", *pctPtr)
    //cli.Println("i", *readPtr, *writePtr, *sendPtr, *addrPtr, *dataPtr)
    devName := strings.ToUpper(*devNamePtr)
    addr := *addrPtr
    data := *dataPtr
    mode := strings.ToUpper(*modePtr)
    numByte := *numBytePtr

    if *readPtr == true {
        readWriteSend("READ", devName, addr, uint16(data), mode)
        return
    }

    if *writePtr == true {
        readWriteSend("WRITE", devName, addr, uint16(data), mode)
        return
    }

    if *sendPtr == true {
        readWriteSend("SEND", devName, addr, uint16(data), mode)
        return
    }

    if *recvPtr == true {
        readWriteSend("RECEIVE", devName, addr, uint16(data), mode)
        return
    }

    if *readBlkPtr == true {
        readWriteBlk("READ_BLK", devName, addr, data, numByte)
        return
    }

    if *writeBlkPtr == true {
        readWriteBlk("WRITE_BLK", devName, addr, data, numByte)
        return
    }

    if *infoPtr == true {
        i2cinfo.DispI2cInfoAll()
        return
    }
}

