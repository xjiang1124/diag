// Support for fpga spi to cpld designware i2c code
package materafpga

import (
    //"common/cli"
    "fmt"
    //"time"
)

const DW_REG_READ     uint8 = 0x0B
const DW_REG_WRITE    uint8 = 0x02
const DW_MAX_CHANNEL  uint8 = 4
const DW_CHANNEL      uint8 = 3

/*************************************************************
* 
* Read a dw register 
*  
*************************************************************/ 
func DW_readReg(spiNumber uint32, channel uint8, reg uint8) (data32 uint32, err error) {
    rd_data := []byte{}
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, DW_REG_READ)
    spi_cmd = append(spi_cmd, reg)
    spi_cmd = append(spi_cmd, channel)

    rd_data , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2SMBUS, spi_cmd, 5) 
    if err != nil {
        return
    }

    if len(rd_data) != 5 {
        err = fmt.Errorf("ERROR: Length of read data from dw module is not 5 bytes.  Read Lenght=%d\n", len(rd_data))
        fmt.Printf("%v", err)
        return
    }

    data32 = uint32(rd_data[1])
    data32 = data32 | (uint32(rd_data[2])<<8)
    data32 = data32 | (uint32(rd_data[3])<<16)
    data32 = data32 | (uint32(rd_data[4])<<24)

    return
}


/*************************************************************
* 
* Write a single spi-2-i2c controller register
* 
*************************************************************/ 
func DW_writeReg(spiNumber uint32, channel uint8, reg uint8, data32 uint32) (err error) {
    spi_cmd := []byte{}
    spi_cmd = append(spi_cmd, DW_REG_WRITE)
    spi_cmd = append(spi_cmd, reg)
    spi_cmd = append(spi_cmd, channel)
    spi_cmd = append(spi_cmd, uint8(data32 & 0xFF))
    spi_cmd = append(spi_cmd, uint8(((data32>>8) & 0xFF)))
    spi_cmd = append(spi_cmd, uint8(((data32>>16) & 0xFF)))
    spi_cmd = append(spi_cmd, uint8(((data32>>24) & 0xFF)))
    spi_cmd = append(spi_cmd, 0x00)
    _ , err = matera_spi_generic_transaction(spiNumber, SPI_TRGT_DEVICE_SPI2SMBUS, spi_cmd, 0) 
    if err != nil {
        return
    }

    return
}


/*************************************************************
* 
* Dump the DW register set for a channel
*  
*************************************************************/ 
func DW_regDump(spiNumber uint32, channel uint8) (err error) {
    var data32 uint32 = 0

    fmt.Printf("MATERA FPGA REGISTER DUMP---\n")
    for _, entry := range(DW_ALL_REGISTERS) {

        data32, err = DW_readReg(spiNumber, channel, entry.Address) 
        if err != nil {
            return
        }
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }
    fmt.Printf("\n");

    return
}

func DW_enable(spiNumber uint32, channel uint8, enable bool) (err error) {
    var ena uint32 = 0
    if enable == true {
        ena = 1
    }
    err = DW_writeReg(spiNumber, channel, DW_IC_ENABLE, ena)
    if err != nil {
        return
    }
    return
}


func DW_enable_and_wait(spiNumber uint32, channel uint8, enable bool) (err error) {
    var ena, data32 uint32
    var timeout int = 100

    if enable == true {
        ena = 1
    }

    err = DW_writeReg(spiNumber, channel, DW_IC_ENABLE, ena)
    if err != nil {
        return
    }

    for i:=0; i<timeout; i++ {
        data32, err = DW_readReg(spiNumber, channel, DW_IC_ENABLE_STATUS)
        if err != nil {
            return
        }
        if (data32 & 0x1) == ena {
            break
        }

        if i == (timeout-2) {
            err = fmt.Errorf("ERROR: Timed our waiting for enable/disable. DW ENABLE STATUS = %d.  Epxected %d\n", data32, ena)
            fmt.Printf("%v", err)
            return
        }
    }

    return
}


func i2c_dw_disable(spiNumber uint32, channel uint8) (err error) {

    //Disable controller
    err = DW_enable_and_wait(spiNumber, channel, false) 
    if err != nil {
        return
    }

    // Disable all interupts 
    err = DW_writeReg(spiNumber, channel, DW_IC_INTR_MASK, 0x00000000)
    if err != nil {
        return
    }
    _ , err = DW_readReg(spiNumber, channel, DW_IC_CLR_INTR)
    if err != nil {
        return
    }

    return
}


func DW_scl_hcnt(ic_clk uint32, tSYMBOL uint32, tf uint32, cond int, offset uint32) (val uint32) {
    /*
     * DesignWare I2C core doesn't seem to have solid strategy to meet
     * the tHD;STA timing spec.  Configuring _HCNT based on tHIGH spec
     * will result in violation of the tHD;STA spec.
     */
    if cond > 0 {
            /*
             * Conditional expression:
             *
             *   IC_[FS]S_SCL_HCNT + (1+4+3) >= IC_CLK * tHIGH
             *
             * This is based on the DW manuals, and represents an ideal
             * configuration.  The resulting I2C bus speed will be
             * faster than any of the others.
             *
             * If your hardware is free from tHD;STA issue, try this one.
             */
            val = (ic_clk * tSYMBOL + 500000) / 1000000 - 8 + offset
    } else {
            /*
             * Conditional expression:
             *
             *   IC_[FS]S_SCL_HCNT + 3 >= IC_CLK * (tHD;STA + tf)
             *
             * This is just experimental rule; the tHD;STA period turned
             * out to be proportinal to (_HCNT + 3).  With this setting,
             * we could meet both tHIGH and tHD;STA timing specs.
             *
             * If unsure, you'd better to take this alternative.
             *
             * The reason why we need to take into account "tf" here,
             * is the same as described in i2c_dw_scl_lcnt().
             */
            val = (ic_clk * (tSYMBOL + tf) + 500000) / 1000000 - 3 + offset
    }
    return
}

func DW_scl_lcnt(ic_clk uint32, tLOW uint32, tf uint32, offset uint32) (val uint32) {
    /*
     * Conditional expression:
     *
     *   IC_[FS]S_SCL_LCNT + 1 >= IC_CLK * (tLOW + tf)
     *
     * DW I2C core starts counting the SCL CNTs for the LOW period
     * of the SCL clock (tLOW) as soon as it pulls the SCL line.
     * In order to meet the tLOW timing spec, we need to take into
     * account the fall time of SCL signal (tf).  Default tf value
     * should be 0.3 us, for safety.
     */
    val = ((ic_clk * (tLOW + tf) + 500000) / 1000000) - 1 + offset
    return
}



/*************************************************************
* 
* Dump the DW register set for a channel
*  
*************************************************************/ 
func DW_Init(spiNumber uint32, channel uint8, i2cAddr uint8) (err error) {
    var data32 uint32 = 0
    //var addr64 uint32 = 0
    var clock uint32 = (100000 / 1000)

    // Disable the device controller to be able set TAR 
    err = i2c_dw_disable(spiNumber, channel) 
    if err != nil {
        return
    }

    hcnt := DW_scl_hcnt(clock,
                        4000,   /* tHD;STA = tHIGH = 4.0 us */
                        300,
                        0,	/* 0: DW default, 1: Ideal */
                        0);	/* No offset */
    lcnt := DW_scl_lcnt(clock,
                        4700,   /* tLOW = 4.7 us */
                        300,
                        0);     /* No offset */

    err = DW_writeReg(spiNumber, channel, DW_IC_SS_SCL_HCNT, hcnt)
    if err != nil {
        return
    }
    err = DW_writeReg(spiNumber, channel, DW_IC_SS_SCL_LCNT, lcnt)
    if err != nil {
        return
    }


    // Set high speed mode SCL HCNT / LCNT here if we ever run in high speed mode
    // Since we are hooked to an EEPROM, this seems unlikely
     

    data32 = (IC_CON_MASTER_MODE | IC_CON_SPD_STANDARD | IC_CON_RESTART_EN | IC_CON_SLV_DISABLED)
    err = DW_writeReg(spiNumber, channel, DW_IC_CON, data32)
    if err != nil {
        return
    }

    /* Set RX fifo threshold level.
     * Setting it to zero automatically triggers interrupt
     * RX_FULL whenever there is data received.
     */
    err = DW_writeReg(spiNumber, channel, DW_IC_RX_TL, 0x00)
    if err != nil {
        return
    }

    /* Set TX fifo threshold level.
     * TX_EMPTY interrupt is triggered only when the
     * TX FIFO is truly empty. So that we can let
     * the controller do the transfers for longer period
     * before we need to fill the FIFO again. This may
     * cause some pauses during transfers, but this keeps
     * the device from interrupting often.
    */
    err = DW_writeReg(spiNumber, channel, DW_IC_TX_TL, 0x00)
    if err != nil {
        return
    }


    data32 , err = DW_readReg(spiNumber, channel, DW_IC_TAR)
    if err != nil {
        return
    }
    //MASK OUT ADDR BITS[9:0]
    data32 = data32 & 0xFFFFFC00

    //MASK OUT 10-BIT MODE (BIT12)
    data32 = data32 & 0xFFFFEFFF

    //Set the target Address
    data32 = data32 | uint32(i2cAddr)

    err = DW_writeReg(spiNumber, channel, DW_IC_TAR, data32)
    if err != nil {
        return
    }

    // Enable the adapter 
    DW_enable(spiNumber, channel, true)

    // Clear and enable interrupts
    _ , err = DW_readReg(spiNumber, channel, DW_IC_CLR_INTR)
    if err != nil {
        return
    }
    err = DW_writeReg(spiNumber, channel, DW_IC_INTR_MASK, DW_IC_INTR_MASTER_MASK)
    if err != nil {
        return
    }

    return
}
