package main

import (
    //"device/fpga/taorfpga"
    "os"
    "fmt"
    "strconv"
    //"common/cli"
    //"common/errType"
    //"hardware/hwinfo"
    "device/bcm/td3"
    "platform/taormina"
)


const errhelp = "\ntor:\n" +
        "tor fantest\n" +
        "\n" +
        "td3 prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>\n" +
        "td3 snake <elbPortMask> <time> <phy/ext>\n" +
        "end\n"        
        

                               

func main() {
    argc := len(os.Args[0:])

    if argc < 2 {
        fmt.Printf(" %s \n", errhelp)
        return
    }
    if os.Args[1] == "fantest" {
        fmt.Printf(" FAN TEST\n")
        taormina.Fan_RPM_test(10)

        return
    } else if os.Args[1] == "td3" {  
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        if os.Args[2] == "prbs" {
            if argc < 4 { fmt.Printf(" Not enough args... prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>"); return; }
            time, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            td3.Prbs(int(time), os.Args[4])
        }
        if os.Args[2] == "snake" {
            if argc < 5 { fmt.Printf(" Not enough args..."); return; }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            duration, _ := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            td3.Snake_All_Ports(uint32(mask), uint32(duration), os.Args[5])
        }
        if os.Args[2] == "checkgb" {
            td3.CheckForRevA_Gearbox()
        }
        if os.Args[2] == "printvlan" {
            td3.PrintBCMShellVLANcmd()
        }
    }
    return
}


 
