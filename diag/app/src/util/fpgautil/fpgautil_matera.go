package main


import (
    "os"
    "fmt"
    "strconv"
    "time"
    "common/cli"
    //"unsafe"
    "device/fpga/materafpga"
    "platform/matera"
)

const errhelpMatera = "\nfpgautil:\n" +
        "fpgautil regdump\n" + 
        "fpgautil r32 <addr>\n" +
        "fpgautil w32 <addr> <data>\n" +
        "\n" +
        "fpgautil flash help  << Display debug commands in the CLI >>\n" +
        "fpgautil flash program/verify/generate <primary/secondary/allflash> <filename>\n" +
        "\n" +
        "fpgautil show fan\n" +
        "\n" +
        "fpgautil mdiord <inst#> <phy> <addr>\n" +
        "fpgautil mdiowr <inst#> <phy> <addr> <data>\n" +
        "fpgautil mvldump <inst#> <port#>, use port#=-1 to dump all ports\n" +
        "fpgautil mvlclear <inst#>\n"
        

                               

func matera_fpga_cli() {
    
    var data32 uint32
    var data64, addr, bar uint64
    var err error
    var inst, phy uint64
    var port int64
    var data16 uint16
    //var i int = 0

    argc := len(os.Args[0:])

    if argc < 2 {
        fmt.Printf(" %s \n", errhelpMatera)
        return
    }

    if os.Args[1] == "regdump" {
        materafpga.FpgaDumpRegionRegisters()
        os.Exit(0)
    } else if os.Args[1] == "show" {
        if os.Args[2][0] == 'f' || os.Args[2][0] == 'F' {
            matera.ShowFanInfo()
        }
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
    //
    //FPGA Local Flash commands 
    //
    } else if os.Args[1] == "flash" {
        var flashID uint32 = materafpga.SPI_FPGA
        const errhelpMateraFlash = "\nfpgautil:\n" +
        "fpgautil flash devid/readsr/writesr <data>\n" +
        "fpgautil flash read <addr> <length>\n" +
        "fpgautil flash w32 <addr> <data>\n" +
        "fpgautil flash flash sectorerase <addr>/all\n" +
        "fpgautil flash program/verify/generate <primary/secondary/allflash> <filename>\n" 

        if argc < 2 {
            fmt.Printf(" %s \n", errhelpMatera)
            os.Exit(-1)
        }

        if os.Args[2][0] == 'h' ||  os.Args[2][0] == 'H' {
            fmt.Printf(" %s \n", errhelpMateraFlash)
            os.Exit(-1)
        }

        if os.Args[2] == "devid" {
            value, _ := materafpga.Spi_flash_read_id(flashID) 
            fmt.Printf(" FLASH DEV ID=%.08x\n", value)
        } else if os.Args[2] == "we" {
            materafpga.Spi_flash_WriteEnable(flashID)
            materafpga.Spi_flash_CheckWriteEnable(flashID)
        } else if os.Args[2] == "readsr" {
            rd32, _  := materafpga.Spi_flash_read_status_register(flashID)
            fmt.Printf(" SR=%.02x\n", rd32 & 0xFF)
        } else if os.Args[2] == "writesr" {
            wr32, _ := strconv.ParseUint(os.Args[3], 0, 32)
            materafpga.Spi_flash_write_status_register(flashID, uint32(wr32))
            fmt.Printf("WROTE %.02x to SR\n", wr32 & 0xFF)
        } else if os.Args[2] == "verify" || os.Args[2] == "generate" || os.Args[2] == "program" || os.Args[2] == "test" {
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpLipari)
                os.Exit(-1)
            }
            if os.Args[2] == "test" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    return
                }
                var err error = nil
                loopcnt, _ := strconv.ParseUint(os.Args[5], 0, 32)
                for i:=0; i<int(loopcnt);i++ {
                    fmt.Printf("Loop-%d\n", i)
                    t1 := time.Now()
                    err = materafpga.Spi_flash_WriteImage(flashID, os.Args[3], os.Args[4])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t2 := time.Now()
                    fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                    err = materafpga.Spi_flash_VerifyImage(flashID, os.Args[3], os.Args[4])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t3 := time.Now()
                    fmt.Println(" Verifying the image took ", t3.Sub(t2), " time")
                }
                os.Exit(0)
            }
            if os.Args[2] == "program" {
                var err error = nil
                t1 := time.Now()
                err = materafpga.Spi_flash_WriteImage(flashID, os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                t2 := time.Now()
                fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                err = materafpga.Spi_flash_VerifyImage(flashID, os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                t3 := time.Now()
                fmt.Println(" Verifying the image took ", t3.Sub(t2), " time")
                os.Exit(0)
            }
            if os.Args[2] == "verify" {
                err = materafpga.Spi_flash_VerifyImage(flashID, os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                os.Exit(0)
            }
            if os.Args[2] == "generate" {
                t1 := time.Now()
                materafpga.Spi_flash_GenerateImageFromFlash(flashID, os.Args[3], os.Args[4]) 
                t2 := time.Now()
                fmt.Println(" Generating the image ", t2.Sub(t1), " time")
                fmt.Printf(" File %s generated\n", os.Args[4])
                os.Exit(0)
            }
        } else if os.Args[2] == "read" || os.Args[2] == "Read" {
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            rdLength, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            fmt.Printf("\n")
            rd_data, _ := materafpga.Spi_elba_flash_Read_N_Bytes(flashID, uint32(addr), uint32(rdLength), 1) 
            for x:=0;x<int(rdLength);x++ {
                if (x%16) == 0 {
                    fmt.Printf("\n%.08x: ", uint32(addr) + uint32(x))
                }
                fmt.Printf("%.02x ", rd_data[x] & 0xff)
            }
            fmt.Printf("\n")
        } else if os.Args[2] == "sectorerase" {
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            materafpga.Spi_flash_erase_sector(flashID, uint32(addr)) 
            fmt.Printf(" Erased Sector associated with Addr 0x%x\n", uint32(addr))
        } else if os.Args[2] == "w32" {
            data8 := make([]byte, 4)
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            data64, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            data8[0] = byte(data64 & 0xff)
            data8[1] = byte((data64 & 0xff00)>>8)
            data8[2] = byte((data64 & 0xff0000)>>16)
            data8[3] = byte((data64 & 0xff000000)>>24)
            materafpga.Spi_flash_Write_N_Bytes(flashID, data8, uint32(addr)) 
            fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
        } else {
            fmt.Printf(" ERROR: Invalid Flash Command\n");
            os.Exit(-1)
        }
    //
    //MDIO Commands
    //
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
        inst, err = strconv.ParseUint(os.Args[2], 0, 8)
        if err != nil {
            fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        port, err = strconv.ParseInt(os.Args[3], 0, 8)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        materafpga.MvlDump(uint8(inst), int8(port))
    } else if os.Args[1] == "mvlclear" {
        inst, err = strconv.ParseUint(os.Args[2], 0, 8)
        if err != nil {
            fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        materafpga.MvlClear(uint8(inst))
    } else {
        fmt.Printf("\n Incorrect Arg or Command used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelpMatera)
        os.Exit(-1)
    }

    return
}

 
