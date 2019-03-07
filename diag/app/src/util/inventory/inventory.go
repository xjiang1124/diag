package main

import (
    "fmt"
    "flag"
    "os"
    "strconv"

    "common/cli"
    "common/errType"
    "device/cpld/naples100Cpld"
    "device/cpld/naples25Cpld"
    "device/cpld/naplesMtpCpld"
//    "device/cpld/mtpCpld"
    "hardware/hwdev"
)

var powerStatName = []string{"capri vdd", "capri avdd", "capri vdd arm", "capri vdd hbm", "capri emmc", 
                            "nic p1v8", "nic p2v5", "efuse p2v5", "nic p3v3", "nic p5v0", "p12v", "pwr ok"} 
func init() {
}

func uutPresent(uutName string) (data byte, present bool) {
    devName := "CPLD"
    addr := uint64(naples100Cpld.REG_ID)

    cli.DisableVerbose()
    data, err := hwdev.NaplesCpldRd(devName, addr, uutName)
    if err != errType.SUCCESS {
        present = false
    } else {
        present = true
    }
    cli.EnableVerbose()

    return
}

func present() (err int) {
    var presentStr string

    maxUut := 10
//    prsntNoneStr := "UUT_NONE"
    for i := 1; i <= maxUut; i++ {
        uutName := "UUT_"+strconv.Itoa(i)
        data, present := uutPresent(uutName)

        if present == true {
            switch data {
            case naples100Cpld.ID:
                presentStr = "NAPLES100"
            case naples25Cpld.ID:
                presentStr = "NAPLES25"
            case naplesMtpCpld.ID:
                presentStr = "NAPLES_MTP"
            default:
                presentStr = "Unknown"
            }
        }
//        else {
//            cli.DisableVerbose()
//            var inst uint
//            if(i > 5) {
//                inst = 1
//            } else {
//                inst = 0
//            }
//            pcs, _ := mtpCpld.MvlRead(inst, uint((i-1)%5 + 0x10), 0x1)
//            if ((pcs & 0xC000) > 0) && (pcs != 0xffff){
//                presentStr = "PRESENT"
//            } else {
//                presentStr = prsntNoneStr
//            }
//            cli.EnableVerbose()
//        }

        cli.Printf("i", "UUT_%-15d     %s\n", i, presentStr)
    }
    return
}

func powerStatusCheck(slot int)  {
    devName := "CPLD"
    addr := uint64(naples100Cpld.REG_ID)
    uutName := "UUT_"+strconv.Itoa(slot)
    var powerGood bool
    
    cli.DisableVerbose()
    _, err := hwdev.NaplesCpldRd(devName, addr, uutName)
    if err != errType.SUCCESS {
        powerGood = false
    } else {
        powerGood = true
    }
    cli.EnableVerbose()
    
    if powerGood {
        cli.Printf("i", "UUT_%-15d     power good\n", slot)
    } else {
        cli.Printf("i", "UUT_%-15d     power failure\n", slot)
    }

    return   
}

func sysDetect() (err int) {
    var presentStr string
    var fmtStr string = "export UUT_%d=\"%s\"\n"

    file, err1 := os.Create("/home/diag/diag/log/board_env.txt")
    if err1 != nil {
        cli.Println("e", "Cannot create file", err)
    }
    defer file.Close()

    maxUut := 10
    prsntNoneStr := "UUT_NONE"
    for i := 1; i <= maxUut; i++ {
        uutName := "UUT_"+strconv.Itoa(i)
        data, present := uutPresent(uutName)

        if present == true {
            switch data {
            case naples100Cpld.ID:
                presentStr = "NAPLES100"
            case naples25Cpld.ID:
                presentStr = "NAPLES25"
            case naplesMtpCpld.ID:
                presentStr = "NAPLES_MTP"
            default:
                presentStr = "Unknown"
            }
        } else {
            presentStr = prsntNoneStr
        }
        fmt.Fprintf(file, fmtStr, i, presentStr)
    }
    return
}

func powerStatusDump(slot int)  {
    devName := "CPLD"
    uutName := "UUT_"+strconv.Itoa(slot)

    cli.DisableVerbose()
    stat0, _ := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_POWER_STAT0), uutName)
    stat1, _ := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_POWER_STAT1), uutName)
    cli.EnableVerbose()
    
    for i := 0; i < 12; i++ {
        if(i < 8) {
            cli.Printf("i","%-15s%d\n", powerStatName[i], (stat0 >> uint(i)) & 1)
        } else {
            cli.Printf("i","%-15s%d\n", powerStatName[i], (stat1 >> uint(i - 8)) & 1)
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

    presentPtr  := flag.Bool("present", false, "Show UUT present status")
    envPtr  	:= flag.Bool("env", false, "Detect/set environment")
    psPtr  		:= flag.Bool("ps", false, "Power Status")
    slotPtr  	:= flag.Int("slot", 0, "Slot Number")
    powDumpPtr  := flag.Bool("pw", false, "Power state dump")
    
    flag.Parse()
    
    slot := *slotPtr

    if *presentPtr == true {
        present()
        return
    }

    if *envPtr == true {
        sysDetect()
        return
    }
    
    if *psPtr == true {
        powerStatusCheck(slot)
        return
    }
    
    if *powDumpPtr == true {
        powerStatusDump(slot)
        return
    }

    myUsage()
}

