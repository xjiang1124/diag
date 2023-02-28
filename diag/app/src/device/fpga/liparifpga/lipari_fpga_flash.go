/* Support for SPI Access to Elba's Flash, and Routines for Elba's Flash  */
package liparifpga

import (
    //"errors"
    "common/cli"
    "fmt"
    "os"
    "bufio"
)


var flash_region_info flash_region


const GOLDFW = "primary"
const MAINFW = "secondary"
const ALLFLASH = "allflash"


/*****************************************************************************
* SERIAL FLASH FUNCTIONS FOR ELBA 
* SERIAL FLASH FUNCTIONS FOR ELBA 
* SERIAL FLASH FUNCTIONS FOR ELBA  
*****************************************************************************/

func init () {
    //268435456 addresses bytes (2Gb), 4096 erasable sectors.  Sector Size = 64K  SubSector Size = 4K
    flash_region_info.region_size = uint32(0x10000000)  // 2Gb / 256megabyte
    flash_region_info.sector_size = FLASH_SECTOR_SIZE
    flash_region_info.number_of_sectors = flash_region_info.region_size / flash_region_info.sector_size
    flash_region_info.offset = 0
}

func AddrDecipher(partition string) (addr uint32, maxSize uint32, err error) {

    if partition == GOLDFW {
        addr = 0x00
        maxSize = 0x800000
    } else if partition == MAINFW {
        addr = 0x800000
        maxSize = 0x800000
    } else if partition == ALLFLASH {
        addr = 0x00
        maxSize = flash_region_info.region_size
    } else {
        err = fmt.Errorf(" ERROR.  Flash Partition is invalid.  You entered %s.  It needs to be primary, secondary, or allflash\n", partition)
        cli.Printf("e", "%s", err)
        return

    }
    return
}


//uboot0/golduboot/goldfw/allflash
func Spi_flash_GenerateImageFromFlash(spiNumber uint32, partition string, filename string) (err error) {
    var flash_size uint32 = 0 
    var start_addr uint32 = 0
    var read_size uint32 = flash_region_info.sector_size
    var i uint32 = 0
    flashData := []byte{}

    start_addr, flash_size, err =  AddrDecipher(partition) 
    if err != nil {
        fmt.Printf(" ERROR: AddrDecipher failed\n")
        return
    }

    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }

    defer f.Close()

    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }


    for i=start_addr; i<(start_addr + flash_size); i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf(".")
        }
        if (i % 0x1000000) <= read_size {
            err =  Spi_flash_set_extended_addr_register(spiNumber, uint32(i)) 
            if err != nil {
                return
            }
        }
        rd_data, err = Spi_flash_Read_N_Bytes(spiNumber, uint32(i), uint32(read_size), 0)
        if err != nil {
            fmt.Printf(" ERROR: Flash Read Failed\n")
            return
        }
        flashData = append(flashData, rd_data...)
    }
    fmt.Printf("\n")

    f.WriteString(string(flashData[:]))
    return
}

func Spi_flash_VerifyImage(spiNumber uint32, partition string, filename string) (err error) {
    var flash_size uint32 = 0 
    var start_addr uint32 = 0
    var read_size uint32 = uint32(flash_region_info.sector_size)
    var i uint32 = 0
    flashData := []byte{}
    data := []byte{}

    start_addr, flash_size, err =  AddrDecipher(partition) 
    if err != nil {
        fmt.Printf(" ERROR: AddrDecipher failed\n")
        return
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    fmt.Printf(" Verifying Image %s starting at addr=0x%x\n", filename, start_addr)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        data = append(data, b[0])
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        return
    }

    if uint32(len(data)) > flash_size {
        err = fmt.Errorf(" Error: Filesize is bigger than flash partition size. %d vs %d\n", uint32(len(data)), flash_size)
        cli.Printf("e", "%s", err)
        return
    }

    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }


    //fmt.Printf(" len=%d   mod=%d\n", len(data), (len(data) % read_size))
    for i=start_addr; i< start_addr + uint32(len(data)); i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf("%.08x\n", uint32(i))
        } 
        if (i % 0x1000000) <= read_size {
            err =  Spi_flash_set_extended_addr_register(spiNumber, uint32(i)) 
            if err != nil {
                return
            }
        }
         
        rd_data, err = Spi_flash_Read_N_Bytes(spiNumber, uint32(i), uint32(read_size), 0)
        if err != nil {
            fmt.Printf(" ERROR: Flash Read Failed.  StartAddr=%x.  I=%x\n", start_addr, i)
            return
        }
        flashData = append(flashData, rd_data...) 
    }

    for i=0; i<uint32(len(data)); i++ {
        if flashData[i] != data[i] {
            err = fmt.Errorf(" Error: Flash Miscompare at flash address 0x%x:  Flash Read %.02x   File Read %.02x\n", i+start_addr, flashData[i], data[i])
            cli.Printf("e", "%s", err)
            fmt.Printf("Verification failed\n")
            return
        }
    }
    fmt.Printf("\nVerification passed\n")
    return
}


func Spi_flash_WriteImage(spiNumber uint32, partition string, filename string) (err error) {
    var flash_size uint32 = 0 
    var start_addr uint32 = 0
    var i uint32
    var j int
    var write_page bool = false
    var skipped_pages int = 0
    data := []byte{}

    start_addr, flash_size, err =  AddrDecipher(partition) 
    if err != nil {
        fmt.Printf(" ERROR: AddrDecipher failed\n")
        return
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    if uint32(len(data)) > flash_size {
        err = fmt.Errorf(" Error: Filesize is bigger than flash partition size. %d vs %d\n", uint32(len(data)), flash_size)
        cli.Printf("e", "%s", err)
        return
    }
    fmt.Printf(" Writing Image %s starting at addr=0x%x\n", filename, start_addr)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        data = append(data, b[0])
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        return
    }

    tmp := FLASH_PAGE_WRITE_SIZE - (len(data) % FLASH_PAGE_WRITE_SIZE)
    fmt.Printf(" Len=%d  pad length=%d\n", len(data), tmp)
    if tmp != FLASH_PAGE_WRITE_SIZE {
        for i=0; i < uint32(tmp); i++ {
            data = append(data, 0xFF)
        }
    }

    fmt.Printf(" Start Addr=%x, Len Data File = 0x%x\n", start_addr, len(data));
    fmt.Printf(" Erasing flash sectors\n");
    for i=start_addr; i< start_addr + uint32(len(data)); i = i + flash_region_info.sector_size {
        fmt.Printf(".")
        err = Spi_flash_erase_sector(spiNumber, uint32(i))
        if err != nil {
            fmt.Printf(" Erasing Flash Failed\n")
            return
        }
    }
    fmt.Printf("\n")

    /* ////// 
    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    Spi_flash_WriteEnable(spiNumber) 
    err = Spi_flash_CheckWriteEnable(spiNumber)
    if err != nil {
        return
    }
    
    err =  Spi_flash_set_extended_addr_register(spiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }     
    ////// */

    fmt.Printf(" Programming flash sectors\n");
    for i=start_addr; i< start_addr + uint32(len(data)); i = i+uint32(FLASH_PAGE_WRITE_SIZE) {

        /* //////
        if (i % 0x1000000) < 256 {
            err =  Spi_flash_set_extended_addr_register(spiNumber, uint32(i)) 
            if err != nil {
                return
            } 
        }
        ////// */

        if (i%0x20000) == 0 {
            fmt.Printf("%.08x\n", uint32(i))
        }
        wr_data := []byte{}
        write_page = false
        for x:=0; x < FLASH_PAGE_WRITE_SIZE; x++ {
            wr_data = append(wr_data, data[x + j])
            if wr_data[x] != 0xFF {
                write_page = true
            }
        }
        j = j + FLASH_PAGE_WRITE_SIZE 

        if write_page == true {
            err = Spi_flash_Write_N_Bytes(spiNumber, wr_data, uint32(i))
            if err != nil {
                fmt.Printf(" Writing Flash Failed\n")
                return
            }
        } else {
            skipped_pages++
        }
    }
    fmt.Printf("Skipped Pages = %d.  Skipped bytes = 0x%x\n", skipped_pages, (skipped_pages * 256) )
    fmt.Printf("Flashing Partition %s passed\n", partition)
    return
}


func Spi_flash_erase_all_sectors(spiNumber uint32) (err error) {
    //var flash_size int = 0x10000000  //2Gb (256MB)  4096 sectors * 65536
    var i uint32 = 0

    fmt.Printf("SPI BUS=%d\n", spiNumber)
    fmt.Printf("Erasing Sector at addr:")
    for i=0; i<flash_region_info.region_size; i = i + flash_region_info.sector_size {
        fmt.Printf(".")
        err = Spi_flash_erase_sector(spiNumber, i) 
        if err != nil {
            fmt.Printf("\nERROR: Erase All Sectors Failed\n")
            return
        }
    }
    fmt.Printf("\nErase All Sectors Passed\n")
    return
}


func Spi_flash_erase_sector(spiNumber uint32, addr uint32) (err error) {
    //var flash_size int = 0x10000000  //2Gb (256MB)  4096 sectors * 65536

    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }
   
    err = Spi_flash_WriteEnable(spiNumber) 
    if err != nil {
        return
    }
    err = Spi_flash_CheckWriteEnable(spiNumber)
    if err != nil {
        return
    }


    ERASE_SECTOR_OP[1] = byte(addr >> 16)
    ERASE_SECTOR_OP[2] = byte(addr >> 8)
    ERASE_SECTOR_OP[3] = byte(addr)

    _ , err = lipari_spi_generic_transaction(spiNumber, ERASE_SECTOR_OP, ERASE_SECTOR_RDLNG) 
    if err != nil {
        err = fmt.Errorf("ERROR: Spi_flash_erase_sector Failed.  Erase Addr=%.08x\n", addr)
        cli.Printf("e", "%s", err)
        return
    }

    sr_reg, rc := Spi_flash_Poll_STS_WIP(spiNumber,  ELB_SECTOR_ERASE_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: Spi_flash_erase_sector.  Timeout Waiting for Sector Erase to Compelte.  Address Passsed = 0x%x  Delay = %d.   Status Reg=%.02x\n", addr, ELB_SECTOR_ERASE_DELAY, sr_reg)
       cli.Printf("e", "%s", err)
    }
    return


    err = Spi_flash_WriteDisable(spiNumber) 


    return
}


func Spi_flash_Write_N_Bytes(spiNumber uint32, data []byte, addr uint32) (err error) {
    wr_data := []byte{}

    if addr > flash_region_info.region_size {
        err = fmt.Errorf("ERROR: Spi_flash_Write_N_Bytes.  Address passed (0x%x) is greather than flash size - %x\n", addr, flash_region_info.region_size)
        cli.Printf("e", "%s", err)
        return
    }
    if len(data) > FLASH_PAGE_WRITE_SIZE {
        err = fmt.Errorf("ERROR: Spi_flash_Write_N_Bytes.  Number of bytes passed is to many to program with one page write.  Max=%d.  You passed %d bytes\n", FLASH_PAGE_WRITE_SIZE, len(data))
        cli.Printf("e", "%s", err)
        return
    }

    
    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    } 

    err = Spi_flash_WriteEnable(spiNumber) 
    if err != nil {
        return
    } 
    err = Spi_flash_CheckWriteEnable(spiNumber)
    if err != nil {
        return
    }
     

    PAGE_PROGRAM_OP[1] = byte(addr >> 16)
    PAGE_PROGRAM_OP[2] = byte(addr >> 8)
    PAGE_PROGRAM_OP[3] = byte(addr)

    wr_data = append(wr_data, PAGE_PROGRAM_OP...)
    wr_data = append(wr_data, data...)

    data, err = lipari_spi_generic_transaction(spiNumber, wr_data, PAGE_PROGRAM_RDLNG) 
    if err != nil {
       fmt.Printf("ERROR: Spi_flash_Write_N_Bytes.  lipari_spi_generic_transaction Failed\n")
    }

    sr_reg, rc := Spi_flash_Poll_STS_WIP(spiNumber,  ELB_PAGE_WR_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: Spi_flash_Write_N_Bytes.  Timeout Waiting for Sector Erase to Compelte.  Address Passsed = 0x%x  Delay = %d.   Status Reg=%.02x\n", addr, ELB_PAGE_WR_DELAY, sr_reg)
       cli.Printf("e", "%s", err)
       return
    }

    //err = Spi_flash_WriteDisable(spiNumber) 
    //if err != nil {
    //   fmt.Printf("ERROR: Spi_flash_Write_N_Bytes.  Spi_flash_WriteDisable Failed\n")
    //}
    return
}


func Spi_flash_FourByteAddr_Read_N_Bytes(spiNumber uint32, addr uint32, length uint32) (data []byte, err error) {
    /*
    err =  Spi_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }

    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }
    */

    err = Spi_flash_enable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    READ_OP[1] = byte(addr >> 16)
    READ_OP[2] = byte(addr >> 8)
    READ_OP[3] = byte(addr)
    data, err = lipari_spi_generic_transaction(spiNumber, READ_FOUR_BYTE_OP, length) 
    return
}


func Spi_flash_Read_N_Bytes(spiNumber uint32, addr uint32, length uint32, cli_call uint32) (data []byte, err error) {
    if (cli_call > 0) {
        err = Spi_flash_disable_4byte_addr_mode(spiNumber)
        if err != nil {
            return
        }

        err =  Spi_flash_set_extended_addr_register(spiNumber, addr) 
        if err != nil {
            return
        }
    }
    READ_OP[1] = byte(addr >> 16)
    READ_OP[2] = byte(addr >> 8)
    READ_OP[3] = byte(addr)
    data, err = lipari_spi_generic_transaction(spiNumber, READ_OP, length) 
    return
}


func Spi_flash_DualOp_Read_N_Bytes(spiNumber uint32, addr uint32, length uint32) (data []byte, err error) {

    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }

    DUAL_READ_OP[1] = byte(addr >> 16)
    DUAL_READ_OP[2] = byte(addr >> 8)
    DUAL_READ_OP[3] = byte(addr)
    data, err = lipari_spi_generic_transaction(spiNumber, DUAL_READ_OP, length) 
    return
}


func Spi_flash_DualOp_FastRead_N_Bytes(spiNumber uint32, addr uint32, length uint32) (data []byte, err error) {

    err = Spi_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }

    DUAL_FAST_READ_OP[1] = byte(addr >> 16)
    DUAL_FAST_READ_OP[2] = byte(addr >> 8)
    DUAL_FAST_READ_OP[3] = byte(addr)
    data, err = lipari_spi_generic_transaction(spiNumber, DUAL_FAST_READ_OP, length) 
    return
}

