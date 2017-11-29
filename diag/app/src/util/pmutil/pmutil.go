package main

import (
    //"fmt"
    "flag"
    "os"
    "strings"

    "common/cli"
    "common/errType"
    "common/powermodule/tps53659"
    "common/powermodule/tps549a20"
    "common/powermodule/tpsAll"

    "config"
    "hardware/hwvrm"
)

type HwInfo struct {
    cardName string
    vrmTbl []hwvrm.VrmInfo
}

var hwInfo HwInfo

func init() {
    var err int
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    cli.Init("log_"+procName+".txt", config.OutputMode)

    hwInfo.cardName = os.Getenv("CARD_NAME")
    hwInfo.vrmTbl, err = hwvrm.GetVrmTable(hwInfo.cardName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to initialize:", err)
    }
}

func dispStatus(devName string) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps549a20 tps549a20.TPS549A20

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
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
    var tps549a20 tps549a20.TPS549A20

    for _, vrm := range(hwInfo.vrmTbl) {
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        tps.DispStatus(vrm.Name)
    }
}

func info() {
    cli.Println("i", "--------------------")
    cli.Printf("i", "%-15s %-10s %-5s %-5s", "Device", "Component", "Bus", "DevAddr")
    for _, vrm := range(hwInfo.vrmTbl) {
        cli.Printf("i", "%-15s %-10s %-5d 0x%X", vrm.Name, vrm.Comp, vrm.Bus, vrm.DevAddr)
    }
}

func margin(devName string, pct int) (err int){
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps549a20 tps549a20.TPS549A20

    for _, vrm := range(hwInfo.vrmTbl) {
        if devName != vrm.Name {
            continue
        }
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
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

func read(devName string, regAddr uint64, mode string) (err int) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps549a20 tps549a20.TPS549A20
    var data uint16
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
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        if mode == "B" {
            dataB, err = tps.ReadByte(devName, regAddr)
            data = uint16(dataB)
            cli.Printf("d", "data=0x%x", data)
        } else {
            data, err = tps.ReadWord(devName, regAddr)
            cli.Printf("d", "data=0x%x", data)
        }
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to read device", devName, "at", regAddr)
            return
        }
        cli.Printf("i", "Read device %s at addr 0x%d; data=0x%x", devName, regAddr, data)
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func write(devName string, regAddr uint64, data uint16, mode string) (err int) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps549a20 tps549a20.TPS549A20

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
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        if mode == "B" {
            err = tps.WriteByte(devName, regAddr, byte(data))
        } else {
            err = tps.WriteWord(devName, regAddr, data)
        }
        if err != errType.SUCCESS {
            cli.Printf("i", "Write device %s at addr 0x%d with data=0x%x failed: 0x%x", devName, regAddr, data, err)
        } else {
           cli.Printf("i", "Write device %s at addr 0x%d with data=0x%x - Done", devName, regAddr, data)
        }
        return
    }
    cli.Println("e", "Faied to find device", devName)
    err = errType.INVALID_PARAM
    return
}

func readWriteSend(rws string, devName string, regAddr uint64, data uint16, mode string) (err int) {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
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

func main() {
    devNamePtr := flag.String("dev", "ALL", "Device name")
    statusPtr := flag.Bool("status", false, "Device status")
    infoPtr := flag.Bool("info", false, "VRM info")
    marginPtr := flag.Bool("margin", false, "Enable voltage marigining")
    pctPtr := flag.Int("pct", 0x0, "Margin percentage")
    readPtr := flag.Bool("rd", false, "Read register value")
    writePtr := flag.Bool("wr", false, "Write register value")
    sendPtr := flag.Bool("sd", false, "Send byte")
    modePtr := flag.String("mode", "b", "r/w mode: byte(b) or word(w)")
    addrPtr := flag.Uint64("addr", 0, "Register addr")
    dataPtr := flag.Int("data", 0, "Data value")
    flag.Parse()

    //cli.Println("devNamePtr:", *devNamePtr, "statusPtr:", *statusPtr, "marginPtr:", *marginPtr, "pctPtr:", *pctPtr)
    //cli.Println("i", *readPtr, *writePtr, *sendPtr, *addrPtr, *dataPtr)
    devName := strings.ToUpper(*devNamePtr)
    addr := *addrPtr
    data := uint16(*dataPtr)
    mode := strings.ToUpper(*modePtr)
    pct := *pctPtr
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

    if *infoPtr == true {
        info()
        return
    }

    if *readPtr == true {
        readWriteSend("READ", devName, addr, data, mode)
        return
    }

    if *writePtr == true {
        readWriteSend("WRITE", devName, addr, data, mode)
        return
    }

    if *sendPtr == true {
        readWriteSend("SEND", devName, addr, data, mode)
        return
    }

}

