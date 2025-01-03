package main


import (
    "os"
    "fmt"
    "strconv"
    "time"
    "unicode"
    "unsafe"
    "common/cli"
    "platform/matera"
    "device/fpga/materafpga"
    "device/psu/dps2100"
)

const errhelpMatera = "\nfpgautil:\n" +
        "fpgautil regdump\n" + 
        "fpgautil r32 <addr>\n" +
        "fpgautil w32 <addr> <data>\n" +
        "\n" +
        "fpgautil psuupgrade <psu#> <filename>" +
        "\n" + 
        "fpgautil show fan/psu " +
        "\n" + 
        "fpgautil i2c help  << Display i2c debug commands in the CLI >>\n" +
        "\n" +
        "fpgautil flash help  << Display debug commands in the CLI >>\n" +
        "fpgautil flash program/verify/generate <primary/secondary/allflash> <filename>\n" +
        "\n" +
        // "fpgautil flash <slot#> <qspi#> generate/verify/program uboot0/golduboot/goldfw/allflash <filename>\n" +
        "fpgautil flash <slot#> <qspi#> writefile/verifyfile <addr> <filename>\n" +
        "fpgautil flash <slot#> <qspi#> generatefile <addr> <length> <filename>\n" +
        "\n" +
        "fpgautil cpld <slot#> uc/devid/featurebits/featurerow/statusreg/refresh \n" +
        "fpgautil cpld <slot#> generate/verify/erase/program <cfg0/cfg1/ufm2/fea> <filename>\n" +
        "\n" +
        "fpgautil mdiord <inst#> <phy> <addr>\n" +
        "fpgautil mdiowr <inst#> <phy> <addr> <data>\n" +
        "fpgautil mvldump <inst#> <port#>, use port#=-1 to dump all ports\n" +
        "fpgautil mvlclear <inst#>\n" +
        "fpgautil spimode <slot#> on/off\n"
        

                               

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
    } else if os.Args[1] == "psuupgrade" {
        psuNumber, _ := strconv.ParseUint(os.Args[2], 0, 32)
        materafpga.WriteFirmware(os.Args[3], int(psuNumber))
    } else if os.Args[1] == "show" {
        if os.Args[2][0] == 'f' || os.Args[2][0] == 'F' {
            matera.ShowFanInfo()
        }
        if os.Args[2] == "psu" {
            var present bool
            present, _ = materafpga.PSU_present(0)
            if present == true {
                dps2100.DisplayManufacturingInfo("PSU_1", 1)
            } else {
                fmt.Printf(" INFO: PSU_1 is not present")
            }
            present, _ = materafpga.PSU_present(1)
            if present == true {
                dps2100.DisplayManufacturingInfo("PSU_2", 1)
            } else {
                fmt.Printf(" INFO: PSU_2 is not present")
            }
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
    // Spi to Designware i2c
    //
    } else if os.Args[1] == "spi2dw" {
        var slot uint32
        if argc < 4 {
            fmt.Printf(" %s \n", errhelpMatera)
            return
        }
        slotTmp, errG1 := strconv.ParseUint(os.Args[2], 0, 32)
        if errG1 != nil {
            fmt.Printf("ERROR: Pasring Slot number failed. Go Erro ->  %v", errG1)
            os.Exit(-1)
        }
        slot = uint32(slotTmp) - 1

        if (os.Args[3] == "d") {
            materafpga.DW_regDump(slot, materafpga.DW_CHANNEL)
        } else if (os.Args[3] == "r") {
            addr64, _ := strconv.ParseUint(os.Args[4], 0, 32)
            data32, _ := materafpga.DW_readReg(slot, materafpga.DW_CHANNEL, uint8(addr64)) 
            fmt.Printf("Bridge RD[%.02x]=%.08x\n", uint8(addr64), data32)
        } else if (os.Args[3] == "w") {
            addr64, _ := strconv.ParseUint(os.Args[4], 0, 32)
            data64, _ := strconv.ParseUint(os.Args[5], 0, 32)
            materafpga.DW_writeReg(slot, materafpga.DW_CHANNEL, uint8(addr64), uint32(data64))
            fmt.Printf("Bridge WR[%.02x]=%.08x\n", uint8(addr64), uint32(data64))
        }
        os.Exit(0)
    //
    // Spi-2-I2C Bridge
    //
    } else if (os.Args[1] == "spibridge") {
        var slot uint32
        if argc < 4 {
            fmt.Printf(" %s \n", errhelpMatera)
            return
        }
        
        slotTmp, errG1 := strconv.ParseUint(os.Args[2], 0, 32)
        if errG1 != nil {
            fmt.Printf("ERROR: Pasring Slot number failed. Go Erro ->  %v", errG1)
            os.Exit(-1)
        }
        slot = uint32(slotTmp) - 1

        if (os.Args[3] == "d") {
            materafpga.BridgeDumpReg(slot)
        } else if (os.Args[3] == "i") {
            data8, _ := materafpga.BridgeInterruptCheck(slot)
            fmt.Printf("IRQ=%.02x\n", data8)
        } else if (os.Args[3] == "r") {
            addr64, _ := strconv.ParseUint(os.Args[4], 0, 32)
            data8, _ := materafpga.BridgeReadReg(slot, uint8(addr64)) 
            fmt.Printf("Bridge RD[%.02x]=%.02x\n", uint8(addr64), data8)
        } else if (os.Args[3] == "w") {
            addr64, _ := strconv.ParseUint(os.Args[4], 0, 32)
            data64, _ := strconv.ParseUint(os.Args[5], 0, 32)
            materafpga.BridgeWriteReg(slot, uint8(addr64), uint8(data64))
            fmt.Printf("Bridge WR[%.02x]=%.02x\n", uint8(addr64), uint8(data64))
        } else if (os.Args[3] == "i2cr") {
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            i2caddr, _ := strconv.ParseUint(os.Args[5], 0, 32)
            nBytes, _ := strconv.ParseUint(os.Args[6], 0, 32)
            materafpga.BridgeI2Cread(slot, uint8(chnl), uint8(i2caddr), uint8(nBytes)) 
            fmt.Printf("Bridge I2CRD chnl-%d addr-%x length-%d\n", uint8(chnl), uint8(i2caddr), uint8(nBytes))
        } else if (os.Args[3] == "i2cw") {
            data := []uint8{}
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            i2caddr, _ := strconv.ParseUint(os.Args[5], 0, 32)
            nBytes, _ := strconv.ParseUint(os.Args[6], 0, 32)
            for i=7; i<argc; i++ {
                dataArg, _ := strconv.ParseUint(os.Args[i], 0, 32)
                data = append(data, uint8(dataArg))
            }
            materafpga.BridgeI2Cwrite(slot, uint8(chnl), uint8(i2caddr), uint8(nBytes), data) 
            fmt.Printf("Bridge I2CWR chnl-%d addr-%x length-%d\n", uint8(chnl), uint8(i2caddr), uint8(nBytes))
        } else if (os.Args[3] == "fifor") {
            data := []uint8{}
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            nBytes, _ := strconv.ParseUint(os.Args[5], 0, 32)
            data, _ = materafpga.BridgeReadFIFO(slot, uint8(chnl), uint8(nBytes)) 
            fmt.Printf("Bridge FIFO READ length-%d\n", uint8(nBytes))
            for i:=0;i<len(data);i++ {
                fmt.Printf("%.02x ", data[i])
            }
            fmt.Printf("\n")
        } else if (os.Args[3] == "i2creset") {
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            materafpga.BridgeResetI2C(slot, uint8(chnl))
        } else if (os.Args[3] == "i2ctransw") {
            data := []uint8{}
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            i2caddr, _ := strconv.ParseUint(os.Args[5], 0, 32)
            for i=6; i<argc; i++ {
                dataArg, _ := strconv.ParseUint(os.Args[i], 0, 32)
                data = append(data, uint8(dataArg))
            }
            err = materafpga.BridgeI2CtransactionWrite(slot, uint8(chnl), uint8(i2caddr), data) 
            if err != nil {
                os.Exit(-1)
            }
            //fmt.Printf("Bridge I2CWR chnl-%d addr-%x length-%d\n", uint8(chnl), uint8(i2caddr), uint8(nBytes))
        } else if (os.Args[3] == "i2ctransr") {
            data := []uint8{}
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            i2caddr, _ := strconv.ParseUint(os.Args[5], 0, 32)
            nBytes, _ := strconv.ParseUint(os.Args[6], 0, 32)
            data, err = materafpga.BridgeI2CtransactionRead(slot, uint8(chnl), uint8(i2caddr), uint8(nBytes))
            if err != nil {
                os.Exit(-1)
            }
            fmt.Printf("I2C READ length = %d bytes\n", uint8(nBytes))
            for i:=0;i<len(data);i++ {
                fmt.Printf("%.02x ", data[i])
            }
            fmt.Printf("\n")          
        } else if (os.Args[3] == "qsfpcsum") {
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            err := materafpga.QSFPAmphenolVerifyCheckSums(slot, uint8(chnl), 0x50)
            if err != nil {
                os.Exit(-1)
            }
        } else if (os.Args[3] == "qsfpdump") || (os.Args[3] == "d") {
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            err := materafpga.QSFPdump(slot, uint8(chnl), 0x50)
            if err != nil {
                os.Exit(-1)
            }
        } else if (os.Args[3] == "irqt") {
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            err := materafpga.BridgeClearIRQtest(slot, uint8(chnl), 0x50)
            if err != nil {
                os.Exit(-1)
            }
        } else if (os.Args[3] == "resettest") {
            chnl, _ := strconv.ParseUint(os.Args[4], 0, 32)
            err := materafpga.BridgeClearResetTest(slot, uint8(chnl), 0x50)
            if err != nil {
                os.Exit(-1)
            }
        }

        os.Exit(0)
    //
    //I2C Debug commands
    //
    } else if os.Args[1] == "i2c" {
        wrData := []byte{}
        rdData := []byte{}
        var rdSize uint32 = 0
        const helpI2C = "fpgautil i2c bus mux i2c_addr w byte0 [byte1. . . byteN] r len   -- write/read\n" +
                        "fpgautil i2c bus mux i2c_addr r len                              -- read\n" +
                        "fpgautil i2c bus mux i2c_addr w byte0 [byte1 . . . byteN]        -- write\n" +
                        "fpgautil i2c bus mux scan\n" +
                        "fpgautil i2c debug enable/disable\n" 

        if os.Args[3][0] == 'h' || os.Args[3][0] == 'H' {
            fmt.Printf("\n %s \n", helpI2C)
            return
        }
        if os.Args[3] == "reset" {
            bus, err := strconv.ParseUint(os.Args[2], 0, 32)
            if err != nil {
                fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            freq, _ := strconv.ParseUint(os.Args[4], 0, 32)
            fmt.Printf(" Resetting Bus %d.  pre-scaler low=%d\n", int(bus), freq)
            materafpga.I2cResetController2(int(bus), uint8(freq))
            return
        }
        if argc == 4 {
            if os.Args[3][0] == 'd' {
                materafpga.MateraWriteU32(materafpga.FPGA_SCRATCH_3_REG, 0x00)
            } else if os.Args[3][0] == 'e' {
                materafpga.MateraWriteU32(materafpga.FPGA_SCRATCH_3_REG, 0xDEBDEB99)
            } else {
                fmt.Printf(" %s \n", helpI2C)
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
                rdData, err = materafpga.I2c_access( uint32(bus), uint32(mux), uint32(i), 0x00, wrData, 1 )
                if err == nil {
                    matrix[i] = byte(i)
                } else {
                    matrix[i] = 0x99
                }
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
            fmt.Printf(" %s \n", helpI2C)
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
    // CPLD ON NETWORK ADAPTER
    //
    } else if os.Args[1] == "cpld" {
        if argc < 4 { 
            fmt.Printf(" Need more args for this command\n");  
            return 
        }

        slotTmp, errG1 := strconv.ParseUint(os.Args[2], 0, 32)
        if errG1 != nil {
            fmt.Printf("ERROR: Pasring Slot number failed. Go Erro ->  %v", errG1)
            os.Exit(-1)
        }
        slot := uint32(slotTmp)
        //Check slots are 1-10 or 11 for the Debug Slot
        if ( (slot < (materafpga.SPI_SLOT0+1)) || (slot > (materafpga.SPI_DBG_SLOT+1)) ) {
            fmt.Printf("ERROR: Valid slot numbers are %d - %d\n", materafpga.SPI_SLOT0+1, materafpga.SPI_DBG_SLOT+1)
            os.Exit(-1)
        }
        //Switch to zero based slot for underlying code
        slot = slot - 1
        

        if os.Args[3] == "uc" {   //run op usercode
            ucode, _ := materafpga.Spi_cpldXO3_read_usercode(slot) 
            fmt.Printf(" Slot-%d CPLD  UCODE=0x%.08x\n", slot+1, ucode)
        } else if os.Args[3] == "ucwr" {   //run op usercode
            ucode, _ := strconv.ParseUint(os.Args[5], 0, 32)
            materafpga.Spi_cpldXO3_program_usercode(slot, os.Args[4], uint32(ucode)) 
            fmt.Printf(" WR Slot-%d CPLD  UCODE=0x%.08x\n", slot+1, ucode)
        } else if os.Args[3] == "devid" {   
            ucode, _ := materafpga.Spi_cpldXO3_read_device_id(slot) 
            fmt.Printf(" Slot-%d CPLD  Device ID =0x%.08x\n", slot+1, ucode)
        } else if os.Args[3] == "refresh" {   
            materafpga.Spi_cpldXO3_refresh(slot) 
            fmt.Printf(" Slot-%d Salina CPLD  Refresh performed\n", slot+1)
        } else if os.Args[3] == "featurebits" {   
            featurebits, _ := materafpga.Spi_cpldXO3_read_feature_bits(slot) 
            fmt.Printf(" Slot-%d Salina CPLD  Feature BITS =0x%.04x\n", slot+1, featurebits)
        } else if os.Args[3] == "featurerow" { 
            data := []byte{}  
            data, _ = materafpga.Spi_cpldXO3_read_feature_row(slot) 
            fmt.Printf("\n")
            for i:=0; i < len(data); i++ {
                fmt.Printf(" %.02x", data[i])
            }
            fmt.Printf("\n")
        } else if os.Args[3] == "statusreg" {   
            statusreg, _ := materafpga.Spi_cpldXO3_read_status_reg(slot) 
            fmt.Printf(" Slot-%d Salina CPLD  statusreg =0x%.04x\n", slot+1, statusreg)
        } else if os.Args[3] == "busyflag" {   
            statusreg, _ := materafpga.Spi_cpldXO3_read_busy_flag(slot) 
            fmt.Printf(" Slot-%d Salina CPLD  busyflag =0x%.04x\n", slot+1, statusreg)
        } else if os.Args[3] == "erase" {   
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpMatera)
                os.Exit(-1)
            }
            materafpga.Spi_cpldXO3_erase_flash(slot, os.Args[4])
        } else if os.Args[3] == "generate" || os.Args[3] == "verify" || os.Args[3] == "program" {   
            if argc < 6 {
                fmt.Printf(" %s \n", errhelpMatera)
                os.Exit(-1)
            }

            t1 := time.Now()
            if os.Args[3] == "generate" {  //read flash and make an image from it
                err = materafpga.Spi_cpldX03_generate_image_from_flash(slot, os.Args[4], os.Args[5])
                if err != nil {
                    os.Exit(-1)
                }
            } else if os.Args[3] == "verify" {   
                err = materafpga.Spi_cpldXO3_verify_flash_contents(slot, os.Args[4], os.Args[5])
                if err != nil {
                    os.Exit(-1)
                }
            } else if os.Args[3] == "program" {   
                err = materafpga.Spi_cpldXO3_program_flash(slot, os.Args[4], true, os.Args[5], nil)
                if err != nil {
                    os.Exit(-1)
                }
                err = materafpga.Spi_cpldXO3_verify_flash_contents(slot, os.Args[4], os.Args[5])
                if err != nil {
                    os.Exit(-1)
                }
            }
            t2 := time.Now()
            fmt.Println(" Function took ", t2.Sub(t1), " time")
            os.Exit(0)
        } else if os.Args[3] == "read" || os.Args[3] == "Read" {
            if argc < 7 {
                fmt.Printf(" %s \n", errhelpMatera)
                os.Exit(-1)
            }
            addr, _ := strconv.ParseUint(os.Args[5], 0, 32)
            rdLength, _ := strconv.ParseUint(os.Args[6], 0, 32)
            fmt.Printf(" READ COMMAND Addr=%d   rdLength=%d\n", addr,rdLength );
            fmt.Printf("\n")
            rd_data, _ := materafpga.Spi_cpldX03_read_flash(slot, os.Args[4], uint32(addr), uint32(rdLength)) 
            for x:=0;x<int(rdLength);x++ {
                if (x%16) == 0 {
                    fmt.Printf("\n%.08x: ", uint32(addr) + uint32(x))
                }
                fmt.Printf("%.02x ", rd_data[x] & 0xff)
            }
            fmt.Printf("\n")
        } else {
            fmt.Printf(" Args[3] '%s' is incorrect.  See help for the correct arg\n", os.Args[3]); 
            os.Exit(-1) 
        }   
    //
    //FPGA Local Flash commands 
    //
    } else if os.Args[1] == "flash" {
        var flashID uint32 = materafpga.SPI_FPGA            
        const errhelpMateraFlash = "\n"+
            "fpgautil flash:\n" +
            " LOCAL FPGA FLASH PROGRAMMING\n" +
            "fpgautil flash devid/readsr/writesr <data>\n" +
            "fpgautil flash read <addr> <length>\n" +
            "fpgautil flash w32 <addr> <data>\n" +
            "fpgautil flash sectorerase <addr>\n" +
            "fpgautil flash program/verify/generate <primary/secondary/allflash> <filename>\n" + 
            "\n" +
            " NETWORK ADAPTER PROGRAMMING: SLOTS 0-9, DBG SLOT IS 10\n" +
            "\nfpgautil flash <slot#> <qspi#> devid/flagstatus/readsr/writesr <data>\n" +
            "fpgautil flash <slot#> <qspi#> read <addr> <length>\n" +
            "fpgautil flash <slot#> <qspi#> w32/w64 <addr> <data>\n" +
            "fpgautil flash <slot#> <qspi#> sectorerase <addr>/all\n" +
            "fpgautil flash <slot#> <qspi#> test uboot0/golduboot/goldfw/allflash <filename>\n" +
            // "fpgautil flash <slot#> <qspi#> generate/verify/program uboot0/golduboot/goldfw/allflash <filename>\n" +
            "fpgautil flash <slot#> <qspi#> writefile/verifyfile <addr> <filename>\n" +
            "fpgautil flash <slot#> <qspi#> generatefile <start_addr> <length> <filename>\n"

        if argc < 3 {
            fmt.Printf(" %s \n", errhelpMatera)
            os.Exit(-1)
        }

        //FOR FLASHING AN ELBA OR SALINA ASIC IN A SLOT, ARG2 should be a slot number. CHECK FOR A NUMBER HERE AND PROCEED
        //OTHERWISE IT DEFAULTS TO LOCAL FPGA FLASH
        //BEGIN SLOT FLASH CLI FOR ASIC
        if unicode.IsNumber(rune(os.Args[2][0])) == true {
            var flashID, slot, qspiNumber uint32
            if argc < 5 {
                fmt.Printf(" %s \n", errhelpMateraFlash)
                os.Exit(-1)
            }

            //get the slot number and qspi number, check that args are numbers using ParseUint returned error
            slotTmp, errG1 := strconv.ParseUint(os.Args[2], 0, 32)
            if errG1 != nil {
                fmt.Printf("ERROR: Pasring Slot number failed. Go Erro ->  %v", errG1)
                os.Exit(-1)
            }
            qspiTmp, errG2 := strconv.ParseUint(os.Args[3], 0, 32)
            if errG2 != nil {
                fmt.Printf("ERROR: Pasring Qspi number failed. Go Erro ->  %v", errG2)
                os.Exit(-1)
            }
            slot = uint32(slotTmp)
            qspiNumber = uint32(qspiTmp)

            //Check slots are 1-10 or 11 for the Debug Slot
            if ( (slot < (materafpga.SPI_SLOT0+1)) || (slot > (materafpga.SPI_DBG_SLOT+1)) ) {
                fmt.Printf("ERROR: Valid slot numbers are %d - %d\n", materafpga.SPI_SLOT0+1, materafpga.SPI_DBG_SLOT+1)
                os.Exit(-1)
            }
            //Switch to zero based slot for underlying code
            slot = slot - 1
            
            switch slot {
                case 0:  flashID = materafpga.SPI_SLOT0
                case 1:  flashID = materafpga.SPI_SLOT1
                case 2:  flashID = materafpga.SPI_SLOT2
                case 3:  flashID = materafpga.SPI_SLOT3
                case 4:  flashID = materafpga.SPI_SLOT4
                case 5:  flashID = materafpga.SPI_SLOT5
                case 6:  flashID = materafpga.SPI_SLOT6
                case 7:  flashID = materafpga.SPI_SLOT7
                case 8:  flashID = materafpga.SPI_SLOT8
                case 9:  flashID = materafpga.SPI_SLOT9
                case 10: flashID = materafpga.SPI_DBG_SLOT
                default: fmt.Printf(" ERROR: ZERO based slot number must be 0 - 9 for normal slots, and 10 for the Debug slot.  You entered %d\n", slot);  
                         os.Exit(-1)
            }

            if qspiNumber > materafpga.SPI_TRGT_DEVICE_QSPI1 {
                fmt.Printf(" ERROR: qspi number passed must be 0 - 1.  You entered %d\n", qspiNumber);  
                os.Exit(-1)
            }


            fmt.Printf(" Slot-%d Qpsi-%d Zero Based FlashID=%d\n", slot+1, qspiNumber, flashID)

            if os.Args[4] == "devid" {
                devid, _ := materafpga.Spi_flash_read_id(flashID, qspiNumber) 
                fmt.Printf(" FLASH  DevID=0x%.08x\n", devid)
            } else if os.Args[4] == "wrenrdsr" {
                sr, _ := materafpga.Spi_flash_WriteEnableReadSR(flashID, qspiNumber) 
                fmt.Printf(" Wr Enable Set: Status Reg=0x%.02x\n", sr)
            } else if os.Args[4] == "wrenable" {
                materafpga.Spi_flash_WriteEnable(flashID, qspiNumber) 
                fmt.Printf(" Wr Enable Set\n")
            } else if os.Args[4] == "wrdisable" {
                materafpga.Spi_flash_WriteDisable(flashID, qspiNumber) 
                fmt.Printf(" Wr Enable Disabled\n")
            } else if os.Args[4] == "volconfig" {
                config, _ := materafpga.Spi_flash_read_volatile_config(flashID, qspiNumber) 
                fmt.Printf(" FLASH  vol config=0x%.04x\n", config)
            } else if os.Args[4] == "writeenhvolconfig" {
                data, _ := strconv.ParseUint(os.Args[5], 0, 32)
                materafpga.Spi_flash_write_enh_volatile_config(flashID, qspiNumber, uint32(data)) 
                fmt.Printf(" FLASH  WR ENH VOL CONFIG=0x%.02x\n", data)
            } else if os.Args[4] == "writevolconfig" {
                data, _ := strconv.ParseUint(os.Args[5], 0, 32)
                materafpga.Spi_flash_write_volatile_config(flashID, qspiNumber, uint32(data)) 
                fmt.Printf(" FLASH  WR VOL CONFIG=0x%.02x\n", data)
            } else if os.Args[4] == "enhvolconfig" {
                config, _ := materafpga.Spi_flash_read_enhvolatile_config(flashID, qspiNumber) 
                fmt.Printf(" FLASH  enhanced vol config=0x%.04x\n", config)
            } else if os.Args[4] == "nonvolconfig" {
                config, _ := materafpga.Spi_flash_read_nonvolatile_config(flashID, qspiNumber) 
                fmt.Printf(" FLASH  non volatile config=0x%.04x\n", config)
            } else if os.Args[4] == "wrnonvolconfig" {   
                wr32, _ := strconv.ParseUint(os.Args[5], 0, 32)
                materafpga.Spi_flash_write_nonvolatile_config(flashID, qspiNumber, uint16(wr32)) 
                fmt.Printf(" FLASH  wr non volatile config=0x%.04x\n", uint16(wr32))
            } else if os.Args[4] == "readprotreg" {
                prot, _ := materafpga.Spi_flash_read_sector_protection_reg(flashID, qspiNumber) 
                fmt.Printf(" FLASH  sector protect reg=0x%.04x\n", prot)
                lock, _ := materafpga.Spi_flash_read_volatile_lock_reg(flashID, qspiNumber) 
                fmt.Printf(" FLASH  volatile lock reg=0x%.02x\n", lock)
                freeze, _ := materafpga.Spi_flash_read_global_freeze_reg(flashID, qspiNumber) 
                fmt.Printf(" FLASH  freeze reg=0x%.02x\n", freeze)
            } else if os.Args[4] == "4byte" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelpMateraFlash)
                    return
                }
                if os.Args[5] == "enable" {
                    materafpga.Spi_flash_enable_4byte_addr_mode(flashID, qspiNumber)   
                } else if os.Args[5] == "disable" {
                    materafpga.Spi_flash_disable_4byte_addr_mode(flashID, qspiNumber)
                } else {
                    fmt.Printf("ERROR: Argv[5] needs to be disable or enable\n")
                }
            } else if os.Args[4] == "rdextaddr" {
                ext, _ := materafpga.Spi_flash_read_extended_addr_reg(flashID, qspiNumber) 
                fmt.Printf(" Extended Addr Register=0x%.02x\n", ext)
            } else if os.Args[4] == "wrextaddr" {
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                materafpga.Spi_flash_set_extended_addr_register(flashID, qspiNumber, uint32(addr))
                fmt.Printf(" Wr Extended Addr0x%.08x\n", addr)
            } else if os.Args[4] == "discovery" {
                data, _ := materafpga.Spi_flash_discover_read(flashID, qspiNumber) 
                for x:=0;x<len(data);x++ {
                    if (x%16) == 0 {
                        fmt.Printf("\n%.08x: ", uint32(x))
                    }
                    fmt.Printf("%.02x ", data[x] & 0xff)
                }
                fmt.Printf("\n")
            } else if os.Args[4] == "generalpurpose" {
                data, _ := materafpga.Spi_flash_read_general_purpose(flashID, qspiNumber) 
                for x:=0;x<len(data);x++ {
                    if (x%16) == 0 {
                        fmt.Printf("\n%.08x: ", uint32(x))
                    }
                    fmt.Printf("%.02x ", data[x] & 0xff)
                }
                fmt.Printf("\n")
            } else if os.Args[4] == "flagstatus" {
                flag, _ := materafpga.Spi_flash_read_flag_status(flashID, qspiNumber) 
                fmt.Printf(" FLASH  Flag Status Reg=0x%.02x\n", flag)
            } else if os.Args[4] == "writesr" {
                wr32, _ := strconv.ParseUint(os.Args[5], 0, 32)
                materafpga.Spi_flash_write_status_register(flashID, qspiNumber, uint32(wr32))
                fmt.Printf("WROTE %.02x to SR\n", wr32 & 0xFF)                
            } else if os.Args[4] == "readsr" {
                flag, _ := materafpga.Spi_flash_read_status_register(flashID, qspiNumber) 
                fmt.Printf(" FLASH  Status Reg=0x%.02x\n", flag)
            } else if os.Args[4] == "test" {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelpMateraFlash)
                    os.Exit(-1)
                }
                var err error = nil
                loopcnt, _ := strconv.ParseUint(os.Args[7], 0, 32)
                for i:=0; i<int(loopcnt);i++ {
                    fmt.Printf("Loop-%d\n", i)
                    t1 := time.Now()
                    err = materafpga.Spi_salina_flash_WriteImage(flashID, qspiNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t2 := time.Now()
                    fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                    err = materafpga.Spi_salina_flash_VerifyImage(flashID, qspiNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t3 := time.Now()
                    fmt.Println(" Verifyring the image took ", t3.Sub(t2), " time")
                }
                os.Exit(0)
            } else if os.Args[4] == "program" || os.Args[4] == "verify" || os.Args[4] == "generate" {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelpMateraFlash)
                    os.Exit(-1)
                }
                if os.Args[4] == "program" {
                    var err error = nil
                    t1 := time.Now()
                    err = materafpga.Spi_salina_flash_WriteImage(flashID, qspiNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t2 := time.Now()
                    fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                    err = materafpga.Spi_salina_flash_VerifyImage(flashID, qspiNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t3 := time.Now()
                    fmt.Println(" Verifyring the image took ", t3.Sub(t2), " time")
                    os.Exit(0)
                } else if os.Args[4] == "verify" {
                    err = materafpga.Spi_salina_flash_VerifyImage(flashID, qspiNumber, os.Args[5], os.Args[6])
                    if err != nil {
                        os.Exit(-1)
                    }
                    os.Exit(0)
                }
                if os.Args[4] == "generate" {
                    t1 := time.Now()
                    err = materafpga.Spi_salina_flash_GenerateImageFromFlash(flashID, qspiNumber, os.Args[5], os.Args[6]) 
                    if err != nil {
                        os.Exit(-1)
                    }
                    t2 := time.Now()
                    fmt.Println(" Generating the image ", t2.Sub(t1), " time")
                    fmt.Printf(" File %s generated\n", os.Args[5])
                    os.Exit(0)
                }
            } else if os.Args[4] == "sectorerase" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelpMateraFlash)
                    return
                }
                if os.Args[5] == "all" {
                    fmt.Printf(" Erasing the entire flash\n")
                    err = materafpga.Spi_salina_flash_erase_all_sectors(flashID, qspiNumber) 
                } else {
                    addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                    if err != nil {
                        fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err)
                        os.Exit(-1)
                    }
                    fmt.Printf(" Erasing Sector associated with addr-%x\n", uint32(addr))
                    err = materafpga.Spi_salina_flash_erase_sector(flashID, qspiNumber, uint32(addr)) 
                }
                if err != nil {
                    os.Exit(-1)
                }
            } else if os.Args[4] == "read" || os.Args[4] == "Read" {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelpMateraFlash)
                    os.Exit(-1)
                }
                addr, _ := strconv.ParseUint(os.Args[5], 0, 32)
                rdLength, _ := strconv.ParseUint(os.Args[6], 0, 32)
                fmt.Printf(" READ COMMAND Addr=%d   rdLength=%d\n", addr,rdLength );
                fmt.Printf("\n")
                rd_data, _ := materafpga.Spi_salina_flash_Read_N_Bytes(flashID, qspiNumber, uint32(addr), uint32(rdLength), 1) 
                for x:=0;x<int(rdLength);x++ {
                    if (x%16) == 0 {
                        fmt.Printf("\n%.08x: ", uint32(addr) + uint32(x))
                    }
                    fmt.Printf("%.02x ", rd_data[x] & 0xff)
                }
                fmt.Printf("\n")
            } else if os.Args[4] == "w32" {
                var data32 uint32
                if argc < 6 {
                    fmt.Printf(" Need more args for this command\n");  return
                }
                addr, _ := strconv.ParseUint(os.Args[5], 0, 32)
                data64, _ := strconv.ParseUint(os.Args[6], 0, 32)
                data32 = uint32(data64)
                data := (*[4]byte)(unsafe.Pointer(&data32))[:]
                materafpga.Spi_salina_flash_Write_N_Bytes(flashID, qspiNumber, data, uint32(addr))
                fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
            } else if os.Args[4] == "w64" {
                if argc < 6 {
                    fmt.Printf(" Need more args for this command\n");  return
                }
                addr, _ := strconv.ParseUint(os.Args[5], 0, 32)
                data64, _ := strconv.ParseUint(os.Args[6], 0, 64)
                data := (*[8]byte)(unsafe.Pointer(&data64))[:]
                materafpga.Spi_salina_flash_Write_N_Bytes(flashID, qspiNumber, data, uint32(addr))
                fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
            } else if os.Args[4] == "writefile" || os.Args[4] == "verifyfile" {
                // TODO: fpgautil flash <slot#> <qspi#> writefile/verifyfile <addr> <filename>
                if argc < 7 {
                     fmt.Printf(" Need more args for this command\n");  return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                     fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                filename := os.Args[6]
                // enable SPI Mode only once
                materafpga.SetJTAGbusToSPI(flashID)
                materafpga.SpiBusEnableIOexpander(flashID)
                if os.Args[4] == "writefile" {
                    err = materafpga.Spi_salina_flash_WriteFile(flashID, qspiNumber, uint32(addr), filename) 
                    if err != nil {
                        os.Exit(-1)
                    }
                    err = materafpga.Spi_salina_flash_VerifyFile(flashID, qspiNumber, uint32(addr), filename) 
                    if err != nil {
                        os.Exit(-1)
                    }
                } else if os.Args[4] == "verifyfile" {
                    err = materafpga.Spi_salina_flash_VerifyFile(flashID, qspiNumber, uint32(addr), filename) 
                    if err != nil {
                        os.Exit(-1)
                    }
                }
            } else if os.Args[4] == "generatefile" {
                // TODO: fpgautil flash <slot#> <qspi#> generate <start_addr> <length> <filename>
                if argc < 8 {
                    fmt.Printf(" Need more args for this command\n");  return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                length, err := strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[6] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                filename := os.Args[7]
                err = materafpga.Spi_salina_flash_GenerateFile(flashID, qspiNumber, uint32(addr), uint32(length), filename) 
                if err != nil {
                    os.Exit(-1)
                }
            } else {
                fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
                fmt.Printf(" %s \n", errhelpMateraFlash)
                os.Exit(-1)
            }
            os.Exit(0)
        } 
        //END SLOT FLASH CLI FOR ASIC

        // BEGIN LOCAL FPGA FLASH CLI
        if os.Args[2][0] == 'h' ||  os.Args[2][0] == 'H' {
            fmt.Printf(" %s \n", errhelpMateraFlash)
            os.Exit(-1)
        }

        if os.Args[2] == "devid" {
            value, err := materafpga.Spi_flash_read_id(flashID, 0) 
            if err != nil {
                fmt.Printf(" Error reading flash ID\n")
                os.Exit(-1)
            } else {
                fmt.Printf(" FLASH DEV ID=%.08x\n", value)
            }
        } else if os.Args[2] == "we" {
            materafpga.Spi_flash_WriteEnable(flashID,  0)
            materafpga.Spi_flash_CheckWriteEnable(flashID, 0)
        } else if os.Args[2] == "readsr" {
            rd32, err  := materafpga.Spi_flash_read_status_register(flashID, 0)
            if err != nil {
                fmt.Printf(" Error reading status register\n")
                os.Exit(-1)
            } else {
                fmt.Printf(" SR=%.02x\n", rd32 & 0xFF)
            }
        } else if os.Args[2] == "writesr" {
            wr32, _ := strconv.ParseUint(os.Args[3], 0, 32)
            err := materafpga.Spi_flash_write_status_register(flashID, 0, uint32(wr32))
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
            rd_data, _ := materafpga.Spi_flash_Read_N_Bytes(flashID, uint32(addr), uint32(rdLength), 1) 
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
    } else if os.Args[1] == "spimode" {
        if argc < 4 {
            fmt.Printf(" %s \n", errhelpMatera)
            os.Exit(-1)
        }
        fmt.Printf("**************************************************************************\n")
        fmt.Printf("************** NOTE: SLOT IS NOW 1 BASED (FROM 0 BASE) *******************\n")
        fmt.Printf("**************************************************************************\n")

        slotTmp, errG1 := strconv.ParseUint(os.Args[2], 0, 32)
        if errG1 != nil {
            fmt.Printf("ERROR: Pasring Slot number failed. Go Erro ->  %v", errG1)
            os.Exit(-1)
        }
        slot := uint32(slotTmp)
        //Check slots are 1-10 or 11 for the Debug Slot
        if ( (slot < (materafpga.SPI_SLOT0+1)) || (slot > (materafpga.SPI_DBG_SLOT+1)) ) {
            fmt.Printf("ERROR: Valid slot numbers are %d - %d\n", materafpga.SPI_SLOT0+1, materafpga.SPI_DBG_SLOT+1)
            os.Exit(-1)
        }
        //Switch to zero based slot for underlying code
        slot = slot - 1
        if os.Args[3] == "on" {
            fmt.Printf("setting SPI Mode to ON\n")
            materafpga.SetJTAGbusToSPI(slot)
            materafpga.SpiBusEnableIOexpander(slot)
        } else if os.Args[3] == "off" {
            fmt.Printf("setting SPI Mode to OFF\n")
            materafpga.SpiBusDisableIOexpander(slot)
            materafpga.SetJTAGbusToJTAG(slot)
        } else {
            fmt.Printf(" ERROR: Invalid SPI Mode Command\n")
            fmt.Printf(" %s \n", errhelpMatera)
            os.Exit(-1)
        }
    } else {
        fmt.Printf("\n Incorrect Arg or Command used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelpMatera)
        os.Exit(-1)
    }

    return
}

 
