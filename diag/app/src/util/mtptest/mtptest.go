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

    psuPtr		:= flag.Bool("psu",     false, "PSU test")
    psumaskPtr	:= flag.Uint("psumask",     3, "PSU mask")
    fanPtr		:= flag.Bool("fan",     false, "Fan test")
    fanSpdPtr	:= flag.Bool("fanspd",     false, "Fan speed test")
    fanAltPtr	:= flag.Bool("fanalt",     false, "Fan alert test")
    fantmpPtr	:= flag.Bool("fantmp",     false, "Fan tempe sensor test")
    tmpmodePtr	:= flag.String("tmpmode",     "AMB", "Fan tempe mode")
    vrmPtr		:= flag.Bool("vrm",     false, "VRM test")
    stsPtr		:= flag.Bool("sts",     false, "Status check")
    mvlIntPtr	:= flag.Bool("mvl",		false, "Marvell switch interrupt test")
    wdtIntPtr	:= flag.Bool("wdt",		false, "Watch dog interrupt test")
    uutPowPtr	:= flag.Bool("uut",		false, "UUT power test")
    peRstPtr	:= flag.Bool("perst",	false, "UUT pe reset test")
    pcsPtr		:= flag.Bool("pcs",		false, "SGMII PCS sync test")
    uutIndexPtr := flag.Uint("index",	0,		"UUT index, zero based")
    flag.Parse()

    tmpmode := strings.ToUpper(*tmpmodePtr)
    index	:= *uutIndexPtr

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

    if *fanAltPtr == true {
        fanAlertTest()
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

    if *stsPtr == true {
        stsCheck(*psumaskPtr)
        return
    }

    if *mvlIntPtr == true {
        mvlIntTest()
        return
    }

    if *wdtIntPtr == true {
        wdtIntTest()
        return
    }

    if *uutPowPtr == true {
        uutPowTest(*psumaskPtr)
        return
    }

    if *peRstPtr == true {
        peRstTest(*psumaskPtr)
        return
    }

    if *pcsPtr == true {
        pcsTest(index)
        return
    }

    myUsage()
}

