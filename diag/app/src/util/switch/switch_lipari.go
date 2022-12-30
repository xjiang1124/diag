package main

import (
    "os"
    "fmt"
    "strconv"
    //"strings"
    //"common/cli"
    "common/errType"
    "platform/taormina"
)


const errhelpLipari = "\nswitch:\n" +
        "switch cpu memtest <# test threads> <percent of mem to test 1-100> <time>\n" +
        "\n"
        

                               

func lipari_cli() {
    argc := len(os.Args[0:])

    if argc < 2 {
        fmt.Printf(" %s \n", errhelpLipari)
        return
    }

    if os.Args[1] == "cpu" {
        if os.Args[2][0] == 'm' || os.Args[2][0] == 'M' {  //memtest
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpLipari)
                os.Exit(-1)
            }
            threads, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            percent, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            if percent > 100 {
                fmt.Printf(" Percent of memory to test cannot be more than 100%.  You entered %d percent\n", percent); os.Exit(-1)
            }
            time, err := strconv.ParseUint(os.Args[5], 0, 32)
            if err != nil {
                fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            rc := taormina.X86_CPU_MemoryTest(uint32(threads), uint32(percent), uint32(time), 1) 
            if rc != errType.SUCCESS {
                os.Exit(-1)
            } else { 
                os.Exit(0)
            }
        }
    }
    return
}



 
