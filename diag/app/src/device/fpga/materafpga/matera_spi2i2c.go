// Support for Matera FPGA SPI BUS
package materafpga

import (
    //"common/cli"
    "fmt"
    "time"
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
    BRIDGE_REGISTERS{"I2C1 COMMAND STATUS REGISTER  ",  SPI_I2C1_CMD_STS_REG}, }


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
            fmt.Printf("  --> RESET       = %d\n", ((data8 & 0x80)>>7))
            fmt.Printf("  --> RXFIFO_CLR  = %d\n", ((data8 & 0x40)>>6))
            fmt.Printf("  --> TXFIFO_CLR  = %d\n", ((data8 & 0x20)>>5))
            fmt.Printf("  --> ABORT       = %d\n", ((data8 & 0x10)>>4))
            fmt.Printf("  --> RXRDFIFO_CLR= %d\n", ((data8 & 0x08)>>3))
            fmt.Printf("  --> RXRDFIFO_CLR= %d\n", ((data8 & 0x04)>>2))
            fmt.Printf("  --> INT_CLR     = %d\n", ((data8 & 0x02)>>1))
            fmt.Printf("  --> START       = %d\n", ((data8 & 0x01)>>0))
        }
        if (entry.Address == SPI_I2C0_MODE_REG) || (entry.Address == SPI_I2C1_MODE_REG) {
            fmt.Printf("  --> BPS[1]      = %d\n", ((data8 & 0x80)>>7))
            fmt.Printf("  --> BPS[0]      = %d\n", ((data8 & 0x40)>>6))
            fmt.Printf("  --> TX_IE       = %d\n", ((data8 & 0x20)>>5))
            fmt.Printf("  --> ACK_POL     = %d\n", ((data8 & 0x10)>>4))
            fmt.Printf("  --> RX_IE       = %d\n", ((data8 & 0x08)>>3))
            fmt.Printf("  --> RESERVED    = %d\n", ((data8 & 0x04)>>2))
            fmt.Printf("  --> RESERVED    = %d\n", ((data8 & 0x02)>>1))
            fmt.Printf("  --> RESERVED    = %d\n", ((data8 & 0x01)>>0))
        }
        if (entry.Address == SPI_I2C0_CMD_STS_REG) || (entry.Address == SPI_I2C1_CMD_STS_REG) {
            fmt.Printf("  --> I2C_BUSY    = %d\n", ((data8 & 0x80)>>7))
            fmt.Printf("  --> NO_ANS      = %d\n", ((data8 & 0x40)>>6))
            fmt.Printf("  --> NO_ACK      = %d\n", ((data8 & 0x20)>>5))
            fmt.Printf("  --> TX_ERR      = %d\n", ((data8 & 0x10)>>4))
            fmt.Printf("  --> RX_ERR      = %d\n", ((data8 & 0x08)>>3))
            fmt.Printf("  --> ABORT_ACK   = %d\n", ((data8 & 0x04)>>2))
            fmt.Printf("  --> TS(FIFOCMP) = %d\n", ((data8 & 0x02)>>1))
            fmt.Printf("  --> RESERVED    = %d\n", ((data8 & 0x01)>>0))
        }
    }
    fmt.Printf("\n")

    return
} 


/*************************************************************
* 
* Read a single spi-2-i2c controller register
* 
*************************************************************/ 
func BridgeReadReg(spiNumber uint32, reg uint8) (data8 uint8, err error) {
    rd_data := []byte{}
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, (CMD_RD_REG | (reg & RADR_MASK)) )
    rd_data , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 1) 
    if err != nil {
        return
    }

    data8 = rd_data[0]

    return
}


/*************************************************************
* 
* Write a single spi-2-i2c controller register
* 
*************************************************************/ 
func BridgeWriteReg(spiNumber uint32, reg uint8, data8 uint8) (err error) {
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, (CMD_WR_REG | (reg & RADR_MASK)) )
    spi_cmd = append(spi_cmd, data8)
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
* 0011  x000  00000010 0XXXXXXX byte1 byte2 ... byteN
* SPI   I2C   NUMB OF  I2C ADD
* CMD   MSTR  BYTES   
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
    spi_cmd = append(spi_cmd, i2cAddr)


    //Add bytes to write
    for i:=0; i<int(NumbBytes); i++ {
        spi_cmd = append(spi_cmd, data8[i])
    }

    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 0) 
    if err != nil {
        return
    }

    return
}


/**********************************************************************************
* 0011  x000  00000010 0XXXXXXX byte1 byte2 ... byteN
* SPI   I2C   NUMB OF  I2C ADD
* CMD   MSTR  BYTES    
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

    //Add I2C ADDR
    spi_cmd = append(spi_cmd, i2cAddr)

    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, 0) 
    if err != nil {
        return
    }

    return
}


/**********************************************************************************
*  
* Read data from the controller FIFO after running an i2c read command 
*  
***********************************************************************************/
func BridgeReadFIFO(spiNumber uint32, chnl uint8, numBytes uint8) (rd_data []uint8, err error) {
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, (CMD_RD_FIFO | uint8(chnl << 1)))

    rd_data , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2I2C, spi_cmd, uint32(numBytes+1)) 
    if err != nil {
        return
    }

    rd_data = rd_data[1:]

    return
}

/**********************************************************************************
* 
* Reset a single controller
* 
***********************************************************************************/
func BridgeResetI2C(spiNumber uint32, bus uint8) (err error) {
    var reg uint8
    if bus == 0 { reg = SPI_I2C0_CONFIG_REG 
    } else {      reg = SPI_I2C1_CONFIG_REG }
    err = BridgeWriteReg(spiNumber, reg, 0x92)
    if err != nil {
        return
    }
    err = BridgeWriteReg(spiNumber, reg, 0x00)
    if err != nil {
        return
    }
    fmt.Printf(" Reset of controller-%d complete\n", bus);
    return
}


func BridgeFifoClear(spiNumber uint32, bus uint8) (err error) {
    var reg uint8
    if bus == 0 { reg = SPI_I2C0_CONFIG_REG 
    } else {      reg = SPI_I2C1_CONFIG_REG }

    err = BridgeWriteReg(spiNumber, reg, 0x6C)
    if err != nil {
        return
    }
    err = BridgeWriteReg(spiNumber, reg, 0x00)
    if err != nil {
        return
    }
    return
}


func BridgeIRQClear(spiNumber uint32, bus uint8) (err error) {
    var data8, reg uint8
    if bus == 0 { reg = SPI_I2C0_CONFIG_REG 
    } else {      reg = SPI_I2C1_CONFIG_REG }

    err = BridgeWriteReg(spiNumber, reg, 0x02)
    if err != nil {
        return
    }
    
    data8, err = BridgeReadReg(spiNumber, reg)
    if err != nil {
        return
    }
    if data8 != 0x02 {
        err = fmt.Errorf("ERROR: BridgeIRQClear Expect I2C BUS-%d CONFIG TO BE 0x02.. Config=%x\n", bus, data8);
        fmt.Printf("%v", err)
        return
    } 

    err = BridgeWriteReg(spiNumber, reg, 0x00)
    if err != nil {
        return
    }
    data8, err = BridgeReadReg(spiNumber, reg) 
    if data8 != 0x00 {
        err = fmt.Errorf("ERROR: BridgeIRQClear Expect I2C BUS-%d CONFIG TO BE ZERO.. Config=%x\n", bus, data8);
        fmt.Printf("%v", err)
        return
    } 

    return
}


func BridgeSetMode(spiNumber uint32, bus uint8, ACKenable uint8) (err error) {
    var wrData, reg uint8
    if bus == 0 { reg = SPI_I2C0_MODE_REG 
    } else {      reg = SPI_I2C1_MODE_REG }

    if ACKenable > 0 {
        wrData = 0x2A
    } else {
        wrData = 0x3A
    }

    err = BridgeWriteReg(spiNumber, reg, wrData)
    if err != nil {
        return
    }
    return
}


/**********************************************************************************
*  
* I2C Write through the spi-2-i2c Bridge 
*  
***********************************************************************************/
func BridgeI2CtransactionWrite(spiNumber uint32, bus uint8, i2cAddr uint8, data []uint8) (err error) {
    var CFGreg, STSreg uint8
    var data8 uint8
    max_try := 100
    i := 0

    if bus == 0 { CFGreg = SPI_I2C0_CONFIG_REG 
    } else {      CFGreg = SPI_I2C1_CONFIG_REG }

    if bus == 0 { STSreg = SPI_I2C0_CMD_STS_REG 
    } else {      STSreg = SPI_I2C1_CMD_STS_REG }

    err = BridgeSetMode(spiNumber, bus, 1) 
    if err != nil {
        return
    }
    err = BridgeFifoClear(spiNumber, bus) 
    if err != nil {
        return
    } 
    err = BridgeIRQClear(spiNumber, bus) 
    if err != nil {
        return
    }


    //Work around for issue where random IRQ is set after clearing IRQ
    //Try to clear them again if we see random IRQ set
    /*
    for i=0;i<10;i++ {
        data8, err = BridgeReadReg(spiNumber, STSreg) 
        if data8 != 0x00 {
            fmt.Printf(" WARN: IRQ REG NO CLEAR, RESETTING IRQ AGAIN reg=%x\n", data8)
            err = BridgeIRQClear(spiNumber, bus) 
            if err != nil {
                return
            }
            err = BridgeSetMode(spiNumber, bus, 1) 
            if err != nil {
                return
            }
            data8, _ = ReadByteSmbus("CPLD", 0xB2, spiNumber) 
            fmt.Printf(" AFTER IRQ RE-CLEAR DATA8=%d\n", data8)
        }
    } 
    */ 
    //time.Sleep(time.Duration(100) * time.Millisecond)
    data8, err = BridgeReadReg(spiNumber, STSreg) 
    if data8 != 0x00 {
        err = fmt.Errorf(" ERROR: IRQ REG NOT CLEAR, reg=%x\n", data8)
        fmt.Printf("%v", err)
        return
    } 
     

    //Run i2c write command
    err = BridgeI2Cwrite(spiNumber, bus, i2cAddr, uint8(len(data)), data) 
    if err != nil {
        return
    }

    //Run START (for i2c write command)
    err = BridgeWriteReg(spiNumber, CFGreg, 0x01)
    if err != nil {
        return
    }
    //Check Status Transaction Complete
    for i=0; i<max_try; i++ {
        time.Sleep(time.Duration(1) * time.Millisecond)
        data8, err = BridgeReadReg(spiNumber, STSreg) 
        if (data8 & 0x02) == 0x02 {
            break
        }
        if (data8 > 0) && (data8 != 0x80) {
            err = fmt.Errorf("ERROR: BridgeI2CtransactionWrite I2C Write Failed due to wrong IRQ. (%d) STS Reg=0x%x\n", i, data8)
            fmt.Printf("ERROR -> %v", err)
            return
        }
        if (i == (max_try - 2)) {
            err = fmt.Errorf("ERROR: BridgeI2CtransactionWrite I2C Write Failed due to timeout. (%d) STS Reg=0x%x\n", i, data8)
            fmt.Printf("ERROR -> %v", err)
            return
        }
    }
    return
}


/**********************************************************************************
*  
* I2C Read through the spi-2-i2c Bridge  
*  
***********************************************************************************/
func BridgeI2CtransactionRead(spiNumber uint32, bus uint8, i2cAddr uint8, numBytes uint8) (data []uint8, err error) {
    var CFGreg, STSreg uint8
    var data8 uint8
    max_try := 100
    i := 0

    if bus == 0 { CFGreg = SPI_I2C0_CONFIG_REG 
    } else {      CFGreg = SPI_I2C1_CONFIG_REG }

    if bus == 0 { STSreg = SPI_I2C0_CMD_STS_REG 
    } else {      STSreg = SPI_I2C1_CMD_STS_REG }

    err = BridgeSetMode(spiNumber, bus, 0) 
    if err != nil {
        return
    }
    err = BridgeFifoClear(spiNumber, bus) 
    if err != nil {
        return
    } 

    err = BridgeIRQClear(spiNumber, bus) 
    if err != nil {
        return
    }


    //Work around for issue where random IRQ is set after clearing IRQ
    //Try to clear them again if we see random IRQ set
    /*
    for i=0;i<10;i++ {
        data8, err = BridgeReadReg(spiNumber, STSreg) 
        if data8 != 0x00 {
            fmt.Printf(" WARN: ABORT ACK SET, RESETTING IRQ AGAIN reg=%x\n", data8)
            err = BridgeIRQClear(spiNumber, bus) 
            if err != nil {
                return
            }
            err = BridgeSetMode(spiNumber, bus, 0) 
            if err != nil {
                return
            }
            data8, _ = ReadByteSmbus("CPLD", 0xB2, spiNumber) 
            fmt.Printf(" AFTER IRQ RE-CLEAR DATA8=%d\n", data8)
        }
    }
    */ 
    //time.Sleep(time.Duration(100) * time.Millisecond)
    data8, err = BridgeReadReg(spiNumber, STSreg) 
    if data8 != 0x00 {
        err = fmt.Errorf(" ERROR: IRQ REG NOT CLEAR, reg=%x\n", data8)
        fmt.Printf("%v", err)
        return
    }
    

    //Run i2c read command
    err = BridgeI2Cread(spiNumber, bus, i2cAddr, numBytes)
    if err != nil {
        return
    }

    //Run START (for i2c read command)
    err = BridgeWriteReg(spiNumber, CFGreg, 0x01)
    if err != nil {
        return
    }

    //Check I2C Transaction Complete
    for i=0; i<max_try; i++ {
        time.Sleep(time.Duration(1) * time.Millisecond)
        data8, err = BridgeReadReg(spiNumber, STSreg) 
        if (data8 & 0x02) == 0x02 {
            break
        }
        if (data8 > 0) && (data8 != 0x80) {
            err = fmt.Errorf("ERROR: BridgeI2CtransactionRead I2C Read Failed due to IRQ Error. (%d) STS Reg=0x%x\n", i, data8)
            fmt.Printf("ERROR -> %v", err)
            return
        }
        if (i == (max_try - 2)) {
            err = fmt.Errorf("ERROR: BridgeI2CtransactionRead I2C Read TIMED OUT. (%d) STS Reg=0x%x\n", i, data8)
            fmt.Printf("ERROR -> %v", err)
            return
        }
    }

    data, err = BridgeReadFIFO(spiNumber, bus, numBytes)
    if err != nil {
        return
    }
    return
}



func QSFP112VerifyCheckSums(spiNumber uint32, bus uint8, i2cAddr uint8) (err error) {
    var computed_cc uint8  = 0
    rdData := []uint8{}
    wrData := []uint8{}

    fmt.Printf("Testing QSFP Checksum on Slot-%d Bus-%d\n", spiNumber, bus)

    //Set the address pointer in the qsfp
    wrData = append(wrData, 128)
    err = BridgeI2CtransactionWrite(spiNumber, bus, i2cAddr, wrData) 
    if err != nil {
        return
    }

    //Read the data needed for the checksum
    for i:=128; i < (223+1); i+=int(I2C_MAX_BYTES) {
        tmpRdData := []uint8{}
        tmpRdData, err = BridgeI2CtransactionRead(spiNumber, bus, i2cAddr, I2C_MAX_BYTES) 
        if err != nil {
            return
        }
        rdData = append(rdData, tmpRdData...)
    }

    for i:=0; i < 94; i++ {
        computed_cc = computed_cc + rdData[i]
    }

    for i:=0; i < len(rdData); i++ {
        if i%16 == 0 {
            fmt.Printf("\n")
        }
        fmt.Printf("%.02x ", rdData[i]) 
    }
    fmt.Printf("\ndone\n");

    if computed_cc != rdData[94] {
        err = fmt.Errorf("Error:  Computer CC and Read CC Do not match.  Read CC = 0x%x.   Computed CC = 0x%x\n", rdData[94], computed_cc)
        fmt.Printf("%v", err)
        return
    }

    //fmt.Printf("Testing CSUM Passed\n")

    return
}


func QSFPAmphenolVerifyCheckSums(spiNumber uint32, bus uint8, i2cAddr uint8) (err error) {
    var computed_cc uint8  = 0
    rdData := []uint8{}
    wrData := []uint8{}

    fmt.Printf("Testing QSFP Checksum on Slot-%d Bus-%d\n", spiNumber+1, bus)

    //Set the address pointer in the qsfp
    wrData = append(wrData, 128)
    err = BridgeI2CtransactionWrite(spiNumber, bus, i2cAddr, wrData) 
    if err != nil {
        return
    }

    //Read the data needed for the checksum
    for i:=128; i < 191; i+=int(I2C_MAX_BYTES) {
        tmpRdData := []uint8{}
        tmpRdData, err = BridgeI2CtransactionRead(spiNumber, bus, i2cAddr, I2C_MAX_BYTES) 
        if err != nil {
            return
        }
        rdData = append(rdData, tmpRdData...)
    }

    for i:=0; i < 63; i++ {
        computed_cc = computed_cc + rdData[i]
    }

    if computed_cc != rdData[63] {
        for i:=0; i < len(rdData); i++ {
            if i%16 == 0 {
                fmt.Printf("\n")
            }
            fmt.Printf("%.02x ", rdData[i]) 
        }
        err = fmt.Errorf("Error:  Computer CC and Read CC Do not match.  Read CC = 0x%x.   Computed CC = 0x%x\n", rdData[63], computed_cc)
        fmt.Printf("%v", err)
        return
    }

    fmt.Printf("Testing CSUM Base Passed Read CSUM=0x%x.  Computed CSUMC=0x%x\n", rdData[63], computed_cc)


    rdData = nil
    computed_cc = 0
    //Set the address pointer in the qsfp
    wrData[0] = 192
    err = BridgeI2CtransactionWrite(spiNumber, bus, i2cAddr, wrData) 
    if err != nil {
        return
    }

    //Read the data needed for the checksum
    for i:=192; i < 223; i+=int(I2C_MAX_BYTES) {
        tmpRdData := []uint8{}
        tmpRdData, err = BridgeI2CtransactionRead(spiNumber, bus, i2cAddr, I2C_MAX_BYTES) 
        if err != nil {
            return
        }
        rdData = append(rdData, tmpRdData...)
    }

    for i:=0; i < 31; i++ {
        computed_cc = computed_cc + rdData[i]
    }

    if computed_cc != rdData[31] {
        for i:=0; i < 32; i++ {
            if i%16 == 0 {
                fmt.Printf("\n")
            }
            fmt.Printf("%.02x ", rdData[i]) 
        }
        err = fmt.Errorf("Error:  Computer CC and Read CC Do not match.  Read CC = 0x%x.   Computed CC = 0x%x\n", rdData[31], computed_cc)
        fmt.Printf("%v", err)
        return
    }

    fmt.Printf("Testing CSUM Base Passed Read CSUM=0x%x.  Computed CSUMC=0x%x\n", rdData[31], computed_cc)

    return
}


func QSFPdump(spiNumber uint32, bus uint8, i2cAddr uint8) (err error) {
    rdData := []uint8{}
    wrData := []uint8{ 0x00 }

    //Read the data needed for the checksum
    for i:=0; i < (256); i+=int(I2C_MAX_BYTES) {

        //Set the address pointer in the qsfp
        wrData[0] = uint8(i)
        err = BridgeI2CtransactionWrite(spiNumber, bus, i2cAddr, wrData) 
        if err != nil {
            return
        }

        tmpRdData := []uint8{}
        tmpRdData, err = BridgeI2CtransactionRead(spiNumber, bus, i2cAddr, I2C_MAX_BYTES) 
        if err != nil {
            return
        }
        rdData = append(rdData, tmpRdData...)
    }

    for i:=0; i < len(rdData); i++ {
        if i%16 == 0 {
            fmt.Printf("\n%.04x: ", i)
        }
        fmt.Printf("%.02x ", rdData[i]) 
    }
    fmt.Printf("\n")
    var identifier = rdData[128]
    if (identifier == 0x11) {
        // SFF-8636 format (e.g. Multilane loopback)
        fmt.Printf("Vendor   ='%s'\n", string(rdData[148:163]))
        fmt.Printf("Vendor PN='%s'\n", string(rdData[168:185]))
        fmt.Printf("Vendor SN='%s'\n", string(rdData[196:211]))
    } else if (identifier == 0x1e) {
        // CMIS format (e.g. Infraeo loopback)
        fmt.Printf("Vendor   ='%s'\n", string(rdData[129:144]))
        fmt.Printf("Vendor PN='%s'\n", string(rdData[148:165]))
        fmt.Printf("Vendor SN='%s'\n", string(rdData[166:181]))
    }
    return
}



/**********************************************************************************
*  
* I2C Test issue with Random IRQ being set after resetting the IRQ's. 
*  
***********************************************************************************/
func BridgeClearIRQtest(spiNumber uint32, bus uint8, i2cAddr uint8) (err error) {
    var STSreg uint8
    var data8 uint8
    i := 0
    j := 0

    if bus == 0 { STSreg = SPI_I2C0_CMD_STS_REG 
    } else {      STSreg = SPI_I2C1_CMD_STS_REG }

    /*err = BridgeSetMode(spiNumber, bus, 1) 
    if err != nil {
        return
    }
    err = BridgeFifoClear(spiNumber, bus) 
    if err != nil {
        return
    }*/


    //data8, err = BridgeReadReg(spiNumber, 1)
    //fmt.Printf("FIFO REG=%x\n", data8)

    err = BridgeIRQClear(spiNumber, bus) 
    if err != nil {
        return
    }


    //Work around for issue where random IRQ is set after clearing IRQ
    //Try to clear them again if we see random IRQ set
    for i=0;i<100;i++ {
        data8, err = BridgeReadReg(spiNumber, STSreg) 
        if data8 != 0x00 {
            cpldreg, _ := ReadByteSmbus("CPLD", 0xB2, spiNumber)
            fmt.Printf(" DEBUG: CPLD REG 0xB2=%.02x\n", cpldreg)

            fmt.Printf(" ERROR: IRQ REG NOT CLEAR reg=%x\n", data8)
            if j > 0 {
               err = fmt.Errorf("FAIL")
               return
            }
            j++
        } else {
            break;
        }
    } 
    fmt.Printf("end\n");
 
     
    return
}


/**********************************************************************************
*  
* I2C Test issue with Random IRQ being set after resetting the IRQ's. 
* Try the i2c controller reset to see if the issue happens 
*  
***********************************************************************************/
func BridgeClearResetTest(spiNumber uint32, bus uint8, i2cAddr uint8) (err error) {
    var STSreg uint8
    i := 0
    j := 0

    var data8, reg uint8
    if bus == 0 { reg = SPI_I2C0_CONFIG_REG 
    } else {      reg = SPI_I2C1_CONFIG_REG }

    err = BridgeWriteReg(spiNumber, reg, 0x80)
    if err != nil {
        return
    }

    err = BridgeWriteReg(spiNumber, reg, 0x00)
    if err != nil {
        return
    }
    
    data8, err = BridgeReadReg(spiNumber, reg)
    if err != nil {
        return
    }
    if data8 != 0x00 {
        err = fmt.Errorf("ERROR: BridgeClearResetTest Expect SPI-2-I2C BUS-%d CONFIG TO BE 0x00.. Config Register=%x\n", bus, data8);
        fmt.Printf("%v", err)
        return
    } 

    //Work around for issue where random IRQ is set after clearing IRQ
    //Try to clear them again if we see random IRQ set
    for i=0;i<100;i++ {
        data8, err = BridgeReadReg(spiNumber, STSreg) 
        if data8 != 0x00 {
            cpldreg, _ := ReadByteSmbus("CPLD", 0xB2, spiNumber)
            fmt.Printf(" DEBUG: CPLD REG 0xB2=%.02x\n", cpldreg)

            fmt.Printf(" ERROR: IRQ REG NOT CLEAR reg=%x\n", data8)
            if j > 0 {
               err = fmt.Errorf("FAIL")
               return
            }
            j++
        } else {
            break;
        }
    } 
    fmt.Printf("end\n");
 
     
    return
}

