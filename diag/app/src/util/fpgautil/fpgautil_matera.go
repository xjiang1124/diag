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
        "fpgautil w32 <fgpa#> <addr> <data>\n" +
        "fpgautil mdiord <inst#> <phy> <addr>\n" +
        "fpgautil mdiowr <inst#> <phy> <addr> <data>\n" +
        "fpgautil mvldump <inst#>\n"
        

                               

func matera_fpga_cli() {
    
    var data32 uint32
    var data64, addr, bar uint64
    var err error
    var inst, phy uint64
    var data16 uint16
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
        if (os.Args[1] == "r32") && argc < 3  {
            if argc < 4 {
                fmt.Printf(" ERROR r32:  Not enough args\n")
                os.Exit(-1)
            }
        }
        if (os.Args[2] == "w32") && argc < 4  {
            if argc < 4 {
                fmt.Printf(" ERROR w32:  Not enough args\n") 
                os.Exit(-1)
            }
        }
        addr, err = strconv.ParseUint(os.Args[2], 0, 64)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }

        if (os.Args[1] == "r32") {
            data32, err = materafpga.MateraReadU32(uint64(bar + addr))
            if err != nil {
                cli.Printf("e", "LipariReadU32 Failed")
                os.Exit(-1)
            }
            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", bar + addr, data32)
        } else {
            data64, err = strconv.ParseUint(os.Args[3], 0, 32)
            err = materafpga.MateraWriteU32(uint64(bar + addr), uint32(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.08x\n", bar + addr, uint32(data64))
        }
        os.Exit(0)
    } else if os.Args[1] == "mdiord" || os.Args[1] == "mdiowr" {
        if (os.Args[1] == "mdiord") && argc < 5  {
            if argc < 5 {
                fmt.Printf(" ERROR mdiord:  Not enough args\n")
                os.Exit(-1)
            }
        }
        if (os.Args[1] == "mdiowr") && argc < 6  {
            if argc < 6 {
                fmt.Printf(" ERROR mdiowr:  Not enough args\n") 
                os.Exit(-1)
            }
        }
        inst, err = strconv.ParseUint(os.Args[2], 0, 8)
        if err != nil {
            fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        phy, err = strconv.ParseUint(os.Args[3], 0, 8)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        addr, err = strconv.ParseUint(os.Args[4], 0, 8)
        if err != nil {
            fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        if (os.Args[1] == "mdiord") {
            data16, err = materafpga.MdioRead(uint8(inst), uint8(phy), uint8(addr))
            if err != nil {
                cli.Printf("e", "MdioRead Failed")
                os.Exit(-1)
            }
            fmt.Printf("RD [0x%.02x] = 0x%.04x\n", addr, data16)
        } else {
            data64, err = strconv.ParseUint(os.Args[5], 0, 16)
            err = materafpga.MdioWrite(uint8(inst), uint8(phy), uint8(addr), uint16(data64))
            if err != nil {
                cli.Printf("e", "MdioWrite Failed")
                os.Exit(-1)
            }
            fmt.Printf("WR [0x%.02x] = 0x%.04x\n", addr, uint16(data64))
        }
        os.Exit(0)
    } else if os.Args[1] == "mvldump" {
        materafpga.MvlDump(uint8(inst))
    } else {
        fmt.Printf("\n Incorrect Arg or Command used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelpMatera)
        os.Exit(-1)
    }

    return
}

 
