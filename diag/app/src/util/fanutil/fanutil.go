package main

import (
    //"device/fpga/taorfpga"
    "os"
    "fmt"
    "strconv"
    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "hardware/hwdev"
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
    devName, err := get_fan_device_name(int(data64))
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
        //"fanutil <fanctrl#> speed get <fan# / all>\n" +  
        if os.Args[3] == "all" {
            for i:=0; i<8; i++ {
                rpm[i], err =  hwdev.FanSpeedGet(devName, uint64(i)) 
                fmt.Printf(" Fan-%d   RPM = %d\n", i, rpm[i])
            }
        } else {
            data64, _ = strconv.ParseUint(os.Args[4], 0, 32)
            if data64 > 7 { fmt.Printf(" ERROR: Max fan number is 7\n"); return }
            rpm[data64], err =  hwdev.FanSpeedGet(devName, data64) 
            fmt.Printf(" Fan-%d   RPM = %d\n", data64, rpm[data64])
        }
    } else if os.Args[2] == "pwm" {
        var mask uint64
        if argc < 5  { fmt.Printf(" ERROR Not enough args\n"); return }
        pct, _ := strconv.ParseUint(os.Args[3], 0, 32)
        if os.Args[4] == "all" {
            if i2cinfo.CardType == "TAORMINA" {
                mask = 0x7
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

func get_fan_device_name(devNumber int) (device string, err int) {
    cardType := os.Getenv("CARD_TYPE")
    if cardType == "MTP" {
        device = "FAN"
    } else if cardType == "TAORMINA" {
        device = fmt.Sprintf("FAN_%d", devNumber+1)
    } else {
        cli.Printf("e", "INVALID CARD_TYPE.  Make sure card type is set in the environment\n")
        err = errType.FAIL
    }
    fmt.Printf("DEBUG:  Device=%s\n", device)
    return
}

 
