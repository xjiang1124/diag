package main


import (
    "os"
    "fmt"
    "strconv"
    "time"
    "common/cli"
    "platform/panarea"
    "device/fpga/panareafpga"
    "device/psu/dps2100"
)

const errhelpPanarea = "\nfpgautil:\n" +
        "fpgautil regdump\n" + 
        "fpgautil r32 <addr>\n" +
        "fpgautil w32 <addr> <data>\n" +
        "\n" + 
        "fpgautil show fan/psu\n" +
        "\n" +
        "fpgautil flash help  << Display debug commands in the CLI >>\n" +
        "fpgautil flash program/verify/generate <primary/secondary/allflash> <filename>\n" +
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
        } else if os.Args[2][0] == 'p' || os.Args[2][0] == 'P' {
            var present bool
            present, _ = panareafpga.PSU_present(0)
            if present == true {
                dps2100.DisplayManufacturingInfo("PSU_1", 1)
            } else {
                fmt.Printf(" INFO: PSU_1 is not present")
            }
            present, _ = panareafpga.PSU_present(1)
            if present == true {
                dps2100.DisplayManufacturingInfo("PSU_2", 1)
            } else {
                fmt.Printf(" INFO: PSU_2 is not present")
            }
        } else {
            fmt.Printf("ERROR: show argv[2] is incorrect.  You entered '%s'  Please check the help\n", os.Args[2])
            os.Exit(-1)
        }
    //
    //FPGA Local Flash commands 
    //
    } else if os.Args[1] == "flash" {
        var flashID uint32 = panareafpga.SPI_FPGA            
        const errhelpPanareaFlash = "\n"+
            "fpgautil flash:\n" +
            " LOCAL FPGA FLASH PROGRAMMING\n" +
            "fpgautil flash devid/readsr/writesr <data>\n" +
            "fpgautil flash read <addr> <length>\n" +
            "fpgautil flash w32 <addr> <data>\n" +
            "fpgautil flash sectorerase <addr>\n" +
            "fpgautil flash program/verify/generate <primary/secondary/allflash> <filename>\n\n"  

        if argc < 3 {
            fmt.Printf(" %s \n", errhelpPanarea)
            os.Exit(-1)
        }

        // BEGIN LOCAL FPGA FLASH CLI
        if os.Args[2][0] == 'h' ||  os.Args[2][0] == 'H' {
            fmt.Printf(" %s \n", errhelpPanareaFlash)
            os.Exit(-1)
        }

        if os.Args[2] == "devid" {
            value, err := panareafpga.Spi_flash_read_id(flashID, 0) 
            if err != nil {
                fmt.Printf(" Error reading flash ID\n")
                os.Exit(-1)
            } else {
                fmt.Printf(" FLASH DEV ID=%.08x\n", value)
            }
        } else if os.Args[2] == "we" {
            panareafpga.Spi_flash_WriteEnable(flashID,  0)
            panareafpga.Spi_flash_CheckWriteEnable(flashID, 0)
        } else if os.Args[2] == "readsr" {
            rd32, err  := panareafpga.Spi_flash_read_status_register(flashID, 0)
            if err != nil {
                fmt.Printf(" Error reading status register\n")
                os.Exit(-1)
            } else {
                fmt.Printf(" SR=%.02x\n", rd32 & 0xFF)
            }
        } else if os.Args[2] == "writesr" {
            wr32, _ := strconv.ParseUint(os.Args[3], 0, 32)
            err := panareafpga.Spi_flash_write_status_register(flashID, 0, uint32(wr32))
            if err != nil {
                fmt.Printf(" Error reading flash ID\n")
                os.Exit(-1)
            } else {
                fmt.Printf("WROTE %.02x to SR\n", wr32 & 0xFF)
            }
        } else if os.Args[2] == "verify" || os.Args[2] == "generate" || os.Args[2] == "program" || os.Args[2] == "test" {
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpPanareaFlash)
                os.Exit(-1)
            }
            if os.Args[2] == "test" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelpPanareaFlash)
                    return
                }
                var err error = nil
                loopcnt, _ := strconv.ParseUint(os.Args[5], 0, 32)
                for i:=0; i<int(loopcnt);i++ {
                    fmt.Printf("Loop-%d\n", i)
                    t1 := time.Now()
                    err = panareafpga.Spi_flash_WriteImage(flashID, os.Args[3], os.Args[4])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t2 := time.Now()
                    fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                    err = panareafpga.Spi_flash_VerifyImage(flashID, os.Args[3], os.Args[4])
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
                err = panareafpga.Spi_flash_WriteImage(flashID, os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                t2 := time.Now()
                fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                err = panareafpga.Spi_flash_VerifyImage(flashID, os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                t3 := time.Now()
                fmt.Println(" Verifying the image took ", t3.Sub(t2), " time")
                os.Exit(0)
            }
            if os.Args[2] == "verify" {
                err = panareafpga.Spi_flash_VerifyImage(flashID, os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                os.Exit(0)
            }
            if os.Args[2] == "generate" {
                t1 := time.Now()
                panareafpga.Spi_flash_GenerateImageFromFlash(flashID, os.Args[3], os.Args[4]) 
                t2 := time.Now()
                fmt.Println(" Generating the image ", t2.Sub(t1), " time")
                fmt.Printf(" File %s generated\n", os.Args[4])
                os.Exit(0)
            }
        } else if os.Args[2] == "read" || os.Args[2] == "Read" {
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpPanareaFlash)
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
            rd_data, _ := panareafpga.Spi_flash_Read_N_Bytes(flashID, uint32(addr), uint32(rdLength), 1) 
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
            panareafpga.Spi_flash_erase_sector(flashID, uint32(addr)) 
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
            panareafpga.Spi_flash_Write_N_Bytes(flashID, data8, uint32(addr)) 
            fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
        } else {
            fmt.Printf(" ERROR: Invalid Flash Command\n");
            os.Exit(-1)
        }
    } else {
        fmt.Printf("\n Incorrect Arg or Command used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelpPanarea)
        os.Exit(-1)
    }

    return
}

 
