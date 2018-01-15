package main

import (
    "fmt"
    //"log"
    "flag"

    //"common/cli"
    //"common/misc"
    "common/powermodule/tps53659"
    //"common/powermodule/tps549a20"
    //"protocol/smbus"

)

func main() {

    devNamePtr := flag.String("devname", "VRM_DVDD", "Device name")
    cmdPtr := flag.Int("cmd", 0x98, "Cmd")
    dataPtr := flag.Int("data", 0x1, "Data")
    pctPtr := flag.Int("pct", 0x0, "Margin pct")
    flag.Parse()

    fmt.Printf("devName: %s, cmd: 0x%x, data: 0x%x, pct: %d\n", *devNamePtr, *cmdPtr, *dataPtr, *pctPtr)

    var vrm *tps53659.TPS53659
    var devName string
    devName = "VRM_CAPRI_DVDD"

    if *pctPtr == 23 {
        vrm.DispStatus(devName)
        return
    }

    //vrm.DispStatus(devName)
    //vrm.SetVMargin(devName, *pctPtr)
    vrm.DispStatus(devName)
    vrm.SetVMargin(devName, *pctPtr)
    vrm.DispStatus(devName)

    //var vrm *tps549a20.TPS549A20
    //var devName string
    //devName = "VRM_3V3"

    //vrm.SetVMargin(devName, *pctPtr)
    //vrm.DispStatus(devName)

}


