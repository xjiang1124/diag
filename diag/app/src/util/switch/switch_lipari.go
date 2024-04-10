package main

import (
    "os"
    "fmt"
    "strconv"
    //"strings"
    //"common/cli"
    "common/errType"
    "platform/lipari"
    "platform/matera"
)


const errhelpLipari = "\nswitch:\n" +
        "switch test fan\n" +
        "switch cpu memtest <# test threads> <percent of mem to test 1-100> <time>\n" +
        "switch show <power/temperature/fans>\n" +
        "switch margin <name> <pct>\n" +
        "\n"
                             

func lipari_switch_cli() {
    argc := len(os.Args[0:])
    rc := 0

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
            rc := lipari.X86_CPU_MemoryTest(uint32(threads), uint32(percent), uint32(time), 1) 
            if rc != errType.SUCCESS {
                os.Exit(-1)
            } else { 
                os.Exit(0)
            }
        }
    } else if os.Args[1] == "test" {
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        if os.Args[2] == "fan" {
            fmt.Printf(" FAN TEST\n")
            rc := lipari.Fan_RPM_test(10)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
            rc = matera.Fan_RPM_test(10)
        }
    } else if os.Args[1] == "show" {
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        if os.Args[2][0] == 'p' || os.Args[2][0] == 'P' {    //power
            rc = lipari.ShowPower()
        } else if os.Args[2][0] == 't' || os.Args[2][0] == 'T' {    //temperature
            rc = lipari.ShowTemperature()
        } else if os.Args[2][0] == 'f' || os.Args[2][0] == 'F' {    //fans
            rc = lipari.ShowFanSpeed()
        } else {
            fmt.Printf(" Bad ARG--> ARGV[2]=%s\n", os.Args[2])
            rc = errType.FAIL
        }
        if rc != errType.SUCCESS {
            os.Exit(-1)
        } else { 
            os.Exit(0)
        }
    } else if os.Args[1] == "margin" {
        if argc < 4 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        //os.Args[2]  == name
        percent, err := strconv.ParseInt(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
        }

        fmt.Printf(" Margin %s %d\n", os.Args[2], percent)
        rc = lipari.Margin(os.Args[2], int(percent))
        if rc != errType.SUCCESS {
            os.Exit(-1)
        } else { 
            os.Exit(0)
        }
    }

    return
}



 
