/* 
 
   Code ported from Lipari and Taormina to reflash elba qspi.
   We cannot used it on Ortano cards on Matera.
   File will need touch up for Salina bring up board 
*/
package materafpga

import (
    //"errors"
    "common/cli"
    "fmt"
    "os"
    "bufio"
    "time"
    "hardware/i2cinfo"
)

/*
 * Description of a single Erase region
 */
type flash_region struct {
  offset            uint32
  region_size       uint32
  number_of_sectors  uint32
  sector_size        uint32
} 


var elba_flash_info flash_region

const FLASH_SECTOR_SIZE    uint32 = 0x10000


const STS_REG_WIP   uint32 = 0x01    //WRITE IN PROGRESS
const STS_REG_WE    uint32 = 0x02    //WRITE ENABLE
const STS_REG_BP0   uint32 = 0x04
const STS_REG_BP1   uint32 = 0x08
const STS_REG_BP2   uint32 = 0x10
const STS_REG_TBP   uint32 = 0x20
const STS_REG_SP    uint32 = 0x40
const STS_REG_SRP   uint32 = 0x80


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

var READ_FLASH_DISCOVERY_OP             = []byte{0x5A, 0x00, 0x00, 0x00, 0x00}
var READ_FLASH_DISCOVERY_RDLNG          uint32 = 2048

var READ_FLASH_GENERAL_PURP_OP          = []byte{0x96, 0x00}
var READ_FLASH_GENERAL_PURP_RDLNG       uint32 = 64

var READ_FLAG_STATUS_REG_OP             = []byte{0x70}
var READ_FLAG_STATUS_REG_RDLNG          uint32 = 1

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
var WRITE_NON_VOLATILE_CONFIG           = []byte{0xB1, 0x00, 0x00}
var WRITE_NON_VOLATILE_CONFIG_RDLNG     uint32 = 0

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

//sector protection register
var READ_SECTOR_PROT_REG_OP           = []byte{0x2D}
var READ_SECTOR_PROT_REG_RDLNG        uint32 = 2 
//volatile lock 
var READ_VOLATILE_LOCK_REG_OP         = []byte{0xE8, 0x00, 0x00, 0x00}
var READ_VOLATILE_LOCK_REG_RDLNG      uint32 = 1 
//global freeze register
var READ_GLOBAL_FREEZE_REG_OP         = []byte{0xA7}
var READ_GLOBAL_FREEZE_REG_RDLNG      uint32 = 1 

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
    elba_flash_info.region_size = uint32(0x10000000)  // 2Gb/256MB  
    elba_flash_info.sector_size = FLASH_SECTOR_SIZE
    elba_flash_info.number_of_sectors = elba_flash_info.region_size / elba_flash_info.sector_size
    elba_flash_info.offset = 0
}


func UpdateFlashSize(slot uint32) () {
    uut := fmt.Sprintf("UUT_%d", slot+1)
    uutType, _ := i2cinfo.FindUutTypeMtp(uut) 
    if uutType == "POLLARA" {
        elba_flash_info.region_size = uint32(0x2000000)  //32MB 
        elba_flash_info.number_of_sectors = elba_flash_info.region_size / elba_flash_info.sector_size
    }
}


func  Spi_flash_set_extended_addr_register_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, addr uint32, spiBusEnable bool) (err error) {
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
        err = fmt.Errorf("ERROR:  Spi_flash_set_extended_addr_register.  Passed Address if to greater than the flash size.  Spi=%d Addr=%.08x\n", spiNumber, addr)
        cli.Printf("e", "%s", err)
        return
    }

    err = Spi_flash_WriteEnable_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable) 
    if err != nil {
        return
    }
    err = Spi_flash_CheckWriteEnable_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable)
    if err != nil {
        return
    }

    _ , err = matera_spi_generic_transaction_w_spiBus_enable(spiNumber, qspiNumber, WRITE_EXTENDED_ADDR_REG_OP, WRITE_EXTENDED_ADDR_REG_RDLNG, spiBusEnable) 
    if err != nil {
        return
    }

    return
}

func  Spi_flash_set_extended_addr_register(spiNumber uint32, qspiNumber uint32, addr uint32) (err error) {
    return Spi_flash_set_extended_addr_register_w_spiBus_enable(spiNumber, qspiNumber, addr, true)
}


func Spi_flash_enable_4byte_addr_mode(spiNumber uint32, qspiNumber uint32) (err error) {
    _, err = matera_spi_generic_transaction(spiNumber, qspiNumber, WRITE_ENABLE_4BYTE_ADDR_OP, WRITE_ENABLE_4BYTE_ADDR_RDLNG) 
    return
}


func Spi_flash_disable_4byte_addr_mode_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, spiBusEnable bool) (err error) {
    _, err = matera_spi_generic_transaction_w_spiBus_enable(spiNumber, qspiNumber, WRITE_DISABLE_4BYTE_ADDR_OP, WRITE_DISABLE_4BYTE_ADDR_RDLNG, spiBusEnable) 
    return
}

func Spi_flash_disable_4byte_addr_mode(spiNumber uint32, qspiNumber uint32) (err error) {
    return Spi_flash_disable_4byte_addr_mode_w_spiBus_enable(spiNumber, qspiNumber, true)
}


func Spi_flash_read_extended_addr_reg(spiNumber uint32, qspiNumber uint32) (ext uint32, err error) {
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_EXTENDED_ADDR_REG_OP, READ_EXTENDED_ADDR_REG_RDLNG) 
    ext = uint32(data[0])
    return
}


func Spi_flash_read_id(spiNumber uint32, qspiNumber uint32) (id uint32, err error) {
    var i int
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_ID_OP, READ_ID_RDLNG) 
    for i=0; i<int(READ_ID_RDLNG); i++ {
        id = id | uint32(data[i]) << uint32(i*8)
    }
    return
}


func Spi_flash_read_sector_protection_reg(spiNumber uint32, qspiNumber uint32) (reg uint32, err error) {
    var i int
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_SECTOR_PROT_REG_OP, READ_SECTOR_PROT_REG_RDLNG) 
    for i=0; i<int(READ_SECTOR_PROT_REG_RDLNG); i++ {
        reg = reg | uint32(data[i]) << uint32(i*8)
    }
    return
}


func Spi_flash_read_volatile_lock_reg(spiNumber uint32, qspiNumber uint32) (reg uint32, err error) {
    var i int
    data := []byte{}
    READ_VOLATILE_LOCK_REG_OP[1] = 0x00
    READ_VOLATILE_LOCK_REG_OP[2] = 0x00
    READ_VOLATILE_LOCK_REG_OP[3] = 0x00
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_VOLATILE_LOCK_REG_OP, READ_VOLATILE_LOCK_REG_RDLNG) 
    for i=0; i<int(READ_VOLATILE_LOCK_REG_RDLNG); i++ {
        reg = reg | uint32(data[i]) << uint32(i*8)
    }
    return
}


func Spi_flash_read_global_freeze_reg(spiNumber uint32, qspiNumber uint32) (reg uint32, err error) {
    var i int
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_GLOBAL_FREEZE_REG_OP, READ_GLOBAL_FREEZE_REG_RDLNG) 
    for i=0; i<int(READ_GLOBAL_FREEZE_REG_RDLNG); i++ {
        reg = reg | uint32(data[i]) << uint32(i*8)
    }
    return
}


func Spi_flash_write_volatile_config(spiNumber uint32, qspiNumber uint32, data uint32) (err error) {
    err = Spi_flash_WriteEnable(spiNumber, qspiNumber) 
    if err != nil {
        return
    }
    err = Spi_flash_CheckWriteEnable(spiNumber, qspiNumber)
    if err != nil {
        return
    }

    WRITE_VOLATILE_CONFIG[1] = uint8(data & 0xff)
    fmt.Printf(" WR VOL CONFIG=0x%.02x%.02x\n", WRITE_VOLATILE_CONFIG[1], WRITE_VOLATILE_CONFIG[0])
    _ , err = matera_spi_generic_transaction(spiNumber, qspiNumber, WRITE_VOLATILE_CONFIG, WRITE_VOLATILE_CONFIG_RDLNG) 
    if err != nil {
        return
    }

    err = Spi_flash_WriteDisable(spiNumber, qspiNumber) 

    return
}


func Spi_flash_read_volatile_config(spiNumber uint32, qspiNumber uint32) (config byte, err error) {
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_VOLATILE_CONFIG, READ_VOLATILE_CONFIG_RDLNG) 
    config = data[0]
    return
}


func Spi_flash_write_enh_volatile_config(spiNumber uint32, qspiNumber uint32, data uint32) (err error) {
    err = Spi_flash_WriteEnable(spiNumber, qspiNumber) 
    if err != nil {
        return
    }
    err = Spi_flash_CheckWriteEnable(spiNumber, qspiNumber)
    if err != nil {
        return
    }

    WRITE_ENH_VOLATILE_CONFIG[1] = uint8(data & 0xff)
    fmt.Printf(" WR ENH VOL CONFIG=0x%.02x%.02x\n", WRITE_ENH_VOLATILE_CONFIG[1], WRITE_ENH_VOLATILE_CONFIG[0])
    _ , err = matera_spi_generic_transaction(spiNumber, qspiNumber, WRITE_ENH_VOLATILE_CONFIG, WRITE_ENH_VOLATILE_CONFIG_RDLNG) 
    if err != nil {
        return
    }

    err = Spi_flash_WriteDisable(spiNumber, qspiNumber) 

    return
}


func Spi_flash_read_enhvolatile_config(spiNumber uint32, qspiNumber uint32) (config byte, err error) {
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_ENH_VOLATILE_CONFIG, READ_ENH_VOLATILE_CONFIG_RDLNG) 
    config = data[0]
    return
}


func Spi_flash_read_nonvolatile_config(spiNumber uint32, qspiNumber uint32) (config uint16, err error) {
    var i int
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_NON_VOLATILE_CONFIG, READ_NON_VOLATILE_CONFIG_RDLNG) 
    for i=0; i<int(READ_NON_VOLATILE_CONFIG_RDLNG); i++ {
        config = config | uint16(data[i]) << uint16(i*8)
    }
    return
}


func Spi_flash_write_nonvolatile_config(spiNumber uint32, qspiNumber uint32, data16 uint16) (err error) {
    err = Spi_flash_WriteEnable(spiNumber, qspiNumber) 
    if err != nil {
        return
    }
    err = Spi_flash_CheckWriteEnable(spiNumber, qspiNumber)
    if err != nil {
        return
    } 
    WRITE_NON_VOLATILE_CONFIG[1] = uint8(data16 >> 8)
    WRITE_NON_VOLATILE_CONFIG[2] = uint8(data16 & 0xFF)
    _, err = matera_spi_generic_transaction(spiNumber, qspiNumber, WRITE_NON_VOLATILE_CONFIG, WRITE_NON_VOLATILE_CONFIG_RDLNG) 
    return
}


func Spi_flash_read_status_register_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, spiBusEnable bool) (flag uint32, err error) {
    data := []byte{}
    data, err = matera_spi_generic_transaction_w_spiBus_enable(spiNumber, qspiNumber, READ_STATUS_REG_OP, READ_STATUS_REG_RDLNG, spiBusEnable) 
    if err == nil {
        flag = uint32(data[0])
    } else {
        fmt.Printf("ERROR: Spi-%d Qspi-%d:Spi_flash_read_status_register Failed\n", spiNumber, qspiNumber)
    }
    return
}


func Spi_flash_read_status_register(spiNumber uint32, qspiNumber uint32) (flag uint32, err error) {
    return Spi_flash_read_status_register_w_spiBus_enable(spiNumber, qspiNumber, true)
}


func Spi_flash_write_status_register(spiNumber uint32, qspiNumber uint32, data uint32) (err error) {
    err = Spi_flash_WriteEnable(spiNumber, qspiNumber) 
    if err != nil {
        return
    }
    err = Spi_flash_CheckWriteEnable(spiNumber, qspiNumber)
    if err != nil {
        return
    } 
     

    WRITE_STATUS_REG_OP[1] = uint8(data & 0xff)
    fmt.Printf(" WRITE_STATUS_REG_OP=0x%.02x%.02x\n", WRITE_STATUS_REG_OP[1], WRITE_STATUS_REG_OP[0])
    _ , err = matera_spi_generic_transaction(spiNumber, qspiNumber, WRITE_STATUS_REG_OP, WRITE_STATUS_REG_RDLNG) 
    if err != nil {
        return
    }

    err = Spi_flash_WriteDisable(spiNumber, qspiNumber) 

    return
}


func Spi_flash_discover_read(spiNumber uint32, qspiNumber uint32) (data []byte, err error) {
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_FLASH_DISCOVERY_OP, READ_FLASH_DISCOVERY_RDLNG) 
    return
}


func Spi_flash_read_general_purpose(spiNumber uint32, qspiNumber uint32) (data []byte, err error) {
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_FLASH_GENERAL_PURP_OP, READ_FLASH_GENERAL_PURP_RDLNG) 
    return
}


func Spi_flash_read_flag_status(spiNumber uint32, qspiNumber uint32) (flag uint32, err error) {
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_FLAG_STATUS_REG_OP, READ_FLAG_STATUS_REG_RDLNG) 
    flag = uint32(data[0])
    return
}


//Check if the flash is busy before executing erase or write
func Spi_flash_Poll_STS_WIP_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, timeout_ms int, spiBusEnable bool) (sr_reg uint32, err int) {
    var errGo error
    for i:=0; i<timeout_ms; i++ {
        sr_reg, errGo = Spi_flash_read_status_register_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable)  
        if errGo != nil {
            fmt.Printf("ERROR: Spi_flash_Poll_STS_WIP-> Read Status Failed\n")
            err = 1
            return
        } 
        if sr_reg & STS_REG_WIP != STS_REG_WIP {
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)
    } 
    err = 1
    return 
}


func Spi_flash_Poll_STS_WIP(spiNumber uint32, qspiNumber uint32, timeout_ms int) (sr_reg uint32, err int) {
    return Spi_flash_Poll_STS_WIP_w_spiBus_enable(spiNumber, qspiNumber, timeout_ms, true)
}


//Check if the flash is busy before executing erase or write
func Spi_flash_CheckWriteEnable_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, spiBusEnable bool) (err error) {
    var errGo error
    var sr_reg uint32
    for i:=0; i< 5000; i++ {
        sr_reg, errGo = Spi_flash_read_status_register_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable)  
        if errGo != nil {
            fmt.Printf("ERROR: Slot-%d Qspi-%d: Spi_flash_CheckWriteEnable-> Read Status Failed\n", spiNumber+1, qspiNumber)
            return
        }
        if sr_reg & STS_REG_WE == STS_REG_WE {
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)  //Sleep ums
    }
    err = fmt.Errorf("ERROR: Slot-%d Qspi-%d: FlashCheckWriteEnable.  Write Enable is not set: Status Reg=%.02x\n", spiNumber+1, qspiNumber, sr_reg)
    cli.Printf("e", "%s", err)
    return 
}


func Spi_flash_CheckWriteEnable(spiNumber uint32, qspiNumber uint32) (err error) {
    return Spi_flash_CheckWriteEnable_w_spiBus_enable(spiNumber, qspiNumber, true)
}


func Spi_flash_WriteEnable_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, spiBusEnable bool) (err error) {
    _ , err = matera_spi_generic_transaction_w_spiBus_enable(spiNumber, qspiNumber, WRITE_ENABLE_OP, WRITE_ENABLE_RDLNG, spiBusEnable)
    if err != nil {
        err = fmt.Errorf("ERROR: Slot-%d Qspi-%d: Spi_flash_WriteEnable Failed\n", spiNumber+1, qspiNumber)
        cli.Printf("e", "%s", err)
    }
    return
}


func Spi_flash_WriteEnable(spiNumber uint32, qspiNumber uint32) (err error) {
    return Spi_flash_WriteEnable_w_spiBus_enable(spiNumber, qspiNumber, true)
}


func Spi_flash_WriteEnableReadSR(spiNumber uint32, qspiNumber uint32) (flag uint32, err error) {
    data := []byte{}
    _ , err = matera_spi_generic_transaction(spiNumber, qspiNumber, WRITE_ENABLE_OP, WRITE_ENABLE_RDLNG)
    if err != nil {
        err = fmt.Errorf("ERROR: Slot-%d Qspi-%d: Spi_flash_WriteEnable Failed\n", spiNumber+1, qspiNumber)
        cli.Printf("e", "%s", err)
    }
    
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_STATUS_REG_OP, READ_STATUS_REG_RDLNG) 
    if err == nil {
        flag = uint32(data[0])
    } else {
        err = fmt.Errorf("ERROR: Slot-%d Qspi-%d:Spi_flash_read_status_register Failed\n", spiNumber+1, qspiNumber)
        cli.Printf("e", "%s", err)
    }
    return
}


func Spi_flash_WriteDisable(spiNumber uint32, qspiNumber uint32) (err error) {
    _ , err = matera_spi_generic_transaction(spiNumber, qspiNumber, WRITE_DISABLE_OP, WRITE_DISABLE_RDLNG) 
    if err != nil {
        err = fmt.Errorf("ERROR: Slot-%d Qspi-%d:  Spi_flash_WriteDisable Failed\n", spiNumber+1, qspiNumber)
        cli.Printf("e", "%s", err)
    }
    return
}

func Spi_salina_flash_get_partition_info(spiNumber uint32, partition string) (flash_size int, start_addr int, err error) {
    if partition == "uboot0" {
        flash_size = 0x20000
        start_addr = 0x00100000
    } else if partition == "ubootb" {
        flash_size = 0x800000
        start_addr = 0x07000000
    } else if partition == "uboota" {
        flash_size = 0x800000
        start_addr = 0x06800000
    } else if partition == "zephyr_llc" {
        flash_size = 0x01000000
        start_addr = 0x04A00000
    } else if partition == "golduboot" {
        flash_size = 0x200000
        start_addr = 0x00180000
    } else if partition == "goldfw" {
        flash_size = 0x3C00000
        start_addr = 0x00400000 
    } else if partition == "allflash" {
        //Check if the card is Pollara which has a 32MB flash
        UpdateFlashSize(spiNumber)
        flash_size = int(elba_flash_info.region_size )
        start_addr = 0
    } else {
        err = fmt.Errorf(" ERROR: parition '%s' is not a valid partition\n", partition)
        cli.Printf("e", "%s", err)
        return
    }

    return
}


/*************************************************************************************************** 
* 
* valid partition strings --> uboot0/uboota/ubootb/golduboot/goldfw/allflash 
* 
****************************************************************************************************/ 
func Spi_salina_flash_GenerateImageFromFlash(spiNumber uint32, qspiNumber uint32, partition string, filename string) (err error) {
    var flash_size int = 0 
    var start_addr int = 0
    var read_size int = int(elba_flash_info.sector_size)
    var i int = 0
    flashData := []byte{}

    flash_size, start_addr, err = Spi_salina_flash_get_partition_info(spiNumber, partition) 
    if err != nil {
        fmt.Printf(" ERROR: Slot-%d Qspi-%d: Spi_salina_flash_get_partition_info failed\n", spiNumber+1, qspiNumber)
        return
    }

    err = Spi_flash_disable_4byte_addr_mode(spiNumber, qspiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, qspiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }


    for i=start_addr; i<(start_addr + flash_size); i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf(".")
        }
        if (i % 0x1000000) <= read_size {
            err =  Spi_flash_set_extended_addr_register(spiNumber, qspiNumber, uint32(i)) 
            if err != nil {
                return
            }
        }
        rd_data, err = Spi_salina_flash_Read_N_Bytes(spiNumber, qspiNumber, uint32(i), uint32(read_size), 0)
        if err != nil {
            fmt.Printf("ERROR: Slot-%d Qspi-%d: Flash Read Failed\n", spiNumber+1, qspiNumber)
            return
        }
        flashData = append(flashData, rd_data...)
    }
    fmt.Printf("\n")

    //Write image to a file
    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf("ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    f.WriteString(string(flashData[:]))
    f.Close()
    return
}


func Spi_salina_flash_VerifyImage(spiNumber uint32, qspiNumber uint32, partition string, filename string) (err error) {
    var flash_size int = 0 
    var start_addr int = 0
    var read_size int = int(elba_flash_info.sector_size)
    var i int = 0
    flashData := []byte{}
    data := []byte{}

    flash_size, start_addr, err = Spi_salina_flash_get_partition_info(spiNumber, partition) 
    if err != nil {
        fmt.Printf(" ERROR: Slot-%d Qspi-%d:  Spi_salina_flash_get_partition_info failed\n", spiNumber+1, qspiNumber)
        return
    }


    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }

    fmt.Printf(" Verifying Image %s starting at addr=0x%x\n", filename, start_addr)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)
    for scanner.Scan() {
        b := scanner.Bytes()
        data = append(data, b[0])
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        f.Close()
        return
    }
    f.Close()

    if len(data) > flash_size {
        err = fmt.Errorf(" Error: Filesize is bigger than flash partition size. %d vs %d\n", len(data), flash_size)
        cli.Printf("e", "%s", err)
        return
    }

    err = Spi_flash_disable_4byte_addr_mode(spiNumber, qspiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, qspiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }

    for i=start_addr; i< start_addr + len(data); i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf("%.08x\n", uint32(i))
        } 
        if (i % 0x1000000) <= read_size {
            err =  Spi_flash_set_extended_addr_register(spiNumber, qspiNumber, uint32(i)) 
            if err != nil {
                return
            }
        }
         
        rd_data, err = Spi_salina_flash_Read_N_Bytes(spiNumber, qspiNumber, uint32(i), uint32(read_size), 0)
        if err != nil {
            fmt.Printf(" ERROR: Slot-%d Qspi-%d: Flash Read Failed.  StartAddr=%x.  I=%x\n", spiNumber+1, qspiNumber, start_addr, i)
            return
        }
        flashData = append(flashData, rd_data...) 
    }

    for i=0; i<len(data); i++ {
        if flashData[i] != data[i] {
            err = fmt.Errorf(" Error:  Slot-%d Qspi-%d:  Flash Miscompare at flash address 0x%x:  Flash Read %.02x   File Read %.02x\n", spiNumber+1, qspiNumber, i+start_addr, flashData[i], data[i])
            cli.Printf("e", "%s", err)
            fmt.Printf("Verification failed\n")
            return
        }
    }
    fmt.Printf("\nVerification passed\n")
    return
}


func Spi_salina_flash_WriteImage(spiNumber uint32, qspiNumber uint32, partition string, filename string) (err error) {
    var flash_size int = 0 
    var start_addr int = 0
    var i, j int = 0, 0
    var write_page bool = false
    var skipped_pages int = 0
    data := []byte{}

    flash_size, start_addr, err = Spi_salina_flash_get_partition_info(spiNumber, partition) 
    if err != nil {
        fmt.Printf(" ERROR: Slot-%d Qspi-%d:  Spi_salina_flash_get_partition_info failed\n", spiNumber+1, qspiNumber)
        return
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }

    if len(data) > flash_size {
        err = fmt.Errorf(" Error: Filesize is bigger than flash partition size. %d vs %d\n", len(data), flash_size)
        cli.Printf("e", "%s", err)
        f.Close()
        return
    }
    fmt.Printf(" Writing Image %s starting at addr=0x%x\n", filename, start_addr)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)
    for scanner.Scan() {
        b := scanner.Bytes()
        data = append(data, b[0])
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        f.Close()
        return
    }
    f.Close()

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
        err = Spi_salina_flash_erase_sector(spiNumber, qspiNumber, uint32(i))
        if err != nil {
            fmt.Printf("ERROR: Slot-%d Qspi-%d: Erasing Flash Failed\n", spiNumber+1, qspiNumber)
            return
        }
    }
    fmt.Printf("\n")


    fmt.Printf(" Programming flash sectors\n");
    for i=start_addr; i< start_addr + len(data); i = i+FLASH_PAGE_WRITE_SIZE {
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
            err = Spi_salina_flash_Write_N_Bytes(spiNumber, qspiNumber, wr_data, uint32(i))
            if err != nil {
                fmt.Printf("ERROR:  Slot-%d Qspi-%d:  Writing Flash Failed\n", spiNumber+1, qspiNumber)
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


func Spi_salina_flash_erase_all_sectors(spiNumber uint32, qspiNumber uint32) (err error) {
    var i uint32 = 0

    //Check if the card is Pollara which has a 32MB flash
    UpdateFlashSize(spiNumber)

    fmt.Printf("SPI BUS=%d QSPI=%d\n", spiNumber, qspiNumber)
    fmt.Printf("Erasing Sector at addr:")
    for i=0; i<elba_flash_info.region_size; i = i + elba_flash_info.sector_size {
        fmt.Printf(".")
        err = Spi_salina_flash_erase_sector_w_spiBus_enable(spiNumber, qspiNumber, i, false) 
        if err != nil {
            fmt.Printf("\nERROR: Erase All Sectors Failed.  Slot-%d Qspi-%d:\n", spiNumber+1, qspiNumber)
            return
        }
    }
    fmt.Printf("\nErase All Sectors Passed\n")
    return
}


func Spi_salina_flash_erase_sector_w_spiBus_enable(spiNumber uint32, qspiNumber uint32,  addr uint32, spiBusEnable bool) (err error) {
    err = Spi_flash_disable_4byte_addr_mode_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register_w_spiBus_enable(spiNumber, qspiNumber, addr, spiBusEnable) 
    if err != nil {
        return
    }
   
    err = Spi_flash_WriteEnable_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable) 
    if err != nil {
        return
    }
    err = Spi_flash_CheckWriteEnable_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable)
    if err != nil {
        return
    }


    ERASE_SECTOR_OP[1] = byte(addr >> 16)
    ERASE_SECTOR_OP[2] = byte(addr >> 8)
    ERASE_SECTOR_OP[3] = byte(addr)

    _ , err = matera_spi_generic_transaction_w_spiBus_enable(spiNumber, qspiNumber, ERASE_SECTOR_OP, ERASE_SECTOR_RDLNG, spiBusEnable)
    if err != nil {
        err = fmt.Errorf("ERROR: Spi_salina_flash_erase_sector Failed. Slot-%d Qspi-%d:  Erase Addr=%.08x\n", spiNumber+1, qspiNumber, addr)
        cli.Printf("e", "%s", err)
        return
    }

    sr_reg, rc := Spi_flash_Poll_STS_WIP_w_spiBus_enable(spiNumber, qspiNumber, ELB_SECTOR_ERASE_DELAY, spiBusEnable)
    if rc != 0 {
       err = fmt.Errorf("ERROR: Spi_salina_flash_erase_sector.  Slot-%d Qspi-%d: Timeout Waiting for Sector Erase to Compelte.  Address Passsed = 0x%x  Delay = %d.   Status Reg=%.02x\n", spiNumber+1, qspiNumber, addr, ELB_SECTOR_ERASE_DELAY, sr_reg)
       cli.Printf("e", "%s", err)
    }
    return
}


func Spi_salina_flash_erase_sector(spiNumber uint32, qspiNumber uint32,  addr uint32) (err error) {
    return Spi_salina_flash_erase_sector_w_spiBus_enable(spiNumber, qspiNumber, addr, true)
}


func Spi_salina_flash_Write_N_Bytes_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, data []byte, addr uint32, spiBusEnable bool) (err error) {
    wr_data := []byte{}

    //Check if the card is Pollara which has a 32MB flash
    UpdateFlashSize(spiNumber)
    
    if addr > elba_flash_info.region_size {
        err = fmt.Errorf("ERROR: Spi_salina_flash_Write_N_Bytes. Slot-%d Qspi-%d  Address passed (0x%x) is greather than flash size - %x\n", spiNumber+1, qspiNumber,  addr, elba_flash_info.region_size)
        cli.Printf("e", "%s", err)
        return
    }
    if len(data) > FLASH_PAGE_WRITE_SIZE {
        err = fmt.Errorf("ERROR: Spi_salina_flash_Write_N_Bytes. Slot-%d Qspi-%d  Number of bytes passed is to many to program with one page write.  Max=%d.  You passed %d bytes\n", spiNumber+1, qspiNumber, FLASH_PAGE_WRITE_SIZE, len(data))
        cli.Printf("e", "%s", err)
        return
    }

    
    err = Spi_flash_disable_4byte_addr_mode_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register_w_spiBus_enable(spiNumber, qspiNumber, addr, spiBusEnable) 
    if err != nil {
        return
    } 

    Spi_flash_WriteEnable_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable) 
    err = Spi_flash_CheckWriteEnable_w_spiBus_enable(spiNumber, qspiNumber, spiBusEnable)
    if err != nil {
        return
    }
     
    PAGE_PROGRAM_OP[1] = byte(addr >> 16)
    PAGE_PROGRAM_OP[2] = byte(addr >> 8)
    PAGE_PROGRAM_OP[3] = byte(addr)

    wr_data = append(wr_data, PAGE_PROGRAM_OP...)
    wr_data = append(wr_data, data...)

    data, err = matera_spi_generic_transaction_w_spiBus_enable(spiNumber, qspiNumber, wr_data, PAGE_PROGRAM_RDLNG, spiBusEnable) 
    if err != nil {
       err = fmt.Errorf("ERROR: Spi_salina_flash_Write_N_Bytes.  Slot-%d Qspi-%d: matera_spi_generic_transaction Failed\n", spiNumber+1, qspiNumber,)
       cli.Printf("e", "%s", err)
    }

    sr_reg, rc := Spi_flash_Poll_STS_WIP_w_spiBus_enable(spiNumber, qspiNumber, ELB_PAGE_WR_DELAY, spiBusEnable)
    if rc != 0 {
       err = fmt.Errorf("ERROR: Spi_salina_flash_Write_N_Bytes.  Slot-%d Qspi-%d: Timeout Waiting for Write To Compelte.  Address Passsed = 0x%x  Delay = %d.   Status Reg=%.02x\n", spiNumber+1, qspiNumber, addr, ELB_PAGE_WR_DELAY, sr_reg)
       cli.Printf("e", "%s", err)
       return
    }

    return
}


func Spi_salina_flash_Write_N_Bytes(spiNumber uint32, qspiNumber uint32, data []byte, addr uint32) (err error) {
    return Spi_salina_flash_Write_N_Bytes_w_spiBus_enable(spiNumber, qspiNumber, data, addr, true)
}


func Spi_salina_flash_FourByteAddr_Read_N_Bytes(spiNumber uint32, qspiNumber uint32, addr uint32, length uint32) (data []byte, err error) {

    err = Spi_flash_enable_4byte_addr_mode(spiNumber, qspiNumber)
    if err != nil {
        return
    }

    READ_OP[1] = byte(addr >> 16)
    READ_OP[2] = byte(addr >> 8)
    READ_OP[3] = byte(addr)
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_FOUR_BYTE_OP, length) 
    return
}


func Spi_salina_flash_Read_N_Bytes_w_spiBus_enable(spiNumber uint32, qspiNumber uint32, addr uint32, length uint32, cli_call uint32, spiBusEnable bool) (data []byte, err error) {

    READ_OP[1] = byte(addr >> 16)
    READ_OP[2] = byte(addr >> 8)
    READ_OP[3] = byte(addr)
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, READ_OP, length) 
    return
}


func Spi_salina_flash_Read_N_Bytes(spiNumber uint32, qspiNumber uint32, addr uint32, length uint32, cli_call uint32) (data []byte, err error) {
    return Spi_salina_flash_Read_N_Bytes_w_spiBus_enable(spiNumber, qspiNumber, addr, length, cli_call, true)
}



func Spi_salina_flash_DualOp_Read_N_Bytes(spiNumber uint32, qspiNumber uint32, addr uint32, length uint32) (data []byte, err error) {

    DUAL_READ_OP[1] = byte(addr >> 16)
    DUAL_READ_OP[2] = byte(addr >> 8)
    DUAL_READ_OP[3] = byte(addr)
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, DUAL_READ_OP, length) 
    return
}


func Spi_salina_flash_DualOp_FastRead_N_Bytes(spiNumber uint32, qspiNumber uint32, addr uint32, length uint32) (data []byte, err error) {

    DUAL_FAST_READ_OP[1] = byte(addr >> 16)
    DUAL_FAST_READ_OP[2] = byte(addr >> 8)
    DUAL_FAST_READ_OP[3] = byte(addr)
    data, err = matera_spi_generic_transaction(spiNumber, qspiNumber, DUAL_FAST_READ_OP, length) 
    return
}


// Only used by QSPI programming, skip SPI bus enable
func Spi_salina_flash_WriteFile(spiNumber uint32, qspiNumber uint32, start_addr uint32, filename string)(err error) {
    var flash_size uint32
    var i, count int = 0, 0
    var j uint32 = 0
    var write_page bool = false
    var skipped_pages int = 0

    //Check if the card is Pollara which has a 32MB flash
    UpdateFlashSize(spiNumber)
    flash_size = uint32(elba_flash_info.region_size)

    data := []byte{}

    // get file size
    fileInfo, err := os.Stat(filename)
    if err != nil {
        fmt.Printf("ERROR: Unable to get file size.  os.Stat Err msg=%s\n", err); 
        return
    }
    file_size := fileInfo.Size()

    // check if flash has enough size
    if (start_addr + uint32(file_size) > flash_size) {
        fmt.Errorf(" Error: input length is bigger than flash size. 0x%X starting from offset 0x%X is larger than 0x%X\n", file_size, start_addr, flash_size)
        fmt.Printf("%s", err)
        return
    }

    // check if offset 64 kB aligned
    if start_addr % FLASH_SECTOR_SIZE != 0 {
        fmt.Errorf(" ERROR: Offset 0x%X is not 64 KB aligned\n", start_addr)
        fmt.Printf("%s", err)
        return
    }

    // open file
    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" ERROR: Failed to open filename=%s.  os.Open err=%s\n", filename, err)
        return
    }

    fmt.Printf(" Writing file %s starting at addr=0x%X\n", filename, start_addr)
    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)
    for scanner.Scan() {
        b := scanner.Bytes()
        if len(b) > 0 { // check token is not empty
            data = append(data, b[0])
        }
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        f.Close()
        return
    }
    f.Close()

    // append padding to data if needed
    padding_size := FLASH_PAGE_WRITE_SIZE - (len(data) % FLASH_PAGE_WRITE_SIZE)
    fmt.Printf(" Len=0x%X  pad length=0x%X\n", len(data), FLASH_PAGE_WRITE_SIZE%padding_size)
    if padding_size != FLASH_PAGE_WRITE_SIZE {
        for i=0; i < padding_size; i++ {
            data = append(data, 0xFF)
        }
    }

    // Remove from flash
    fmt.Printf(" Start Addr=0x%X, Len Data File = 0x%X\n", start_addr, len(data));
    fmt.Printf(" Erasing flash sectors\n");
    for j=start_addr; j<start_addr + uint32(len(data)); j = j+elba_flash_info.sector_size {
        fmt.Printf(".")
        err = Spi_salina_flash_erase_sector_w_spiBus_enable(spiNumber, qspiNumber, j, false)
        if err != nil {
           fmt.Printf(" ERROR: Erasing Flash Failed\n")
           return
        }
    }
    fmt.Printf("\n")

    // write file to flash
    fmt.Printf(" Programming flash sectors\n");
    for j=start_addr; j<start_addr + uint32(len(data)); j = j+uint32(FLASH_PAGE_WRITE_SIZE) {
       if (j%0x20000) == 0 {
           fmt.Printf("\r%.08x", j)
       }
       wr_data := []byte{}
       write_page = false
       for x:=0; x < FLASH_PAGE_WRITE_SIZE; x++ {
           wr_data = append(wr_data, data[x + count])
           if wr_data[x] != 0xFF {
               write_page = true
           }
       }
       count = count + FLASH_PAGE_WRITE_SIZE 

       if write_page == true {
           err = Spi_salina_flash_Write_N_Bytes_w_spiBus_enable(spiNumber, qspiNumber, wr_data, j, false)
           if err != nil {
               fmt.Printf("\n ERROR: Writing Flash Failed\n")
               return
           }
       } else {
           skipped_pages++
       }
    }
    fmt.Printf("\n")
    fmt.Printf("Skipped Pages = %d.  Skipped bytes = 0x%X\n", skipped_pages, (skipped_pages * 256) )
    fmt.Printf("Programming PASSED\n")
    
    return
}

// Only used by QSPI programming, skip SPI bus enable
func Spi_salina_flash_VerifyFile(spiNumber uint32, qspiNumber uint32, start_addr uint32, filename string) (err error) {
    var flash_size uint32
    var read_size = uint32(elba_flash_info.sector_size)
    var i uint32 = 0

    //Check if the card is Pollara which has a 32MB flash
    UpdateFlashSize(spiNumber)
    flash_size = uint32(elba_flash_info.region_size)

    flash_data := []byte{}
    file_data := []byte{}

    if start_addr % FLASH_SECTOR_SIZE != 0 {
        fmt.Errorf(" ERROR: Offset 0x%X is not 64 KB aligned\n", start_addr)
        fmt.Printf("%s", err)
        return
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" ERROR: Failed to open filename=%s.  os.Open err=%s\n", filename, err)
        return
    }

    // get file size
    fileInfo, err := os.Stat(filename)
    if err != nil {
        fmt.Printf(" ERROR: Unable to get file size.  os.Stat err=%s\n", err); 
        f.Close()
        return
    }
    file_size := fileInfo.Size()

    if (start_addr + uint32(file_size) > flash_size) {
        fmt.Errorf(" ERROR: input length is bigger than flash size. 0x%X starting from offset 0x%X is larger than 0x%X\n", len(file_data), start_addr, flash_size)
        fmt.Printf("%s", err)
        f.Close()
        return
    }

    fmt.Printf(" Verifying Image %s starting at addr=0x%X\n", filename, start_addr)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)
    for scanner.Scan() {
        b := scanner.Bytes()
        file_data = append(file_data, b[0])
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        f.Close()
        return
    }
    f.Close()

    err = Spi_flash_disable_4byte_addr_mode_w_spiBus_enable(spiNumber, qspiNumber, false)
    if err != nil {
        return
    }

    err = Spi_flash_set_extended_addr_register_w_spiBus_enable(spiNumber, qspiNumber, start_addr, false) 
    if err != nil {
        return
    }

    for i=start_addr; i< start_addr + uint32(len(file_data)); i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf("\r%.08x", i)
        }
        if (i % 0x1000000) <= read_size {
            err = Spi_flash_set_extended_addr_register_w_spiBus_enable(spiNumber, qspiNumber, i, false) 
            if err != nil {
                return
            }
        }
         
        rd_data, err = Spi_salina_flash_Read_N_Bytes_w_spiBus_enable(spiNumber, qspiNumber, i, read_size, 0, false)
        if err != nil {
            fmt.Printf("\n ERROR: Flash Read Failed.  StartAddr=0x%X.  I=0x%X\n", start_addr, i)
            return
        }
        flash_data = append(flash_data, rd_data...) 
    }
    fmt.Printf("\n")

    for i=0; i < uint32(len(file_data)); i++ {
        if (flash_data[i] != file_data[i]) {
            err = fmt.Errorf(" ERROR: Flash Miscompare at flash address 0x%X:  Flash Read 0x%.02X   File Read 0x%.02X\n", i+start_addr, flash_data[i], file_data[i])
            fmt.Printf("e", "%s", err)
            fmt.Printf("Verification failed\n")
            return
        }
    }
    fmt.Printf("\nVerification passed\n")
    return
}

func Spi_salina_flash_GenerateFile(spiNumber uint32, qspiNumber uint32, start_addr uint32, length uint32, filename string) (err error) {
    var flash_size uint32
    var read_size = uint32(elba_flash_info.sector_size)
    var i uint32 = 0
    flash_data := []byte{}

    //Check if the card is Pollara which has a 32MB flash
    UpdateFlashSize(spiNumber)
    flash_size = uint32(elba_flash_info.region_size)

    // check if offset 64 kB aligned
    if start_addr % FLASH_SECTOR_SIZE != 0 {
        fmt.Errorf("ERROR: Offset 0x%X is not 64 KB aligned\n", start_addr)
        cli.Printf("e", "%s", err)
        return
    }

    // check if flash has enough size
    if start_addr + length > flash_size {
        err = fmt.Errorf(" Error: input length is bigger than flash size. 0x%X starting from offset 0x%X is larger than 0x%X\n", length, start_addr, flash_size)
        cli.Printf("e", "%s", err)
        return
    }

    err = Spi_flash_disable_4byte_addr_mode(spiNumber, qspiNumber)
    if err != nil {
        return
    }

    err =  Spi_flash_set_extended_addr_register(spiNumber, qspiNumber, uint32(start_addr)) 
    if err != nil {
        return
    }

    for i=start_addr; i< start_addr + length; i = i+read_size {
        rd_data := []byte{}
        if (i%0x20000) == 0 {
            fmt.Printf(".")
        }
        if (i % 0x1000000) <= read_size {
            err =  Spi_flash_set_extended_addr_register(spiNumber, qspiNumber, uint32(i)) 
            if err != nil {
                return
            }
        }
        rd_data, err = Spi_salina_flash_Read_N_Bytes(spiNumber, qspiNumber, uint32(i), uint32(read_size), 0)
        if err != nil {
            fmt.Printf(" ERROR: Flash Read Failed\n")
            return
        }
        if (i + read_size - 1 > start_addr + length) {
            flash_data = append(flash_data, rd_data[0 : start_addr + length - i]...)
        } else {
            flash_data = append(flash_data, rd_data...)
        }
        
    }
    fmt.Printf("\n")

    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    f.WriteString(string(flash_data[:]))
    f.Close()

    return
}
