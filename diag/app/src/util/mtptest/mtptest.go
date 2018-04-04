package main

import (
    "flag"
    "strings"
)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
}

func main() {
    //var err int
    flag.Usage = myUsage

    psuPtr     := flag.Bool("psu",     false, "PSU test")
    psumaskPtr := flag.Int("psumask",     2, "PSU mask")
    fanPtr     := flag.Bool("fan",     false, "Fan test")
    fanSpdPtr  := flag.Bool("fanspd",     false, "Fan speed test")
    fantmpPtr  := flag.Bool("fantmp",     false, "Fan tempe sensor test")
    tmpmodePtr := flag.String("tmpmode",     "AMB", "Fan tempe mode")
    vrmPtr     := flag.Bool("vrm",     false, "VRM test")
    flag.Parse()

    tmpmode := strings.ToUpper(*tmpmodePtr)

    if *psuPtr == true {
        psuTest(*psumaskPtr)
        return
    }

    if *fanPtr == true {
        fanTest()
        return
    }

    if *fanSpdPtr == true {
        fanSpeedTest()
        return
    }

    if *fantmpPtr == true {
        fanTempTest(tmpmode)
        return
    }

    if *vrmPtr == true {
        vrmTest()
        return
    }

    myUsage()
}

