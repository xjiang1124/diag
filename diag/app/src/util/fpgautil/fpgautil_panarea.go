package main


import (
    "os"
    "fmt"
    "strconv"
    "common/cli"
    "platform/panarea"
    "device/fpga/panareafpga"
)

const errhelpPanarea = "\nfpgautil:\n" +
        "fpgautil regdump\n" + 
        "fpgautil r32 <addr>\n" +
        "fpgautil w32 <addr> <data>\n" +
        "\n" + 
        "fpgautil show fan" +
        "\n"


func panarea_fpga_cli() {
    
    var data32 uint32
    var data64, addr uint64
    var err error

    argc := len(os.Args[0:])

    if argc < 2 {
        fmt.Printf(" %s \n", errhelpPanarea)
        return
    }

    if os.Args[1] == "regdump" {
        panareafpga.FpgaDumpRegionRegisters()
        os.Exit(0)
    } else if os.Args[1] == "r32" || os.Args[1] == "w32" {
        if (os.Args[1] == "r32") && argc < 3  {
            fmt.Printf(" ERROR r32:  Not enough args\n")
            os.Exit(-1)
        }
        if (os.Args[2] == "w32") && argc < 4  {
            fmt.Printf(" ERROR w32:  Not enough args\n") 
            os.Exit(-1)
        }
        addr, err = strconv.ParseUint(os.Args[2], 0, 64)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }

        if (os.Args[1] == "r32") {
            data32, err = panareafpga.ReadU32(uint64(addr))
            if err != nil {
                cli.Printf("e", "MateraReadU32 Failed")
                os.Exit(-1)
            }
            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", addr, data32)
        } else {
            data64, err = strconv.ParseUint(os.Args[3], 0, 32)
            err = panareafpga.WriteU32(uint64(addr), uint32(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.08x\n", addr, uint32(data64))
        }
        os.Exit(0)
    } else if os.Args[1] == "show" {
        if os.Args[2][0] == 'f' || os.Args[2][0] == 'F' {
            panarea.ShowFanInfo()
        }
    } else {
        fmt.Printf("\n Incorrect Arg or Command used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelpPanarea)
        os.Exit(-1)
    }

    return
}

 
