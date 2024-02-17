package main


import (
    "os"
    "fmt"
    "strconv"
    //"time"
    "common/cli"
    //"unsafe"
    "device/fpga/materafpga"
)

const errhelpMatera = "\nfpgautil:\n" +
        "<fpga#> will be 0 or 1\n" +
        "fpgautil regdump <fgpa#>\n" + 
        "fpgautil r32 <fgpa#> <addr>\n" +
        "fpgautil w32 <fgpa#> <addr> <data>\n"
        

                               

func matera_fpga_cli() {
    
    var data32 uint32
    var data64, addr, bar uint64
    //var err error
    //var i int = 0

    argc := len(os.Args[0:])

    if argc < 3 {
        fmt.Printf(" %s \n", errhelpMatera)
        return
    }

    if os.Args[1] == "regdump" {
        materafpga.FpgaDumpRegionRegisters()
        os.Exit(0)
    } else if os.Args[1] == "r32" || os.Args[1] == "w32" {
        if (os.Args[1] == "r32") && argc < 4  {
            if argc < 4 {
                fmt.Printf(" ERROR r32:  Not enough args\n")
                os.Exit(-1)
            }
        }
        if (os.Args[2] == "w32") && argc < 5  {
            if argc < 4 {
                fmt.Printf(" ERROR w32:  Not enough args\n") 
                os.Exit(-1)
            }
        }
        fpga_number, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        addr, err = strconv.ParseUint(os.Args[3], 0, 64)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }

        if (os.Args[1] == "r32") {
            data32, err = materafpga.LipariReadU32(uint32(fpga_number) , uint64(bar + addr))
            if err != nil {
                cli.Printf("e", "LipariReadU32 Failed")
                os.Exit(-1)
            }
            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", bar + addr, data32)
        } else {
            data64, err = strconv.ParseUint(os.Args[4], 0, 32)
            err = materafpga.LipariWriteU32(uint32(fpga_number), uint64(bar + addr), uint32(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.08x\n", bar + addr, uint32(data64))
        }
        os.Exit(0)
    } else {
        fmt.Printf("\n Incorrect Arg or Command used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelpMatera)
        os.Exit(-1)
    }

    return
}

 
