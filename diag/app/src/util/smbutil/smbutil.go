package main

import (
    //"fmt"
    "flag"
    "strings"

    "common/cli"
    "common/errType"

    "hardware/i2cinfo"

    "protocol/smbus"
)

const(
    MDIO_ACC_ENA 		uint64 = 0x1
    MDIO_RD_ENA			uint64 = 0x2
    MDIO_WR_ENA			uint64 = 0x4
    
    MDIO_CRTL_LO_REG 	uint64 = 0x6
    MDIO_CRTL_HI_REG 	uint64 = 0x7
    MDIO_DATA_LO_REG 	uint64 = 0x8
    MDIO_DATA_HI_REG 	uint64 = 0x9
    
    SMI_CMD_REG			uint64 = 0x18
    SMI_DATA_REG		uint64 = 0x19
    SMI_PHY_ADDR		uint64 = 0x1C
    
    SMI_BUSY			uint64 = (1 << 15)
    SMI_MODE			uint64 = (1 << 12)
    SMI_READ			uint64 = (1 << 11)
    SMI_WRITE			uint64 = (1 << 10)
    DEV_BITS			uint64 = 5
)

func init() {
}

func readWriteSend(rws string, devName string, regAddr uint64, data uint16, mode string) (value uint16, err int) {
    var dataB byte

    mode = strings.ToUpper(mode)
    if (mode != "B" && mode != "W") {
        cli.Println("e", "Unsupported mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    for _, vrm := range(i2cinfo.CurI2cTbl) {
        if devName != vrm.Name {
            continue
        }
        switch rws {
        case "READ":
            if mode == "B" {
                dataB, err = smbus.ReadByte(devName, regAddr)
                value = uint16(dataB)
            } else {
                value, err = smbus.ReadWord(devName, regAddr)
                //cli.Printf("d", "data=0x%x\n", data)
            }
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device", devName, "at", regAddr)
            } else {
                cli.Printf("i", "Read device %s at addr 0x%x; data=0x%x\n", devName, regAddr, value)
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

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    for _, vrm := range(i2cinfo.CurI2cTbl) {
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
            if numByte > 8 {
                cli.Println("f", "Maximun 8 bytes of block write is allowed! Reveived request of ", numByte, "bytes")
                return errType.FAIL
            }
            for i:=0; uint64(i) < numByte; i++ {
                dataBuf[i] = byte((data >> (8*uint64(i))) & 0xFF)
                cli.Printf("d", "data[%d]=0x%x", i, dataBuf[i])
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

func readWriteMdio(rws string, phyAddr uint64, regAddr uint64, data uint16, mode string) (err int) {
    var dataL, dataH uint16

    switch rws {
        case "READ":
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_HI_REG, uint16(regAddr), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, uint16(phyAddr << 3 | MDIO_RD_ENA | MDIO_ACC_ENA), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, 0, mode)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to write device CPLD", "at", regAddr)
            }
            dataL, err = readWriteSend("READ", "CPLD", MDIO_DATA_LO_REG, 0, mode)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device CPLD", "at", regAddr)
            }
            dataH, err = readWriteSend("READ", "CPLD", MDIO_DATA_HI_REG, 0, mode)
            data = dataH << 8 | dataL
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device SWITCH", "at", regAddr)
            } else {
                cli.Printf("i", "Read device SWITCH at addr 0x%x; data=0x%x\n", regAddr, data)
            }
        case "WRITE":
            dataL = data & 0xFF
            dataH = (data >> 8) & 0xFF 
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_HI_REG, uint16(regAddr), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_LO_REG, uint16(dataL), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_HI_REG, uint16(dataH), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, uint16(phyAddr << 3 | MDIO_WR_ENA | MDIO_ACC_ENA), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, 0, mode)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to write device CPLD", "at", regAddr)
            }
    }
    return
}

func procCallBlk(devName string, regAddr uint64, data uint64, numByte uint64) (err int) {
    dataBuf := make([]byte, numByte)
    var byteCnt int
    var dataRet []byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    for _, vrm := range(i2cinfo.CurI2cTbl) {
        if devName != vrm.Name {
            continue
        }
        if numByte > 8 {
            cli.Println("f", "Maximun 8 bytes of block write is allowed! Reveived request of ", numByte, "bytes")
            return errType.FAIL
        }
        for i:=0; uint64(i) < numByte; i++ {
            dataBuf[i] = byte((data >> (8*uint64(i))) & 0xFF)
            cli.Printf("d", "data[%d]=0x%x", i, dataBuf[i])
        }
        dataRet, err = smbus.ProcessCall(devName, regAddr, dataBuf)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to write block device", devName, "at", regAddr)
        } else {
            cli.Printf("i", "Write block device %s at addr 0x%x with %d bytes\n", devName, regAddr, byteCnt)
        }
        for i:=0; i<len(dataRet); i++ {
            cli.Printf("i", "data[%d] = 0x%x\n", i, dataRet[i])
        }

        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func readWriteSmi(rws string, phyAddr uint64, regAddr uint64, data uint16, mode string) (err int) {
    var dataL, dataH uint16

    switch rws {
        case "READ":
            data = (uint16)(SMI_BUSY | SMI_MODE | SMI_READ | phyAddr << DEV_BITS | regAddr)
            dataL = data & 0xFF
            dataH = (data >> 8) & 0xFF 
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_HI_REG, uint16(SMI_CMD_REG), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_LO_REG, uint16(dataL), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_HI_REG, uint16(dataH), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, uint16(SMI_PHY_ADDR << 3 | MDIO_WR_ENA | MDIO_ACC_ENA), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, 0, mode)
            
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_HI_REG, uint16(SMI_DATA_REG), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, uint16(SMI_PHY_ADDR << 3 | MDIO_RD_ENA | MDIO_ACC_ENA), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, 0, mode)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to write device CPLD", "at", regAddr)
            }
            dataL, err = readWriteSend("READ", "CPLD", MDIO_DATA_LO_REG, 0, mode)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device CPLD", "at", regAddr)
            }
            dataH, err = readWriteSend("READ", "CPLD", MDIO_DATA_HI_REG, 0, mode)
            data = dataH << 8 | dataL
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device SWITCH", "at", regAddr)
            } else {
                cli.Printf("i", "Read device SWITCH at addr 0x%x; data=0x%x\n", regAddr, data)
            }
        case "WRITE":
            dataL = data & 0xFF
            dataH = (data >> 8) & 0xFF 
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_HI_REG, uint16(SMI_DATA_REG), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_LO_REG, uint16(dataL), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_HI_REG, uint16(dataH), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, uint16(SMI_PHY_ADDR << 3 | MDIO_WR_ENA | MDIO_ACC_ENA), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, 0, mode)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to write device CPLD", "at", regAddr)
            }
            
            data = (uint16)(SMI_BUSY | SMI_MODE | SMI_WRITE | phyAddr << DEV_BITS | regAddr)
            dataL = data & 0xFF
            dataH = (data >> 8) & 0xFF
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_HI_REG, uint16(SMI_CMD_REG), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_LO_REG, uint16(dataL), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_DATA_HI_REG, uint16(dataH), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, uint16(SMI_PHY_ADDR << 3 | MDIO_WR_ENA | MDIO_ACC_ENA), mode)
            _, err = readWriteSend("WRITE", "CPLD", MDIO_CRTL_LO_REG, 0, mode)
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
    readBlkPtr  := flag.Bool(  "rdb",  false, "Read register block value")
    writePtr    := flag.Bool(  "wr",   false, "Write register value")
    writeBlkPtr := flag.Bool(  "wrb",  false, "Write register block value")
    pcBlkPtr    := flag.Bool(  "pc",   false, "Process call")
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
                readWriteSmi("READ", phyAddr, addr, uint16(data), mode)
            } else {
                readWriteMdio("READ", phyAddr, addr, uint16(data), mode)
            }
        } else {
            readWriteSend("READ", devName, addr, uint16(data), mode)
        }
        return
    }

    if *writePtr == true {
        if devName == "SWITCH" {
            if *smiPtr == true {
                readWriteSmi("WRITE", phyAddr, addr, uint16(data), mode)
            } else {
                readWriteMdio("WRITE", phyAddr, addr, uint16(data), mode)
            }
        } else {
            readWriteSend("WRITE", devName, addr, uint16(data), mode)
        }
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

    if *pcBlkPtr == true {
        procCallBlk(devName, addr, data, numByte)
        return
    }

    if *infoPtr == true {
        i2cinfo.DispI2cInfoAll()
        return
    }

    myUsage()
}

