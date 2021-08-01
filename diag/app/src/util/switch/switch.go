package main

import (
    //"device/fpga/taorfpga"
    "os"
    "fmt"
    //"strconv"
    //"common/cli"
    //"common/errType"
    //"hardware/hwinfo"
    "platform/taormina"
)


const errhelp = "\ntor:\n" +
        "tor fantest\n" +
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
    }

    return
}


 
