// Support for Matera FPGA SPI BUS
package materafpga

import (
    //"errors"
    "common/cli"
    "fmt"
    //"os"
    //"bufio"
    //"strings"
    //"strconv"
    "time"
)


type spiDevMap struct{
    fpgaNumber    uint32
    spiMBaddr     uint64
    devname string
}


const SPI_FPGA0_FLASH      uint32 = 0
const SPI_CPU_CPLD         uint32 = 1
const SPI_FPGA1_FLASH      uint32 = 2
const SPI_ELBA0_CPLD       uint32 = 3
const SPI_ELBA1_CPLD       uint32 = 4
const SPI_ELBA2_CPLD       uint32 = 5
const SPI_ELBA3_CPLD       uint32 = 6
const SPI_ELBA4_CPLD       uint32 = 7
const SPI_ELBA5_CPLD       uint32 = 8
const SPI_ELBA6_CPLD       uint32 = 9
const SPI_ELBA7_CPLD       uint32 = 10
const SPI_ELBA0_FLASH      uint32 = 11
const SPI_ELBA1_FLASH      uint32 = 12
const SPI_ELBA2_FLASH      uint32 = 13
const SPI_ELBA3_FLASH      uint32 = 14
const SPI_ELBA4_FLASH      uint32 = 15
const SPI_ELBA5_FLASH      uint32 = 16
const SPI_ELBA6_FLASH      uint32 = 17
const SPI_ELBA7_FLASH      uint32 = 18
const SPI_NUMB_BUSES       uint32 = 19

var SpiTable = map[uint32]spiDevMap {
    SPI_FPGA0_FLASH : { fpgaNumber:0, spiMBaddr:FPGA_S0_SPI_RXDATA_REG , devname:"FPGA0 FLASH", } , 
/*    SPI_CPU_CPLD    : { fpgaNumber:0, spiMBaddr:FPGA0_SPI1_RXDATA_REG , devname:"CPU CPLD",    } , 
    SPI_FPGA1_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI0_RXDATA_REG , devname:"FPGA1 FLASH", } , 
    SPI_ELBA0_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI1_RXDATA_REG , devname:"ELBA0 CPLD",  } , 
    SPI_ELBA1_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI2_RXDATA_REG , devname:"ELBA1 CPLD", } , 
    SPI_ELBA2_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI3_RXDATA_REG , devname:"ELBA2 CPLD", } , 
    SPI_ELBA3_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI4_RXDATA_REG , devname:"ELBA3 CPLD", } , 
    SPI_ELBA4_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI5_RXDATA_REG , devname:"ELBA4 CPLD", } , 
    SPI_ELBA5_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI6_RXDATA_REG , devname:"ELBA5 CPLD", } , 
    SPI_ELBA6_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI7_RXDATA_REG , devname:"ELBA6 CPLD", } , 
    SPI_ELBA7_CPLD :  { fpgaNumber:0, spiMBaddr:FPGA1_SPI8_RXDATA_REG , devname:"ELBA7 CPLD", } , 
    SPI_ELBA0_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI9_RXDATA_REG , devname:"ELBA0 FLASH", } , 
    SPI_ELBA1_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI10_RXDATA_REG , devname:"ELBA1 FLASH", } , 
    SPI_ELBA2_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI11_RXDATA_REG , devname:"ELBA2 FLASH", } , 
    SPI_ELBA3_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI12_RXDATA_REG , devname:"ELBA3 FLASH", } , 
    SPI_ELBA4_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI13_RXDATA_REG , devname:"ELBA4 FLASH", } , 
    SPI_ELBA5_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI14_RXDATA_REG , devname:"ELBA5 FLASH", } , 
    SPI_ELBA6_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI15_RXDATA_REG , devname:"ELBA6 FLASH", } , 
    SPI_ELBA7_FLASH : { fpgaNumber:0, spiMBaddr:FPGA1_SPI16_RXDATA_REG , devname:"ELBA7 FLASH", } , */
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


func Spi_load_register_set(spiNumber uint32) (err error) {
    fmt.Printf(" SPI LOAD REG SET\n")
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
        if ((data32 & 0xC0000000) > 0) {
            //time.Sleep(time.Duration(150) * time.Nanosecond)
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




func matera_spi_generic_transaction(spiNumber uint32, opCode []byte, rdLength uint32) (rdData []byte, err error) {
    var data32 uint32 = 0
    var tmpRdLength uint32 = 0
    var ChkTxDrain uint32 = 0


        if spiNumber >= SPI_NUMB_BUSES {
        err = fmt.Errorf("ERROR matera_spi_generic_transaction. Spi Bus entered = %x.  Max Bus Number=%x    i=%d\n", spiNumber, (SPI_NUMB_BUSES - 1))
        cli.Printf("e", "%s", err)
        return
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
        


    } 
    return 
}

