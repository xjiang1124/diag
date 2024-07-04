// Support for Matera FPGA SPI BUS
package materafpga

import (
    "common/cli"
    "common/errType"
    "device/ioexpander/mcp23008"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    "fmt"
    "protocol/smbusNew"
    "time"
)


type spiDevMap struct{
    spiMBaddr     uint64
    devname string
}


const SPI_SLOT0            uint32 = 0
const SPI_SLOT1            uint32 = 1
const SPI_SLOT2            uint32 = 2
const SPI_SLOT3            uint32 = 3
const SPI_SLOT4            uint32 = 4
const SPI_SLOT5            uint32 = 5
const SPI_SLOT6            uint32 = 6
const SPI_SLOT7            uint32 = 7
const SPI_SLOT8            uint32 = 8
const SPI_SLOT9            uint32 = 9
const SPI_DBG              uint32 = 10
const SPI_FPGA             uint32 = 11
const SPI_NUMB_BUSES       uint32 = 12

var SpiTable = map[uint32]spiDevMap {
    SPI_SLOT0 : { spiMBaddr:FPGA_S0_SPI_RXDATA_REG , devname:"SLOT0", } , 
    SPI_SLOT1 : { spiMBaddr:FPGA_S1_SPI_RXDATA_REG , devname:"SLOT1", } , 
    SPI_SLOT2 : { spiMBaddr:FPGA_S2_SPI_RXDATA_REG , devname:"SLOT2", } , 
    SPI_SLOT3 : { spiMBaddr:FPGA_S3_SPI_RXDATA_REG , devname:"SLOT3", } , 
    SPI_SLOT4 : { spiMBaddr:FPGA_S4_SPI_RXDATA_REG , devname:"SLOT4", } , 
    SPI_SLOT5 : { spiMBaddr:FPGA_S5_SPI_RXDATA_REG , devname:"SLOT5", } , 
    SPI_SLOT6 : { spiMBaddr:FPGA_S6_SPI_RXDATA_REG , devname:"SLOT6", } , 
    SPI_SLOT7 : { spiMBaddr:FPGA_S7_SPI_RXDATA_REG , devname:"SLOT7", } , 
    SPI_SLOT8 : { spiMBaddr:FPGA_S8_SPI_RXDATA_REG , devname:"SLOT8", } , 
    SPI_SLOT9 : { spiMBaddr:FPGA_S9_SPI_RXDATA_REG , devname:"SLOT9", } , 
    SPI_DBG   : { spiMBaddr:FPGA_DBG_SPI_RXDATA_REG , devname:"DBG", } , 
    SPI_FPGA  : { spiMBaddr:FPGA_FPGA_SPI_RXDATA_REG , devname:"FGPA", } , 
}

const SPI_RXDATA_OFFSET            uint64 = 0x00       //SPI0 = FPGA FLASH
const SPI_TXDATA4B_OFFSET          uint64 = 0x04
const SPI_TXDATA2B_OFFSET          uint64 = 0x08
const SPI_TXDATA1B_OFFSET          uint64 = 0x0C
const SPI_STATUS_OFFSET            uint64 = 0x10
const SPI_CONTROL_OFFSET           uint64 = 0x14
const SPI_SEM_OFFSET               uint64 = 0x18
const SPI_SLAVESEL_OFFSET          uint64 = 0x1C
const SPI_EOP_VALUE_OFFSET         uint64 = 0x20
const SPI_MUXSEL_OFFSET            uint64 = 0x24

//SPI STATUS BITS
const SPI_STA_FIFO_SUPPORT      uint32 = 0x80000000
const SPI_STA_TXFIFO_FULL       uint32 = 0x8000  //TX FIFO FULL
const SPI_STA_TXFIFO_EMPTY      uint32 = 0x4000  //TX FIFO EMPTY
const SPI_STA_RXFIFO_FULL       uint32 = 0x2000  //RX FIFO FULL
const SPI_STA_RXFIFO_EMPTY      uint32 = 0x1000  //RX FIFO EMPTY
const SPI_STA_RXFIFO_HFULL      uint32 = 0x0400  //RXFIFO has more than 128 entries of vaild data. When this bit is 1, it is safe to read upto 128 Dwords of RXDATA without checking RRDY
const SPI_STA_TXFIFO_HFULL      uint32 = 0x0200  //1: TXFIFO has less than 128 entries left for write operation.  When this bit is 0, it is safe to write upto 128 Dwords of TXDATA without checking TRDY
const SPI_STA_ERROR             uint32 = 0x0100
const SPI_STA_RCV_RDY           uint32 = 0x0080
const SPI_STA_TMT_RDY           uint32 = 0x0040
const SPI_STA_TRANSMIT_COMPL    uint32 = 0x0020
const SPI_STA_TOE               uint32 = 0x0010
const SPI_STA_ROE               uint32 = 0x0008



const SPI_TRGT_DEVICE_QSPI0       uint32 = 0  //salina qspi-0
const SPI_TRGT_DEVICE_QSPI1       uint32 = 1  //salina qspi-1
const SPI_TRGT_DEVICE_CPLD_FLASH  uint32 = 2  //cpld flash
const SPI_TRGT_DEVICE_CPLD_REG    uint32 = 3  //cpld register spcace
const SPI_TRGT_DEVICE_FPGA        uint32 = 4  //fpga flash

//Global to keep track if we have enabled a spi at the cpld so we don't do constant i2c access to the cpld to enable it on every spi transcation
var TARGET_SPI_ENABLED             uint32 = 999
var TARGET_QSPI_UNRESET            bool = false
var TARGET_SPI_IOEXPANDER_EN       bool = false


func ReadByteSmbus(devName string, offset uint, slot uint32) (Data byte, err int) {
    err = errType.SUCCESS

    uut := fmt.Sprintf("UUT_%d", slot+1)
    lock, _ := hwinfo.PreUutSetup(uut)
    defer hwinfo.PostUutClean(lock)

    //Opens smbus connection
    i2cSmbus, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain smbus info for dev", devName)
        return
    }
    err = smbusNew.Open(devName, i2cSmbus.Bus, i2cSmbus.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open smbus: dev", devName,
                    "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
        return
    }

    Data, err = smbusNew.ReadByte(devName, uint64(offset))
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read from %s at offset 0x%02x", devName, offset))
    }

    smbusNew.Close()

    return
}


func WriteByteSmbus(devName string, offset uint, val byte, slot uint32) (err int) {
    err = errType.SUCCESS

    uut := fmt.Sprintf("UUT_%d", slot+1)
    lock, _ := hwinfo.PreUutSetup(uut)
    defer hwinfo.PostUutClean(lock)

    //Opens smbus connection
    i2cSmbus, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain smbus info for dev", devName)
        return
    }
    err = smbusNew.Open(devName, i2cSmbus.Bus, i2cSmbus.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open smbus: dev", devName,
                    "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
        return
    }

    err = smbusNew.WriteByte(devName, uint64(offset), val)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write", devName, " at offset", offset, "with value", val)
    }

    smbusNew.Close()

    return
}


/*********************************************************************
* Set the SPI SELECT on the Netwrok Adapter CPLD
* 
* DEV = CPLD_SLOT0 - CPLD_SLOT9 
*  
* SPI_SLAVE_SEL[2:0] -- Bit 7,4,3: 
* For MTP
* 001:  SPI-to-I2C bridge,  used for I2C access to FP0 and FP1 transceiver 
* 100:  CPLD Internal Flash (CFG0, CFG1, UFMn)
* 101:  external QSPI0 Flash
* 110:  external QSPI1 Flash
*********************************************************************/
func CpldEnableSPI(spiNumber uint32, targetSPI uint32) (err error) {
    var data8 uint8
    var err_i int
    devName := fmt.Sprintf("CPLD")
    //check if we enabled this spi target already at the cpld, and just return
    if TARGET_SPI_ENABLED == targetSPI {
        return
    }

    data8, err_i = ReadByteSmbus(devName, 0x24, spiNumber) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: CpldEnableSPI %s i2c access failed at offset 0x24\n", devName);
        fmt.Printf("%w\n", err)
        return
    }

    data8 = data8 & (^(uint8(1<<7) | uint8(1<<4) | uint8(1<<3))) //mask out spi select bits

    switch(targetSPI){
        case SPI_TRGT_DEVICE_CPLD_FLASH: 
            data8 = data8 | 0x80
        case SPI_TRGT_DEVICE_QSPI0:
            data8 = data8 | 0x88
        case SPI_TRGT_DEVICE_QSPI1:
            data8 = data8 | 0x90
        case SPI_TRGT_DEVICE_CPLD_REG:
            data8 = data8 | 0x98
        default: {
            err = fmt.Errorf("ERROR: Invalid arg targetSPI passed.   You passed %d", targetSPI);
            fmt.Printf("%w\n", err)
            return
        }
    }

    err_i = WriteByteSmbus(devName, uint(0x24), data8, spiNumber) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: CpldEnableSPI %s i2c write access to 0x24 failed\n", devName);
        fmt.Printf("%w\n", err)
        return
    }

    TARGET_SPI_ENABLED = targetSPI 

    return
}


/*********************************************************************
* QSPI reset on Salinas CPLD 
*  
* targetQSPI = SPI_TRGT_DEVICE_QSPI0, SPI_TRGT_DEVICE_QSPI1  
* SetReset = 1 will put the part into reset, 0 will remove reset 
* 
*********************************************************************/
func CpldQSPIreset(spiNumber uint32, targetQSPI uint32, SetReset uint32) (err error) {
    var data8, bitPos byte
    err_i := errType.SUCCESS
    devName := fmt.Sprintf("CPLD")

    if TARGET_QSPI_UNRESET == true {
        return
    }

    data8, err_i = ReadByteSmbus(devName, 0x1F, spiNumber) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: CpldQSPIreset: %s i2c access failed\n", devName);
        return
    }

    switch(targetQSPI){
        case SPI_TRGT_DEVICE_QSPI0: 
            bitPos = (1<<4)
        case SPI_TRGT_DEVICE_QSPI1:
            bitPos = (1<<5)
        default: {
            err = fmt.Errorf("ERROR: CpldQSPIreset: Invalid arg targetQSPI passed.   You passed %d", targetQSPI);
            fmt.Printf("%w\n", err)
            return
        }
    }
    if SetReset > 0 {
        data8 = data8 | bitPos
    } else {
        data8 = data8 & (^bitPos)
    }

    err_i = WriteByteSmbus(devName, 0x1F, data8, spiNumber) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: CpldQSPIreset: %s i2c access failed\n", devName);
        fmt.Printf("%w\n", err)
        return
    }

    TARGET_QSPI_UNRESET = true

    return
}


/*********************************************************************
* Enable the SPI Bus on the MATERA IOB MPC23008 I/O EXPANDER
* "IOBL" = SLOT 0-4
* "IOBR" = SLOT 5-9
*********************************************************************/
func SpiBusEnableIOexpander(spiNumber uint32) (err error) {
    var dev string
    var shift, data8 byte
    err_i := errType.SUCCESS

    if TARGET_SPI_IOEXPANDER_EN == true {
        return
    }

    if ( spiNumber <= SPI_SLOT4 ) {
        dev = "EXPDER_IOBL"
        shift = byte(spiNumber)
    } else {
        dev = "EXPDER_IOBR"
        shift = byte(spiNumber - 5)
    }


    //Set the I/O DIRECTION. 0 = OUTPUT
    data8, err_i = mcp23008.ReadByteSmbus(dev, mcp23008.IODIR) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        fmt.Printf("%w\n", err)
        return
    }

    data8 = data8 & byte(^(1 << shift))

    err_i = mcp23008.WriteByteSmbus(dev, mcp23008.IODIR, data8) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        fmt.Printf("%w\n", err)
        return
    }

    //Drive the signal high. 
    data8, err_i = mcp23008.ReadByteSmbus(dev, mcp23008.GPIO) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        fmt.Printf("%w\n", err)
        return
    }

    data8 = data8 | byte(1 << shift)

    err_i = mcp23008.WriteByteSmbus(dev, mcp23008.GPIO, data8) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        fmt.Printf("%w\n", err)
        return
    }

    TARGET_SPI_IOEXPANDER_EN = true

    return
}


/*********************************************************************
* Disable the SPI Bus on the MATERA IOB I/O EXPANDER
* "IOBL" = SLOT 0-4
* "IOBR" = SLOT 5-9
*********************************************************************/
func SpiBusDisableIOexpander(spiNumber uint32) (err error) {
    var dev string
    var shift, data8 byte
    err_i := errType.SUCCESS

    if ( spiNumber <= SPI_SLOT4 ) {
        dev = "EXPDER_IOBL"
        shift = byte(spiNumber)
    } else {
        dev = "EXPDER_IOBR"
        shift = byte(spiNumber - 5)
    }


    //Set the I/O DIRECTION. 1 = INPUT.   INTERFACE DISABLED
    data8, err_i = mcp23008.ReadByteSmbus(dev, mcp23008.IODIR) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        return
    }

    data8 = data8 | byte(1 << shift)

    err_i = mcp23008.WriteByteSmbus(dev, mcp23008.IODIR, data8) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        return
    }

    //Drive the signal low. 
    data8, err_i = mcp23008.ReadByteSmbus(dev, mcp23008.GPIO) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        return
    }

    data8 = data8 & byte((^(1 << shift)))

    err_i = mcp23008.WriteByteSmbus(dev, mcp23008.GPIO, data8) 
    if err_i != errType.SUCCESS {
        err = fmt.Errorf("ERROR: %s i2c access failed\n", dev);
        return
    }

    return
}



//Enable the SPI Bus via the FPGA MSIC CONTROL REGISTER
func SpiBusEnableAtFPGA(spiNumber uint32) (err error) {
    var data32 uint32 = 0

    //Only slots 0-9 and the DEBUG slot (10) need this.  The FPGA does not need this
    if spiNumber > SPI_DBG {
        return
    }

    //Mask in the enable bit
    data32, err = MateraReadU32(FPGA_MISC_CTRL_REG)
    data32 |= (FPGA_MISC_CTRL_SLOT0_SPI_EN << spiNumber) 
    MateraWriteU32(FPGA_MISC_CTRL_REG, data32) 

    return
}

//Disable the SPI Bus via the FPGA MSIC CONTROL REGISTER
func SpiBusDisableAtFPGA(spiNumber uint32) (err error) {
    var data32 uint32 = 0

    //Only slots 0-9 and the DEBUG slot (10) need this.  The FPGA does not need this
    if spiNumber > SPI_DBG {
        return
    }

    //Mask out the enable bit
    data32, err = MateraReadU32(FPGA_MISC_CTRL_REG)
    data32 = data32 & (^(FPGA_MISC_CTRL_SLOT0_SPI_EN << spiNumber))
    MateraWriteU32(FPGA_MISC_CTRL_REG, data32) 

    return
}


//Check TX FIFO EMPTY
func Spi_check_tx_fifo_empty(spiNumber uint32) (err error) {
    var data32 uint32 = 0
    var timeout, x uint32 = 500, 0

    //check status reg for status on tx data drain
    for x=0; x<timeout; x++ {
        data32, err = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET)
        if (data32 & SPI_STA_TXFIFO_EMPTY) == SPI_STA_TXFIFO_EMPTY {
            break;
        }
    }
    if x == timeout {
        err = fmt.Errorf("ERROR Spi_check_tx_complete. Spi-%d, not seeing transmit complete.  Status Reg = 0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }
    return
}

//Check Tx/Rx Transaction is done
func Spi_check_tx_complete(spiNumber uint32) (err error) {
    var data32 uint32 = 0
    var timeout, x uint32 = 500, 0

    //check status reg for status on tx data drain
    for x=0; x<timeout; x++ {
        data32, err = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET)
        if (data32 & SPI_STA_TRANSMIT_COMPL) == SPI_STA_TRANSMIT_COMPL {
            break;
        }
    }
    if x == timeout {
        err = fmt.Errorf("ERROR Spi_check_tx_complete. Spi-%d, not seeing transmit complete.  Status Reg = 0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }
    return
}


func Spi_check_tx_drain(spiNumber uint32) (err error) {
    var data32 uint32 = 0
    var timeout, x uint32 = 500, 0

    //check status reg for status on tx data drain
    for x=0; x<timeout; x++ {
        data32, err = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET)
        if (data32 & SPI_STA_TOE) == SPI_STA_TOE {   //transmit overrun error
            err = fmt.Errorf("ERROR Spi_check_tx_drain. Spi-%d, TRANSMIT OVERRUN ERROR SET.  Status Reg = 0x%x\n", spiNumber, data32)
            cli.Printf("e", "%s", err)
            return
        }
        if (data32 & SPI_STA_TMT_RDY) == SPI_STA_TMT_RDY {
            break;
        }
    }
    if x == timeout {
        err = fmt.Errorf("ERROR Spi_check_tx_drain. Spi-%d, not seeing transmitter ready.  Status Reg = 0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }
    return
}

func Spi_check_rx_ready(spiNumber uint32) (err error) {
    var data32 uint32 = 0
    var timeout, x uint32 = 500, 0

    //check status reg for status on tx data drain
    for x=0; x<timeout; x++ {
        data32, err = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET)
        if (data32 & SPI_STA_ROE) == SPI_STA_ROE {   //receive overrun error
            err = fmt.Errorf("ERROR Spi_check_rx_ready. Spi-%d, RECEIVE OVERRUN ERROR SET.  Status Reg = 0x%x\n", spiNumber, data32)
            cli.Printf("e", "%s", err)
            return
        }
        if (data32 & SPI_STA_RCV_RDY) == SPI_STA_RCV_RDY {
            break;
        }
    }
    if x == timeout {
        err = fmt.Errorf("ERROR Spi_check_rx_ready. Spi-%d, not seeing receiver ready.  Status Reg = 0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
        return
    }
    return
}


func Spi_Read_Data(spiNumber uint32) (data32 uint32, err error) {
    var timeout, x uint32 = 100, 0
    var statsreg uint32

    for x=0; x<timeout; x++ {
        data32, err = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_RXDATA_OFFSET)
        //BIT[31:30] represent how many bytes can be read from 1 to 3 bytes.
        //If any bit[31:30] is set there is data to read
        //If we never see these bits set, there is no read data.  Return an error
        if ((data32 & 0xC0000000) > 0) {
            return;
        }
        
        //Just capture a snapshot of the status reg in case the read times out so we have an initial snap shot for debug
        if x == 0 {
            statsreg, _ = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET)
        }
        //Poll sleep
        time.Sleep(time.Duration(1) * time.Microsecond)
    }
    
    err = fmt.Errorf("ERROR Spi_Read_Data. Spi-%d, Not seeing Data Valid Bit. X=%d StatusReg=%x  RXDATA_REG Reg = 0x%x\n", spiNumber, x, statsreg, data32)
    cli.Printf("e", "%s", err)

    return
}



// ***********************************************************************************
// *
// *   Do a spi transaction.   For SPI Number mapping see the top of the file.  
// *   The spi number corresponds to the spi mail box in the fpga.
// *
// ***********************************************************************************
func matera_spi_generic_transaction(spiNumber uint32, spiDevice uint32, opCode []byte, rdLength uint32) (rdData []byte, err error) {
    var data32 uint32 = 0
    var tmpRdLength uint32 = 0
    var ChkTxDrain uint32 = 0


    if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR matera_spi_generic_transaction. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        cli.Printf("e", "%s", err)
        return
    }

    //For network adapter slots, need to set various enables / muxes to get spi working
    if spiNumber < SPI_FPGA {
        //Enable the spi bus mux on the fpga that muxes between spi and j2c.  
        //This is seperate from the spi mailbox mux that controls the mux between the fpga and elba.
        //Too many muxes.......
        SpiBusEnableAtFPGA(spiNumber)

        //Enable spi bus on the iob card via the mcp23008 i/o expander
        err = SpiBusEnableIOexpander(spiNumber)
        if err != nil {
            goto SPI_TRANSACTION_END2
        }

        //Take QSPI out of reset on the network adapter CPLD
        if (spiDevice == SPI_TRGT_DEVICE_QSPI0) || (spiDevice == SPI_TRGT_DEVICE_QSPI1) {
            err = CpldQSPIreset(spiNumber, spiDevice, 0) 
            if err != nil {
                goto SPI_TRANSACTION_END2
            }
        }

        //Enable Targeted SPI BUS on the network adapter CPLD
        if (spiDevice != SPI_TRGT_DEVICE_FPGA) {
            err = CpldEnableSPI(spiNumber, spiDevice)
            if err != nil {
                goto SPI_TRANSACTION_END2
            }
        }
    }

    data32, err = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET)
    if (data32 & SPI_STA_FIFO_SUPPORT) == SPI_STA_FIFO_SUPPORT {   //Newer SPI Method that supports FIFO
        var FIFORDLENGTH uint32 = (32 * 256)  //8K
        var wr_length int = len(opCode)
        //fmt.Printf("DEBUG: NEWER FIFO..RD LENGTH=%d\n", rdLength);
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_CONTROL_OFFSET, 0x00)   //turn off spi to reset fifo's in case it's on     
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_MUXSEL_OFFSET, 0x00)    //turn mux select to FPGA on     
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_SLAVESEL_OFFSET, 0x01)  //enable slave access
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_CONTROL_OFFSET, 0x400)  //turn on spi output
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET, 0x00)    //clear status

        data32, err = MateraReadU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET)
        if (data32 & SPI_STA_TMT_RDY) != SPI_STA_TMT_RDY {
            err = fmt.Errorf("ERROR matera_spi_generic_transaction. Spi-%d, TX FIFO IS NOT EMPTY AT START OF TRANSACTION.  Status Reg = 0x%x\n", spiNumber, data32)
            cli.Printf("e", "%s", err)
            goto SPI_TRANSACTION_END
        }
        for i:=0; i<wr_length; i++ {
            MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_TXDATA1B_OFFSET, uint32(opCode[i]))    //clear status
            //time.Sleep(time.Duration(2) * time.Microsecond)
            if (i!=0) && ((i%1024) == 0) {
                ChkTxDrain = 1
            }
            if i == (len(opCode)-1) {
                ChkTxDrain = 1
                if rdLength > 0 {
                    if rdLength > FIFORDLENGTH {
                        tmpRdLength = FIFORDLENGTH;
                    } else {
                        tmpRdLength = rdLength
                    } 
                    //fmt.Printf("Writing Control Reg with Read Lenght=%d  (ctrl reg = 0x%.08x)\n", tmpRdLength, (0x400 | (tmpRdLength << 16)))  
                    MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_CONTROL_OFFSET, (0x400 | (tmpRdLength << 16)))
                }
            }

            
            if ChkTxDrain > 0 {
                err = Spi_check_tx_drain(spiNumber)
                if err != nil {
                    goto SPI_TRANSACTION_END
                }
                ChkTxDrain = 0
            }
        }

        //clear status
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_STATUS_OFFSET, 0x00)

        //read data if we need to do reads
        rdLength = rdLength + 1
        for i:=1; i<int(rdLength); i++ {
            data32, err = Spi_Read_Data(spiNumber) 
            if err != nil {
                cli.Printf("e", "matera_spi_generic_transaction -> Spi_Read_Data Failed.  i=%d\n", i)
                goto SPI_TRANSACTION_END
            }
            //fmt.Printf(" Data32=0x%.08x\n", data32);
            rdData = append(rdData, byte(data32))
            if ((data32 & 0xC0000000) == 0x80000000) {
                rdData = append(rdData, byte((data32>>8)))
                i = i + 1
            }
            if ((data32 & 0xC0000000) == 0xC0000000) {
                rdData = append(rdData, byte((data32>>8)))
                rdData = append(rdData, byte((data32>>16)))
                i = i + 2
            }

            if ((i%int(FIFORDLENGTH))==0) && (i != int(rdLength-1))  {
                if (rdLength - uint32(i)) > (FIFORDLENGTH - 1) {
                    tmpRdLength = FIFORDLENGTH
                } else {
                    tmpRdLength = ((rdLength-1) % FIFORDLENGTH)
                }
                MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_CONTROL_OFFSET, (0x400 | (tmpRdLength << 16))) //pipe in next read length
            } 
             
        }

        err = Spi_check_tx_complete(spiNumber)
        if err != nil {
            goto SPI_TRANSACTION_END
        }
        err = Spi_check_tx_fifo_empty(spiNumber)
        if err != nil {
            goto SPI_TRANSACTION_END
        }
        
SPI_TRANSACTION_END:
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_CONTROL_OFFSET, 0x00) //turn off spi output
        MateraWriteU32(SpiTable[spiNumber].spiMBaddr + SPI_MUXSEL_OFFSET, 0x01)  //turn mux select to FPGA off
    } else {
        err = fmt.Errorf("ERROR matera_spi_generic_transaction. Spi-%d, STATUS REGISTER, BIT31 (FIFO MODE) NOT SET.  Status Reg = 0x%x\n", spiNumber, data32)
        cli.Printf("e", "%s", err)
    }
SPI_TRANSACTION_END2:

    //For network adapter slots, need to set various enables / muxes to get spi working
    if spiNumber < SPI_FPGA {
        //Disable the spi bus mux that muxes between spi and j2c
        //SpiBusDisableAtFPGA(spiNumber)

        //Enable spi bus on the iob card via the mcp23008 i/o expander
        //SpiBusDisableIOexpander(spiNumber)
    }
    return 
}

