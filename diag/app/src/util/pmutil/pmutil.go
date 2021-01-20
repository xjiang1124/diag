package main

import (
    //"fmt"
    "flag"
    "os"
    "strings"

    "common/cli"
    "common/errType"
    "device/powermodule/tps53659"
    "device/powermodule/tps53659a"
    "device/powermodule/tps549a20"
    "device/powermodule/tpsAll"

    "config"
    "hardware/i2cinfo"
)

type HwInfo struct {
    cardName string
    vrmTbl []i2cinfo.I2cInfo
}

var hwInfo HwInfo

func init() {
    var err int
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    cli.Init("log_"+procName+".txt", config.OutputMode)

    hwInfo.cardName = os.Getenv("CARD_TYPE")
    hwInfo.vrmTbl, err = i2cinfo.GetI2cTable(hwInfo.cardName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to initialize:", err)
    }
}

func devInfo(devName string) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A
    var tps549a20 tps549a20.TPS549A20

    for _, vrm := range(hwInfo.vrmTbl) {
        cli.Println("i", vrm.Name)
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        tps.Info(vrm.Name)
        return
    }
    cli.Println("e", "Faied to find device", devName)
}

func dispStatus(devName string) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A
    var tps549a20 tps549a20.TPS549A20

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        tps.DispStatus(vrm.Name)
        return
    }
    cli.Println("e", "Faied to find device", devName)
}

func dispStatusAll() {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A
    var tps549a20 tps549a20.TPS549A20

    for _, vrm := range(hwInfo.vrmTbl) {
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        tps.DispStatus(vrm.Name)
    }
}

func list() {
    cli.Println("i", "--------------------")
    cli.Printf("i", "%-15s %-10s %-5s %-5s", "Device", "Component", "Bus", "DevAddr")
    for _, vrm := range(hwInfo.vrmTbl) {
        cli.Printf("i", "%-15s %-10s %-5d 0x%X", vrm.Name, vrm.Comp, vrm.Bus, vrm.DevAddr)
    }
}

func margin(devName string, pct int) (err int){
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A
    var tps549a20 tps549a20.TPS549A20

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        err = tps.SetVMargin(vrm.Name, pct)
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func readWriteSend(rws string, devName string, regAddr uint64, data uint16, mode string) (err int) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A
    var tps549a20 tps549a20.TPS549A20
    var dataB byte

    mode = strings.ToUpper(mode)
    if (mode != "B" && mode != "W") {
        cli.Println("e", "Unsupported mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        switch rws {
        case "READ":
            if mode == "B" {
                dataB, err = tps.ReadByte(devName, regAddr)
                data = uint16(dataB)
            } else {
                data, err = tps.ReadWord(devName, regAddr)
                cli.Printf("d", "data=0x%x", data)
            }
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device", devName, "at", regAddr)
            } else {
                cli.Printf("i", "Read device %s at addr 0x%x; data=0x%x", devName, regAddr, data)
            }
        case "WRITE":
            if mode == "B" {
                err = tps.WriteByte(devName, regAddr, byte(data))
            } else {
                err = tps.WriteWord(devName, regAddr, data)
            }
            if err != errType.SUCCESS {
                cli.Printf("i", "Write device %s at addr 0x%x with data=0x%x failed: 0x%x", devName, regAddr, data, err)
            } else {
               cli.Printf("i", "Write device %s at addr 0x%x with data=0x%x - Done", devName, regAddr, data)
            }
        case "SEND":
            err = tps.SendByte(devName, byte(regAddr))
        }
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func readWriteBlk(rws string, devName string, regAddr uint64, data uint64) (err int) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A
    var byteCnt int
    dataLen := 6
    dataBuf := make([]byte, dataLen)

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else {
            continue
        }
        switch rws {
        case "READ_BLK":
            byteCnt, err = tps.ReadBlock(devName, regAddr, dataBuf)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read block device", devName, "at", regAddr)
            } else {
                cli.Printf("i", "Read block device %s at addr 0x%x with %d bytes", devName, regAddr, byteCnt)
                cli.Printf("i", "0x%x", dataBuf)
                for i:=0; i<len(dataBuf); i++ {
                    cli.Printf("i", "data[%d] = 0x%x", i, dataBuf[i])
                }
            }
        case "WRITE_BLK":
            byteCnt, err = tps.WriteBlock(devName, regAddr, dataBuf)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to write block device", devName, "at", regAddr)
            } else {
                cli.Printf("i", "Write block device %s at addr 0x%x with %d bytes", devName, regAddr, byteCnt)
            }
        }
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func program (devName string, fileName string, verbose bool) (err int) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else {
            continue
        }
        err = tps.ProgramVerifyNvm(devName, fileName, "PROGRAM", verbose)
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func verify (devName string, fileName string, verbose bool) (err int) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps53659a tps53659a.TPS53659A

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS53659A" {
            tps = &tps53659a
        } else {
            continue
        }
        err = tps.ProgramVerifyNvm(devName, fileName, "VERIFY", verbose)
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func main() {
    devNamePtr := flag.String("dev", "ALL", "Device name")
    statusPtr := flag.Bool("status", false, "Device status")
    listPtr := flag.Bool("list", false, "VRM list")
    infoPtr := flag.Bool("info", false, "Device info")
    marginPtr := flag.Bool("margin", false, "Enable voltage marigining")
    pctPtr := flag.Int("pct", 0x0, "Margin percentage")
    readPtr := flag.Bool("rd", false, "Read register value")
    readBlkPtr := flag.Bool("rdb", false, "Read register block value")
    writePtr := flag.Bool("wr", false, "Write register value")
    writeBlkPtr := flag.Bool("wrb", false, "Write register block value")
    sendPtr := flag.Bool("sd", false, "Send byte")
    modePtr := flag.String("mode", "b", "r/w mode: byte(b) or word(w)")
    addrPtr := flag.Uint64("addr", 0, "Register addr")
    dataPtr := flag.Uint64("data", 0, "Data value")
    programPtr := flag.Bool("program", false, "Program with specified file")
    verifyPtr := flag.Bool("verify", false, "Verify NVM content with specified file")
    filePtr := flag.String("file", "", "/path/to/image.file")
    verbosePtr := flag.Bool("verbose", false, "Verbose")
    flag.Parse()

    //cli.Println("devNamePtr:", *devNamePtr, "statusPtr:", *statusPtr, "marginPtr:", *marginPtr, "pctPtr:", *pctPtr)
    //cli.Println("i", *readPtr, *writePtr, *sendPtr, *addrPtr, *dataPtr)
    devName := strings.ToUpper(*devNamePtr)
    addr := *addrPtr
    data := *dataPtr
    mode := strings.ToUpper(*modePtr)
    pct := *pctPtr
    verbose := *verbosePtr
    if *statusPtr == true {
        if *devNamePtr == "ALL" {
            dispStatusAll()
            return
        } else {
            dispStatus(devName)
            return
        }
    }

    if *marginPtr == true {
        err := margin(devName, pct)
        if err != errType.SUCCESS {
            cli.Println("e", "Voltage margin failed!")
        } else {
            dispStatus(devName)
            cli.Println("i", "Voltage margin set at", pct, "percent")
        }
        return
    }

    if *listPtr == true {
        list()
        return
    }

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

    if *readBlkPtr == true {
        readWriteBlk("READ_BLK", devName, addr, data)
        return
    }

    if *writeBlkPtr == true {
        readWriteBlk("WRITE_BLK", devName, addr, data)
        return
    }

    if *programPtr == true {
        program(devName, *filePtr, verbose)
    }

    if *verifyPtr == true {
        verify(devName, *filePtr, verbose)
    }

    if *infoPtr == true {
        devInfo(devName)
    }

}

