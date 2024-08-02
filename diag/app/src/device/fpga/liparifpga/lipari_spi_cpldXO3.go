/* Support for Taormina MachXO3 9400 LUT cpld.  */
package liparifpga

import (
    //"errors"
    "common/cli"
    "fmt"
    "os"
    "bufio"
    "strings"
    "strconv"
    "time"
    "io"
)



const MACHXO3_9400_PAGE_SIZE             uint32 = 16
const MACHXO3_9400_CFG0_FLASH_SIZE       uint32 = (12541 * 16)    //12541 pages * 128 bits each = 200624 bytes
const MACHXO3_9400_CFG1_FLASH_SIZE       uint32 = (12541 * 16)    //12541 pages * 128 bits each = 200624 bytes
const MACHXO3_9400_UFM0_FLASH_SIZE       uint32 = (3582 * 16)     //3582 pages * 128 bits each = 57312 bytes
const MACHXO3_9400_UFM1_FLASH_SIZE       uint32 = (3582 * 16)     //3582 pages * 128 bits each = 57312 bytes
const MACHXO3_9400_UFM2_FLASH_SIZE       uint32 = (1150 * 16)    
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

const CPLD_STS_REG_BUSY_BIT         uint32 = 0x1000
const CPLD_STS_REG_FAIL_BIT         uint32 = 0x2000
const CPLD_BUSYFLAG_BUSY_BIT        uint32 = 0x80 
 
/*
var CPLDXO3_ENABLE_CONFIG_INTF_OP      = []byte{0x74, 0x08, 0x00, 0x00}   //enable configuration logic
var CPLDXO3_ENABLE_CONFIG_INTF_OP_RDLNG uint32 = 0



var CPLDXO3_RD_FEA_ROW_OP              = []byte{0xE7, 0x00, 0x00, 0x00}
var CPLDXO3_RD_FEA_ROW_OP_RDLNG        uint32 = 16



*/



var CPLDXO3_RD_STATUS_REG_OP           = []byte{0x3C, 0x00, 0x00, 0x00}
var CPLDXO3_RD_STATUS_REG_RDLNG        uint32 = 4

var CPLDXO3_ENABLE_CONFIG_INTF_OP      = []byte{0x74, 0x08, 0x00, 0x00}   //enable configuration logic
var CPLDXO3_ENABLE_CONFIG_INTF_OP_RDLNG uint32 = 0

var CPLDXO3_DISABLE_CONFIG_INTF_OP     = []byte{0x26, 0x00, 0x00}   //disable configuration logic
var CPLDXO3_DISABLE_CONFIG_INTF_OP_RDLNG uint32 = 0

var CPLDXO3_RD_USERCODE_OP             = []byte{0xC0, 0x00, 0x00, 0x00}
var CPLDXO3_RD_USERCODE_OP_RDLNG       uint32 = 4

var CPLDXO3_RD_DEVICE_ID_OP            = []byte{0xE0, 0x00, 0x00, 0x00}
var CPLDXO3_RD_DEVICE_ID_OP_RDLNG      uint32 = 4

var CPLDXO3_NO_OP                      = []byte{0xFF, 0xFF, 0xFF, 0xFF}   
var CPLDXO3_NO_OP_RDLNG                uint32 = 0

var CPLDXO3_RESET_CONFIG0_FLASH_OP     = []byte{0x46, 0x00, 0x01, 0x00}   
var CPLDXO3_RESET_CONFIG1_FLASH_OP     = []byte{0x46, 0x00, 0x02, 0x00}   
var CPLDXO3_RESET_FEATURE_ROW_OP       = []byte{0x46, 0x00, 0x04, 0x00}   //reset page pointer in flash
var CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG uint32 = 0

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
var CPLDXO3_ERASE_FEATURE_ROW_OP        = []byte{0x0E, 0x04, 0x00, 0x00}   //erase feature row
var CPLDXO3_ERASE_CONFIG_FLASH_RDLNG   uint32 = 0

var CPLDXO3_FEATURE_ROW_PROGRAM_OP      = []byte{0xE4, 0x00, 0x00, 0x00}
var CPLDXO3_FLASH_PROGRAM_PAGE_OP      = []byte{0x70, 0x00, 0x00, 0x01}
var CPLDXO3_FLASH_PROGRAM_PAGE_OP_RDLNG uint32 = 0

var CPLDXO3_RD_FLASH_OP                = []byte{0x73, 0x00, 0x00, 0x01}
var CPLDXO3_RD_FLASH_OP_RDLNG          uint32 = 16

var CPLDXO3_RD_FEA_BITS_OP             = []byte{0xFB, 0x00, 0x00}         
var CPLDXO3_RD_FEA_BITS_OP_RDLNG       uint32 = 2



func Spi_cpldXO3_read_usercode(spiNumber uint32) (ucode uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_USERCODE_OP, CPLDXO3_RD_USERCODE_OP_RDLNG) 
    if err != nil {
        return
    }
    for i=(int(CPLDXO3_RD_USERCODE_OP_RDLNG-1) * 8); i>=0; i=(i-8) {
        ucode = ucode | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpldXO3_read_device_id(spiNumber uint32) (devid uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_DEVICE_ID_OP, CPLDXO3_RD_DEVICE_ID_OP_RDLNG) 
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
    _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_ENABLE_CONFIG_INTF_OP, CPLDXO3_ENABLE_CONFIG_INTF_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}

func Spi_cpldXO3_disable_config_interface(spiNumber uint32) (err error) {
    _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_DISABLE_CONFIG_INTF_OP, CPLDXO3_DISABLE_CONFIG_INTF_OP_RDLNG) 
    return
}

func Spi_cpldXO3_no_op_cmd(spiNumber uint32) (err error) {
    _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_NO_OP, CPLDXO3_NO_OP_RDLNG) 
    return
}

func Spi_cpldXO3_read_feature_bits(spiNumber uint32) (FeatureBits uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}

    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_FEA_BITS_OP, CPLDXO3_RD_FEA_BITS_OP_RDLNG) 
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

    _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RESET_FEATURE_ROW_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    if err != nil {
        return
    }
     
    data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_FEA_ROW_OP, CPLDXO3_RD_FEA_ROW_OP_RDLNG) 
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
    data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_BUSYFLAG_OP, CPLDXO3_RD_BUSYFLAG_OP_RDLNG) 
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
    data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_STATUS_REG_OP, CPLDXO3_RD_STATUS_REG_RDLNG) 
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
    _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_ENABLE_OFFLINE_MODE_OP, CPLDXO3_ENABLE_OFFLINE_MODE_OP_RDLNG) 
    return
}

func Spi_cpldX03_return_flash_space_from_cli_arg(image string) (config uint32, err error) {
    if image == "cfg0" {
        config = CONFIG0
    } else if image == "cfg1" {
        config = CONFIG1
    } else if image == "fea" {
        config = FEATUREROW
    } else {
        err = fmt.Errorf("ERROR: FLASH PARTITION SPACE ENTERED IS NOT VALID.  YOU ENTERED '%s'\n", image)
        cli.Printf("e","%s", err)
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
        _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RESET_CONFIG0_FLASH_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == CONFIG1 {
        _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RESET_CONFIG1_FLASH_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    if space == FEATUREROW {
        _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RESET_FEATURE_ROW_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
    }
    return
}


func Spi_cpldXO3_set_programming_done(spiNumber uint32) (err error) {
    _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_PROGRAM_DONE_OP, CPLDXO3_PROGRAM_DONE_OP_RDLNG) 
    return
}

func Spi_cpldXO3_refresh(spiNumber uint32) (err error) {
    _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_REFRESH_OP, CPLDXO3_REFRESH_OP_RDLNG) 
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
        _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_ERASE_CONFIG0_FLASH_OP, CPLDXO3_ERASE_CONFIG_FLASH_RDLNG) 
    }
    if space == CONFIG1 {
        _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_ERASE_CONFIG1_FLASH_OP, CPLDXO3_ERASE_CONFIG_FLASH_RDLNG) 
    }
    if space == FEATUREROW {
        _ , err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_ERASE_FEATURE_ROW_OP, CPLDXO3_RESET_CONFIG_FLASH_OP_RDLNG) 
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
            err = fmt.Errorf("ERROR1 SPIBUS-%d: FLASH ERASE STUCK WAITING FOR BUSY FLAG TO CLEAR.  REG=0x%x\n", spiNumber, data32)
            cli.Printf("e","%s", err)
            return
        }
    }


    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e","%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e","%s", err)
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

    _ , err = lipari_spi_generic_transaction(spiNumber, spi_cmd, CPLDXO3_FLASH_PROGRAM_PAGE_OP_RDLNG) 
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
            err = fmt.Errorf("ERROR1 SPIBUS-%d: FLASH PROGRAM PAGE STUCK WAITING FOR BUSY FLAG TO CLEAR.  REG=0x%x\n", spiNumber, data32)
            cli.Printf("e","%s", err)
            return
        }


        data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
        if err != nil {
            return
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            cli.Printf("e","%s", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            cli.Printf("e","%s", err)
            return
        }
    }
    
    return
}


func Spi_cpldXO3_program_config_flash_cmd(spiNumber uint32, data []byte) (err error) {
    var sleep, max_try int = 1, 100
    var data32 uint32
    


    for j:=0; j < len(data); j=(j + int(MACHXO3_9400_PAGE_SIZE)) {
        spi_cmd := []byte{}

        if (j % 1600) == 0 {
            fmt.Printf(".")
        }

        for i:=0; i<len(CPLDXO3_FLASH_PROGRAM_PAGE_OP); i++ {
            spi_cmd = append(spi_cmd, CPLDXO3_FLASH_PROGRAM_PAGE_OP[i]) 
        }
        for i:=0; i<int(MACHXO3_9400_PAGE_SIZE); i++ {
            spi_cmd = append(spi_cmd, data[i + j]) 
        }

        _ , err = lipari_spi_generic_transaction(spiNumber, spi_cmd, CPLDXO3_FLASH_PROGRAM_PAGE_OP_RDLNG) 
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
                err = fmt.Errorf("ERROR1 SPIBUS-%d: FLASH PROGRAM PAGE STUCK WAITING FOR BUSY FLAG TO CLEAR.  REG=0x%x\n", spiNumber, data32)
                cli.Printf("e","%s", err)
                return
            }
        }


        data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
        if err != nil {
            return
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            cli.Printf("e","%s", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            cli.Printf("e","%s", err)
            return
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
    flashData := []byte{}
    fileData := []byte{}


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR spi_cpldXO3_verify_flash_contents. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        cli.Printf("e","%s", err)
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

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    fmt.Printf(" Verifying Image %s against CPLD flash\n", filename)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        fileData = append(fileData, b[0])
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
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e","%s", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e","%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e","%s", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }


    if config == FEATUREROW {
        flashData, _ = Spi_cpldXO3_read_feature_row(spiNumber) 
    } else {
        for j:=0; j<int(MACHXO3_9400_CFG0_FLASH_SIZE); j=(j + int(CPLDXO3_RD_FLASH_OP_RDLNG)) {
            data := []byte{}

            data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
            if err != nil {
                return
            }
            if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
                err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
                cli.Printf("e", "%s", err)
                return
            }
            if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
                err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
                cli.Printf("e", "%s", err)
                return
            }

            if (j % 500) == 0 {
                fmt.Printf(".")
            }

            data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_FLASH_OP, CPLDXO3_RD_FLASH_OP_RDLNG)
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
    if len(flashData) != len(fileData) {
        err = fmt.Errorf(" ERROR: File and Flash data size do not match.   Flash Data Size = %d.   File Data Size = %d\n", len(flashData), len(fileData) ) 
        cli.Printf("e", "%s", err)
        return;
    } 
    for i:=0; i<len(flashData); i++ {
        if flashData[i] != fileData[i] {
            err = fmt.Errorf(" ERROR: Data Mismatch at address 0x%x. Flash=%.02x   Expect=0x%02x\n", i, flashData[i], fileData[i] ) 
            cli.Printf("e", "%s", err)
            break
        }
    }
    if err == nil {
        fmt.Printf("Verification passed\n")
    } else {
        fmt.Printf("Verification failed\n")
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


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR Spi_cpldX03_generate_image_from_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        cli.Printf("e", "%s", err)
        return
    }
    //if spiNumber!=1 && spiNumber!=2 {
    //    err = fmt.Errorf("ERROR Spi_cpldX03_generate_image_from_flash. Only supprots CPLD on spi 1 and 2.  You entered %d\n", spiNumber)
    //    cli.Printf("e", "%s", err)
    //    return
    //}
    config, err = Spi_cpldX03_return_flash_space_from_cli_arg(image) 
    if err != nil {
        fmt.Printf("[ERROR] INVALID IMAGE TYPE  ERR=%s\n", err)
        return
    }


    err = os.Remove(filename)
    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
    }

    defer f.Close()

    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }

    err = Spi_cpldXO3_reset_config_flash(spiNumber, image)
    if err != nil {
        return
    }


    if config == FEATUREROW {
        flashData, _ = Spi_cpldXO3_read_feature_row(spiNumber)
    } else {
        for j:=0; j<int(MACHXO3_9400_CFG0_FLASH_SIZE); j=(j + int(CPLDXO3_RD_FLASH_OP_RDLNG)) {
            data := []byte{}

            data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
            if err != nil {
                return
            }
            if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
                err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
                cli.Printf("e", "%s", err)
                return
            }
            if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
                err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
                cli.Printf("e", "%s", err)
                return
            }

            if (j % 100) == 0 {
                fmt.Printf(".")
            }

            data, err = lipari_spi_generic_transaction(spiNumber, CPLDXO3_RD_FLASH_OP, CPLDXO3_RD_FLASH_OP_RDLNG) 
            if err != nil {
                return
            }
            for i:=0; i<int(CPLDXO3_RD_FLASH_OP_RDLNG); i++ {
                flashData = append(flashData, data[i])
            }
        }
    }


    f.WriteString(string(flashData[:]))

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




/////////////////////////////////////////////////////
//  
// ERASE FLASH SECTION
//  
//////////////////////////////////////////////////////
func Spi_cpldXO3_erase_flash(spiNumber uint32, image string) (err error) {
    var data32 uint32 = 0


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR Spi_cpldXO3_erase_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        cli.Printf("e", "%s", err)
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
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
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
        fmt.Printf("Erasing passed\n")
    } else {
        fmt.Printf("Erasing failed\n")
    }

    return
}







/////////////////////////////////////////////////////
//  
// PROGRAM A FILE INTO CFG FLASH
//  
//////////////////////////////////////////////////////
func Spi_cpldXO3_program_flash(spiNumber uint32, image string, filename string) (err error) {
    var data32 uint32 = 0
    var config uint32 = 0
    //flashData := []byte{}
    fileData := []byte{}


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("[ERROR]  Spi_cpldXO3_program_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        cli.Printf("e", "%s", err)
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
                fmt.Printf("ERRPR: Failed to convert filename=%s.  Exiting Programming CPLD  ERR=%s\n", filename, err)
                return
            }
        } else {
            err = fmt.Errorf("ERROR:  Spi_cpldXO3_program_flash. FEA FILE PASSED for programming cfg0 or cgf1.  File needs to be jed or bin\n")
            cli.Printf("e", "%s", err)
            return
        }
        filename = strings.Replace(filename, "fea", "bin", 1)
    }
    if strings.Contains(filename, "jed")==true {
        fmt.Printf(" Jed file detected..Converting to a BIN file\n")
        err = Spi_cpldXO3_convert_jed_file(filename)
        if err != nil {
            fmt.Printf("ERRPR: Failed to convert filename=%s.  Exiting Programming CPLD  ERR=%s\n", filename, err)
            return
        }
        filename = strings.Replace(filename, "jed", "bin", 1)
    }

     
    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    fmt.Printf(" Programming Image %s to CPLD flash\n", filename)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        fileData = append(fileData, b[0])
    }
    fmt.Printf(" Length File Data = %d\n", len(fileData))

    err = Spi_cpldXO3_enable_config_interface(spiNumber)
    if err != nil {
        return
    }
    data32, err = Spi_cpldXO3_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }

    data32, err = Spi_cpldXO3_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
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
        err = Spi_cpldXO3_program_feature_row_cmd(spiNumber, fileData)
        if err != nil {
            return
        }
    } else {
        err = Spi_cpldXO3_program_config_flash_cmd(spiNumber, fileData)
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
        fmt.Printf("Programming passed\n")
    } else {
        fmt.Printf("Programming failed\n")
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
        cli.Printf("e", "%s", err)
        return
    }

    inF, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    filename = strings.Replace(filename, "jed", "bin", 1)
    fmt.Printf(" BIN FILENAME = %s\n", filename)
    outF, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer func() { 
        inF.Close()
        outF.Close()
    } ()

    
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
        return
    }

    outF.WriteString(string(WRdata[:]))

    return
}


func Spi_cpldXO3_convert_featurerow_jed_file(filename string) (err error) {
    WRdata := []byte{}
    bytes := []uint8{}
    var u64 uint64 = 0

    if strings.Contains(filename, "fea")==true {
        fmt.Printf(" fea file detected\n")
    } else {
        err = fmt.Errorf("ERROR: Input file is not a fea file type!!\n")
        cli.Printf("e", "%s", err)
        return
    }

    inF, err := os.Open(filename)
    if err != nil {
        fmt.Printf("ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    filename = strings.Replace(filename, "fea", "bin", 1)
    fmt.Printf(" BIN FILENAME = %s\n", filename)

    outF, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if err != nil {
        fmt.Printf("ERROR: Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer func() { 
        inF.Close()
        outF.Close()
    } ()

    rd := bufio.NewReader(inF)
    for {
        tbyte := []byte{}
        tbyte, err = rd.ReadBytes('\n')

        bytes = append(bytes, tbyte...)

        if err == io.EOF {
                break
        }

        if err != nil {
            fmt.Printf("ERROR: READING FEATURE ROW FILE  ERR=%s\n", err)
            return 
            break              
        }
    }

    for i:=0x97; i<len(bytes); {
        u64, _ = strconv.ParseUint(string(bytes[i:(i+8)]), 2, 8)
        WRdata = append(WRdata, uint8(u64))
        if i==0xF7 {
            i = i+2
        }
        i = i + 8
    }
    outF.WriteString(string(WRdata[:]))

    return
}






