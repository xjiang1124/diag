/* Support for Taormina MachXO2-2000 cpld.  Device ID 0x01 2B B0 43   */
package taorfpga

import (
    //"errors"
    "fmt"
    "os"
    "bufio"
    "time"
)

const SPI_SLICE_SZ      uint32 = 0x20
const SPI_NUMB_BUSES    uint32 = 0x08
const SPI_FPGA_DOMAIN   uint32 = 0x02

const SPI_STA_EOP       uint32 = 0x0200
const SPI_STA_ERROR     uint32 = 0x0100
const SPI_STA_RCV_RDY   uint32 = 0x0080
const SPI_STA_TMT_RDY   uint32 = 0x0040
const SPI_STA_TMTS_RDY  uint32 = 0x0020
const SPI_STA_TOE       uint32 = 0x0010
const SPI_STA_ROE       uint32 = 0x0004

/* 
ccpld     machXO2 2k
ecpld0    machX03D 9400 LUT
ecpld1    machX03D 9400 LUT
gcpld0    machXO2 2k
gcpld1    machXO2 2k
gcpld2    machXO2 2k
eqspi0    Micron 2G serial flash
eqspi1    Micron 2G serial flash
 
const D2_SPI0_RXDATA_REG            uint64 = 0x400
const D2_SPI0_TXDATA_REG            uint64 = 0x404
const D2_SPI0_STATUS_REG            uint64 = 0x408
const D2_SPI0_CONTROL_REG           uint64 = 0x40c
const D2_SPI0_SEM_REG               uint64 = 0x410
const D2_SPI0_SLAVESEL_REG          uint64 = 0x414
const D2_SPI0_EOP_VALUE_REG         uint64 = 0x418
const D2_SPI0_MUXSEL_REG            uint64 = 0x41c 
*/

const MACHXO2_2K_PAGE_SIZE            uint32 = 16
const MACHXO2_2K_CFG_FLASH_SIZE       uint32 = (3198 * 16)    //3198 pages * 128 bits each = 51168 bytes
const MACHXO2_2K_UFM_FLASH_SIZE       uint32 = (640 * 16)     //640 pages * 128 bits each = 10240 bytes

var FPGA_SPI_DEV_NAME = []string{"ccpld", "ecpld0", "ecpld0", "gcpld0", "gcpld1", "gcpld2", "eqspi0", "eqspi0",}


var CPLD_ERASE_CONFIG_FLASH_OP      = []byte{0x0E, 0x04, 0x00, 0x00}   //erase config flash
var CPLD_ERASE_CONFIG_FLASH_RDLNG   uint32 = 0

var CPLD_DISABLE_CONFIG_INTF_OP     = []byte{0x26, 0x00, 0x00}   //disable configuration logic
var CPLD_DISABLE_CONFIG_INTF_OP_RDLNG uint32 = 0

var CPLD_RD_STATUS_REG_OP           = []byte{0x3C, 0x00, 0x00, 0x00}
var CPLD_RD_STATUS_REG_RDLNG        uint32 = 4
const CPLD_STS_REG_BUSY_BIT         uint32 = 0x1000
const CPLD_STS_REG_FAIL_BIT         uint32 = 0x2000
const CPLD_BUSYFLAG_BUSY_BIT        uint32 = 0x80

var CPLD_RESET_CONFIG_FLASH_OP      = []byte{0x46, 0x00, 0x00, 0x00}   //reset page pointer in flash
var CPLD_RESET_FEATURE_ROW_OP      = []byte{0x46, 0x00, 0x04, 0x00}   //reset page pointer in flash
var CPLD_RESET_CONFIG_FLASH_OP_RDLNG uint32 = 0

var CPLD_PROGRAM_DONE_OP            = []byte{0x5E, 0x00, 0x00, 0x00}   //programming done bit
var CPLD_PROGRAM_DONE_OP_RDLNG      uint32 = 0

var CPLD_FLASH_PROGRAM_PAGE_OP      = []byte{0x70, 0x00, 0x00, 0x01}
var CPLD_FLASH_PROGRAM_PAGE_OP_RDLNG uint32 = 0

var CPLD_RD_FLASH_OP                = []byte{0x73, 0x00, 0x00, 0x01}
var CPLD_RD_FLASH_OP_RDLNG          uint32 = 16

var CPLD_ENABLE_CONFIG_INTF_OP      = []byte{0x74, 0x08, 0x00, 0x00}   //enable configuration logic
var CPLD_ENABLE_CONFIG_INTF_OP_RDLNG uint32 = 0

var CPLD_REFRESH_OP                 = []byte{0x79, 0x00, 0x00}
var CPLD_REFRESH_OP_RDLNG           uint32 = 0

var CPLD_RD_USERCODE_OP             = []byte{0xC0, 0x00, 0x00, 0x00}
var CPLD_RD_USERCODE_OP_RDLNG       uint32 = 4

var CPLD_ENABLE_OFFLINE_MODE_OP     = []byte{0xC6, 0x08, 0x00, 0x00}   
var CPLD_ENABLE_OFFLINE_MODE_OP_RDLNG uint32 = 0

var CPLD_RD_DEVICE_ID_OP            = []byte{0xE0, 0x00, 0x00, 0x00}
var CPLD_RD_DEVICE_ID_OP_RDLNG      uint32 = 4

var CPLD_RD_FEA_ROW_OP              = []byte{0xE7, 0x00, 0x00, 0x00}
var CPLD_RD_FEA_ROW_OP_RDLNG        uint32 = 16

var CPLD_RD_BUSYFLAG_OP             = []byte{0xF0, 0x00, 0x00, 0x00}
var CPLD_RD_BUSYFLAG_OP_RDLNG       uint32 = 1

var CPLD_RD_FEA_BITS_OP             = []byte{0xFB, 0x00, 0x00}         
var CPLD_RD_FEA_BITS_OP_RDLNG       uint32 = 2

var CPLD_NO_OP                      = []byte{0xFF, 0xFF, 0xFF, 0xFF}   
var CPLD_NO_OP_RDLNG                uint32 = 0


func Spi_load_register_set(spiNumber uint32) (err error) {
    fmt.Printf(" SPI LOAD REG SET\n")
    return
}


func Spi_check_tx_drain(spiNumber uint32) (err error) {
    var data32 uint32 = 0
    var timeout, x uint32 = 500, 0

    //check status reg for status on tx data drain
    for x=0; x<timeout; x++ {
        data32, err = TaorReadU32(SPI_FPGA_DOMAIN, (D2_SPI0_STATUS_REG + uint64(SPI_SLICE_SZ * spiNumber)))    
        if (data32 & SPI_STA_TOE) == SPI_STA_TOE {   //transmit overrun error
            err = fmt.Errorf("ERROR Spi_check_tx_drain. Spi-%d, TRANSMIT OVERRUN ERROR SET.  Status Reg = 0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }
        if (data32 & SPI_STA_TMT_RDY) == SPI_STA_TMT_RDY {
            break;
        }


        const SPI_STA_TOE       uint32 = 0x0010
    }
    if x == timeout {
        err = fmt.Errorf("ERROR Spi_check_tx_drain. Spi-%d, not seeing transmitter ready.  Status Reg = 0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }
    return
}

func Spi_check_rx_ready(spiNumber uint32) (err error) {
    var data32 uint32 = 0
    var timeout, x uint32 = 500, 0

    //check status reg for status on tx data drain
    for x=0; x<timeout; x++ {
        data32, err = TaorReadU32(SPI_FPGA_DOMAIN, (D2_SPI0_STATUS_REG + uint64(SPI_SLICE_SZ * spiNumber)))    
        if (data32 & SPI_STA_ROE) == SPI_STA_ROE {   //receive overrun error
            err = fmt.Errorf("ERROR Spi_check_rx_ready. Spi-%d, RECEIVE OVERRUN ERROR SET.  Status Reg = 0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }
        if (data32 & SPI_STA_RCV_RDY) == SPI_STA_RCV_RDY {
            break;
        }
    }
    if x == timeout {
        err = fmt.Errorf("ERROR Spi_check_rx_ready. Spi-%d, not seeing receiver ready.  Status Reg = 0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }
    return
}



func Fpga_spi_generic_transaction(spiNumber uint32, opCode []byte, rdLength uint32) (rdData []byte, err error) {
    var data32 uint32 = 0

    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR Fpga_spi_generic_transaction. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        fmt.Printf("%s", err)
        return
    }

    TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_MUXSEL_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0x00)  //turn mux select to FPGA on
    TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_SLAVESEL_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0x01)  //enable slave access
    TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_CONTROL_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0x400)  //turn on spi output
    //clear status
    TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_STATUS_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0x00)


    for i:=0; i<len(opCode); i++ {
        TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_TXDATA_REG + uint64(SPI_SLICE_SZ * spiNumber)) , uint32(opCode[i]))
        err = Spi_check_tx_drain(spiNumber)
        if err != nil {
            return
        }
        err = Spi_check_rx_ready(spiNumber)
        if err != nil {
            return
        }
        //Just discard this.. keeps errors from getting set in the status register
        data32, err = TaorReadU32(SPI_FPGA_DOMAIN, (D2_SPI0_RXDATA_REG + uint64(SPI_SLICE_SZ * spiNumber)))
    }
     
  
    //clear status
    TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_STATUS_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0x00)

    for i:=0; i<int(rdLength); i++ {
        TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_TXDATA_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0xFF)
        err = Spi_check_tx_drain(spiNumber)
        if err != nil {
            return
        }
        err = Spi_check_rx_ready(spiNumber)
        if err != nil {
            return
        }
        data32, err = TaorReadU32(SPI_FPGA_DOMAIN, (D2_SPI0_RXDATA_REG + uint64(SPI_SLICE_SZ * spiNumber)))
        rdData = append(rdData, byte(data32))
    }

    TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_CONTROL_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0x00)  //turn off spi output
    TaorWriteU32(SPI_FPGA_DOMAIN, (D2_SPI0_MUXSEL_REG + uint64(SPI_SLICE_SZ * spiNumber)) , 0x01)  //turn mux select to FPGA off

    return 
}


func Spi_cpld_read_usercode(spiNumber uint32) (ucode uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_USERCODE_OP, CPLD_RD_USERCODE_OP_RDLNG) 
    for i=(int(CPLD_RD_USERCODE_OP_RDLNG-1) * 8); i>=0; i=(i-8) {
        ucode = ucode | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpld_read_device_id(spiNumber uint32) (devid uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_DEVICE_ID_OP, CPLD_RD_DEVICE_ID_OP_RDLNG) 
    for i=(int(CPLD_RD_DEVICE_ID_OP_RDLNG-1) * 8); i>=0; i=i-8 {
        devid = devid | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpld_read_feature_bits(spiNumber uint32) (FeatureBits uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}

    err = Spi_cpld_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_FEA_BITS_OP, CPLD_RD_FEA_BITS_OP_RDLNG) 
    for i=(int(CPLD_RD_FEA_BITS_OP_RDLNG-1) * 8); i>=0; i=i-8 {
        FeatureBits = FeatureBits | (uint32(data[j])<<uint32(i))
        j++
    }

    err = Spi_cpld_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpld_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    return

}

func Spi_cpld_read_feature_row(spiNumber uint32) (data []byte, err error) {
    //var i, j int = 0, 0;
    //data := []byte{}


    
    err = Spi_cpld_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_RESET_FEATURE_ROW_OP, CPLD_RESET_CONFIG_FLASH_OP_RDLNG) 
    if err != nil {
        return
    }
     

    data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_FEA_ROW_OP, CPLD_RD_FEA_ROW_OP_RDLNG) 
    //for i=(int(CPLD_RD_FEA_ROW_OP_RDLNG-1) * 8); i>=0; i=i-8 {
    //    FeatureBits = FeatureBits | (uint32(data[j])<<uint32(i))
    //    j++
    //}

    err = Spi_cpld_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpld_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    return

}


func Spi_cpld_read_busy_flag(spiNumber uint32) (BusyFlag uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_BUSYFLAG_OP, CPLD_RD_BUSYFLAG_OP_RDLNG) 
    for i=(int(CPLD_RD_BUSYFLAG_OP_RDLNG-1) * 8); i>=0; i=i-8 {
        BusyFlag = BusyFlag | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpld_read_status_reg(spiNumber uint32) (StatusReg uint32, err error) {
    var i, j int = 0, 0;
    data := []byte{}
    data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_STATUS_REG_OP, CPLD_RD_STATUS_REG_RDLNG) 
    for i=(int(CPLD_RD_STATUS_REG_RDLNG-1) * 8); i>=0; i=i-8 {
        StatusReg = StatusReg | (uint32(data[j])<<uint32(i))
        j++
    }
    return
}

func Spi_cpld_enable_config_interface(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_ENABLE_CONFIG_INTF_OP, CPLD_ENABLE_CONFIG_INTF_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}

func Spi_cpld_enable_offline_mode(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_ENABLE_OFFLINE_MODE_OP, CPLD_ENABLE_OFFLINE_MODE_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}

func Spi_cpld_no_op_cmd(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_NO_OP, CPLD_NO_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}


func Spi_cpld_reset_config_flash(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_RESET_CONFIG_FLASH_OP, CPLD_RESET_CONFIG_FLASH_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}


func Spi_cpld_disable_config_interface(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_DISABLE_CONFIG_INTF_OP, CPLD_DISABLE_CONFIG_INTF_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}


func Spi_cpld_set_programming_done(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_PROGRAM_DONE_OP, CPLD_PROGRAM_DONE_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}

func Spi_cpld_refresh(spiNumber uint32) (err error) {
    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_REFRESH_OP, CPLD_REFRESH_OP_RDLNG) 
    if err != nil {
        return
    }
    return
}



func Spi_cpld_erase_config_flash(spiNumber uint32) (err error) {
    var sleep, max_try int = 100, 100
    var data32 uint32

    _ , err = Fpga_spi_generic_transaction(spiNumber, CPLD_ERASE_CONFIG_FLASH_OP, CPLD_ERASE_CONFIG_FLASH_RDLNG) 
    if err != nil {
        return
    }

    for i:=0; i<max_try; i++ {
        data32, err = Spi_cpld_read_busy_flag(spiNumber)
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
            fmt.Printf("%s", err)
            return
        }
    }


    data32, err = Spi_cpld_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }
    
    return
}


func Spi_cpld_program_config_flash_cmd(spiNumber uint32, data []byte) (err error) {
    var sleep, max_try int = 1, 100
    var data32 uint32
    


    for j:=0; j < len(data); j=(j + int(MACHXO2_2K_PAGE_SIZE)) {
        spi_cmd := []byte{}

        if (j % 1600) == 0 {
            fmt.Printf(".")
        }

        for i:=0; i<len(CPLD_FLASH_PROGRAM_PAGE_OP); i++ {
            spi_cmd = append(spi_cmd, CPLD_FLASH_PROGRAM_PAGE_OP[i]) 
        }
        for i:=0; i<int(MACHXO2_2K_PAGE_SIZE); i++ {
            spi_cmd = append(spi_cmd, data[i + j]) 
        }

        _ , err = Fpga_spi_generic_transaction(spiNumber, spi_cmd, CPLD_FLASH_PROGRAM_PAGE_OP_RDLNG) 
        if err != nil {
            return
        }

        for i:=0; i<max_try; i++ {
            data32, err = Spi_cpld_read_busy_flag(spiNumber)
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
                fmt.Printf("%s", err)
                return
            }
        }


        data32, err = Spi_cpld_read_status_reg(spiNumber)
        if err != nil {
            return
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }
    }
    
    return
}



/***************************************************** 
*  
* VERIFY FLASH CONTENTS VS A FILE
*  
*****************************************************/ 
func Spi_cpld_machxO2_verify_flash_contents(spiNumber uint32, filename string) (err error) {
    var data32 uint32 = 0
    flashData := []byte{}
    fileData := []byte{}


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR Spi_cpld_machxO2_verify_flash_contents. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        fmt.Printf("%s", err)
        return
    }
    if spiNumber!=0 && spiNumber!=3 && spiNumber!=4 && spiNumber!=5 {
        err = fmt.Errorf("ERROR Spi_cpld_machxO2_verify_flash_contents. Only supprots CPLd on spi 0,3,4,5.  You entered %d\n", spiNumber)
        fmt.Printf("%s", err)
        return
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
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        return
    }

    err = Spi_cpld_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data32, err = Spi_cpld_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }

    data32, err = Spi_cpld_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }

    err = Spi_cpld_reset_config_flash(spiNumber)
    if err != nil {
        return
    }


    for j:=0; j<int(MACHXO2_2K_CFG_FLASH_SIZE); j=(j + int(CPLD_RD_FLASH_OP_RDLNG)) {
        data := []byte{}
        data32, err = Spi_cpld_read_status_reg(spiNumber)
        if err != nil {
            return
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }

        if (j % 500) == 0 {
            fmt.Printf(".")
        }

        data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_FLASH_OP, CPLD_RD_FLASH_OP_RDLNG) 
        for i:=0; i<int(CPLD_RD_FLASH_OP_RDLNG); i++ {
            flashData = append(flashData, data[i])
        }
    }
    fmt.Printf("\n")

    err = Spi_cpld_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpld_no_op_cmd(spiNumber)
    if err != nil {
        return
    }


    //f.WriteString(string(flashData[:]))
    if len(flashData) != len(fileData) {
        err = fmt.Errorf(" ERROR: File and Flash data size do not match.   Flash Data Size = %d.   File Data Size = %d\n", len(flashData), len(fileData) ) 
        fmt.Printf("%s", err)
        return;
    } 
    for i:=0; i<len(flashData); i++ {
        if flashData[i] != fileData[i] {
            err = fmt.Errorf(" ERROR: Data Mismatch at address 0x%x. Flash=%.02x   Expect=0x%02x\n", i, flashData[i], fileData[i] ) 
            fmt.Printf("%s", err)
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

/***************************************************** 
*  
* READ LOCAL IMAGE AND WRITE IT TO A FILE 
*  
*****************************************************/ 
func Spi_cpld_machxO2_generate_image_from_flash(spiNumber uint32, filename string) (err error) {
    var data32 uint32 = 0
    flashData := []byte{}


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR spi_cpld_generate_image_from_flash. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        fmt.Printf("%s", err)
        return
    }
    if spiNumber!=0 && spiNumber!=3 && spiNumber!=4 && spiNumber!=5 {
        err = fmt.Errorf("ERROR spi_cpld_generate_image_from_flash. Only supprots CPLd on spi 0,3,4,5.  You entered %d\n", spiNumber)
        fmt.Printf("%s", err)
        return
    }

    err = os.Remove(filename)
    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
    }

    defer f.Close()

    err = Spi_cpld_enable_config_interface(spiNumber)
    if err != nil {
        return
    }

    data32, err = Spi_cpld_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }

    data32, err = Spi_cpld_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }

    err = Spi_cpld_reset_config_flash(spiNumber)
    if err != nil {
        return
    }


    for j:=0; j<int(MACHXO2_2K_CFG_FLASH_SIZE); j=(j + int(CPLD_RD_FLASH_OP_RDLNG)) {
        data := []byte{}

        data32, err = Spi_cpld_read_status_reg(spiNumber)
        if err != nil {
            return
        }
        if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }
        if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
            err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
            fmt.Printf("%s", err)
            return
        }

        if (j % 100) == 0 {
            fmt.Printf(".")
        }

        data, err = Fpga_spi_generic_transaction(spiNumber, CPLD_RD_FLASH_OP, CPLD_RD_FLASH_OP_RDLNG) 
        for i:=0; i<int(CPLD_RD_FLASH_OP_RDLNG); i++ {
            flashData = append(flashData, data[i])
        }
    }


    f.WriteString(string(flashData[:]))

    err = Spi_cpld_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpld_no_op_cmd(spiNumber)
    if err != nil {
        return
    }

    return 
}





/***************************************************** 
*  
* PROGRAM A FILE INTO CFG FLASH
*  
*****************************************************/ 
func Spi_cpld_machxO2_program_flash(spiNumber uint32, filename string) (err error) {
    var data32 uint32 = 0
    //flashData := []byte{}
    fileData := []byte{}


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR Spi_cpld_machxO2_verify_flash_contents. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        fmt.Printf("%s", err)
        return
    }
    if spiNumber!=0 && spiNumber!=3 && spiNumber!=4 && spiNumber!=5 {
        err = fmt.Errorf("ERROR Spi_cpld_machxO2_verify_flash_contents. Only supprots CPLd on spi 0,3,4,5.  You entered %d\n", spiNumber)
        fmt.Printf("%s", err)
        return
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    fmt.Printf(" Programming Image %s against CPLD flash\n", filename)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        fileData = append(fileData, b[0])
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        return
    }
    fmt.Printf(" Length File Data = %d\n", len(fileData))

    err = Spi_cpld_enable_config_interface(spiNumber)
    if err != nil {
        return
    }
    data32, err = Spi_cpld_read_busy_flag(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_BUSYFLAG_BUSY_BIT == CPLD_BUSYFLAG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }

    data32, err = Spi_cpld_read_status_reg(spiNumber)
    if err != nil {
        return
    }
    if data32 & CPLD_STS_REG_BUSY_BIT == CPLD_STS_REG_BUSY_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH BUSY FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }
    if data32 & CPLD_STS_REG_FAIL_BIT == CPLD_STS_REG_FAIL_BIT {
        err = fmt.Errorf("ERROR1 SPIBUS-%d: CPLD STS REG: FLASH FAIL FLAG IS SET.  REG=0x%x\n", spiNumber, data32)
        fmt.Printf("%s", err)
        return
    }

    err = Spi_cpld_reset_config_flash(spiNumber)
    if err != nil {
        return
    }


    err = Spi_cpld_erase_config_flash(spiNumber) 
    if err != nil {
        return
    }


    err = Spi_cpld_reset_config_flash(spiNumber)
    if err != nil {
        return
    }

    err = Spi_cpld_program_config_flash_cmd(spiNumber, fileData)
    if err != nil {
        return
    }

    err = Spi_cpld_set_programming_done(spiNumber)
    if err != nil {
        return
    }

    err = Spi_cpld_disable_config_interface(spiNumber)
    if err != nil {
        return
    }
    err = Spi_cpld_no_op_cmd(spiNumber)
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




