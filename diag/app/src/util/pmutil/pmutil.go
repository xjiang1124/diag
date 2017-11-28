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

func main() {
    devNamePtr := flag.String("dev", "ALL", "Device name")
    statusPtr := flag.Bool("status", false, "Device status")
    infoPtr := flag.Bool("info", false, "VRM info")
    marginPtr := flag.Bool("margin", false, "Enable voltage marigining")
    pctPtr := flag.Int("pct", 0x0, "Margin percentage")
    flag.Parse()

    //cli.Println("devNamePtr:", *devNamePtr, "statusPtr:", *statusPtr, "marginPtr:", *marginPtr, "pctPtr:", *pctPtr)
    devName := strings.ToUpper(*devNamePtr)
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
}

