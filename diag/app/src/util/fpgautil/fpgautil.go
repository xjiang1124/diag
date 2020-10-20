/* CS0 = FPGA  / CS1 = SPI-to-I2C interface  / CS2 = SPI FLASH */
package main

//#cgo CFLAGS: -I. -I../../../../lib/util
//// #cgo CFLAGS: -I../../../../../include
//#cgo LDFLAGS: -lutil -lcpld
//#include <util.h> 
// #include <stdlib.h>
// #include "../../../../lib/capricpld/cpld.h" 
import "C"

import (
    "errors"
    "fmt"
    //"flag"
    "os"
    "strconv"
    //"common/cli"
    "golang.org/x/exp/io/spi"
    //"sync"
    "time"

    //"syscall"
    //"unsafe"
)


const QSFP_1_I2C_BUS        uint8  = 0
const QSFP_1_SLAVE_ADDRESS  uint8  = 0x50

const QSFP_2_I2C_BUS        uint8  = 1
const QSFP_2_SLAVE_ADDRESS  uint8  = 0x50

const QSFP_DOM_1_I2C_BUS        uint8  = 0
const QSFP_DOM_1_SLAVE_ADDRESS  uint8  = 0x51

const QSFP_DOM_2_I2C_BUS        uint8  = 1
const QSFP_DOM_2_SLAVE_ADDRESS  uint8  = 0x51

const I2C_BUS                   uint8  = 2
const FRU_SLAVE_ADDRESS         uint8  = 0x50
const FRU_SIZE                  uint16 = 256

//const I2C_BASE          uint16 = 0x400
//const I2C_STRIDE        uint16 = 0x400
const S2I_BUS_STRIDE    uint16 = 0x100

/*
 * Registers offset
 */
const IC_CON            uint8 = 0x0
const IC_TAR            uint8 = 0x4
const IC_SAR            uint8 = 0x8
const IC_HS_MADDR       uint8 = 0xC
const IC_DATA_CMD       uint8 = 0x10
const IC_SS_SCL_HCNT    uint8 = 0x14
const IC_SS_SCL_LCNT    uint8 = 0x18
const IC_FS_SCL_HCNT    uint8 = 0x1c
const IC_FS_SCL_LCNT    uint8 = 0x20
const IC_INTR_STAT      uint8 = 0x2c
const IC_INTR_MASK      uint8 = 0x30
const IC_RAW_INTR_STAT	uint8 = 0x34
const IC_RX_TL          uint8 = 0x38
const IC_TX_TL          uint8 = 0x3c
const IC_CLR_INTR       uint8 = 0x40
const IC_CLR_RX_UNDER   uint8 = 0x44
const IC_CLR_RX_OVER    uint8 = 0x48
const IC_CLR_TX_OVER    uint8 = 0x4c
const IC_CLR_RD_REQ     uint8 = 0x50
const IC_CLR_TX_ABRT    uint8 = 0x54
const IC_CLR_RX_DONE    uint8 = 0x58
const IC_CLR_ACTIVITY   uint8 = 0x5c
const IC_CLR_STOP_DET   uint8 = 0x60
const IC_CLR_START_DET  uint8 = 0x64
const IC_CLR_GEN_CALL   uint8 = 0x68
const IC_ENABLE         uint8 = 0x6c
const IC_STATUS         uint8 = 0x70
const IC_TXFLR          uint8 = 0x74
const IC_RXFLR          uint8 = 0x78
const IC_SDA_HOLD       uint8 = 0x7c
const IC_TX_ABRT_SOURCE	uint8 = 0x80
const IC_ENABLE_STATUS  uint8 = 0x9c
const IC_SDA_SETUP      uint8 = 0x94
const IC_FS_SPKLEN      uint8 = 0xa0
const IC_COMP_PARAM_1   uint8 = 0xf4
const IC_COMP_VERSION   uint8 = 0xf8
const IC_SDA_HOLD_MIN_VERS  uint32 = 0x3131312A
const IC_COMP_TYPE          uint8  = 0xfc
const IC_COMP_TYPE_VALUE    uint32 = 0x44570140

const IC_INTR_RX_UNDER  uint16 = 0x001
const IC_INTR_RX_OVER   uint16 = 0x002
const IC_INTR_RX_FULL   uint16 = 0x004
const IC_INTR_TX_OVER   uint16 = 0x008
const IC_INTR_TX_EMPTY  uint16 = 0x010
const IC_INTR_RD_REQ    uint16 = 0x020
const IC_INTR_TX_ABRT   uint16 = 0x040
const IC_INTR_RX_DONE   uint16 = 0x080
const IC_INTR_ACTIVITY  uint16 = 0x100
const IC_INTR_STOP_DET  uint16 = 0x200
const IC_INTR_START_DET uint16 = 0x400
const IC_INTR_GEN_CALL  uint16 = 0x800

const IC_INTR_DEFAULT_MASK  uint16 =    ( IC_INTR_RX_FULL | 
                                          IC_INTR_TX_EMPTY | 
                                          IC_INTR_TX_ABRT  | 
                                          IC_INTR_STOP_DET )

type ABP_I2C_REGISTERS struct {
    Name     string
    Address  uint8
}


var APB_REG_s = []ABP_I2C_REGISTERS {
    ABP_I2C_REGISTERS{"IC_CON",             IC_CON},
    ABP_I2C_REGISTERS{"IC_TAR",             IC_TAR},
    ABP_I2C_REGISTERS{"IC_SAR",             IC_SAR},
    ABP_I2C_REGISTERS{"IC_HS_MADDR",        IC_HS_MADDR},
    ABP_I2C_REGISTERS{"IC_DATA_CMD",        IC_DATA_CMD},
    ABP_I2C_REGISTERS{"IC_SS_SCL_HCNT",     IC_SS_SCL_HCNT},
    ABP_I2C_REGISTERS{"IC_SS_SCL_LCNT",     IC_SS_SCL_LCNT},
    ABP_I2C_REGISTERS{"IC_FS_SCL_HCNT",     IC_FS_SCL_HCNT},
    ABP_I2C_REGISTERS{"IC_FS_SCL_LCNT",     IC_FS_SCL_LCNT},
    ABP_I2C_REGISTERS{"IC_INTR_STAT",       IC_INTR_STAT},
    ABP_I2C_REGISTERS{"IC_INTR_MASK",       IC_INTR_MASK},
    ABP_I2C_REGISTERS{"IC_RAW_INTR_STAT",   IC_RAW_INTR_STAT},
    ABP_I2C_REGISTERS{"IC_RX_TL",           IC_RX_TL},
    ABP_I2C_REGISTERS{"IC_TX_TL",           IC_TX_TL},
    ABP_I2C_REGISTERS{"IC_CLR_INTR",        IC_CLR_INTR},
    ABP_I2C_REGISTERS{"IC_CLR_RX_UNDER",    IC_CLR_RX_UNDER},
    ABP_I2C_REGISTERS{"IC_CLR_RX_OVER",     IC_CLR_RX_OVER},
    ABP_I2C_REGISTERS{"IC_CLR_TX_OVER",     IC_CLR_TX_OVER},
    ABP_I2C_REGISTERS{"IC_CLR_RD_REQ",      IC_CLR_RD_REQ},
    ABP_I2C_REGISTERS{"IC_CLR_TX_ABRT",     IC_CLR_TX_ABRT},
    ABP_I2C_REGISTERS{"IC_CLR_RX_DONE",     IC_CLR_RX_DONE},
    ABP_I2C_REGISTERS{"IC_CLR_ACTIVITY",    IC_CLR_ACTIVITY},
    ABP_I2C_REGISTERS{"IC_CLR_STOP_DET",    IC_CLR_STOP_DET},
    ABP_I2C_REGISTERS{"IC_CLR_START_DET",   IC_CLR_START_DET},
    ABP_I2C_REGISTERS{"IC_CLR_GEN_CALL",    IC_CLR_GEN_CALL},
    ABP_I2C_REGISTERS{"IC_ENABLE",          IC_ENABLE},
    ABP_I2C_REGISTERS{"IC_STATUS",          IC_STATUS},
    ABP_I2C_REGISTERS{"IC_TXFLR",           IC_TXFLR},
    ABP_I2C_REGISTERS{"IC_RXFLR",           IC_RXFLR},
    ABP_I2C_REGISTERS{"IC_SDA_HOLD",        IC_SDA_HOLD},
    ABP_I2C_REGISTERS{"IC_TX_ABRT_SOURCE",  IC_TX_ABRT_SOURCE},
    ABP_I2C_REGISTERS{"IC_ENABLE_STATUS",   IC_ENABLE_STATUS},
    ABP_I2C_REGISTERS{"IC_SDA_SETUP",       IC_SDA_SETUP},
    ABP_I2C_REGISTERS{"IC_FS_SPKLEN",       IC_FS_SPKLEN},
    ABP_I2C_REGISTERS{"IC_COMP_PARAM_1",    IC_COMP_PARAM_1},
    ABP_I2C_REGISTERS{"IC_COMP_VERSION",    IC_COMP_VERSION},
}





const errhelp = "\nfpgautil:\n" +
        "### READ / WRITE FPGA CS0 ###\n" +
        "fpgautil r <addr>\n"   +
        "fpgautil w <addr> <data>\n" +
        "fpgautil apbr <addr>\n"   +
        "fpgautil apbw <addr> <data>\n" +
        "fpgautil ee r  <addr> \n" +
        "fpgautil ee w  <addr> <data>\n" +
        "fpgautil apbdump < bus>\n" +
        "mappedi2c bus i2c_addr w byte0 [byte1. . . byteN] r len   -- write/read\n" +
        "mappedi2c bus i2c_addr r len                              -- read\n" +
        "mappedi2c bus i2c_addr w byte0 [byte1 . . . byteN]        -- write\n" +
        "### 32-bit and 64-bit memory read/write ###\n" +
        "fpgautil mem r32 <addr>\n" +
        "fpgautil mem w32 <addr> <data>\n" +
        "fpgautil mem r64 <addr>\n" +
        "fpgautil mem w64 <addr> <data>\n" 

                               

func main() {
    var rc C.int = 0
    var data64 C.uint64_t = 0
    var acc_type C.uint32_t = 1
    var data8 byte = 0
    var data16 uint16 = 0

    //var data32 uint32 = 0x12345678
    //var data8_p *uint8
    //data8_p = (* uint8)(unsafe.Pointer(&data32))
    //if *data8_p == 0x12 {
    //    fmt.Printf(" BIG ENGDIAN\n")
    //} else {
    //    fmt.Printf(" LITTLE ENDIAN\n")
    //}

    

    argc := len(os.Args[0:])
    //fmt.Printf("Arg length is %d\n", argc)

    //for i, a := range os.Args[1:] {
    //    fmt.Printf("Arg %d is %s\n", i+1, a) 
    //}

    if argc < 3 {
        fmt.Printf(" %s \n", errhelp)
        os.Exit(-1);
    }
    arg2, err := strconv.ParseUint(os.Args[2], 0, 32);
    if err != nil {
        fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
    }

    if os.Args[1][0] == 'r' || os.Args[1][0] == 'r' {
        var err1 error
        err1 = elba_fpga_rd(byte(arg2), &data8)
        if err1 == nil {
            fmt.Printf("FPGA RD [0x%.02x] = 0x%.02x\n", arg2, data8)
        } else {
            fmt.Printf("FPGA RD FAILED\n")
        }
        

    } else if os.Args[1][0] == 'w' || os.Args[1][0] == 'W' {
        if argc < 3 {
            fmt.Printf(" ERROR fpgautil w:  Not enough args\n");  os.Exit(-1)
        }
        data, err := strconv.ParseUint(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
        }
        //Write Function
        err1 := elba_fpga_wr(byte(arg2), byte(data))
        if err1 == nil {
            fmt.Printf("FPGA WR [0x%.02x] = 0x%.02x\n", arg2, byte(data))
        } else {
            fmt.Printf("FPGA WR FAILED\n")
        }
    } else if os.Args[1] == "apbr" {
        var data uint32 = 0
        var err1 error
        err1 = spi_read_fpga_apb(uint16(arg2) + (S2I_BUS_STRIDE * uint16(I2C_BUS)), &data)
        if err1 == nil {
            fmt.Printf("APB RD [0x%.04x] = 0x%.08x\n", arg2, data)
        } else {
            fmt.Printf("APB RD FAILED\n")
        }
        

    } else if os.Args[1] == "apbw" {
        if argc < 3 {
            fmt.Printf(" ERROR apbw:  Not enough args\n");  os.Exit(-1)
        }
        data, err := strconv.ParseUint(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
        }
        //Write Function
        err1 := spi_write_fpga_apb(uint16(arg2) + (S2I_BUS_STRIDE * uint16(I2C_BUS)), uint32(arg2)) 
        if err1 == nil {
            fmt.Printf("APB WR [0x%.04x] = 0x%.08x\n", arg2, data)
        } else {
            fmt.Printf("APB WR FAILED\n")
        }
    } else if os.Args[1] == "apbdump" {
        if argc < 3 {
            fmt.Printf(" ERROR apbdump <bus>:  Not enough args\n");  os.Exit(-1)
        }
        if(uint8(arg2)>I2C_BUS){
            fmt.Printf(" ERROR: Bus entered is to large.  Max BUS Number is %d\n", I2C_BUS); os.Exit(-1)
        }
        fpga_dump_abp(uint8(arg2))
    } else if os.Args[1] == "ee" {
        if argc < 4 {
            fmt.Printf(" %s \n", errhelp)
            os.Exit(-1);
        }
        addr, err := strconv.ParseUint(os.Args[3], 0, 32);
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
        }
        if os.Args[2][0] == 'r' || os.Args[2][0] == 'r' {
            var err1 error
            err1 = s2i_transaction_eeprom (uint16(I2C_BUS), FRU_SLAVE_ADDRESS, uint16(addr), &data16, false)
            if err1 == nil {
                fmt.Printf("StoI EE RD [0x%.02x] = 0x%.04x\n", addr, data16)
            } else {
                fmt.Printf("StoI EE RD FAILED\n")
            }
        } else if os.Args[2][0] == 'w' || os.Args[2][0] == 'W' {
            if argc < 5 {
                fmt.Printf(" ERROR fpgautil w:  Not enough args\n");  os.Exit(-1)
            }
            data, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            //Write Function
            data16 = uint16(data & 0xFFFF)
            err1 := s2i_transaction_eeprom (uint16(I2C_BUS), FRU_SLAVE_ADDRESS, uint16(addr), &data16, true)
            if err1 == nil {
                fmt.Printf("StoI EE WR [0x%.02x] = 0x%.04x\n", addr, data16)
            } else {
                fmt.Printf("StoI EE WR FAILED\n")
            }
        } else {
            fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
            fmt.Printf(" %s \n", errhelp)
            os.Exit(-1);
        }
    } else if os.Args[1] == "mappedi2c" {
        "mappedi2c bus i2c_addr w byte0 [byte1. . . byteN] r len   -- write/read\n" +
        "mappedi2c bus i2c_addr r len                              -- read\n" +
        "mappedi2c bus i2c_addr w byte0 [byte1 . . . byteN]        -- write\n" +
        //arg2 = bus

    } else if os.Args[1] == "mem" {
        //"fpgautil mem r32 <addr>\n" +
        //"fpgautil mem w32 <addr> <data>\n" +
        //Check the arg count
        if (os.Args[2] == "r32" || os.Args[2] == "r64") && argc < 4  {
            if argc < 4 {
                fmt.Printf(" ERROR fpgautil mem r32/r64:  Not enough args\n"); os.Exit(-1)
            }
        }
        if (os.Args[2] == "w32" || os.Args[2] == "w64") && argc < 5  {
            if argc < 4 {
                fmt.Printf(" ERROR fpgautil mem w32/w64:  Not enough args\n"); os.Exit(-1)
            }
        }

        if os.Args[2] == "r32" {
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            rc = C.cpu_mem_read(C.uint32_t(addr), &data64, acc_type)
            if rc != 0 {
                os.Exit(-1);
            }
            fmt.Printf("RD [0x%.08x] = 0x%.08x\n", addr, (data64 & 0xFFFFFFFF))
        } else if os.Args[2] == "w32" {
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            data, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            rc = C.cpu_mem_write(C.uint32_t(addr), C.uint64_t(data), acc_type)
            if rc != 0 {
                os.Exit(-1);
            }
            fmt.Printf("WR [0x%.08x] = 0x%.08x\n", addr, data)
        }
    } else {
        fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelp)
        os.Exit(-1);
    }

    return
}

    

//export c_elba_fpga_wr
func c_elba_fpga_wr(addr byte, data byte) int {
    ReadData := make([]byte, 1)

    dev, err := spi.Open(&spi.Devfs{
        Dev:      "/dev/spidev0.0",
        Mode:     spi.Mode0,
        MaxSpeed: 12000000,
    })
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return -1
    }
    defer dev.Close()

    //err = dev.Tx([]byte{0x02, addr, data, 0x00}, ReadData)
    err = dev.SPI_WR([]byte{0x02, addr, data, 0x00}, ReadData)
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return -1
    }

    return 0
}

func elba_fpga_wr(addr byte, data byte) error {
    ReadData := make([]byte, 1)

    dev, err := spi.Open(&spi.Devfs{
        Dev:      "/dev/spidev0.0",
        Mode:     spi.Mode0,
        MaxSpeed: 12000000,
    })
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return(err)
    }
    defer dev.Close()

    //err = dev.Tx([]byte{0x02, addr, data, 0x00}, ReadData)
    err = dev.SPI_WR([]byte{0x02, addr, data, 0x00}, ReadData)
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
    }

    return(err)
}



//export c_elba_fpga_rd
func c_elba_fpga_rd(addr byte, data *byte) int {
    ReadData := make([]byte, 1)

    dev, err := spi.Open(&spi.Devfs{
        Dev:      "/dev/spidev0.0",
        Mode:     spi.Mode0,
        MaxSpeed: 12000000,
    })
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return -1
    }
    defer dev.Close()

    err = dev.SPI_WR_RD([]byte{0x0b, addr, *data,}, ReadData)
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return -1
    }
    *data = ReadData[0]
    return 0
}

func elba_fpga_rd(addr byte, data *byte) error {
    ReadData := make([]byte, 1)

    dev, err := spi.Open(&spi.Devfs{
        Dev:      "/dev/spidev0.0",
        Mode:     spi.Mode0,
        MaxSpeed: 12000000,
    })
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return err
    }
    defer dev.Close()

    err = dev.SPI_WR_RD([]byte{0x0b, addr, *data,}, ReadData)
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
    }
    *data = ReadData[0]
    return err
}







//
//  cmd:8, addr:16, data:32  .. followed by 1 byte dummy read?
//
func spi_write_fpga_apb(addr uint16, data uint32) error {
    ReadData := make([]byte, 1)

    dev, err := spi.Open(&spi.Devfs{
        Dev:      "/dev/spidev0.1",
        Mode:     spi.Mode0,
        MaxSpeed: 12000000,
    })
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return(err)
    }
    defer dev.Close()

    err = dev.SPI_WR_RD([]byte{0x02, byte(addr), byte(addr>>8), byte(data), byte(data>>8), byte(data>>16), byte(data>>24)}, ReadData)
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
    }
    return(err)
}



//
//  WR cmd:8, addr:16, dummy:8    RD data:32
//
func spi_read_fpga_apb(addr uint16, data *uint32) error {
    ReadData := make([]byte, 4)

    dev, err := spi.Open(&spi.Devfs{
        Dev:      "/dev/spidev0.1",
        Mode:     spi.Mode0,
        MaxSpeed: 12000000,
    })
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        return(err)
    }
    defer dev.Close()

    err = dev.SPI_WR_RD([]byte{0x0b, byte(addr), byte(addr>>8), 0x00}, ReadData)
    if err != nil {
        fmt.Printf(" Err !=nil:   ERR = '%s'\n", err)  // err is a pointer type to a string
        *data = 0xDEADBEEF
        return(err)
    }

    *data =   uint32(ReadData[0])
    *data |= (uint32(ReadData[1])<<8)
    *data |= (uint32(ReadData[2])<<16)
    *data |= (uint32(ReadData[3])<<24)

    return(err)
}



func fpga_dump_abp(bus uint8) error {

    var data32 uint32
    var err error = nil

    for _, entry := range(APB_REG_s) {
        err = spi_read_fpga_apb( uint16(entry.Address) + (S2I_BUS_STRIDE * uint16(bus)), &data32)
        if err != nil {
            return err
        }
        fmt.Printf("DUMPING APB REGISTERS ON BUS-%d\n", bus)
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }

    return err
}


/* 
Hmm, probably a better way to do this in GoLang 
*/ 
func s2i_poll_apb_reg(bus uint8, reg uint8, bit uint32) error {
    var rc int = -2
    var err error = nil
    var data32 uint32 = 0;
    go func() {   
        for ((data32 & bit) != bit) {
            err = spi_read_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(reg),  &data32)
            if err != nil {
                rc = -1
                return
            }
        }
        rc = 0
        return
    } ()
    <-time.After(500 * time.Millisecond)
    if rc == 0 {
        return nil
    } else if rc == -1 {
        fmt.Printf(" ERROR s2i_poll_apb_reg on BUS-%d failed reading apb!!\n", bus)
        return err
    } else {
        errStr := fmt.Sprintf("POLL TIMED OUT ON BUS-%d:  REG 0x%x = 0x%x\n", bus, reg, data32)
        fmt.Printf(errStr)
        return(errors.New(errStr))
        
    }
}


func s2i_transaction_eeprom (bus uint16, i2caddr uint8, ee_addr uint16, data *uint16, WR bool) error {
    //uint16_t read_value = 0;
    var err error = nil
    var data32 uint32 = 0;
    //var timeout uint32 = 0;

    fmt.Printf(" DEV=%d   I2CADDR=0x%x   REG=0x%x   WR=%v\n", bus, i2caddr, ee_addr, WR)
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_ENABLE), 0)
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_SS_SCL_HCNT), 0x212)
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_SS_SCL_LCNT), 0x1D6)
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_FS_SPKLEN), 0x1)
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_CON), 0x63)  //master, standard speed, restart en, slave disabled
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_TAR), uint32(i2caddr))

    spi_read_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_TAR), &data32)
    fmt.Printf(" TAR REG=0x%x\n", data32)

    //Write IC_INTR_MASK to enable all interrupts
    //Write IC_RX_RL to set Rx FIFO threshold level
    //Write IC_TX_TL to set Tx FIFO threshold level
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_ENABLE), 1)
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_CLR_INTR), 1)

    /* Check transmit FIFO is empty */
    err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x2)
    if err != nil { return err }

   
    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), uint32((ee_addr>>8)&0xFF))
    /* Check transmit FIFO is empty */
    err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x2)
    if err != nil { return err }

    spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), uint32(ee_addr & 0xFF))
    /* Check transmit FIFO is empty */
    err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x2)
    if err != nil { return err }

    if WR == true {  //WRITE

        spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), uint32(*data & 0xFF))

        /* Check transmit FIFO is empty */
        err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x2)
        if err != nil { return err }

        spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), uint32((*data>>8) & 0xFF) | 0x200)

    } else {  //READ

        spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), 0x500)
        /* Check transmit FIFO is empty */
        err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x2)
        if err != nil { return err }

        spi_write_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), 0x300)

        /* Check Rx FIFO is not empty */
        err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x8)
        if err != nil { return err }

        spi_read_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), &data32)
        *data = uint16(data32 & 0xFF)

        /* Check Rx FIFO is not empty */
        err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x8)
        if err != nil { return err }

        spi_read_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_DATA_CMD), &data32)
        *data |= uint16((data32 & 0xFF)<<8)
    }


    /* Check Rx FIFO is not empty */
    err = s2i_poll_apb_reg(uint8(bus), IC_STATUS, 0x1)
    if err != nil { return err }
    
    spi_read_fpga_apb( (S2I_BUS_STRIDE * uint16(bus)) + uint16(IC_RAW_INTR_STAT),  &data32)
    if (data32 & 0x40) == 0x40 {
       fmt.Printf("s2i_transaction_eeprom:ERROR: No target response!\n");
       return(errors.New(" ERROR"))
   }

   return err   
   
/*      
   if (WR == 1) {
      elb_i2c_writereg( device, IC_DATA_CMD, data&0xFF);
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x2) == 0x2)) {
      }
      elb_i2c_writereg( device, IC_DATA_CMD, ((data>>8)&0xFF)|0x200);
   } else {
      elb_i2c_writereg( device, IC_DATA_CMD, 0x500);
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x2) == 0x2)) {
      }
      elb_i2c_writereg( device, IC_DATA_CMD, 0x300);
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x8) == 0x8)) {
      }
      read_value = elb_i2c_readreg( device, IC_DATA_CMD) & 0xFF;
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x8) == 0x8)) {
      }
      read_value = read_value | (((elb_i2c_readreg( device, IC_DATA_CMD)) & 0xFF)<<8);
   }

   while (elb_i2c_readreg( device, IC_STATUS) & 0x1) {
   }
   if ((elb_i2c_readreg( device, IC_RAW_INTR_STAT) & 0x40) == 0x40) {
       printf("s2i_transaction_eeprom:ERROR: No target response!\n");
   }

   if (WR == 1) {
       return 0;
   } else {
       printf("s2i_transaction_eeprom: s2i_transaction_eeprom, dev=%d, target=0x%x, read byte_num=0x%x, data=0x%x\n",device, target, byte_num, read_value);
       return read_value;
   }
   */   
}


/* 
 
//
//  cmd:8, addr:16, data:32
//
int
spi2apb_write(uint32_t addr, uint32_t data)
{
    int fd;
    struct spi_ioc_transfer msg[2];
    uint8_t txbuf[7];
    uint8_t rxbuf[1];

    //assert(spi2apb_fd >= 0);

    txbuf[0] = 0x02;  // write
    txbuf[1] = addr >> 0;
    txbuf[2] = addr >> 8;
    txbuf[3] = data >> 0;
    txbuf[4] = data >> 8;
    txbuf[5] = data >> 16;
    txbuf[6] = data >> 24;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 7;
    msg[1].rx_buf = (intptr_t)rxbuf;
    msg[1].len = 1;

    fd = open(spidev1_path, O_RDWR, 0);
    if (fd < 0) {
        perror(spidev1_path);
        return -1;
    }
    if (ioctl(fd, SPI_IOC_MESSAGE(2), msg) < 0) {
        perror("SPI_IOC_MESSAGE");
        exit(1);
    }
    close(fd);
    return 0;
}

//
//  cmd:8, addr:16, dummy:8, data:32
//
uint32_t
spi2apb_read(uint32_t addr)
{
    struct spi_ioc_transfer msg[2];
    uint8_t txbuf[4];
    uint8_t rxbuf[4];
    int fd;

    //assert(spi2apb_fd >= 0);

    txbuf[0] = 0x0b;  // read
    txbuf[1] = addr >> 0;
    txbuf[2] = addr >> 8;
    txbuf[3] = 0;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 4;
    msg[1].rx_buf = (intptr_t)rxbuf;
    msg[1].len = 4;

    fd = open(spidev1_path, O_RDWR, 0);
    if (fd < 0) {
        perror(spidev1_path);
        return -1;
    }
    if (ioctl(fd, SPI_IOC_MESSAGE(2), msg) < 0) {
        perror("SPI_IOC_MESSAGE");
        exit(1);
    }
    close(fd);
    return ((uint32_t)rxbuf[3] << 24) | ((uint32_t)rxbuf[2] << 16) |
           ((uint32_t)rxbuf[1] << 8) | ((uint32_t)rxbuf[0] << 0);
} 

 
void elb_i2c_writereg(unsigned int dev, unsigned int reg, unsigned int val) {

  (void) spi2apb_write((reg+(dev*S2I_BUS_STRIDE)), val);
}

uint32_t elb_i2c_readreg (unsigned int dev, unsigned int reg) {
  return spi2apb_read((reg+(dev*S2I_BUS_STRIDE)));
} 
 
uint16_t s2i_transaction_eeprom (unsigned int device, uint8_t target, uint16_t byte_num, bool WR, uint16_t data) {
   uint16_t read_value = 0;
   elb_i2c_writereg( device, IC_ENABLE, 0);
   elb_i2c_writereg( device, IC_SS_SCL_HCNT, 0x212);
   elb_i2c_writereg( device, IC_SS_SCL_LCNT, 0x1D6);
   elb_i2c_writereg( device, IC_FS_SPKLEN, 0x1);
   elb_i2c_writereg( device, IC_CON, 0x63);  //master, standard speed, restart en, slave disabled
   elb_i2c_writereg( device, IC_TAR, target);
 
   //Write IC_INTR_MASK to enable all interrupts
   //Write IC_RX_RL to set Rx FIFO threshold level
   //Write IC_TX_TL to set Tx FIFO threshold level
 
   elb_i2c_writereg( device, IC_ENABLE, 1);
   elb_i2c_writereg( device, IC_CLR_INTR, 1);

   while(!((elb_i2c_readreg( device, IC_STATUS) & 0x2) == 0x2)) {
   }

   elb_i2c_writereg( device, IC_DATA_CMD, (byte_num>>8)&0xFF);
   while(!((elb_i2c_readreg( device, IC_STATUS) & 0x2) == 0x2)) {
   }

   elb_i2c_writereg( device, IC_DATA_CMD, byte_num & 0xFF);
   while(!((elb_i2c_readreg( device, IC_STATUS) & 0x2) == 0x2)) {
   }

   if (WR == 1) {
      elb_i2c_writereg( device, IC_DATA_CMD, data&0xFF);
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x2) == 0x2)) {
      }
      elb_i2c_writereg( device, IC_DATA_CMD, ((data>>8)&0xFF)|0x200);
   } else {
      elb_i2c_writereg( device, IC_DATA_CMD, 0x500);
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x2) == 0x2)) {
      }
      elb_i2c_writereg( device, IC_DATA_CMD, 0x300);
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x8) == 0x8)) {
      }
      read_value = elb_i2c_readreg( device, IC_DATA_CMD) & 0xFF;
      while(!((elb_i2c_readreg( device, IC_STATUS) & 0x8) == 0x8)) {
      }
      read_value = read_value | (((elb_i2c_readreg( device, IC_DATA_CMD)) & 0xFF)<<8);
   }

   while (elb_i2c_readreg( device, IC_STATUS) & 0x1) {
   }
   if ((elb_i2c_readreg( device, IC_RAW_INTR_STAT) & 0x40) == 0x40) {
       printf("s2i_transaction_eeprom:ERROR: No target response!\n");
   }

   if (WR == 1) {
       return 0;
   } else {
       printf("s2i_transaction_eeprom: s2i_transaction_eeprom, dev=%d, target=0x%x, read byte_num=0x%x, data=0x%x\n",device, target, byte_num, read_value);
       return read_value;
   }
}
*/





