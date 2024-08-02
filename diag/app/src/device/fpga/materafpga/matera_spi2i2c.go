// Support for Matera FPGA SPI BUS
package materafpga

import (
    //"common/cli"
    //"common/errType"
    //"device/ioexpander/mcp23008"
    //"hardware/hwinfo"
    //"hardware/i2cinfo"
    "fmt"
    //"protocol/smbusNew"
    //"time"
)


const CMD_WR_REG    uint8 = 0x00
const CMD_RD_REG    uint8 = 0x10
const CMD_INT_CHK   uint8 = 0x20
const CMD_I2C_WR    uint8 = 0x30
const CMD_I2C_RD    uint8 = 0x40
const CMD_RD_FIFO   uint8 = 0x50

const I2C_MASTER0   uint8 = 0x00  //BIT[3:1]  0
const I2C_MASTER1   uint8 = 0x02  //BIT[3:1]  1
const I2C_MAX_BYTES uint8 = 0x08  //Max 8 bytes write or read

const CMD_MASK      uint8 = 0xF0  //CMD MASK
const RADR_MASK     uint8 = 0x0F  //READ ADDRESS MASK
const I2CM_MASK     uint8 = 0x0E  //I2C

const SPI_FIFO_STS_REG      uint8 = 0x01   //FIFO STATUS REGISTER
const SPI_REVISION_REG      uint8 = 0x03   //REVISION ID REGISTER
const SPI_I2C0_CONFIG_REG   uint8 = 0x04   //I2C0 CONFIGURATION REGISTER
const SPI_I2C0_MODE_REG     uint8 = 0x05   //I2C0 MODE REGISTER
const SPI_I2C0_CMD_STS_REG  uint8 = 0x06   //I2C0 COMMAND STATUS REGISTER
const SPI_I2C1_CONFIG_REG   uint8 = 0x0A   //I2C1 CONFIGURATION REGISTER
const SPI_I2C1_MODE_REG     uint8 = 0x0B   //I2C1 MODE REGISTER
const SPI_I2C1_CMD_STS_REG  uint8 = 0x0C   //I2C1 COMMAND STATUS REGISTER

type BRIDGE_REGISTERS struct {
    Name     string
    Address  uint8
}

var SPI2I2C_BRIDGE_REGISTERS = []BRIDGE_REGISTERS {
    BRIDGE_REGISTERS{"FIFO STATUS REGISTER         ",  SPI_FIFO_STS_REG},
    BRIDGE_REGISTERS{"REVISION ID REGISTER         ",  SPI_REVISION_REG},
    BRIDGE_REGISTERS{"I2C0 CONFIGURATION REGISTER  ",  SPI_I2C0_CONFIG_REG},
    BRIDGE_REGISTERS{"I2C0 MODE REGISTER           ",  SPI_I2C0_MODE_REG},
    BRIDGE_REGISTERS{"I2C0 COMMAND STATUS REGISTER ",  SPI_I2C0_CMD_STS_REG},
    BRIDGE_REGISTERS{"I2C1 CONFIGURATION REGISTER  ",  SPI_I2C1_CONFIG_REG},
    BRIDGE_REGISTERS{"I2C1 MODE REGISTER           ",  SPI_I2C1_MODE_REG},
    BRIDGE_REGISTERS{"2C1 COMMAND STATUS REGISTER  ",  SPI_I2C1_CMD_STS_REG}, }


func BridgeDumpReg(spiNumber uint32) (err error) {
    var data8 uint8 = 0

    fmt.Printf("SPI-2-I2C BRIDGE REGISTER DUMP---\n")
    for _, entry := range(SPI2I2C_BRIDGE_REGISTERS) {

        data8, err = BridgeReadReg(spiNumber, entry.Address) 
        if err != nil {
            return
        }
        fmt.Printf("%-20s [%.02x] = %.02x\n", entry.Name, entry.Address, data8)
        if (entry.Address == SPI_I2C0_CONFIG_REG) || (entry.Address == SPI_I2C1_CONFIG_REG) {
            fmt.Printf("  --> RESET      = %d\n", ((data8 & 0x80)>>7))
            fmt.Printf("  --> RXFIFO_CLR = %d\n", ((data8 & 0x40)>>6))
            fmt.Printf("  --> TXFIFO_CLR = %d\n", ((data8 & 0x20)>>5))
            fmt.Printf("  --> ABORT      = %d\n", ((data8 & 0x10)>>4))
            fmt.Printf("  --> RESERVED   = %d\n", ((data8 & 0x08)>>3))
            fmt.Printf("  --> RESERVED   = %d\n", ((data8 & 0x04)>>2))
            fmt.Printf("  --> INT_CLR    = %d\n", ((data8 & 0x02)>>1))
            fmt.Printf("  --> START      = %d\n", ((data8 & 0x01)>>0))
        }
        if (entry.Address == SPI_I2C0_MODE_REG) || (entry.Address == SPI_I2C1_MODE_REG) {
            fmt.Printf("  --> BPS[1]     = %d\n", ((data8 & 0x80)>>7))
            fmt.Printf("  --> BPS[0]     = %d\n", ((data8 & 0x40)>>6))
            fmt.Printf("  --> TX_IE      = %d\n", ((data8 & 0x20)>>5))
            fmt.Printf("  --> ACK_POL    = %d\n", ((data8 & 0x10)>>4))
            fmt.Printf("  --> RX_IE      = %d\n", ((data8 & 0x08)>>3))
            fmt.Printf("  --> RESERVED   = %d\n", ((data8 & 0x04)>>2))
            fmt.Printf("  --> RESERVED   = %d\n", ((data8 & 0x02)>>1))
            fmt.Printf("  --> RESERVED   = %d\n", ((data8 & 0x01)>>0))
        }
        if (entry.Address == SPI_I2C0_CMD_STS_REG) || (entry.Address == SPI_I2C1_CMD_STS_REG) {
            fmt.Printf("  --> I2C_BUSY   = %d\n", ((data8 & 0x80)>>7))
            fmt.Printf("  --> NO_ANS     = %d\n", ((data8 & 0x40)>>6))
            fmt.Printf("  --> NO_ACK     = %d\n", ((data8 & 0x20)>>5))
            fmt.Printf("  --> TX_ERR     = %d\n", ((data8 & 0x10)>>4))
            fmt.Printf("  --> RX_ERR     = %d\n", ((data8 & 0x08)>>3))
            fmt.Printf("  --> ABORT_ACK  = %d\n", ((data8 & 0x04)>>2))
            fmt.Printf("  --> TS(FIFOCMP)= %d\n", ((data8 & 0x02)>>1))
            fmt.Printf("  --> RESERVED   = %d\n", ((data8 & 0x01)>>0))
        }
    }
    fmt.Printf("\n")

    return
} 

func BridgeReadReg(spiNumber uint32, reg uint8) (data8 uint8, err error) {
    rd_data := []byte{}
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, (CMD_RD_REG | (reg & RADR_MASK)) )

    //for i:=0; i<len(spi_cmd); i++ {
    //    fmt.Printf("%.02x ", spi_cmd[i])
    //}
    //fmt.Printf("\n")
    rd_data , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 1) 
    if err != nil {
        return
    }

    data8 = rd_data[0]

    return
}


func BridgeWriteReg(spiNumber uint32, reg uint8, data8 uint8) (err error) {
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, (CMD_WR_REG | (reg & RADR_MASK)) )
    spi_cmd = append(spi_cmd, data8)
    //fmt.Printf(" BRIDGE WR REG\n")
    //for i:=0; i<len(spi_cmd); i++ {
    //    fmt.Printf("%.02x ", spi_cmd[i])
    //}
    //fmt.Printf("\n")
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 0) 
    if err != nil {
        return
    }

    return
}


func BridgeInterruptCheck(spiNumber uint32) (data8 uint8, err error) {
    rd_data := []byte{}
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, CMD_INT_CHK)

    rd_data , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 1) 
    if err != nil {
        return
    }

    data8 = rd_data[0]

    return
}


/**********************************************************************************
* 0011  x000  00000010 XXXXXXX0 byte1 byte2 ... byteN
* SPI   I2C   NUMB OF  I2C ADD
* CMD   MSTR  BYTES    + W
*
***********************************************************************************/
func BridgeI2Cwrite(spiNumber uint32, i2cChnl uint8, i2cAddr uint8, NumbBytes uint8, data8 []uint8) (err error) {
    spi_cmd := []byte{}

    if i2cChnl == 0 {
        spi_cmd = append(spi_cmd, (CMD_I2C_WR | I2C_MASTER0) )
    } else {
        spi_cmd = append(spi_cmd, (CMD_I2C_WR | I2C_MASTER1) )
    }

    if len(data8) < int(NumbBytes) {
        err = fmt.Errorf("ERROR: BridgeI2Cwrite: Arg error.  Number of bytes to write - %d is larger than number of bytes passed -%d\n", NumbBytes, len(data8));
        fmt.Printf("%v", err)
        return
    }

    //Add Number of Bytes
    spi_cmd = append(spi_cmd, NumbBytes)

    //Add I2C ADDR
    spi_cmd = append(spi_cmd, (i2cAddr<<1) )


    //Add bytes to write
    for i:=0; i<int(NumbBytes); i++ {
        spi_cmd = append(spi_cmd, data8[i])
    }

    fmt.Printf(" BridgeI2Cwrite\n")
    for i:=0; i<len(spi_cmd); i++ {
        fmt.Printf("%.02x ", spi_cmd[i])
    }
    fmt.Printf("\n")

    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 0) 
    if err != nil {
        return
    }

    return
}


/**********************************************************************************
* 0011  x000  00000010 XXXXXXX1 byte1 byte2 ... byteN
* SPI   I2C   NUMB OF  I2C ADD
* CMD   MSTR  BYTES    + R
*
***********************************************************************************/
func BridgeI2Cread(spiNumber uint32, i2cChnl uint8, i2cAddr uint8, NumbBytes uint8) (err error) {
    spi_cmd := []byte{}

    if i2cChnl == 0 {
        spi_cmd = append(spi_cmd, (CMD_I2C_RD | I2C_MASTER0) )
    } else {
        spi_cmd = append(spi_cmd, (CMD_I2C_RD | I2C_MASTER1) )
    }

    if NumbBytes > I2C_MAX_BYTES {
        err = fmt.Errorf("ERROR: BridgeI2Cread: Arg error.  Number of bytes to read - %d is larger than max number of bytes possible -%d\n", NumbBytes, I2C_MAX_BYTES);
        fmt.Printf("%v", err)
        return
    }

    //Add Number of Bytes to read
    spi_cmd = append(spi_cmd, NumbBytes)

    //Add I2C ADDR + READ BIT
    spi_cmd = append(spi_cmd,  ((i2cAddr <<1) | 0x01) )

    fmt.Printf(" BridgeI2Cread\n")
    for i:=0; i<len(spi_cmd); i++ {
        fmt.Printf("%.02x ", spi_cmd[i])
    }
    fmt.Printf("\n")

    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, uint32(NumbBytes)) 
    if err != nil {
        return
    }

    return
}


/**********************************************************************************
* 
* 
***********************************************************************************/
func BridgeReadFIFO(spiNumber uint32, reg uint8) (data8 uint8, err error) {
    rd_data := []byte{}
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, CMD_RD_FIFO)

    fmt.Println(" SPI2I2C BridgeReadFIFO ->", spi_cmd)
    rd_data , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 1) 
    if err != nil {
        return
    }

    data8 = rd_data[0]

    return
}
