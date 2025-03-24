/* Support for Taormina MachXO3 9400 LUT cpld.  */
package materafpga

import (
    //"errors"
    "common/cli"
    "fmt"
    "os"
    "bufio"
    "strings"
    "strconv"
    "time"
    //"io"
)



const MACHXO3_9400_PAGE_SIZE             uint32 = 16
const MACHXO3_9400_CFG0_FLASH_SIZE       uint32 = (12541 * 16)    //12541 pages * 128 bits each = 200,656 bytes
const MACHXO3_9400_CFG1_FLASH_SIZE       uint32 = (12541 * 16)    //12541 pages * 128 bits each = 200,656 bytes
const MACHXO3_9400_UFM0_FLASH_SIZE       uint32 = (3582 * 16)     //3582 pages * 128 bits each = 57312 bytes
const MACHXO3_9400_UFM1_FLASH_SIZE       uint32 = (3582 * 16)     //3582 pages * 128 bits each = 57312 bytes
const MACHXO3_9400_UFM2_FLASH_SIZE       uint32 = (1150 * 16)     //18400 bytes
const MACHXO3_9400_UFM3_FLASH_SIZE       uint32 = (191 * 16)    


const MACHXO3_ERASE_CFG0    uint32 = 0x0100
const MACHXO3_ERASE_CFG1    uint32 = 0x0200
const MACHXO3_ERASE_UFM0    uint32 = 0x0400
const MACHXO3_ERASE_UFM1    uint32 = 0x0800
const MACHXO3_ERASE_UFM2    uint32 = 0x1000
const MACHXO3_ERASE_UFM3    uint32 = 0x2000
const MACHXO3_ERASE_CSEC    uint32 = 0x4000
const MACHXO3_ERASE_USEC    uint32 = 0x8000
const MACHXO3_ERASE_PUBKEY  uint32 = 0x10000
const MACHXO3_ERASE_AESKEY  uint32 = 0x20000
const MACHXO3_ERASE_FAE     uint32 = 0x30000

const CONFIG0               uint32 = 0x1
const CONFIG1               uint32 = 0x2
const FEATUREROW            uint32 = 0x3
const UFM0                  uint32 = 0x4
const UFM1                  uint32 = 0x5
const UFM2                  uint32 = 0x6
const UFM3                  uint32 = 0x7

const CPLD_STS_REG_BUSY_BIT         uint32 = 0x1000
const CPLD_STS_REG_FAIL_BIT         uint32 = 0x2000
const CPLD_BUSYFLAG_BUSY_BIT        uint32 = 0x80 
 

var CPLDXO3_RD_STATUS_REG_OP           = []byte{0x3C, 0x00, 0x00, 0x00}
var CPLDXO3_RD_STATUS_REG_RDLNG        uint32 = 4

var CPLDXO3_ENABLE_CONFIG_INTF_OP      = []byte{0x74, 0x08, 0x00, 0x00}   //enable configuration logic
var CPLDXO3_ENABLE_CONFIG_INTF_OP_RDLNG uint32 = 0

var CPLDXO3_DISABLE_CONFIG_INTF_OP     = []byte{0x26, 0x00, 0x00}   //disable configuration logic
var CPLDXO3_DISABLE_CONFIG_INTF_OP_RDLNG uint32 = 0

var CPLDXO3_RD_USERCODE_OP             = []byte{0xC0, 0x00, 0x00, 0x00}
var CPLDXO3_RD_USERCODE_OP_RDLNG       uint32 = 4

var CPLDXO3_WR_USERCODE_OP             = []byte{0xC2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}
var CPLDXO3_WR_USERCODE_OP_RDLNG       uint32 = 0

var CPLDXO3_RD_DEVICE_ID_OP            = []byte{0xE0, 0x00, 0x00, 0x00}
var CPLDXO3_RD_DEVICE_ID_OP_RDLNG      uint32 = 4

var CPLDXO3_NO_OP                      = []byte{0xFF, 0xFF, 0xFF, 0xFF}   
var CPLDXO3_NO_OP_RDLNG                uint32 = 0

var CPLDXO3_RESET_CONFIG0_FLASH_OP     = []byte{0x46, 0x00, 0x01, 0x00}   //reset page pointer in flash
var CPLDXO3_RESET_CONFIG1_FLASH_OP     = []byte{0x46, 0x00, 0x02, 0x00}   //reset page pointer in flash
//var CPLDXO3_RESET_FEATURE_ROW_OP       = []byte{0x46, 0x00, 0x04, 0x00}   //reset page pointer in flash
var CPLDXO3_RESET_FEATURE_ROW_OP       = []byte{0x46, 0x04, 0x00, 0x00}   //reset page pointer in flash
var CPLDXO3_RESET_PUBKEY_OP            = []byte{0x46, 0x00, 0x08, 0x00}
var CPLDXO3_RESET_AESKEY_OP            = []byte{0x46, 0x00, 0x10, 0x00}
var CPLDXO3_RESET_CSEC_OP              = []byte{0x46, 0x00, 0x20, 0x00}
var CPLDXO3_RESET_UFM0_OP              = []byte{0x46, 0x00, 0x40, 0x00}
var CPLDXO3_RESET_UFM1_OP              = []byte{0x46, 0x00, 0x80, 0x00}
var CPLDXO3_RESET_UFM2_OP              = []byte{0x46, 0x01, 0x00, 0x00}   //reset page pointer in flash
var CPLDXO3_RESET_UFM3_OP              = []byte{0x46, 0x02, 0x00, 0x00}   //reset page pointer in flash
var CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG uint32 = 0

var CPLDXO3_RESET_UFM0_ADDR_OP         = []byte{0x47, 0x00, 0x04, 0x00}
var CPLDXO3_RESET_UFM1_ADDR_OP         = []byte{0x47, 0x00, 0x08, 0x00}
var CPLDXO3_RESET_UFM2_ADDR_OP         = []byte{0x47, 0x00, 0x10, 0x00}
var CPLDXO3_RESET_UFM3_ADDR_OP         = []byte{0x47, 0x00, 0x20, 0x00}

var CPLDXO3_RD_FEA_ROW_OP              = []byte{0xE7, 0x00, 0x00, 0x00}
var CPLDXO3_RD_FEA_ROW_OP_RDLNG        uint32 = 16

var CPLDXO3_RD_BUSYFLAG_OP             = []byte{0xF0, 0x00, 0x00, 0x00}
var CPLDXO3_RD_BUSYFLAG_OP_RDLNG       uint32 = 1

var CPLDXO3_ENABLE_OFFLINE_MODE_OP     = []byte{0xC6, 0x08, 0x00, 0x00}   
var CPLDXO3_ENABLE_OFFLINE_MODE_OP_RDLNG uint32 = 0

var CPLDXO3_PROGRAM_DONE_OP            = []byte{0x5E, 0x00, 0x00, 0x00}   //programming done bit
var CPLDXO3_PROGRAM_DONE_OP_RDLNG      uint32 = 0

var CPLDXO3_REFRESH_OP                 = []byte{0x79, 0x00, 0x00}
var CPLDXO3_REFRESH_OP_RDLNG           uint32 = 0

var CPLDXO3_ERASE_CONFIG0_FLASH_OP      = []byte{0x0E, 0x00, 0x01, 0x00}   //erase config0 flash
var CPLDXO3_ERASE_CONFIG1_FLASH_OP      = []byte{0x0E, 0x00, 0x02, 0x00}   //erase config1 flash
var CPLDXO3_ERASE_UFM0_OP               = []byte{0x0E, 0x00, 0x04, 0x00}   //erase UFM0
var CPLDXO3_ERASE_UFM1_OP               = []byte{0x0E, 0x00, 0x08, 0x00}   //erase UFM1
var CPLDXO3_ERASE_UFM2_OP               = []byte{0x0E, 0x00, 0x10, 0x00}   //erase UFM2
var CPLDXO3_ERASE_UFM3_OP               = []byte{0x0E, 0x00, 0x20, 0x00}   //erase UFM3                                                                           
var CPLDXO3_ERASE_FEATURE_ROW_OP        = []byte{0x0E, 0x04, 0x00, 0x00}   //erase feature row

var CPLDXO3_ERASE_CONFIG_FLASH_RDLNG   uint32 = 0

//Program page Operations
var CPLDXO3_FEATURE_ROW_PROGRAM_OP      = []byte{0xE4, 0x00, 0x00, 0x00}
var CPLDXO3_FLASH_PROGRAM_PAGE_OP       = []byte{0x70, 0x00, 0x00, 0x01}
var CPLDXO3_FLASH_PROGRAM_UFM_PAGE_OP   = []byte{0xC9, 0x00, 0x00, 0x01}
var CPLDXO3_FLASH_PROGRAM_PAGE_OP_RDLNG uint32 = 0

var CPLDXO3_RD_FLASH_OP                = []byte{0x73, 0x00, 0x00, 0x01}
var CPLDXO3_RD_FLASH_OP_RDLNG          uint32 = 16

var CPLDXO3_RD_FEA_BITS_OP             = []byte{0xFB, 0x00, 0x00, 0x00}         
var CPLDXO3_RD_FEA_BITS_OP_RDLNG       uint32 = 4


func Spi_cpldXO3_spi_read_reg(spiNumber uint32, reg uint8) (rd_data uint8, err error) {
    data := []byte{}
    rddata := []byte{}
    rddata = append(rddata, reg)
    data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLDI2C_RD, rddata, 1) 
    if err != nil {
        return
    }
    rd_data = data[0]

    return
}

func Spi_cpldXO3_spi_write_reg(spiNumber uint32, reg uint8, data uint8) (err error) {
    wrdata := []byte{}
    wrdata = append(wrdata, reg)
    wrdata = append(wrdata, data)
    fmt.Println(wrdata)
    _, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLDI2C_WR, wrdata, 0) 
    if err != nil {
        return
    }
    return
}

func Spi_cpldXO3_read_usercode(spiNumber uint32) (ucode uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_USERCODE_OP, CPLDXO3_RD_USERCODE_OP_RDLNG) 
    if err != nil {
        return
    }
    for i=(int(CPLDXO3_RD_USERCODE_OP_RDLNG-1) * 8); i>=0; i=(i-8) {
        ucode = ucode | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpldXO3_write_usercode(spiNumber uint32, usercode uint32) (err error) {

    CPLDXO3_WR_USERCODE_OP[4] = uint8((usercode>>24) & 0xFF)
    CPLDXO3_WR_USERCODE_OP[5] = uint8((usercode>>16) & 0xFF)
    CPLDXO3_WR_USERCODE_OP[6] = uint8((usercode>>8)  & 0xFF)
    CPLDXO3_WR_USERCODE_OP[7] = uint8(usercode & 0xFF)
    fmt.Println(CPLDXO3_WR_USERCODE_OP)
    _, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_WR_USERCODE_OP, CPLDXO3_WR_USERCODE_OP_RDLNG) 
    if err != nil {
        return
    }
    
    return
}

func Spi_cpldXO3_read_device_id(spiNumber uint32) (devid uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_DEVICE_ID_OP, CPLDXO3_RD_DEVICE_ID_OP_RDLNG) 
    if err != nil {
        return
    }
    for i=(int(CPLDXO3_RD_DEVICE_ID_OP_RDLNG-1) * 8); i>=0; i=i-8 {
        devid = devid | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpldXO3_enable_config_interface(spiNumber uint32) (err error) {
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ENABLE_CONFIG_INTF_OP, CPLDXO3_ENABLE_CONFIG_INTF_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}

func Spi_cpldXO3_disable_config_interface(spiNumber uint32) (err error) {
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_DISABLE_CONFIG_INTF_OP, CPLDXO3_DISABLE_CONFIG_INTF_OP_RDLNG) 
    return
}

func Spi_cpldXO3_no_op_cmd(spiNumber uint32) (err error) {
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_NO_OP, CPLDXO3_NO_OP_RDLNG) 
    return
}

/************************************************************************************* 
NOTE: RETURNS 4 BYTES.  BUT ONLU USE BITS[16:0].  i.e. 4 BYTES HAVE A MASK
 
READ FEATURE BITS 
00 00 86 20 
MASK 
00 01 FF FF 
**************************************************************************************/ 
func Spi_cpldXO3_read_feature_bits(spiNumber uint32) (FeatureBits uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}

    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_FEA_BITS_OP, CPLDXO3_RD_FEA_BITS_OP_RDLNG) 
    if err != nil {
        return
    }
    for i=(int(CPLDXO3_RD_FEA_BITS_OP_RDLNG-1) * 8); i>=0; i=i-8 {
        FeatureBits = FeatureBits | (uint32(data[j])<<uint32(i))
        j++
    }

    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    return

}

func Spi_cpldXO3_read_feature_row(spiNumber uint32) (data []byte, err error) {
    
    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_FEATURE_ROW_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    if err != nil {
        return
    }

    data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_FEA_ROW_OP, CPLDXO3_RD_FEA_ROW_OP_RDLNG) 
    if err != nil {
        return
    }

    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    return
}

func Spi_cpldXO3_read_busy_flag(spiNumber uint32) (BusyFlag uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_BUSYFLAG_OP, CPLDXO3_RD_BUSYFLAG_OP_RDLNG) 
    if err != nil {
        return
    }
    for i=(int(CPLDXO3_RD_BUSYFLAG_OP_RDLNG-1) * 8); i>=0; i=i-8 {
        BusyFlag = BusyFlag | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpldXO3_read_status_reg(spiNumber uint32) (StatusReg uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_STATUS_REG_OP, CPLDXO3_RD_STATUS_REG_RDLNG) 
    if err != nil {
        return
    }
    for i=(int(CPLDXO3_RD_STATUS_REG_RDLNG-1) * 8); i>=0; i=i-8 {
        StatusReg = StatusReg | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpldXO3_enable_offline_mode(spiNumber uint32) (err error) {
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ENABLE_OFFLINE_MODE_OP, CPLDXO3_ENABLE_OFFLINE_MODE_OP_RDLNG) 
    return
}

func Spi_cpldX03_return_flash_space_from_cli_arg(image string) (config uint32, err error) {
    if image == "cfg0" {
        config = CONFIG0
    } else if image == "cfg1" {
        config = CONFIG1
    } else if image == "ufm0" {
        config = UFM0
    } else if image == "ufm1" {
        config = UFM1
    } else if image == "ufm2" {
        config = UFM2
    } else if image == "ufm3" {
        config = UFM3
    } else if image == "fea" {
        config = FEATUREROW
    } else {
        err = fmt.Errorf("ERROR: FLASH PARTITION SPACE ENTERED IS NOT VALID.  YOU ENTERED '%s'\n", image)
        cli.Printf("e","%v", err)
        return
    }
    return
}



func Spi_cpldX03_get_flash_size(config uint32) (size uint32, err error) {
    if config == CONFIG0 {
        size = MACHXO3_9400_CFG0_FLASH_SIZE
    } else if config == CONFIG1 {
        size = MACHXO3_9400_CFG1_FLASH_SIZE
    } else if config == FEATUREROW {
        size = FEATUREROW
    } else if config == UFM0 {
        size = MACHXO3_9400_UFM0_FLASH_SIZE
    } else if config == UFM1 {
        size = MACHXO3_9400_UFM1_FLASH_SIZE
    } else if config == UFM2 {
        size = MACHXO3_9400_UFM2_FLASH_SIZE
    } else if config == UFM3 {
        size = MACHXO3_9400_UFM3_FLASH_SIZE
    } else {
        err = fmt.Errorf("ERROR: Spi_cpldX03_return_flash_space_from_cli_arg FLASH PARTITION SPACE ENTERED IS NOT VALID.  YOU ENTERED '%d'\n", config)
        cli.Printf("e","%v", err)
        return
    }
    return
}

func Spi_cpldXO3_reset_config_flash(spiNumber uint32, image string) (err error) {
    var space uint32 = CONFIG0
    space, err = Spi_cpldX03_return_flash_space_from_cli_arg(image)
    if err != nil {
        return
    }

    if space == CONFIG0 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_CONFIG0_FLASH_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == CONFIG1 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_CONFIG1_FLASH_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == FEATUREROW {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_FEATURE_ROW_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM0 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_UFM0_ADDR_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM1 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_UFM1_ADDR_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM2 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_UFM2_ADDR_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM3 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RESET_UFM3_ADDR_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    return
}


func Spi_cpldXO3_set_programming_done(spiNumber uint32) (err error) {
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_PROGRAM_DONE_OP, CPLDXO3_PROGRAM_DONE_OP_RDLNG) 
    return
}

func Spi_cpldXO3_refresh(spiNumber uint32) (err error) {
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_REFRESH_OP, CPLDXO3_REFRESH_OP_RDLNG) 
    return
}


func Spi_cpldXO3_erase_config_flash(spiNumber uint32, image string) (err error) {
    var sleep, max_try int = 100, 100
    var data32 uint32
    var space uint32 = CONFIG0
    space, err = Spi_cpldX03_return_flash_space_from_cli_arg(image)
    if err != nil {
        return
    }

    if space == CONFIG0 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ERASE_CONFIG0_FLASH_OP, CPLDXO3_ERASE_CONFIG_FLASH_RDLNG) 
    }
    if space == CONFIG1 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ERASE_CONFIG1_FLASH_OP, CPLDXO3_ERASE_CONFIG_FLASH_RDLNG) 
    }
    if space == FEATUREROW {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ERASE_FEATURE_ROW_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM0 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ERASE_UFM0_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM1 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ERASE_UFM1_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM2 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ERASE_UFM2_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == UFM3 {
        _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_ERASE_UFM3_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }

    if err != nil {
        return
    }

    for i:=0; i<max_try; i++ {
        data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
        if err != nil {
            return
        }
        //Wait for flash to not be busy erasing
        if data32 & CPLD_BUSYFLAG_BUSY_BIT != CPLD_BUSYFLAG_BUSY_BIT {   
            break
        }

        time.Sleep(time.Duration(sleep) * time.Millisecond)

        if i == (max_try -1) {
            err = fmt.Errorf("ERROR: Slot-%d: FLASH ERASE STUCK WAITING FOR BUSY FLAG TO CLEAR.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e","%v", err)
            return
        }
    }


    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e","%v", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e","%v", err)
        return
    }
    
    return
}


func Spi_cpldXO3_program_feature_row_cmd(spiNumber uint32, data []byte) (err error) {
    var sleep, max_try int = 1, 100
    var data32 uint32
    spi_cmd := []byte{}

    spi_cmd = append(spi_cmd, CPLDXO3_FEATURE_ROW_PROGRAM_OP...) 
    spi_cmd = append(spi_cmd, data...) 

    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, spi_cmd, CPLDXO3_FLASH_PROGRAM_PAGE_OP_RDLNG) 
    if err != nil {
        return
    }

    for i:=0; i<max_try; i++ {
        data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
        if err != nil {
            return
        }
        //Wait for flash to not be busy erasing
        if data32 & CPLD_BUSYFLAG_BUSY_BIT != CPLD_BUSYFLAG_BUSY_BIT {   
            break
        }

        time.Sleep(time.Duration(sleep) * time.Millisecond)

        if i == (max_try -1) {
            err = fmt.Errorf("ERROR: Slot-%d: FLASH PROGRAM PAGE STUCK WAITING FOR BUSY FLAG TO CLEAR.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e","%v", err)
            return
        }


        data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
        if err != nil {
            return
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e","%v", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e","%v", err)
            return
        }
    }
    
    return
}


func Spi_cpldXO3_program_page_flash_cmd(spiNumber uint32, config uint32, data []byte) (err error) {
    var sleep, max_try int = 1, 100
    var data32 uint32
    

    //For UFM any size file can be used.  i.e. file may not divide by flash page size of 16-bytes.
    //Pad out the file so it is 16-byte aligned since we program a 16-byte page at a time
    if config == UFM0 || 
       config == UFM1 ||
       config == UFM2 ||
       config == UFM3 {
           fmt.Printf(" Padding UFM file to be 16-byte aligned\n")
           for i:=0;i<(len(data)%int(MACHXO3_9400_PAGE_SIZE));i++ {
               data = append(data, 0x00)
           }
    }
    

    for j:=0; j < len(data); j=(j + int(MACHXO3_9400_PAGE_SIZE)) {
        spi_cmd := []byte{}

        if (j % 1600) == 0 {
            fmt.Printf(".")
            //fmt.Printf("j=%d  len(data)=%d\n", j, len(data));
        }

        if config == UFM0 || 
           config == UFM1 ||
           config == UFM2 ||
           config == UFM3 {
            for i:=0; i<len(CPLDXO3_FLASH_PROGRAM_UFM_PAGE_OP); i++ {
                spi_cmd = append(spi_cmd, CPLDXO3_FLASH_PROGRAM_UFM_PAGE_OP[i]) 
            }
            for i:=0; i<int(MACHXO3_9400_PAGE_SIZE); i++ {
                spi_cmd = append(spi_cmd, data[i + j]) 
            }

            _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, spi_cmd, CPLDXO3_FLASH_PROGRAM_PAGE_OP_RDLNG) 
            if err != nil {
                return
            }

        } else {
            for i:=0; i<len(CPLDXO3_FLASH_PROGRAM_PAGE_OP); i++ {
                spi_cmd = append(spi_cmd, CPLDXO3_FLASH_PROGRAM_PAGE_OP[i]) 
            }
            for i:=0; i<int(MACHXO3_9400_PAGE_SIZE); i++ {
                spi_cmd = append(spi_cmd, data[i + j]) 
            }

            _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, spi_cmd, CPLDXO3_FLASH_PROGRAM_PAGE_OP_RDLNG) 
            if err != nil {
                return
            }
            time.Sleep(time.Duration(2) * time.Millisecond)
        }

        for i:=0; i<max_try; i++ {
            data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
            if err != nil {
                fmt.Printf("ERROR: Slot-%d CPLD Read Busy Flag Failed\n", spiNumber+1);
                return
            }
            //Wait for flash to not be busy erasing
            if data32 & CPLD_BUSYFLAG_BUSY_BIT != CPLD_BUSYFLAG_BUSY_BIT {   
                break
            }

            time.Sleep(time.Duration(sleep) * time.Millisecond)

            if i == (max_try -1) {
                err = fmt.Errorf("ERROR: Slot-%d: FLASH PROGRAM PAGE STUCK WAITING FOR BUSY FLAG TO CLEAR.  Read Busy Flag Op returned=0x%x\n", spiNumber+1, data32)
                cli.Printf("e","%v", err)
                return
            }
        }


        for i:=0; i<10; i++ {
        data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
        if err != nil {
            fmt.Printf(" Read Status Reg Failed\n");
            fmt.Printf("ERROR: Slot-%d CPLD Read Status Register Failed\n", spiNumber+1);
            continue
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e","%v", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e","%v", err)
            return
        }
        }
    }
    
    return
}


//////////////////////////////////////////////////////
//  
// VERIFY FLASH CONTENTS VS A FILE
//  
//////////////////////////////////////////////////////
func Spi_cpldXO3_verify_flash_contents(spiNumber uint32, image string, filename string) (err error) {
    var data32 uint32 = 0
    var config uint32 = 0
    var size uint32 = 0
    flashData := []byte{}
    fileData := []byte{}


    if spiNumber > SPI_DBG_SLOT {
        err = fmt.Errorf("ERROR spi_cpldXO3_verify_flash_contents. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, SPI_DBG_SLOT)
        cli.Printf("e","%v", err)
        return
    }

    config, err = Spi_cpldX03_return_flash_space_from_cli_arg(image) 
    if err != nil {
        fmt.Printf("[ERROR] INVALID IMAGE TYPE  ERR=%s\n", err)
        return
    }

    if strings.Contains(filename, "fea")==true {
        if config == FEATUREROW {
            err = Spi_cpldXO3_convert_featurerow_jed_file(filename)
            if err != nil {
                fmt.Printf("ERROR: Failed to convert filename=%s.  Exiting Programming CPLD\n", filename)
                return
            }
        } else {
            err = fmt.Errorf("[ERROR]  Spi_cpldXO3_program_flash. FEA FILE PASSED for programming cfg0 or cgf1.  File needs to be jed or bin\n")
            cli.Printf("e","%v", err)
            return
        }
        filename = strings.Replace(filename, "fea", "bin", 1)
    }
    if strings.Contains(filename, "jed")==true {
        fmt.Printf(" Jed file detected..Converting to a BIN file\n")
        err = Spi_cpldXO3_convert_jed_file(filename)
        if err != nil {
            fmt.Printf(" Failed to convert filename=%s.  Exiting Programming CPLD\n", filename)
            return
        }
        filename = strings.Replace(filename, "jed", "bin", 1)
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }

    fmt.Printf(" Verifying Image %s against CPLD flash\n", filename)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        fileData = append(fileData, b[0])
    }
    f.Close()

    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e","%v", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e","%v", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e","%v", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }


    if config == FEATUREROW {
        flashData, _ = Spi_cpldXO3_read_feature_row(spiNumber) 
    } else {
        if (config == UFM0 || config == UFM1 || config == UFM2 || config == UFM3) {
            size = uint32(len(fileData))
        } else {
            size, _ = Spi_cpldX03_get_flash_size(config)
        }
        for j:=0; j<int(size); j=(j + int(CPLDXO3_RD_FLASH_OP_RDLNG)) {
            data := []byte{}

            data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
            if err != nil {
                return
            }
            if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
                err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
                cli.Printf("e", "%v", err)
                return
            }
            if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
                err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
                cli.Printf("e", "%v", err)
                return
            }

            if (j % 500) == 0 {
                fmt.Printf(".")
            }

            data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_FLASH_OP, CPLDXO3_RD_FLASH_OP_RDLNG)
            if err != nil {
                return
            }             
            for i:=0; i<int(CPLDXO3_RD_FLASH_OP_RDLNG); i++ {
                flashData = append(flashData, data[i])
            }
        }
    }
    fmt.Printf("\n")

    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    //f.WriteString(string(flashData[:]))
    if (config == CONFIG0 || config == CONFIG1) && (len(flashData) != len(fileData)) {
        err = fmt.Errorf(" ERROR: File and Flash data size do not match.   Flash Data Size = %d.   File Data Size = %d\n", len(flashData), len(fileData) ) 
        cli.Printf("e", "%v", err)
        return;
    } 

    if (config == FEATUREROW) {
        //The feature row read mask is 4 bytes dont care, 12 bytes of data
        //In order to get the converted .fea file to match, we need to pre-append 4 bytes of 0x00 since the first 4 bytes of the feature row read are not in the mask
        tempSlice := []byte{ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }
        copy(tempSlice[4:16], fileData[0:12])
        fileData = tempSlice
        fmt.Printf("\n FILE  -> ")
        for i:=0; i<len(fileData); i++ {
            fmt.Printf("%.02x ", fileData[i])
        }
        fmt.Printf("\n FLASH -> ")
        for i:=0; i<len(flashData); i++ {
            fmt.Printf("%.02x ", flashData[i])
        }
        fmt.Printf("\n")
    }
    for i:=0; i<len(fileData); i++ {
        if flashData[i] != fileData[i] {
            err = fmt.Errorf(" ERROR: Data Mismatch at address 0x%x. Flash=%.02x   Expect=0x%02x\n", i, flashData[i], fileData[i] ) 
            cli.Printf("e", "%v", err)
            break
        }
    }
    if err == nil {
        fmt.Printf("Slot-%d CPLD Verification passed\n", spiNumber+1)
    } else {
        fmt.Printf("Slot-%d CPLD Verification failed\n", spiNumber+1)
    }
    
    return 
}

// 
//////////////////////////////////////////////////////
//  
// READ LOCAL IMAGE AND WRITE IT TO A FILE
//  
//////////////////////////////////////////////////////
func Spi_cpldX03_generate_image_from_flash(spiNumber uint32, image string, filename string) (err error) {
    var data32 uint32 = 0
    flashData := []byte{}
    var config uint32 = 0

    if spiNumber > SPI_DBG_SLOT {
        err = fmt.Errorf("ERROR Spi_cpldX03_generate_image_from_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, SPI_DBG_SLOT)
        cli.Printf("e", "%v", err)
        return
    }

    config, err = Spi_cpldX03_return_flash_space_from_cli_arg(image) 
    if err != nil {
        fmt.Printf("[ERROR] INVALID IMAGE TYPE  ERR=%s\n", err)
        return
    }


    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }


    if config == FEATUREROW {
        flashData, _ = Spi_cpldXO3_read_feature_row(spiNumber)
    } else {
        size, _ := Spi_cpldX03_get_flash_size(config)

        for j:=0; j<int(size); j=(j + int(CPLDXO3_RD_FLASH_OP_RDLNG)) {
            data := []byte{}

            data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
            if err != nil {
                return
            }
            if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
                err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
                cli.Printf("e", "%v", err)
                return
            }
            if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
                err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
                cli.Printf("e", "%v", err)
                return
            }

            if (j % 100) == 0 {
                fmt.Printf(".")
            }

            data, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_FLASH_OP, CPLDXO3_RD_FLASH_OP_RDLNG) 
            if err != nil {
                return
            }
            for i:=0; i<int(CPLDXO3_RD_FLASH_OP_RDLNG); i++ {
                flashData = append(flashData, data[i])
            }
        }
    }

    os.Remove(filename)
    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
    }
    f.WriteString(string(flashData[:]))
    f.Close()

    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    return 
}



// 
//////////////////////////////////////////////////////
//  
// READ DATA INTO SLICE AND RETURN IT
// ONLY VALID FOR CFG AND UFM SPACES 
//////////////////////////////////////////////////////
func Spi_cpldX03_read_flash(spiNumber uint32, image string, offset uint32, length uint32) (data []uint8, err error) {
    var data32 uint32 = 0
    flashData := []uint8{}
    var config uint32 = 0

    if spiNumber > SPI_DBG_SLOT {
        err = fmt.Errorf("ERROR Spi_cpldX03_generate_image_from_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, SPI_DBG_SLOT)
        cli.Printf("e", "%v", err)
        return
    }

    config, err = Spi_cpldX03_return_flash_space_from_cli_arg(image) 
    if err != nil {
        fmt.Printf("[ERROR] INVALID IMAGE TYPE  ERR=%s\n", err)
        return
    }

    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }


    size, _ := Spi_cpldX03_get_flash_size(config)

    if ((offset + length) > size) {
        fmt.Errorf("ERROR: Spi_cpldX03_read_flash: offset-%d + length-%d > flash read size-%d\n", offset, length, size);
        cli.Printf("e", "%v", err)
        return
    }

    for j:=0; j<int((offset + length)); j=(j + int(CPLDXO3_RD_FLASH_OP_RDLNG)) {
        rddata := []byte{}

        data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
        if err != nil {
            return
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e", "%v", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
            cli.Printf("e", "%v", err)
            return
        }

        if (j != 0) && ((j % 512) == 0) {
            fmt.Printf(".")
        }

        rddata, err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_CPLD_FLASH, CPLDXO3_RD_FLASH_OP, CPLDXO3_RD_FLASH_OP_RDLNG) 
        if err != nil {
            return
        }
        for i:=0; i<int(CPLDXO3_RD_FLASH_OP_RDLNG); i++ {
            flashData = append(flashData, rddata[i])
        }
    }


    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    data = append(flashData[offset:(offset+length)])

    return 
}




/////////////////////////////////////////////////////
//  
// ERASE FLASH SECTION
//  
//////////////////////////////////////////////////////
func Spi_cpldXO3_erase_flash(spiNumber uint32, image string) (err error) {
    var data32 uint32 = 0


    if spiNumber > SPI_DBG_SLOT {
        err = fmt.Errorf("ERROR:Spi_cpldXO3_erase_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, SPI_DBG_SLOT)
        cli.Printf("e", "%v", err)
        return
    }

    fmt.Printf(" Erasing Flash Section %s\n", image)

    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }
    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }


    err =  Spi_cpldXO3_erase_config_flash(spiNumber, image) 
    if err != nil {
        return
    }


    err = Spi_cpldXO3_set_programming_done(spiNumber)
    if err != nil {
        return
    }

    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }


    if err == nil {
        fmt.Printf("Erasing PASSED\n")
    } else {
        fmt.Printf("Erasing FAILED\n")
    }

    return
}





func Spi_cpldXO3_program_usercode(spiNumber uint32, image string, usercode uint32) (err error) {

    var data32 uint32 = 0
    //var config uint32 = 0


    if spiNumber > SPI_DBG_SLOT {
        err = fmt.Errorf("ERROR:  Spi_cpldXO3_program_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, SPI_DBG_SLOT)
        cli.Printf("e", "%v", err)
        return
    }


    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }
    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }


    fmt.Printf("Writing usercode row 0x%x\n", usercode)
    err = Spi_cpldXO3_write_usercode(spiNumber, usercode)
    if err != nil {
         return
    }

    err = Spi_cpldXO3_set_programming_done(spiNumber)
    if err != nil {
        return
    }

    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }


    if err == nil {
        fmt.Printf("Programming PASSED\n")
    } else {
        fmt.Printf("Programming FAILED\n")
    }

    return
}





/////////////////////////////////////////////////////
//  
// PROGRAM A FILE INTO CFG FLASH
//  
//////////////////////////////////////////////////////

func Spi_cpldXO3_program_flash(spiNumber uint32, image string, tofile bool, filename string, dataSlice []byte) (err error) {

    var data32 uint32 = 0
    var config uint32 = 0
    //flashData := []byte{}
    fileData := []byte{}
    var f *os.File


    if spiNumber > SPI_DBG_SLOT {
        err = fmt.Errorf("ERROR:  Spi_cpldXO3_program_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, SPI_DBG_SLOT)
        cli.Printf("e", "%v", err)
        return
    }

    config, err = Spi_cpldX03_return_flash_space_from_cli_arg(image) 
    if err != nil {
        fmt.Printf("[ERROR] INVALID IMAGE TYPE  ERR=%s\n", err)
        return
    }

    if tofile == true {
        if strings.Contains(filename, "fea")==true {
            if config == FEATUREROW {
                err = Spi_cpldXO3_convert_featurerow_jed_file(filename)
            } else {
                err = fmt.Errorf("[ERROR]  Spi_cpldXO3_program_flash. FEA FILE PASSED for programming cfg0 or cgf1.  File needs to be jed or bin\n")
                cli.Printf("e","%s", err)
                return
            }
            filename = strings.Replace(filename, "fea", "bin", 1)
        }
        if strings.Contains(filename, "jed")==true {
            fmt.Printf(" Jed file detected..Converting to a BIN file\n")
            err = Spi_cpldXO3_convert_jed_file(filename)
            if err != nil {
                fmt.Printf(" Failed to convert filename=%s.  Exiting Programming CPLD  ERR=%s\n", filename, err)
                return
            }
            filename = strings.Replace(filename, "jed", "bin", 1)
        }
    
        f, err = os.Open(filename)
        if err != nil {
            fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
            return
        }

        fmt.Printf(" Programming Image %s to CPLD %s flash\n", filename, image  )
    
        scanner := bufio.NewScanner(f)
        scanner.Split(bufio.ScanBytes)
        for scanner.Scan() {
            b := scanner.Bytes()
            fileData = append(fileData, b[0])
        }    
        f.Close()
    } else {
        fileData = make([]byte, len(dataSlice))
        copy(fileData, dataSlice)
    }
    
    if config == UFM2 {
        if len(fileData) > int(MACHXO3_9400_UFM2_FLASH_SIZE) {
            err = fmt.Errorf("ERROR:  Filesize for UFM2 is to big.   Max size=%d   Filesize=%d\n", MACHXO3_9400_UFM2_FLASH_SIZE, len(fileData))
            fmt.Printf("%v", err)
            return
        }
    }
    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }
    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR: Slot-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber+1, data32)
        cli.Printf("e", "%v", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }

    err =  Spi_cpldXO3_erase_config_flash(spiNumber, image) 
    if err != nil {
        return
    }


    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }

    if config == FEATUREROW {
        //The feature row read mask is 4 bytes dont care, 12 bytes of data
        //In order to get the converted .fea file to match, we need to pre-append 4 bytes of 0x00 since the first 4 bytes of the feature row read are not in the mask
        tempSlice := []byte{ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }
        copy(tempSlice[4:16], fileData[0:12])
        fmt.Println(tempSlice)

        err = Spi_cpldXO3_program_feature_row_cmd(spiNumber, tempSlice)
        if err != nil {
            return
        }
    } else {
        err = Spi_cpldXO3_program_page_flash_cmd(spiNumber, config, fileData)
        if err != nil {
            return
        }
    }

    if config == CONFIG0 {
        fmt.Printf("Writing usercode row 0x10060000\n")
        err = Spi_cpldXO3_write_usercode(spiNumber, 0x10060000)
        if err != nil {
            return
        }
    }
    if config == CONFIG1 {
        fmt.Printf("Writing usercode row 0x10060001\n")
        err = Spi_cpldXO3_write_usercode(spiNumber, 0x10060001)
        if err != nil {
            return
        }
    }

    err = Spi_cpldXO3_set_programming_done(spiNumber)
    if err != nil {
        return
    }

    err = Spi_cpldXO3_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpldXO3_no_op_cmd(spiNumber)
    if err != nil {
        return
    }


    if err == nil {
        fmt.Printf("Programming PASSED\n")
    } else {
        fmt.Printf("Programming FAILED\n")
    }

    return
}


func Spi_cpldXO3_convert_jed_file(filename string) (err error) {
    WRdata := []byte{}
    var max_row int = 12541
    var lines_converted int = 0
    var start_convert int = 0
    var u64 uint64 = 0

    if strings.Contains(filename, "jed")==true {
        fmt.Printf(" Jed file detected\n")
    } else {
        err = fmt.Errorf("ERROR: Input file is not a jed file type!!\n")
        cli.Printf("e", "%v", err)
        return
    }

    inF, err := os.Open(filename)
    if err != nil {
        fmt.Printf("ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    filename = strings.Replace(filename, "jed", "bin", 1)
    fmt.Printf(" BIN FILENAME = %s\n", filename)
    outF, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if err != nil {
        fmt.Printf("ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        inF.Close()
        return
    }

    scanner := bufio.NewScanner(inF)
    for scanner.Scan() {
        if(lines_converted == max_row) {
            break
        }
        lines := scanner.Text()
        bytes := []uint8(lines)
        if strings.Contains(lines, "L000000")==true {
            start_convert=1
            continue
        }
        
        if start_convert > 0 && (len(bytes) > 127) {
            //fmt.Printf(" %d : %d\n", lines_converted, len(bytes) ) 
            u64, _ = strconv.ParseUint(string(bytes[0:8]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[8:16]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[16:24]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[24:32]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[32:40]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[40:48]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[48:56]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[56:64]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[64:72]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[72:80]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[80:88]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[88:96]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[96:104]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[104:112]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[112:120]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            u64, _ = strconv.ParseUint(string(bytes[120:128]), 2, 8)
            WRdata = append(WRdata, uint8(u64))
            lines_converted = lines_converted + 1
        } 
    } 
    
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        inF.Close() 
        outF.Close()
        return
    }

    outF.WriteString(string(WRdata[:]))

    inF.Close()
    outF.Close()

    return
}



/**************************************************************************************** 
AFTER DATA, FIRST 12 BYTES ARE THE FEATURE ROW. 
Then there is a perdiod. 
Data after the period is feature bits (ignore first 2 bytes, use last 2 byteS). 

00000070  67 20 33 30 20 31 36 3a  33 34 3a 31 33 20 0a 44  |g 30 16:34:13 .D|
00000080  41 54 41 3a 0a 30 31 30  30 30 31 30 31 30 30 30  |ATA:.01000101000|
00000090  30 30 30 30 30 30 31 30  30 30 30 30 30 30 30 30  |0000001000000000|
000000a0  30 30 30 30 30 30 30 30  30 30 30 30 30 30 30 30  |0000000000000000|
000000b0  30 30 30 30 30 30 30 30  30 30 30 30 30 30 30 30  |0000000000000000|
000000c0  30 30 30 30 30 30 30 30  30 30 30 30 30 30 30 30  |0000000000000000|
000000d0  30 30 30 30 30 30 30 30  30 30 30 30 30 30 30 30  |0000000000000000|
000000e0  30 30 30 30 30 0a 30 30  30 30 30 30 30 30 30 30  |00000.0000000000|
000000f0  30 30 30 30 30 30 31 30  30 30 30 31 31 30 30 30  |0000001000011000|
00000100  31 30 30 30 30 30                                 |100000|


**** DIAG PROGRAMMING FEATURE ROW *************
[2024-09-04_11:55:14] diag@MTP:$ hexdump -C slot3_feature_row.bin
00000000  45 00 40 00 00 00 00 00  00 00 00 00 00 00 86 20  |E.@............ |
00000010


**** DONGLE PROGRAMMING FEATURE ROW *************
[2024-09-04_11:55:10] diag@MTP:$ hexdump -C fea.bin
00000000  00 00 00 00 45 00 40 00  00 00 00 00 00 00 00 00  |....E.@.........|
00000010 
 
 
READ FEATURE ROW 
00 00 00 00 45 00 40 00 00 00 00 00 00 00 00 00 
MASK 
00 00 00 00 FF FF FF FF FF FF FF FF FF FF FF FF 
 
READ FEATURE BITS 
00 00 86 20 
MASK 
00 00 FF FF 
****************************************************************************************/
func Spi_cpldXO3_convert_featurerow_jed_file(filename string) (err error) {
    WRdata := []byte{}
    //var lines_converted int = 0
    var start_convert int = 0
    //var u64 uint64 = 0

    if strings.Contains(filename, ".fea")==true {
        fmt.Printf(" Jed file detected\n")
    } else {
        err = fmt.Errorf("ERROR: Input file is not a jed file type!!\n")
        cli.Printf("e", "%v", err)
        return
    }

    inF, err := os.Open(filename)
    if err != nil {
        fmt.Printf("ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    filename = strings.Replace(filename, ".fea", ".bin", 1)
    fmt.Printf(" BIN FILENAME = %s\n", filename)
    outF, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if err != nil {
        fmt.Printf("ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        inF.Close()
        return
    }

    scanner := bufio.NewScanner(inF)
    for scanner.Scan() {
        lines := scanner.Text()
        bytes := []uint8(lines)
        if strings.Contains(lines, "DATA:")==true {
            start_convert=1
            continue
        }

        if start_convert > 0 {
            var u64 uint64 = 0
            for i:=0; i<len(bytes); i=i+8 {
                u64, _ = strconv.ParseUint(string(bytes[i:(i+8)]), 2, 8)
                WRdata = append(WRdata, uint8(u64))
            }
        }
    } 
    
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        inF.Close() 
        outF.Close()
        return
    }

    outF.WriteString(string(WRdata[:]))

    inF.Close()
    outF.Close()

    return
}







