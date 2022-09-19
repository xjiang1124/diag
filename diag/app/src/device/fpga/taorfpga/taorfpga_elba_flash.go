/* Support for SPI Access to Elba's Flash, and Routines for Elba's Flash  */
package taorfpga

import (
    //"errors"
    "common/cli"
    "fmt"
    "os"
    "bufio"
    "time"
)


var elba_flash_info flash_region

const ELBA0_SPI_BUS    uint32 = 6
const ELBA1_SPI_BUS    uint32 = 7


var WRITE_STATUS_REG_OP                  = []byte{0x01, 0x00}
var WRITE_STATUS_REG_RDLNG               uint32 = 0

var PAGE_PROGRAM_OP                     = []byte{0x02, 0x00, 0x00, 0x00}   
var PAGE_PROGRAM_RDLNG                  uint32 = 0

var READ_OP                             = []byte{0x03, 0x00, 0x00, 0x00}
var FAST_READ_OP                        = []byte{0x0B, 0x00, 0x00, 0x00}

var DUAL_READ_OP                        = []byte{0x3B, 0x00, 0x00, 0x00}
var DUAL_FAST_READ_OP                   = []byte{0xBB, 0x00, 0x00, 0x00}

var READ_FOUR_BYTE_OP                   = []byte{0x13, 0x00, 0x00, 0x00, 0x00}

var READ_STATUS_REG_OP                  = []byte{0x05}
var READ_STATUS_REG_RDLNG               uint32 = 1


var WRITE_DISABLE_OP                     = []byte{0x04}
var WRITE_DISABLE_RDLNG                  uint32 = 0

var WRITE_ENABLE_OP                     = []byte{0x06}
var WRITE_ENABLE_RDLNG                  uint32 = 0

var READ_FLAG_STATUS_REG_OP             = []byte{0x70}
var READ_FLAG_STATUS_REG_RDLNG          uint32 = 1

//var READ_ID_OP                          = []byte{0x9E}
//var READ_ID_RDLNG                       uint32 = 4

var READ_ID_OP                          = []byte{0x9F}
var READ_ID_RDLNG                       uint32 = 4


var READ_VOLATILE_CONFIG                = []byte{0x85}
var READ_VOLATILE_CONFIG_RDLNG          uint32 = 1
var WRITE_VOLATILE_CONFIG               = []byte{0x81, 0x00}
var WRITE_VOLATILE_CONFIG_RDLNG         uint32 = 0

var READ_ENH_VOLATILE_CONFIG            = []byte{0x65}
var READ_ENH_VOLATILE_CONFIG_RDLNG      uint32 = 1
var WRITE_ENH_VOLATILE_CONFIG           = []byte{0x61, 0x00}
var WRITE_ENH_VOLATILE_CONFIG_RDLNG     uint32 = 0

var READ_NON_VOLATILE_CONFIG            = []byte{0xB5}
var READ_NON_VOLATILE_CONFIG_RDLNG      uint32 = 2

var WRITE_ENABLE_4BYTE_ADDR_OP          = []byte{0xB7}
var WRITE_ENABLE_4BYTE_ADDR_RDLNG       uint32 = 0

var WRITE_DISABLE_4BYTE_ADDR_OP         = []byte{0xE9}
var WRITE_DISABLE_4BYTE_ADDR_RDLNG      uint32 = 0

var WRITE_EXTENDED_ADDR_REG_OP          = []byte{0xC5, 0x00}
var WRITE_EXTENDED_ADDR_REG_RDLNG       uint32 = 0

var READ_EXTENDED_ADDR_REG_OP           = []byte{0xC8}
var READ_EXTENDED_ADDR_REG_RDLNG        uint32 = 1

var ERASE_SECTOR_OP                     = []byte{0xD8, 0x00, 0x00, 0x00}
var ERASE_SECTOR_RDLNG                  uint32 = 0

const FLASH_PAGE_WRITE_SIZE             int = 256




//delays are us
const ELB_WRITE_SR_DELAY    int = 8000
const ELB_PAGE_WR_DELAY     int = 1800 
const ELB_SUBELB_SECTOR_ERASE_DELAY int = 400000
const ELB_SECTOR_ERASE_DELAY    int = 1000000
const ELB_CHIP_ERASE_DELAY      int = 1000000

/*****************************************************************************
* SERIAL FLASH FUNCTIONS FOR ELBA 
* SERIAL FLASH FUNCTIONS FOR ELBA 
* SERIAL FLASH FUNCTIONS FOR ELBA  
*****************************************************************************/

func init () {
    //268435456 addresses bytes (2Gb), 4096 erasable sectors.  Sector Size = 64K  SubSector Size = 4K
    elba_flash_info.region_size = uint32(0x10000000)  // 2Gb / 256megabyte
    elba_flash_info.sector_size = FLASH_SECTOR_SIZE
    elba_flash_info.number_of_sectors = elba_flash_info.region_size / elba_flash_info.sector_size
    elba_flash_info.offset = 0
}


func Spi_elba_flash_set_extended_addr_register(spiNumber uint32, addr uint32) (err error) {
    //var flash_size int = 0x10000000  //2Gb (256MB)  4096 sectors * 65536
   
    if addr < 0x1000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x00
    } else if addr < 0x2000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x01
    } else if addr < 0x3000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x02
    } else if addr < 0x4000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x03
    } else if addr < 0x5000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x04
    } else if addr < 0x6000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x05
    } else if addr < 0x7000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x06
    } else if addr < 0x8000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x07
    } else if addr < 0x9000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x08
    } else if addr < 0xA000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x09
    } else if addr < 0xB000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x0A
    } else if addr < 0xC000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x0B
    } else if addr < 0xD000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x0C
    } else if addr < 0xE000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x0D
    } else if addr < 0xF000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x0E
    } else if addr < 0x10000000 {
        WRITE_EXTENDED_ADDR_REG_OP[1] = 0x0F
    } else {
        err = fmt.Errorf("ERROR: Spi_elba_flash_set_extended_addr_register.  Passed Address if to greater than the flash size.  Addr=%.08x\n", addr)
        cli.Printf("e", "%s", err)
        return
    }

    err = Spi_elba_flash_WriteEnable(spiNumber) 
    if err != nil {
        return
    }

    _ , err = Fpga_spi_generic_transaction(spiNumber, WRITE_EXTENDED_ADDR_REG_OP, WRITE_EXTENDED_ADDR_REG_RDLNG) 
    if err != nil {
        return
    }


    //err = Spi_elba_flash_WriteDisable(spiNumber) 
    //ext, _ := Spi_elba_flash_read_extended_addr_reg(spiNumber) 
    //fmt.Printf(" Extended Register = %.02x\n", ext)

    return
}


func Spi_elba_flash_enable_4byte_addr_mode(spiNumber uint32) (err error) {
    _, err = Fpga_spi_generic_transaction(spiNumber, WRITE_ENABLE_4BYTE_ADDR_OP, WRITE_ENABLE_4BYTE_ADDR_RDLNG) 
    return
}


func Spi_elba_flash_disable_4byte_addr_mode(spiNumber uint32) (err error) {
    _, err = Fpga_spi_generic_transaction(spiNumber, WRITE_DISABLE_4BYTE_ADDR_OP, WRITE_DISABLE_4BYTE_ADDR_RDLNG) 
    return
}


func Spi_elba_flash_read_extended_addr_reg(spiNumber uint32) (ext uint32, err error) {
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_EXTENDED_ADDR_REG_OP, READ_EXTENDED_ADDR_REG_RDLNG) 
    ext = uint32(data[0])
    return
}

func Spi_elba_flash_read_id(spiNumber uint32) (id uint32, err error) {
    var i int
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_ID_OP, READ_ID_RDLNG) 
    for i=0; i<int(READ_ID_RDLNG); i++ {
        id = id | uint32(data[i]) << uint32(i*8)
    }
    return
}


func Spi_elba_flash_write_volatile_config(spiNumber uint32, data uint32) (err error) {
    err = Spi_elba_flash_WriteEnable(spiNumber) 
    if err != nil {
        return
    }

    WRITE_VOLATILE_CONFIG[1] = uint8(data & 0xff)
    fmt.Printf(" WR VOL CONFIG=0x%.02x%.02x\n", WRITE_VOLATILE_CONFIG[1], WRITE_VOLATILE_CONFIG[0])
    _ , err = Fpga_spi_generic_transaction(spiNumber, WRITE_VOLATILE_CONFIG, WRITE_VOLATILE_CONFIG_RDLNG) 
    if err != nil {
        return
    }

    err = Spi_elba_flash_WriteDisable(spiNumber) 

    return
}

func Spi_elba_flash_read_volatile_config(spiNumber uint32) (config byte, err error) {
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_VOLATILE_CONFIG, READ_VOLATILE_CONFIG_RDLNG) 
    config = data[0]
    return
}

func Spi_elba_flash_write_enh_volatile_config(spiNumber uint32, data uint32) (err error) {
    err = Spi_elba_flash_WriteEnable(spiNumber) 
    if err != nil {
        return
    }

    WRITE_ENH_VOLATILE_CONFIG[1] = uint8(data & 0xff)
    fmt.Printf(" WR ENH VOL CONFIG=0x%.02x%.02x\n", WRITE_ENH_VOLATILE_CONFIG[1], WRITE_ENH_VOLATILE_CONFIG[0])
    _ , err = Fpga_spi_generic_transaction(spiNumber, WRITE_ENH_VOLATILE_CONFIG, WRITE_ENH_VOLATILE_CONFIG_RDLNG) 
    if err != nil {
        return
    }

    err = Spi_elba_flash_WriteDisable(spiNumber) 

    return
}

func Spi_elba_flash_read_enhvolatile_config(spiNumber uint32) (config byte, err error) {
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_ENH_VOLATILE_CONFIG, READ_ENH_VOLATILE_CONFIG_RDLNG) 
    config = data[0]
    return
}

func Spi_elba_flash_read_nonvolatile_config(spiNumber uint32) (config uint16, err error) {
    var i int
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_NON_VOLATILE_CONFIG, READ_NON_VOLATILE_CONFIG_RDLNG) 
    for i=0; i<int(READ_NON_VOLATILE_CONFIG_RDLNG); i++ {
        config = config | uint16(data[i]) << uint16(i*8)
    }
    return
}



func Spi_elba_flash_read_status_register(spiNumber uint32) (flag uint32, err error) {
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_STATUS_REG_OP, READ_STATUS_REG_RDLNG) 
    if err == nil {
        flag = uint32(data[0])
    } else {
        fmt.Printf("[ERROR] Spi_elba_flash_read_status_register: Fpga_spi_generic_transaction Failed\n")
    }
    return
}



func Spi_elba_flash_write_status_register(spiNumber uint32, data uint32) (err error) {
    err = Spi_elba_flash_WriteEnable(spiNumber) 
    if err != nil {
        return
    }

    WRITE_STATUS_REG_OP[1] = uint8(data & 0xff)
    fmt.Printf(" WRITE_STATUS_REG_OP=0x%.02x%.02x\n", WRITE_STATUS_REG_OP[1], WRITE_STATUS_REG_OP[0])
    _ , err = Fpga_spi_generic_transaction(spiNumber, WRITE_STATUS_REG_OP, WRITE_STATUS_REG_RDLNG) 
    if err != nil {
        return
    }

    err = Spi_elba_flash_WriteDisable(spiNumber) 

    return
}



func Spi_elba_flash_read_flag_status(spiNumber uint32) (flag uint32, err error) {
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_FLAG_STATUS_REG_OP, READ_FLAG_STATUS_REG_RDLNG) 
    flag = uint32(data[0])
    return
}

//Check if the flash is busy before executing erase or write
func Spi_elba_flash_PollBusyMicroSec(spiNumber uint32, timeout_ms int) (sr_reg uint32, err int) {
    var errGo error
    for i:=0; i<timeout_ms; i++ {
        sr_reg, errGo = Spi_elba_flash_read_status_register(spiNumber)  
        if errGo != nil {
            fmt.Printf("[ERROR] Spi_elba_flash_PollBusyMicroSec-> Read Status Failed\n")
            err = 1
            return
        } 
        if sr_reg & STS_REG_BUSY != STS_REG_BUSY {
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)
    } 
    err = 1
    return 
}

//Check if the flash is busy before executing erase or write
func Spi_elba_flash_PollBusy(spiNumber uint32, timeout_ms int) (sr_reg uint32, err int) {
    var errGo error
    for i:=0; i<timeout_ms; i++ {
        sr_reg, errGo = Spi_elba_flash_read_status_register(spiNumber)  
        if errGo != nil {
            fmt.Printf("[ERROR] Spi_elba_flash_PollBusy-> Read Status Failed\n")
            err = 1
            return
        }
        if sr_reg & STS_REG_BUSY != STS_REG_BUSY {
            return
        }
        time.Sleep(time.Duration(1) * time.Millisecond)
    } 
    err = 1
    return 
}

//Check if the flash is busy before executing erase or write
func Spi_elba_flash_CheckWriteEnable() (spiNumber uint32, err error) {
    var errGo error
    var sr_reg uint32
    for i:=0; i< 5000; i++ {
        sr_reg, errGo = Spi_elba_flash_read_status_register(spiNumber)  
        if errGo != nil {
            fmt.Printf("[ERROR] Spi_elba_flash_CheckWriteEnable-> Read Status Failed\n")
            return
        }
        if sr_reg & STS_REG_WE == STS_REG_WE {
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)  //Sleep ums
    }
    err = fmt.Errorf("ERROR: FlashCheckWriteEnable.  Write Enable is not set: Status Reg=%.02x\n", sr_reg)
    cli.Printf("e", "%s", err)
    return 
}


func Spi_elba_flash_WriteEnable(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, WRITE_ENABLE_OP, WRITE_ENABLE_RDLNG) 
    if err != nil {
        err = fmt.Errorf("ERROR: Spi_elba_flash_WriteEnable Failed\n")
        cli.Printf("e", "%s", err)
    }
    return
}

func Spi_elba_flash_WriteDisable(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, WRITE_DISABLE_OP, WRITE_DISABLE_RDLNG) 
    if err != nil {
        err = fmt.Errorf("ERROR: Spi_elba_flash_WriteEnable Failed\n")
        cli.Printf("e", "%s", err)
    }
    return
}

func Spi_elba_flash_get_partition_info(spiNumber uint32, partition string) (flash_size int, start_addr int, err error) {
    if partition == "uboot0" {
        flash_size = 0x80000
        start_addr = 0x00100000
    } else if partition == "ubootb" {
        flash_size = 0x400000
        start_addr = 0x04600000
    } else if partition == "uboota" {
        flash_size = 0x400000
        start_addr = 0x04200000
    } else if partition == "golduboot" {
        flash_size = 0x200000
        start_addr = 0x00180000
    } else if partition == "goldfw" {
        flash_size = 0x3C00000
        start_addr = 0x00400000 
    } else if partition == "allflash" {
        flash_size = int(elba_flash_info.region_size )
        start_addr = 0
    } else {
        err = fmt.Errorf(" ERROR: parition '%s' is not a valid partition\n", partition)
        cli.Printf("e", "%s", err)
        return
    }

    return
}

//uboot0/golduboot/goldfw/allflash
func Spi_elba_flash_GenerateImageFromFlash(spiNumber uint32, partition string, filename string) (err error) {
    var flash_size int = 0 
    var start_addr int = 0
    var read_size int = int(elba_flash_info.sector_size)
    var i int = 0
    flashData := []byte{}

    flash_size, start_addr, err = Spi_elba_flash_get_partition_info(spiNumber, partition) 
    if err != nil {
        fmt.Printf(" ERROR: Spi_elba_flash_get_partition_info failed\n")
        return
    }

    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }

    defer f.Close()

    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err = Spi_elba_flash_set_extended_addr_register(spiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }


    for i=start_addr; i<(start_addr + flash_size); i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf(".")
        }
        if (i % 0x1000000) <= read_size {
            err = Spi_elba_flash_set_extended_addr_register(spiNumber, uint32(i)) 
            if err != nil {
                return
            }
        }
        rd_data, err = Spi_elba_flash_Read_N_Bytes(spiNumber, uint32(i), uint32(read_size), 0)
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

func Spi_elba_flash_VerifyImage(spiNumber uint32, partition string, filename string) (err error) {
    var flash_size int = 0 
    var start_addr int = 0
    var read_size int = int(elba_flash_info.sector_size)
    var i int = 0
    flashData := []byte{}
    data := []byte{}

    flash_size, start_addr, err = Spi_elba_flash_get_partition_info(spiNumber, partition) 
    if err != nil {
        fmt.Printf(" ERROR: Spi_elba_flash_get_partition_info failed\n")
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

    if len(data) > flash_size {
        err = fmt.Errorf(" Error: Filesize is bigger than flash partition size. %d vs %d\n", len(data), flash_size)
        cli.Printf("e", "%s", err)
        return
    }

    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err = Spi_elba_flash_set_extended_addr_register(spiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }


    //fmt.Printf(" len=%d   mod=%d\n", len(data), (len(data) % read_size))
    for i=start_addr; i< start_addr + len(data); i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf("%.08x\n", uint32(i))
        } 
        if (i % 0x1000000) <= read_size {
            err = Spi_elba_flash_set_extended_addr_register(spiNumber, uint32(i)) 
            if err != nil {
                return
            }
        }
         
        rd_data, err = Spi_elba_flash_Read_N_Bytes(spiNumber, uint32(i), uint32(read_size), 0)
        if err != nil {
            fmt.Printf(" ERROR: Flash Read Failed.  StartAddr=%x.  I=%x\n", start_addr, i)
            return
        }
        flashData = append(flashData, rd_data...) 
    }

    for i=0; i<len(data); i++ {
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


func Spi_elba_flash_WriteImage(spiNumber uint32, partition string, filename string) (err error) {
    var flash_size int = 0 
    var start_addr int = 0
    var i, j int = 0, 0
    var write_page bool = false
    var skipped_pages int = 0
    data := []byte{}

    flash_size, start_addr, err = Spi_elba_flash_get_partition_info(spiNumber, partition) 
    if err != nil {
        fmt.Printf(" ERROR: Spi_elba_flash_get_partition_info failed\n")
        return
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    if len(data) > flash_size {
        err = fmt.Errorf(" Error: Filesize is bigger than flash partition size. %d vs %d\n", len(data), flash_size)
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
        for i=0; i < tmp; i++ {
            data = append(data, 0xFF)
        }
    }

    fmt.Printf(" Start Addr=%x, Len Data File = 0x%x\n", start_addr, len(data));
    fmt.Printf(" Erasing flash sectors\n");
    for i=start_addr; i< start_addr + len(data); i = i+int(elba_flash_info.sector_size) {
        fmt.Printf(".")
        err = Spi_elba_flash_erase_sector(spiNumber, uint32(i))
        if err != nil {
            fmt.Printf(" Erasing Flash Failed\n")
            return
        }
    }
    fmt.Printf("\n")

    /* ////// 
    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    Spi_elba_flash_WriteEnable(spiNumber) 
    
    err = Spi_elba_flash_set_extended_addr_register(spiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }     
    ////// */

    fmt.Printf(" Programming flash sectors\n");
    for i=start_addr; i< start_addr + len(data); i = i+FLASH_PAGE_WRITE_SIZE {

        /* //////
        if (i % 0x1000000) < 256 {
            err = Spi_elba_flash_set_extended_addr_register(spiNumber, uint32(i)) 
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
            err = Spi_elba_flash_Write_N_Bytes(spiNumber, wr_data, uint32(i))
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


func Spi_elba_flash_erase_all_sectors(spiNumber uint32) (err error) {
    //var flash_size int = 0x10000000  //2Gb (256MB)  4096 sectors * 65536
    var i uint32 = 0


    elba_flash_info.region_size = uint32(0x10000000)  // 2Gb / 256megabyte
    elba_flash_info.sector_size = FLASH_SECTOR_SIZE
    elba_flash_info.number_of_sectors = elba_flash_info.region_size / elba_flash_info.sector_size
    elba_flash_info.offset = 0

    fmt.Printf("SPI BUS=%d\n", spiNumber)
    fmt.Printf("Erasing Sector at addr:")
    for i=0; i<elba_flash_info.region_size; i = i + elba_flash_info.sector_size {
        fmt.Printf(".")
        err = Spi_elba_flash_erase_sector(spiNumber, i) 
        if err != nil {
            fmt.Printf("\nERROR: Erase All Sectors Failed\n")
            return
        }
    }
    fmt.Printf("\nErase All Sectors Passed\n")





    return
}


func Spi_elba_flash_erase_sector(spiNumber uint32, addr uint32) (err error) {
    //var flash_size int = 0x10000000  //2Gb (256MB)  4096 sectors * 65536

    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err = Spi_elba_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }
   
    err = Spi_elba_flash_WriteEnable(spiNumber) 
    if err != nil {
        return
    }


    ERASE_SECTOR_OP[1] = byte(addr >> 16)
    ERASE_SECTOR_OP[2] = byte(addr >> 8)
    ERASE_SECTOR_OP[3] = byte(addr)

    _ , err = Fpga_spi_generic_transaction(spiNumber, ERASE_SECTOR_OP, ERASE_SECTOR_RDLNG) 
    if err != nil {
        err = fmt.Errorf("ERROR: Spi_elba_flash_erase_sector Failed.  Erase Addr=%.08x\n", addr)
        cli.Printf("e", "%s", err)
        return
    }

    sr_reg, rc := Spi_elba_flash_PollBusyMicroSec(spiNumber,  ELB_SECTOR_ERASE_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: Spi_elba_flash_erase_sector.  Timeout Waiting for Sector Erase to Compelte.  Address Passsed = 0x%x  Delay = %d.   Status Reg=%.02x\n", addr, ELB_SECTOR_ERASE_DELAY, sr_reg)
       cli.Printf("e", "%s", err)
    }
    return


    err = Spi_elba_flash_WriteDisable(spiNumber) 


    return
}


func Spi_elba_flash_Write_N_Bytes(spiNumber uint32, data []byte, addr uint32) (err error) {
    wr_data := []byte{}

    if addr > elba_flash_info.region_size {
        err = fmt.Errorf("ERROR: Spi_elba_flash_Write_N_Bytes.  Address passed (0x%x) is greather than flash size - %x\n", addr, elba_flash_info.region_size)
        cli.Printf("e", "%s", err)
        return
    }
    if len(data) > FLASH_PAGE_WRITE_SIZE {
        err = fmt.Errorf("ERROR: Spi_elba_flash_Write_N_Bytes.  Number of bytes passed is to many to program with one page write.  Max=%d.  You passed %d bytes\n", FLASH_PAGE_WRITE_SIZE, len(data))
        cli.Printf("e", "%s", err)
        return
    }

    
    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err = Spi_elba_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    } 

    Spi_elba_flash_WriteEnable(spiNumber) 
     

    PAGE_PROGRAM_OP[1] = byte(addr >> 16)
    PAGE_PROGRAM_OP[2] = byte(addr >> 8)
    PAGE_PROGRAM_OP[3] = byte(addr)

    wr_data = append(wr_data, PAGE_PROGRAM_OP...)
    wr_data = append(wr_data, data...)

    data, err = Fpga_spi_generic_transaction(spiNumber, wr_data, PAGE_PROGRAM_RDLNG) 
    if err != nil {
       fmt.Printf("ERROR: Spi_elba_flash_Write_N_Bytes.  Fpga_spi_generic_transaction Failed\n")
    }

    sr_reg, rc := Spi_elba_flash_PollBusyMicroSec(spiNumber,  ELB_PAGE_WR_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: Spi_elba_flash_Write_N_Bytes.  Timeout Waiting for Sector Erase to Compelte.  Address Passsed = 0x%x  Delay = %d.   Status Reg=%.02x\n", addr, ELB_PAGE_WR_DELAY, sr_reg)
       cli.Printf("e", "%s", err)
       return
    }

    //err = Spi_elba_flash_WriteDisable(spiNumber) 
    //if err != nil {
    //   fmt.Printf("ERROR: Spi_elba_flash_Write_N_Bytes.  Spi_elba_flash_WriteDisable Failed\n")
    //}
    return
}


func Spi_elba_flash_FourByteAddr_Read_N_Bytes(spiNumber uint32, addr uint32, length uint32) (data []byte, err error) {
    /*
    err = Spi_elba_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }

    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }
    */

    err = Spi_elba_flash_enable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    READ_OP[1] = byte(addr >> 16)
    READ_OP[2] = byte(addr >> 8)
    READ_OP[3] = byte(addr)
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_FOUR_BYTE_OP, length) 
    return
}


func Spi_elba_flash_Read_N_Bytes(spiNumber uint32, addr uint32, length uint32, cli_call uint32) (data []byte, err error) {
    if (cli_call > 0) {
        err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
        if err != nil {
            return
        }

        err = Spi_elba_flash_set_extended_addr_register(spiNumber, addr) 
        if err != nil {
            return
        }
    }
    READ_OP[1] = byte(addr >> 16)
    READ_OP[2] = byte(addr >> 8)
    READ_OP[3] = byte(addr)
    data, err = Fpga_spi_generic_transaction(spiNumber, READ_OP, length) 
    return
}


func Spi_elba_flash_DualOp_Read_N_Bytes(spiNumber uint32, addr uint32, length uint32) (data []byte, err error) {

    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err = Spi_elba_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }

    DUAL_READ_OP[1] = byte(addr >> 16)
    DUAL_READ_OP[2] = byte(addr >> 8)
    DUAL_READ_OP[3] = byte(addr)
    data, err = Fpga_spi_generic_transaction(spiNumber, DUAL_READ_OP, length) 
    return
}


func Spi_elba_flash_DualOp_FastRead_N_Bytes(spiNumber uint32, addr uint32, length uint32) (data []byte, err error) {

    err = Spi_elba_flash_disable_4byte_addr_mode(spiNumber)
    if err != nil {
        return
    }

    err = Spi_elba_flash_set_extended_addr_register(spiNumber, addr) 
    if err != nil {
        return
    }

    DUAL_FAST_READ_OP[1] = byte(addr >> 16)
    DUAL_FAST_READ_OP[2] = byte(addr >> 8)
    DUAL_FAST_READ_OP[3] = byte(addr)
    data, err = Fpga_spi_generic_transaction(spiNumber, DUAL_FAST_READ_OP, length) 
    return
}

