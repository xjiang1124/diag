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
        "fpgautil i2c bus mux i2c_addr w byte0 [byte1. . . byteN] r len   -- write/read\n" +
        "fpgautil i2c bus mux i2c_addr r len                              -- read\n" +
        "fpgautil i2c bus mux i2c_addr w byte0 [byte1 . . . byteN]        -- write\n" +
        "fpgautil i2c bus mux scan\n" +
        "fpgautil i2c debug enable/disable\n" +
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
    var data64, addr uint64
    var err error
    var inst, phy uint64
    var port int64
    var data16 uint16
    var i int = 0

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
            data32, err = materafpga.MateraReadU32(uint64(addr))
            if err != nil {
                cli.Printf("e", "MateraReadU32 Failed")
                os.Exit(-1)
            }
            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", addr, data32)
        } else {
            data64, err = strconv.ParseUint(os.Args[3], 0, 32)
            err = materafpga.MateraWriteU32(uint64(addr), uint32(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.08x\n", addr, uint32(data64))
        }
        os.Exit(0)
    //
    //I2C Debug commands
    //
    } else if os.Args[1] == "i2c" {
        wrData := []byte{}
        rdData := []byte{}
        var rdSize uint32 = 0

        if argc == 4 {
            if os.Args[3] == "reset" {
                bus, err := strconv.ParseUint(os.Args[2], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                fmt.Printf(" Resetting Bus %d\n", int(bus))
                materafpga.I2cResetController2(int(bus)) 
            } else if os.Args[3][0] == 'd' {
                materafpga.MateraWriteU32(materafpga.FPGA_SCRATCH_3_REG, 0x00)
            } else if os.Args[3][0] == 'e' {
                materafpga.MateraWriteU32(materafpga.FPGA_SCRATCH_3_REG, 0xDEBDEB99)
            } else {
                fmt.Printf(" %s \n", errhelp)
            }
            return
        }
        if argc == 5 {   //scan
            matrix := make([]byte, 128)
            bus, err := strconv.ParseUint(os.Args[2], 0, 32)
            if err != nil {
                fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            mux, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            materafpga.ExecutingScanChain = 1
            for i:=3; i<0x78; i++ {

                //if ((i >= 0x30 && i <= 0x37) || (i >= 0x50 && i <= 0x5F)) {
                    //fmt.Printf("RD(%x) \n", i)
                    rdData, err = materafpga.I2c_access( uint32(bus), uint32(mux), uint32(i), 0x00, wrData, 1 )
                //} else {
                    //fmt.Printf("WR(%x) \n", i)
                //    rdData, err = I2c_access( uint32(bus), uint32(mux), uint32(i), 0x00, wrData, 0x00 )
                //}
                if err == nil {
                    matrix[i] = byte(i)
                } else {
                    matrix[i] = 0x99
                }
                //time.Sleep(time.Duration(10) * time.Millisecond)  //Sleep 2ms
            }
            materafpga.ExecutingScanChain = 0
            fmt.Printf("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
            for i:=0; i<0x80; i++ {
                if (i%0x10)==0 { fmt.Printf("\n%.02x:", i) }
                if matrix[i] == 0 { fmt.Printf("   ") 
                } else if matrix[i] == 0x99 { fmt.Printf(" --") 
                } else { fmt.Printf(" %.02x", matrix[i]) }
            }
            fmt.Printf("\n")
            return
        }
        if argc < 6 {
            fmt.Printf(" ERROR: Not Enough ARGS!!\n")
            fmt.Printf(" %s \n", errhelp)
            return
        }
        bus, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        mux, err := strconv.ParseUint(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        i2cAddr, err := strconv.ParseUint(os.Args[4], 0, 32)
        if err != nil {
            fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }

        if os.Args[5] == "b" || os.Args[5] == "b" {
            fmt.Printf(" Attempting to wipe secure key from the eeprom\n")
            wrData = append(wrData, 0xFF)
            for i:=0x100;i<0x1000;i++ {
                fmt.Printf(".")
                rdData, err = materafpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, 0 )
                if err != nil {
                    os.Exit(-1)
                }
            }
            os.Exit(0)
        }
        if os.Args[5] == "w" || os.Args[5] == "W" {
            for i=6; i<argc; i++ {
                if os.Args[i] == "r" || os.Args[i] == "R" {
                    rdLength, err := strconv.ParseUint(os.Args[i+1], 0, 32)
                    if err != nil {
                        fmt.Printf(" Args[%d] ParseUint is showing ERR = %v.   Exiting Program\n", i+1,  err); return
                    }
                    rdSize = uint32(rdLength)
                    rdData, err = materafpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, rdSize )
                    if err == nil {
                        if err == nil {
                            fmt.Printf("\nWR: ")
                            for i=0;i<len(wrData);i++ {
                                fmt.Printf("0x%02x ", wrData[i])
                            }
                        }
                        fmt.Printf("\nRD: ")
                        for j:=0; j<len(rdData); j++ {
                            fmt.Printf("0x%.02x ", rdData[j])
                        }
                        fmt.Printf("\n")
                        return
                    } else {
                        os.Exit(-1)
                    }
                } else {
                    dataArg, err := strconv.ParseUint(os.Args[i], 0, 32)
                    if err != nil {
                        fmt.Printf(" Args[%d] ParseUint is showing ERR = %v.   Exiting Program\n", i, err); return
                    }
                    wrData = append(wrData, byte(dataArg))
                }
            }

            rdData, err = materafpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, rdSize )
            if err == nil {
                fmt.Printf("\nWR: ")
                for i=0;i<len(wrData);i++ {
                    fmt.Printf("0x%02x ", wrData[i])
                }
                fmt.Printf("\n")
            } else {
                os.Exit(-1)
            }
        } else {       //read only
            rdLength, err := strconv.ParseUint(os.Args[6], 0, 32)
            if err != nil {
                fmt.Printf(" Args[6] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rdData, err = materafpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), 0x00, wrData, uint32(rdLength) )
            if err == nil {
                fmt.Printf("\nRD: ")
                for j:=0; j<len(rdData); j++ {
                    fmt.Printf("0x%.02x ", rdData[j])
                }
                fmt.Printf("\n")
            } else {
                os.Exit(-1)
            }
        }


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

        if argc < 3 {
            fmt.Printf(" %s \n", errhelpMatera)
            os.Exit(-1)
        }

        if os.Args[2][0] == 'h' ||  os.Args[2][0] == 'H' {
            fmt.Printf(" %s \n", errhelpMateraFlash)
            os.Exit(-1)
        }

        if os.Args[2] == "devid" {
            value, err := materafpga.Spi_flash_read_id(flashID) 
            if err != nil {
                fmt.Printf(" Error reading flash ID\n")
                os.Exit(-1)
            } else {
                fmt.Printf(" FLASH DEV ID=%.08x\n", value)
            }
        } else if os.Args[2] == "we" {
            materafpga.Spi_flash_WriteEnable(flashID)
            materafpga.Spi_flash_CheckWriteEnable(flashID)
        } else if os.Args[2] == "readsr" {
            rd32, err  := materafpga.Spi_flash_read_status_register(flashID)
            if err != nil {
                fmt.Printf(" Error reading status register\n")
                os.Exit(-1)
            } else {
                fmt.Printf(" SR=%.02x\n", rd32 & 0xFF)
            }
        } else if os.Args[2] == "writesr" {
            wr32, _ := strconv.ParseUint(os.Args[3], 0, 32)
            err := materafpga.Spi_flash_write_status_register(flashID, uint32(wr32))
            if err != nil {
                fmt.Printf(" Error reading flash ID\n")
                os.Exit(-1)
            } else {
                fmt.Printf("WROTE %.02x to SR\n", wr32 & 0xFF)
            }
        } else if os.Args[2] == "verify" || os.Args[2] == "generate" || os.Args[2] == "program" || os.Args[2] == "test" {
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpMateraFlash)
                os.Exit(-1)
            }
            if os.Args[2] == "test" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelpMateraFlash)
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
                fmt.Printf(" %s \n", errhelpMateraFlash)
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

 
