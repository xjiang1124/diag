package main


import (
    "os"
    "fmt"
    "strconv"
    "time"
    "common/cli"
    "unsafe"
    "device/fpga/liparifpga"
    "device/psu/dps2100"
)

const errhelpLipari = "\nfpgautil:\n" +
        "<fpga#> will be 0 or 1\n" +
        "fpgautil regdump <fgpa#>\n" + 
        "fpgautil r32 <fgpa#> <addr>\n" +
        "fpgautil w32 <fgpa#> <addr> <data>\n" +
        "\n" +
        "fpgautil i2c bus mux i2c_addr w byte0 [byte1. . . byteN] r len   -- write/read\n" +
        "fpgautil i2c bus mux i2c_addr r len                              -- read\n" +
        "fpgautil i2c bus mux i2c_addr w byte0 [byte1 . . . byteN]        -- write\n" +
        "fpgautil i2c bus mux scan\n" +
        //"fpgautil i2c debug enable/disable\n" +
        "\n" +
        "fpgautil power <cycle/on/off> <e#/th4/all> -pciscan -goldfw\n" +
        "\n" +
        "fpgautil flash <fgpa#> devid/readsr/writesr <data>\n" +
        "fpgautil flash <fgpa#> read <addr> <length>\n" +
        "fpgautil flash <fpga#> flash sectorerase <addr>/all\n" +
        //"fpgautil flash <fgpa#> w32/w64 <addr> <data>\n" +
        "fpgautil flash <fgpa#> program/verify/generate <primary/secondary/allflash> <filename>\n" +
        "\n" +
        "fpgautil cpld cpu uc/devid/featurebits/featurerow/statusreg/refresh \n" +
        "fpgautil cpld cpu generate/verify/erase/program <cfg0/cfg1/fea> <filename>\n" +
        "\n" +
        "fpgautil elba <elba#> flash devid/flagstatus/readsr/writesr <data>\n" +
        "fpgautil elba <elba#> flash read <addr> <length>\n" +
        "fpgautil elba <elba#> flash w32/w64 <addr> <data>\n" +
        "fpgautil elba <elba#> flash sectorerase <addr>/all\n" +
        "fpgautil elba <elba#> flash generate/verify/program uboot0/golduboot/goldfw/allflash <filename>\n" +
         " \n" +
        "fpgautil elba <elba#> cpld i2c r/w <addr> <data>\n" +
        "fpgautil elba <elba#> cpld uc/devid/featurebits/featurerow/statusreg/refresh \n" +
        "fpgautil elba <elba#> cpld generate/verify/erase/program <cfg0/cfg1/fea> <filename>\n" 
        

                               

func lipari_fpga_cli() {
    
    var data32 uint32
    var data64, addr, bar uint64
    //var err error
    var i int = 0

    argc := len(os.Args[0:])

    if argc < 3 {
        fmt.Printf(" %s \n", errhelpLipari)
        return
    }

    if os.Args[1] == "regdump" {
        fpga_number, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        liparifpga.FpgaDumpRegionRegisters(uint32(fpga_number))
        fmt.Printf(" FPGA0_FPGA_REV_ID_REG=%x\n  fpga_number=%d", liparifpga.FPGA0_FPGA_REV_ID_REG, fpga_number)
        os.Exit(0)
    } else if os.Args[1] == "show" {
        if os.Args[2] == "psu" {
            var present bool
            present, _ = liparifpga.PSU_present(0)
            if present == true {
                dps2100.DisplayManufacturingInfo("PSU_1", 1)
            } else {
                fmt.Printf(" INFO: PSU_1 is not present")
            }
            present, _ = liparifpga.PSU_present(1)
            if present == true {
                dps2100.DisplayManufacturingInfo("PSU_2", 1)
            } else {
                fmt.Printf(" INFO: PSU_2 is not present")
            }
        }
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
            data32, err = liparifpga.LipariReadU32(uint32(fpga_number) , uint64(bar + addr))
            if err != nil {
                cli.Printf("e", "LipariReadU32 Failed")
                os.Exit(-1)
            }
            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", bar + addr, data32)
        } else {
            data64, err = strconv.ParseUint(os.Args[4], 0, 32)
            err = liparifpga.LipariWriteU32(uint32(fpga_number), uint64(bar + addr), uint32(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.08x\n", bar + addr, uint32(data64))
        }
        os.Exit(0)
    } else if os.Args[1] == "power" {
        var nopciscan uint32 = 1
        var bootgoldfw uint32 = 0
        //"fpgautil power <cycle/on/off> <all/th4/e#> -pciscan -goldfw\n" +
        var state uint32
        var device uint32
        if argc < 4 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        switch os.Args[2] {
            case "on": state = liparifpga.POWER_STATE_ON
            case "off": state = liparifpga.POWER_STATE_OFF
            case "cycle": state = liparifpga.POWER_STATE_CYCLE
            default: fmt.Printf(" Error: arg[2] needs to be cycle, on, or off\n");  return
        }
        switch os.Args[3] {
            case "e0": device = liparifpga.ELBA0
            case "e1": device = liparifpga.ELBA1
            case "e2": device = liparifpga.ELBA2
            case "e3": device = liparifpga.ELBA3
            case "e4": device = liparifpga.ELBA4
            case "e5": device = liparifpga.ELBA5
            case "e6": device = liparifpga.ELBA6
            case "e7": device = liparifpga.ELBA7
            case "th4": device = liparifpga.TH4
            case "all": device = liparifpga.ALL
            default: fmt.Printf(" Error: arg[3] needs to be all, th4, e0, or e1\n");  return
        }
        if contains(os.Args, "-pciscan") {
            nopciscan = 0
        }
        if contains(os.Args, "-goldfw") {
            bootgoldfw = 1
        }
        liparifpga.Asic_PowerCycle(device, state, nopciscan, bootgoldfw) 
        return
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
                liparifpga.I2cResetController2(int(bus)) 
            } else if os.Args[3][0] == 'd' {
                liparifpga.LipariWriteU32(0, liparifpga.FPGA0_SCRATCH_3_REG, 0x00)
            } else if os.Args[3][0] == 'e' {
                liparifpga.LipariWriteU32(0, liparifpga.FPGA0_SCRATCH_3_REG, 0xDEBDEB99)
            } else {
                fmt.Printf(" %s \n", errhelp)
            }
            return
        }
        if os.Args[4] == "scan1" {   //scan1
            wrData = append(wrData, 0x00)
            matrix := make([]byte, 128)
            bus, err := strconv.ParseUint(os.Args[2], 0, 32)
            if err != nil {
                fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            mux, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            liparifpga.ExecutingScanChain = 1
            for i:=3; i<0x78; i++ {

                //if ((i >= 0x30 && i <= 0x37) || (i >= 0x50 && i <= 0x5F)) {
                    //fmt.Printf("RD(%x) \n", i)
                    rdData, err = liparifpga.I2c_access( uint32(bus), uint32(mux), uint32(i), 1, wrData, 1 )
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
            liparifpga.ExecutingScanChain = 0
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
            liparifpga.ExecutingScanChain = 1
            for i:=3; i<0x78; i++ {

                //if ((i >= 0x30 && i <= 0x37) || (i >= 0x50 && i <= 0x5F)) {
                    //fmt.Printf("RD(%x) \n", i)
                    rdData, err = liparifpga.I2c_access( uint32(bus), uint32(mux), uint32(i), 0x00, wrData, 1 )
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
            liparifpga.ExecutingScanChain = 0
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
                rdData, err = liparifpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, 0 )
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
                    rdData, err = liparifpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, rdSize )
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

            rdData, err = liparifpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, rdSize )
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
            rdData, err = liparifpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), 0x00, wrData, uint32(rdLength) )
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

    } else if os.Args[1] == "flash" {
        var flashID uint32

        fpga_number, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        if uint32(fpga_number) == 0 { 
            flashID = liparifpga.SPI_FPGA0_FLASH
        } else if uint32(fpga_number) == 1 {
            flashID = liparifpga.SPI_FPGA1_FLASH
        } else {
            fmt.Printf(" ERROR: FLASH Number Passed must be 0 or 1.  You entered %d\n", uint32(fpga_number))
            os.Exit(-1)
        }
        if os.Args[3] == "devid" {
            value, _ := liparifpga.Spi_flash_read_id(flashID) 
            fmt.Printf(" FLASH DEV ID=%.08x\n", value)
        } else if os.Args[3] == "we" {
            liparifpga.Spi_flash_WriteEnable(flashID)
            liparifpga.Spi_flash_CheckWriteEnable(flashID)
        } else if os.Args[3] == "readsr" {
            rd32, _  := liparifpga.Spi_flash_read_status_register(flashID)
            fmt.Printf(" SR=%.02x\n", rd32 & 0xFF)
        } else if os.Args[3] == "writesr" {
            wr32, _ := strconv.ParseUint(os.Args[4], 0, 32)
            liparifpga.Spi_flash_write_status_register(flashID, uint32(wr32))
            fmt.Printf("WROTE %.02x to SR\n", wr32 & 0xFF)
        /* 
        } else if os.Args[3] == "fileformatconvertright" {
            if argc < 4 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
            liparifpga.FlashConvertImageRight(os.Args[4], os.Args[5])
            return
        } else if os.Args[3] == "fileformatconvertleft" {
            if argc < 4 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
            liparifpga.FlashConvertImageLeft(os.Args[4], os.Args[5])
            return
        */ 
        } else if os.Args[3] == "verify" || os.Args[3] == "generate" || os.Args[3] == "program" || os.Args[3] == "test" {
            //"fpgautil flash program/verify/generateimage <gold/main/allflash> <filename>\n" +
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
            if os.Args[3] == "test" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    return
                }
                var err error = nil
                loopcnt, _ := strconv.ParseUint(os.Args[6], 0, 32)
                for i:=0; i<int(loopcnt);i++ {
                    fmt.Printf("Loop-%d\n", i)
                    t1 := time.Now()
                    err = liparifpga.Spi_flash_WriteImage(flashID, os.Args[4], os.Args[5])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t2 := time.Now()
                    fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                    err = liparifpga.Spi_flash_VerifyImage(flashID, os.Args[4], os.Args[5])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t3 := time.Now()
                    fmt.Println(" Verifyring the image took ", t3.Sub(t2), " time")
                }
                return
            }
            if os.Args[3] == "program" {
                var err error = nil
                t1 := time.Now()
                err = liparifpga.Spi_flash_WriteImage(flashID, os.Args[4], os.Args[5])
                if err != nil {
                    os.Exit(-1)
                }
                t2 := time.Now()
                fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                err = liparifpga.Spi_flash_VerifyImage(flashID, os.Args[4], os.Args[5])
                if err != nil {
                    os.Exit(-1)
                }
                t3 := time.Now()
                fmt.Println(" Verifyring the image took ", t3.Sub(t2), " time")
                os.Exit(0)
            }
            if os.Args[3] == "verify" {
                err = liparifpga.Spi_flash_VerifyImage(flashID, os.Args[4], os.Args[5])
                if err != nil {
                    os.Exit(-1)
                }
                os.Exit(0)
            }
            if os.Args[3] == "generate" {
                t1 := time.Now()
                liparifpga.Spi_flash_GenerateImageFromFlash(flashID, os.Args[4], os.Args[5]) 
                t2 := time.Now()
                fmt.Println(" Generating the image ", t2.Sub(t1), " time")
                fmt.Printf(" File %s generated\n", os.Args[4])
                os.Exit(0)
            }
        } else if os.Args[3] == "read" || os.Args[3] == "Read" {
            if argc < 6 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
            addr, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rdLength, err := strconv.ParseUint(os.Args[5], 0, 32)
            if err != nil {
                fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf("\n")
            rd_data, _ := liparifpga.Spi_elba_flash_Read_N_Bytes(flashID, uint32(addr), uint32(rdLength), 1) 
            for x:=0;x<int(rdLength);x++ {
                if (x%16) == 0 {
                    fmt.Printf("\n%.08x: ", uint32(addr) + uint32(x))
                }
                fmt.Printf("%.02x ", rd_data[x] & 0xff)
            }
            fmt.Printf("\n")
        /*} else if os.Args[3] == "r8" || os.Args[3] == "r32" || os.Args[3] == "r64" {
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
            addr, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rdLength, err := strconv.ParseUint(os.Args[5], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf("\n")
            for i=0;i<int(rdLength); {
                if (i%16) == 0 {
                    fmt.Printf("\n%.08x: ", uint32(addr) + uint32(i))
                }
                if os.Args[3] == "r8" {
                    data32, _ = liparifpga.FlashReadByte( (uint32(addr) + uint32(i)) ) 
                    fmt.Printf("%.02x ", data32 & 0xff)
                    i++
                } else if os.Args[3] == "r32" {
                    data32, _ = liparifpga.FlashReadFourBytes( (uint32(addr) + uint32(i)) ) 
                    fmt.Printf("%.02x %.02x %.02x %02x ", byte(data32 & 0xff), byte((data32 & 0xff00)>>8), byte((data32 & 0xff0000)>>16), byte((data32 & 0xff000000)>>24))
                    i = i + 4
                } else if os.Args[3] == "r64" {
                    data64, _ = liparifpga.FlashReadEightBytes( (uint32(addr) + uint32(i)) ) 
                    fmt.Printf("%.02x %.02x %.02x %02x ", byte(data64 & 0xff), byte((data64 & 0xff00)>>8), byte((data64 & 0xff0000)>>16), byte((data64 & 0xff000000)>>24))
                    fmt.Printf("%.02x %.02x %.02x %02x ", byte((data64 & 0xff00000000)>>32), byte((data64 & 0xff0000000000)>>40), byte((data64 & 0xff000000000000)>>48), byte((data64 & 0xff00000000000000)>>56) )
                    i = i + 8
                } else {
                    fmt.Printf(" Args[2] is not Valid\n"); return
                }
            }
            fmt.Printf("\n")
        */ 
        } else if os.Args[3] == "sectorerase" {
            addr, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            //Disable software WP in the status register
            if addr < 0x800000 {
                err = liparifpga.Spi_flash_write_status_register(flashID, uint32(0x00))
                if err != nil {
                    return
                }
                time.Sleep(time.Duration(50) * time.Millisecond)  
            } 
            liparifpga.Spi_flash_erase_sector(flashID, uint32(addr)) 
            fmt.Printf(" Erased Sector associated with Addr 0x%x\n", uint32(addr))
        /*} else if os.Args[3] == "w32" {
            addr, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            data64, err := strconv.ParseUint(os.Args[5], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            liparifpga.FlashWriteFourBytes(uint32(data64), uint32(addr))
            fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
        } else if os.Args[3] == "w64" {
            addr, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            data64, err := strconv.ParseUint(os.Args[5], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            liparifpga.FlashWriteEightBytes(data64, uint32(addr))
            fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
        */ 
        } else {
            fmt.Printf(" ERROR: Invalid Flash Command\n");
        }
    } else if os.Args[1] == "cpld" {
        var cpldNumber uint32
        if argc < 4 {
            fmt.Printf(" %s \n", errhelpLipari)
            return
        }
        if os.Args[2] == "cpu" {
            cpldNumber = liparifpga.SPI_CPU_CPLD
        } else {
            fmt.Printf(" ERROR: CPLD TYPE ENTERED IS NOT VALID\n")
            return
        }
        //fmt.Printf("%s\n", os.Args[3])
        //cpldNumber, err := strconv.ParseUint(os.Args[2], 0, 32)
        //if err != nil { 
        //    fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return 
        //}
        if os.Args[3] == "uc" {   //run op usercode
            ucode, _ := liparifpga.Spi_cpldXO3_read_usercode(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  UCODE=0x%.08x\n", cpldNumber, ucode)
        } else if os.Args[3] == "devid" {   
            ucode, _ := liparifpga.Spi_cpldXO3_read_device_id(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  Device ID =0x%.08x\n", cpldNumber, ucode)
        } else if os.Args[3] == "refresh" {   
            liparifpga.Spi_cpldXO3_refresh(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  Refresh performed\n", cpldNumber)
        } else if os.Args[3] == "featurebits" {   
            featurebits, _ := liparifpga.Spi_cpldXO3_read_feature_bits(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  Feature BITS =0x%.04x\n", cpldNumber, featurebits)
        } else if os.Args[3] == "featurerow" { 
            data := []byte{}  
            data, _ = liparifpga.Spi_cpldXO3_read_feature_row(uint32(cpldNumber)) 
            fmt.Printf("\n")
            for i:= (len(data) -1); i >= 0; i-- {
                fmt.Printf(" %.02x", data[i])
            }
            fmt.Printf("\n")
            //fmt.Printf(" CPLD-%d  Feature BITS =0x%.04x\n", cpldNumber, featurebits)
        } else if os.Args[3] == "statusreg" {   
            statusreg, _ := liparifpga.Spi_cpldXO3_read_status_reg(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  statusreg =0x%.04x\n", cpldNumber, statusreg)
        } else if os.Args[3] == "generate" || os.Args[3] == "verify" || os.Args[3] == "program" {   

            fmt.Printf("Generate Image\n")
            if argc < 6 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }

            t1 := time.Now()
            if os.Args[3] == "generate" {  //read flash and make an image from it
                fmt.Printf("Generate Image\n")
                liparifpga.Spi_cpldX03_generate_image_from_flash(cpldNumber, os.Args[4], os.Args[5])
            } else if os.Args[3] == "verify" {
                fmt.Printf("Verify Image\n")   
                liparifpga.Spi_cpldXO3_verify_flash_contents(cpldNumber, os.Args[4], os.Args[5])
            } else if os.Args[3] == "program" {
                fmt.Printf("Program Image\n")      
                liparifpga.Spi_cpldXO3_program_flash(cpldNumber, os.Args[4], os.Args[5])
            }
            t2 := time.Now()
            fmt.Println(" Function took ", t2.Sub(t1), " time")
        } else {
            fmt.Printf(" Invalid Arg\n")
        }

        /* else if os.Args[3] == "verifyall" {   //read flash and make an image from it
            if argc < 7 {
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
            loop, _ := strconv.ParseUint(os.Args[6], 0, 32)
            for i:=0; i<int(loop); i++ {
                fmt.Printf("Loop=%d\n", i)
                err := liparifpga.Spi_cpld_machxO2_verify_flash_contents(0, os.Args[4])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
                err = liparifpga.Spi_cpld_machxO2_verify_flash_contents(3, os.Args[5])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
                err = liparifpga.Spi_cpld_machxO2_verify_flash_contents(4, os.Args[5])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
                err = liparifpga.Spi_cpld_machxO2_verify_flash_contents(5, os.Args[5])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
            }
        } */

    } else if os.Args[1] == "elba" {

        var elbaNumber uint32
        if argc < 5 {
            fmt.Printf(" %s \n", errhelpLipari)
            return
        }
        elba, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil { 
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return 
        }
        elbaNumber = uint32(elba)
        if elbaNumber > 7 {
            fmt.Printf(" ERROR: Elba number needs to be 0 or 7\n", err); return 
        }
        if os.Args[3] == "flash" {
            if os.Args[4] == "devid" {
                devid, _ := liparifpga.Spi_flash_read_id(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" FLASH  DevID=0x%.08x\n", devid)
            } else if os.Args[4] == "wrenable" {
                liparifpga.Spi_flash_WriteEnable(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" Wr Enable Set\n")
            } else if os.Args[4] == "volconfig" {
                config, _ := liparifpga.Spi_flash_read_volatile_config(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" FLASH  vol config=0x%.04x\n", config)
            } else if os.Args[4] == "writeenhvolconfig" {
                data, _ := strconv.ParseUint(os.Args[5], 0, 32)
                liparifpga.Spi_flash_write_enh_volatile_config(liparifpga.SPI_ELBA0_FLASH + elbaNumber, uint32(data)) 
                fmt.Printf(" FLASH  WR ENH VOL CONFIG=0x%.02x\n", data)
            } else if os.Args[4] == "writevolconfig" {
                data, _ := strconv.ParseUint(os.Args[5], 0, 32)
                liparifpga.Spi_flash_write_volatile_config(liparifpga.SPI_ELBA0_FLASH + elbaNumber, uint32(data)) 
                fmt.Printf(" FLASH  WR VOL CONFIG=0x%.02x\n", data)
            } else if os.Args[4] == "enhvolconfig" {
                config, _ := liparifpga.Spi_flash_read_enhvolatile_config(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" FLASH  enhanced vol config=0x%.04x\n", config)
            } else if os.Args[4] == "config" {
                config, _ := liparifpga.Spi_flash_read_nonvolatile_config(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" FLASH  DevID=0x%.04x\n", config)
            } else if os.Args[4] == "4byte" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    return
                }
                if os.Args[5] == "enable" {
                    liparifpga.Spi_flash_enable_4byte_addr_mode(liparifpga.SPI_ELBA0_FLASH + elbaNumber)   
                } else if os.Args[5] == "disable" {
                    liparifpga.Spi_flash_disable_4byte_addr_mode(liparifpga.SPI_ELBA0_FLASH + elbaNumber)
                } else {
                    fmt.Printf("ERROR: Argv[5] needs to be disable or enable\n")
                }
            } else if os.Args[4] == "rdextaddr" {
                ext, _ := liparifpga.Spi_flash_read_extended_addr_reg(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" Extended Addr Register=0x%.02x\n", ext)
            } else if os.Args[4] == "wrextaddr" {
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                liparifpga.Spi_flash_set_extended_addr_register(liparifpga.SPI_ELBA0_FLASH + elbaNumber, uint32(addr))
                fmt.Printf(" Wr Extended Addr0x%.08x\n", addr)
            } else if os.Args[4] == "flagstatus" {
                flag, _ := liparifpga.Spi_flash_read_flag_status(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" FLASH  Flag Status Reg=0x%.02x\n", flag)
            } else if os.Args[4] == "readsr" {
                flag, _ := liparifpga.Spi_flash_read_status_register(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                fmt.Printf(" FLASH  Status Reg=0x%.02x\n", flag)
            } else if os.Args[4] == "writesr" {
                wr32, _ := strconv.ParseUint(os.Args[5], 0, 32)
                liparifpga.Spi_flash_write_status_register((liparifpga.SPI_ELBA0_FLASH + elbaNumber), uint32(wr32))
                fmt.Printf("WROTE %.02x to SR\n", wr32 & 0xFF)
            } else if os.Args[4] == "program" || os.Args[4] == "verify" || os.Args[4] == "generate"  {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    return
                }
                t1 := time.Now()
                if os.Args[4] == "program" {
                    liparifpga.Spi_elba_flash_WriteImage(liparifpga.SPI_ELBA0_FLASH + elbaNumber, os.Args[5], os.Args[6]) 
                } else if os.Args[4] == "verify" {
                    liparifpga.Spi_elba_flash_VerifyImage(liparifpga.SPI_ELBA0_FLASH + elbaNumber, os.Args[5], os.Args[6])
                } else if os.Args[4] == "generate" {
                    liparifpga.Spi_elba_flash_GenerateImageFromFlash(liparifpga.SPI_ELBA0_FLASH + elbaNumber, os.Args[5], os.Args[6])
                }
                t2 := time.Now()
                fmt.Println(" Function took ", t2.Sub(t1), " time")
            } else if os.Args[4] == "testread" {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                rdLength, err := strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[6] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                fmt.Printf("\n")
                t1 := time.Now()
                liparifpga.Spi_elba_flash_Read_N_Bytes(liparifpga.SPI_ELBA0_FLASH + elbaNumber, uint32(addr), uint32(rdLength), 1) 
                t2 := time.Now()
                fmt.Println(" Function took ", t2.Sub(t1), " time")
                t3 := time.Now()
                liparifpga.Spi_elba_flash_Read_N_Bytes(liparifpga.SPI_ELBA0_FLASH + elbaNumber, uint32(addr), uint32(rdLength), 1) 
                t4 := time.Now()
                fmt.Println(" Function took ", t4.Sub(t3), " time")
                return
            } else if os.Args[4] == "read" || os.Args[4] == "Read" {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                rdLength, err := strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[6] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                fmt.Printf("\n")
                rd_data, _ := liparifpga.Spi_elba_flash_Read_N_Bytes(liparifpga.SPI_ELBA0_FLASH + elbaNumber, uint32(addr), uint32(rdLength), 1) 
                for x:=0;x<int(rdLength);x++ {
                    if (x%16) == 0 {
                        fmt.Printf("\n%.08x: ", uint32(addr) + uint32(x))
                    }
                    fmt.Printf("%.02x ", rd_data[x] & 0xff)
                }
                fmt.Printf("\n")
            } else if os.Args[4] == "sectorerase" {
                if argc < 5 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    return
                }
                if os.Args[5] == "all" {
                    fmt.Printf(" Erasing the entire flash\n")
                    liparifpga.Spi_elba_flash_erase_all_sectors(liparifpga.SPI_ELBA0_FLASH + elbaNumber) 
                } else {
                    addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                    if err != nil {
                        fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                    }
                    fmt.Printf(" Erasing Sector associated with addr-%x\n", uint32(addr))
                    liparifpga.Spi_elba_flash_erase_sector(liparifpga.SPI_ELBA0_FLASH + elbaNumber, uint32(addr)) 
                }
            } else if os.Args[4] == "w32" {
                var data32 uint32
                if argc < 6 {
                    fmt.Printf(" Need more args for this command\n");  return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data64, err := strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data32 = uint32(data64)
                data := (*[4]byte)(unsafe.Pointer(&data32))[:]
                liparifpga.Spi_elba_flash_Write_N_Bytes(liparifpga.SPI_ELBA0_FLASH + elbaNumber, data, uint32(addr))
                fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
            } else if os.Args[4] == "w64" {
                if argc < 6 {
                    fmt.Printf(" Need more args for this command\n");  return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data64, err := strconv.ParseUint(os.Args[6], 0, 64)
                if err != nil {
                    fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data := (*[8]byte)(unsafe.Pointer(&data64))[:]
                liparifpga.Spi_elba_flash_Write_N_Bytes(liparifpga.SPI_ELBA0_FLASH + elbaNumber, data, uint32(addr))
                fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
            } else {
                fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
                fmt.Printf(" %s \n", errhelpLipari)
                return
            }
        } else if os.Args[3] == "cpld" {
            if argc < 4 { fmt.Printf(" Need more args for this command\n");  return }
            //"fpgautil elba <elba#> cpld i2c r8/w8 <addr> <data>\n" +
            if os.Args[4] == "i2c" {
                wrData := []byte{}
                rdData := []byte{}
                type CpldDevMap struct{
                    bus uint32
                    mux uint32
                }

                var cpld_Map = map[uint32]CpldDevMap {
                    0 : { bus:10 , mux:0 } , 
                    1 : { bus:10 , mux:1 } , 
                    2 : { bus:10 , mux:2 } , 
                    3 : { bus:10 , mux:3 } , 
                    4 : { bus:11 , mux:0 } , 
                    5 : { bus:11 , mux:1 } , 
                    6 : { bus:11 , mux:2 } , 
                    7 : { bus:11 , mux:3 } , 
                }
                if os.Args[5][0] == 'r' || os.Args[5][0] == 'R' {
                    if argc < 7 { fmt.Printf(" Need more args for this command\n");  return }
                    addr, err = strconv.ParseUint(os.Args[6], 0, 32)
                    wrData = append(wrData, byte(addr))
                    rdData, err = liparifpga.I2c_access( cpld_Map[elbaNumber].bus, cpld_Map[elbaNumber].mux, 0x4A, 1, wrData, 1 )
                    fmt.Printf("%.02x\n", rdData[0]);
                } else if os.Args[5][0] == 'w' || os.Args[5][0] == 'W' {
                    if argc < 8 { fmt.Printf(" Need more args for this command\n");  return }
                    addr, err = strconv.ParseUint(os.Args[6], 0, 32)
                    data64, err = strconv.ParseUint(os.Args[7], 0, 32)
                    wrData = append(wrData, byte(addr))
                    wrData = append(wrData, byte(data64))
                    rdData, err = liparifpga.I2c_access( cpld_Map[elbaNumber].bus, cpld_Map[elbaNumber].mux, 0x4A, 2, wrData, 0 )
                    fmt.Printf("WR[%.02x]=%.02x\n", addr, data64);
                } else {
                    fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
                    os.Exit(-1)
                }
            } else if os.Args[4] == "uc" {   //run op usercode
                ucode, _ := liparifpga.Spi_cpldXO3_read_usercode(liparifpga.SPI_ELBA0_CPLD + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  UCODE=0x%.08x\n", elbaNumber, ucode)
            } else if os.Args[4] == "devid" {   
                ucode, _ := liparifpga.Spi_cpldXO3_read_device_id(liparifpga.SPI_ELBA0_CPLD + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  Device ID =0x%.08x\n", elbaNumber, ucode)
            } else if os.Args[4] == "refresh" {   
                liparifpga.Spi_cpldXO3_refresh(liparifpga.SPI_ELBA0_CPLD + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  Refresh performed\n", elbaNumber)
            } else if os.Args[4] == "featurebits" {   
                featurebits, _ := liparifpga.Spi_cpldXO3_read_feature_bits(liparifpga.SPI_ELBA0_CPLD + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLDd  Feature BITS =0x%.04x\n", elbaNumber, featurebits)
            } else if os.Args[4] == "featurerow" { 
                data := []byte{}  
                data, _ = liparifpga.Spi_cpldXO3_read_feature_row(liparifpga.SPI_ELBA0_CPLD + elbaNumber) 
                fmt.Printf("\n")
                for i:=0; i < len(data); i++ {
                    fmt.Printf(" %.02x", data[i])
                }
                fmt.Printf("\n")
                //fmt.Printf(" CPLD-%d  Feature BITS =0x%.04x\n", cpldNumber, featurebits)
            } else if os.Args[4] == "statusreg" {   
                statusreg, _ := liparifpga.Spi_cpldXO3_read_status_reg(liparifpga.SPI_ELBA0_CPLD + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  statusreg =0x%.04x\n", elbaNumber, statusreg)
            } else if os.Args[4] == "erase" {   
                if argc < 5 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    os.Exit(-1)
                }
                liparifpga.Spi_cpldXO3_erase_flash(liparifpga.SPI_ELBA0_CPLD + elbaNumber, os.Args[5])
            } else if os.Args[4] == "generate" || os.Args[4] == "verify" || os.Args[4] == "program" {   
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelpLipari)
                    os.Exit(-1)
                }

                t1 := time.Now()
                if os.Args[4] == "generate" {  //read flash and make an image from it
                    err = liparifpga.Spi_cpldX03_generate_image_from_flash(liparifpga.SPI_ELBA0_CPLD + elbaNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                } else if os.Args[4] == "verify" {   
                    liparifpga.Spi_cpldXO3_verify_flash_contents(liparifpga.SPI_ELBA0_CPLD + elbaNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                } else if os.Args[4] == "program" {   
                    err = liparifpga.Spi_cpldXO3_program_flash(liparifpga.SPI_ELBA0_CPLD + elbaNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                    liparifpga.Spi_cpldXO3_verify_flash_contents(liparifpga.SPI_ELBA0_CPLD + elbaNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                }
                t2 := time.Now()
                fmt.Println(" Function took ", t2.Sub(t1), " time")
                os.Exit(0)
            }
        } else {
            fmt.Printf(" Args[3] '%s' is incorrect.  See help for the correct arg\n", os.Args[3]); os.Exit(-1) 
        }
    } else {
        fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelpLipari)
        os.Exit(-1)
    }
    return
}



func contains(s []string, str string) bool {
    for _, v := range s {
            if len(v) < len(str) {
                continue
            }
            if v[:len(str)] == str {
                    return true
            }
    }

    return false
}

 
