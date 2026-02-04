package main

import (
    "os"
    "fmt"
    "strconv"
    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "hardware/hwdev"
    "device/fpga/liparifpga"
    "device/fpga/materafpga"
    "device/fpga/panareafpga"
)


const errhelp = "\nfanutil:\n" +
        "** <fanctrl#> is 0 or 1 for Taormina\n" +
        "fanutil <fanctrl#> dumpreg\n" +
        "fanutil <fanctrl#> r addr>\n" +
        "fanutil <fanctrl#> w <addr> <data>\n" +
        "fanutil <fanctrl#> setup\n" +
        "fanutil <fanctrl#> pwm <percent> <fan# / all>\n" +
        "fanutil <fanctrl#> speed <fan# / all>\n"        
        

                               

func main() {
    argc := len(os.Args[0:])

    if argc < 3 {
        fmt.Printf(" %s \n", errhelp)
        return
    }

    //Get the fan controller number
    data64, _ := strconv.ParseUint(os.Args[1], 0, 32)
    devName, err := hwdev.FanGetDeviceName(int(data64))
    if err != errType.SUCCESS {
        cli.Printf("e", "Check Your fan device Number.  Exiting CLI\n") 
        return
    } 

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        cli.Printf("e", "Hub/Mux Enable Failed\n") 
        return
    }

    if os.Args[2] == "dumpreg" {
        hwdev.FanDumpReg(devName)
        return
    } else if os.Args[2] == "setup" {
        hwdev.FanSetup(devName)
        return
    } else if os.Args[2] == "r" || os.Args[2] == "w" {
        if (os.Args[2] == "r") && argc < 4  {
            fmt.Printf(" ERROR Not enough args\n"); return
        }
        if (os.Args[2] == "w") && argc < 5  {
                fmt.Printf(" ERROR w:  Not enough args\n"); return
        }
        addr, err := strconv.ParseUint(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }

        if (os.Args[2] == "r") {
            data, _ := hwdev.FanReadReg(devName, uint32(addr))
            fmt.Printf("RD [0x%.04x] = 0x%.02x\n", addr, data)
        } else {
            data64, err = strconv.ParseUint(os.Args[4], 0, 32)
            hwdev.FanWriteReg(devName, uint32(addr), byte(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.02x\n", addr, uint32(data64))
        }

    } else if os.Args[2] == "speed" {
        var rpm [8]uint64
        var rpm2 [8]uint64
        var maxfan int = 8  //number of fan modules
        var daulfan int = 0 //flag to indicate two fans per module

        if i2cinfo.CardType == "LIPARI" {
            maxfan = liparifpga.MAXFAN
            daulfan = liparifpga.DUALFAN
        } else if i2cinfo.CardType == "MTP_MATERA" {
            maxfan = materafpga.MAXFAN
            daulfan = materafpga.DUALFAN
        } else if i2cinfo.CardType == "MTP_PANAREA" {
            maxfan = panareafpga.MAXFAN
            daulfan = panareafpga.DUALFAN
        } else if i2cinfo.CardType == "MTP_PONZA" {
            maxfan = panareafpga.PONZA_MAXFAN
            daulfan = panareafpga.DUALFAN
        }

        if os.Args[3] == "all" {
            for i:=0; i<maxfan; i++ {
                rpm[i], rpm2[i], err =  hwdev.FanSpeedGet(devName, uint64(i)) 
                if daulfan == 0 {
                    fmt.Printf(" Fan-%d   RPM = %d\n", i, rpm[i])
                } else {
                    fmt.Printf(" Fan-%d   RPM Inner = %d  Outer = %d\n", i, rpm[i], rpm2[i])
                }
            }
        } else {
            data64, _ = strconv.ParseUint(os.Args[4], 0, 32)
            if data64 > 7 { fmt.Printf(" ERROR: Max fan number is 7\n"); return }
            rpm[data64], rpm2[data64], err =  hwdev.FanSpeedGet(devName, data64) 
            if daulfan == 0 {
                fmt.Printf(" Fan-%d   RPM = %d\n", data64, rpm[data64])
            } else {
                fmt.Printf(" Fan-%d   RPM Inner = %d  Outer = %d\n", data64, rpm[data64], rpm2[data64])
            }
            
        }
    } else if os.Args[2] == "pwm" {
        var mask uint64
        if argc < 5  { fmt.Printf(" ERROR Not enough args\n"); return }
        pct, _ := strconv.ParseUint(os.Args[3], 0, 32)
        if os.Args[4] == "all" {
            if i2cinfo.CardType == "TAORMINA" {
                mask = 0x7
            } else if i2cinfo.CardType == "LIPARI" {
                mask = 0xF
            } else if i2cinfo.CardType == "MTP_MATERA" || i2cinfo.CardType == "MTP_PANAREA" || i2cinfo.CardType == "MTP_PONZA" {
                mask = 0x1F
            } else {
                mask = 0xFF
            }
        } else {
            shift, _ := strconv.ParseUint(os.Args[4], 0, 32)
            mask = (1<<shift)
        }
        fmt.Printf("Set speed pct=%d, mask=%x\n", pct, mask)
        hwdev.FanSpeedSet(devName, int(pct), mask)
    } else {
        fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelp)
        return
    }

    return
}



 
