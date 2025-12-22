//I2C is based on OpenCore I2C

package panareafpga

import (
    "fmt"
    "strings"
    "time"
    "common/dcli"
)


type OpenI2C_reg_set struct {
    FPGA_NUMBER     uint32
    PRSCL_LO_REG    uint64
    PRSCL_HI_REG    uint64
    CTRL_REG        uint64
    STAT_REG        uint64
    DATA_REG        uint64  //Handles both TX and RX
    CMD_REG         uint64
    MUX_SEL_REG     uint64
    RST_REG         uint64
    SEM_REG         uint64

    State           uint32
    Error           int
    Bus             uint32
    Mux             uint32
    I2Caddr         uint32
    cur_byte        int

    wrData          []byte
    wrSize          uint32
    wrPointer       uint32
    rdData          []byte
    rdSize          uint32
    rdPointer       uint32
}

var I2Creg OpenI2C_reg_set
var ExecutingScanChain int = 0

var buffer [2048]string
var bufptr int

const I2C_NUMBER_CHANNELS    uint32 = 19

const I2C_CLOCK_PRESCALE_100KHZ uint8 = (0x7C) //124 /* TODO: Verify with HW team */
const I2C_TIMEOUT_US    uint32 = 350

// Control register bits
const OCI2C_CTRL_EN       uint32 = 0x80  // enable
const OCI2C_CTRL_IEN      uint32 = 0x40  // enable interrupts

// Command register bits
const OCI2C_CMD_START_BIT uint32 = 0x80  // generate start condition
const OCI2C_CMD_STOP_BIT  uint32 = 0x40  // generate stop condition
const OCI2C_CMD_READ_BIT  uint32 = 0x20  // read from slave
const OCI2C_CMD_WRITE_BIT uint32 = 0x10  // write to slave
const OCI2C_CMD_NOACK_BIT uint32 = 0x08  // do not acknowledge read
const OCI2C_CMD_IACK_BIT  uint32 = 0x01  // clear pending interrupt

// Status register bits
const OCI2C_STAT_NOACK    uint32 = 0x80  // no acknowledge
const OCI2C_STAT_BUSY     uint32 = 0x40  // bus busy after START
const OCI2C_STAT_ARBLOST  uint32 = 0x20  // arbitration lost
const OCI2C_STAT_TIP      uint32 = 0x02  // transfer in progress
const OCI2C_STAT_INT      uint32 = 0x01  // interrupt pending

// Combo commands
const OCI2C_CMD_START     uint32 = (OCI2C_CMD_START_BIT + OCI2C_CMD_WRITE_BIT + OCI2C_CMD_IACK_BIT)
const OCI2C_CMD_STOP      uint32 = (OCI2C_CMD_STOP_BIT + OCI2C_CMD_IACK_BIT)
const OCI2C_CMD_READ      uint32 = (OCI2C_CMD_READ_BIT + OCI2C_CMD_IACK_BIT)
const OCI2C_CMD_READ_LAST uint32 = (OCI2C_CMD_READ_BIT + OCI2C_CMD_NOACK_BIT + OCI2C_CMD_IACK_BIT)
const OCI2C_CMD_WRITE     uint32 = (OCI2C_CMD_WRITE_BIT + OCI2C_CMD_IACK_BIT)
const OCI2C_CMD_IACK      uint32 = (OCI2C_CMD_IACK_BIT)

// Transfer states
const (
    STATE_PRE_START = iota  // ready to start a new message
    STATE_START             // ready to send a START command
    STATE_DATA              // ready to transfer data
    STATE_READ              // READ command in progress
    STATE_WRITE             // WRITE command in progress
    STATE_STOP              // ready to send STOP
    STATE_DONE              // message sequence complete
    STATE_EXIT              // same as DONE, but without IACK
)

const I2C_WR uint32 = 0x00
const I2C_RD uint32 = 0x01



func unixMicro(t time.Time) int64 {
        return t.Round(time.Millisecond).UnixNano() / int64(time.Nanosecond)
}

func makeTimestampMicro() int64 {
        return unixMicro(time.Now())
}



func TStamp() string {
    m := makeTimestampMicro()
    timeStr := fmt.Sprintln(time.Unix(m/1e3, (m%1e3)*int64(time.Millisecond)/int64(time.Nanosecond)))
    timeStrs := strings.Split(timeStr, " ")

    timeStr = fmt.Sprintf("%-23s", timeStrs[0]+"-"+timeStrs[1])
    return timeStr

}

func buffer_reset_counter() {
    bufptr = 0
    return
}

func buffset(s string) () {
    //time.Now().UnixNano() / int64(time.Microsecond)
    nanos := time.Now().UnixNano()

    time.Unix(0, nanos)
    if bufptr < 1024 {
        buffer[bufptr] = fmt.Sprintln(time.Unix(0, nanos),"    ", s)
        bufptr = bufptr + 1
    }
}
 

func i2cLoadDataSet(bus uint32, mux uint32, i2cAddr uint32, wrSize uint32, wrData []byte, rdSize uint32) (err error) {
    var base uint64 = FPGA_S0_I2C_PRSCL_LO_REG
    I2Creg.FPGA_NUMBER = 0

    if bus >= I2C_NUMBER_CHANNELS {
        err = fmt.Errorf("ERROR: BUS ENTERED IS TO HIGH:  MAX BUS=%d    PASSED BUS=%d\n", I2C_NUMBER_CHANNELS, bus)
        dcli.Printf("e"," %v\n", err)
        return
    }

    //set channel base address
    switch bus {
        case 1:  base = FPGA_S1_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 2:  base = FPGA_S2_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 3:  base = FPGA_S3_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 4:  base = FPGA_S4_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 5:  base = FPGA_S5_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 6:  base = FPGA_S6_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 7:  base = FPGA_S7_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 8:  base = FPGA_S8_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 9: base = FPGA_S9_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 10: base = FPGA_DBG_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 11: base = FPGA_PSU0_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 12: base = FPGA_PSU1_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 13: base = FPGA_PMB_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 14: base = FPGA_IOBR_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 15: base = FPGA_IOBL_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 16: base = FPGA_FPIC_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 17: base = FPGA_ID_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
        case 18: base = FPGA_MCIO_I2C_PRSCL_LO_REG; I2Creg.FPGA_NUMBER = 0
    }


    //Set register addresses
    I2Creg.PRSCL_LO_REG = base
    I2Creg.PRSCL_HI_REG = base + 0x04
    I2Creg.CTRL_REG     = base + 0x08
    I2Creg.DATA_REG     = base + 0x0C
    I2Creg.CMD_REG      = base + 0x10
    I2Creg.STAT_REG     = base + 0x10
    I2Creg.MUX_SEL_REG  = base + 0x14
    I2Creg.RST_REG      = base + 0x18
    I2Creg.SEM_REG      = base + 0x1C

    I2Creg.State = STATE_PRE_START
    I2Creg.Bus = bus  
    I2Creg.Mux = mux 
    I2Creg.I2Caddr = i2cAddr

    I2Creg.wrData = nil
    I2Creg.wrData = append(I2Creg.wrData, wrData...)
    I2Creg.wrSize = wrSize
    I2Creg.rdData = nil
    I2Creg.rdSize = rdSize

    I2Creg.wrPointer = 0
    I2Creg.rdPointer = 0
    I2Creg.cur_byte = 0
    I2Creg.Error = 0

    bufptr = 0

    s := fmt.Sprintf("Bus=%x Mux=%x I2cAddr=%x Reg Base Offset=%x WrSize=%x RdSize=%x\n", I2Creg.Bus, I2Creg.Mux, I2Creg.I2Caddr, base, I2Creg.wrSize, I2Creg.rdSize)
    buffset(s)
    
    return
}

func oci2c_get_buff_read_data() (rdData []byte, err error) {
    rdData = append(rdData, I2Creg.rdData...)
    return
}


func i2cMuxSet(mux uint32) (err error) { 
    WriteU32(I2Creg.MUX_SEL_REG, mux)
    return
}

func I2cResetController2(bus int, freq uint8) (err error) { 
    wrData := []byte{}
    var retries int = 25

    if err = i2cLoadDataSet(uint32(bus), 0x00, 0x00, 0x00, wrData, 0x00); err != nil {  //Setup I2C Struct.  Return if this fails.. Catastrophic Failure
        dcli.Printf("e"," Error: I2C Load Data Set Failed\n")
        return
    }
    WriteU32(I2Creg.RST_REG, 0x0D)
    for i:=0; i<retries;i++ {
        data32, _ := ReadU32(I2Creg.RST_REG)
        if (data32 == 0x00) {
            oci2c_enable(freq, 0x00)   //Enable
            break
        }
        time.Sleep(time.Duration(1) * time.Millisecond)
        if i == (retries - 1) {
            err = fmt.Errorf("ERROR I2C BUS %d RESET NOT CLEARING = %x\n", bus, data32) 
            dcli.Printf("e"," %v\n", err)
        }
    }
    return
}

func i2cResetController() (err error) { 
    var retries int = 25
    WriteU32(I2Creg.RST_REG, 0x0D)
    for i:=0; i<retries;i++ {
        data32, _ := ReadU32(I2Creg.CTRL_REG)
        if (data32 == 0x00) {
            break
        }
        time.Sleep(time.Duration(1) * time.Millisecond)
        if i == (retries - 1) {
            err = fmt.Errorf("ERROR I2C BUS %d RESET NOT CLEARING = %x\n", I2Creg.Bus, data32) 
            dcli.Printf("e"," %v\n", err)
        }
    }
    return
}

// Check if an I2C controller is enabled
func oci2c_is_enabled() (enabled bool, err error) {
    enabled = false
    data32, _ := ReadU32(I2Creg.CTRL_REG)
    if data32 & OCI2C_CTRL_EN == OCI2C_CTRL_EN {
        enabled = true
    }
    return 
}

// Disable an I2C controller
func oci2c_disable() (enabled bool, err error) {
    // Disable the controller
    data32, _ := ReadU32(I2Creg.CTRL_REG)
    data32 = (data32 &  ^(OCI2C_CTRL_EN | OCI2C_CTRL_IEN))
    WriteU32(I2Creg.CTRL_REG, data32)
    return
}
 
func oci2c_enable(prelowVal uint8, prehiVal uint8) (err error) { 

    WriteU32(I2Creg.CTRL_REG, 0x00) // disable i2c 
    WriteU32(I2Creg.CMD_REG, 0x00)  // clear any data in cmd

    WriteU32(I2Creg.PRSCL_LO_REG, uint32(prelowVal))
    WriteU32(I2Creg.PRSCL_HI_REG, uint32(prehiVal))

    // Make sure the interrupt flag is clear and enable the controller
    WriteU32(I2Creg.CMD_REG, OCI2C_CMD_IACK)

    WriteU32(I2Creg.CTRL_REG, OCI2C_CTRL_EN)

    time.Sleep(time.Duration(2) * time.Millisecond)  //Sleep 2ms
    return
}; 


func I2c_access(bus uint32, mux uint32, i2cAddr uint32, wrSize uint32, wrData []byte, rdSize uint32)(readData []byte, err error) {

        if err = i2cLoadDataSet(bus, mux, i2cAddr, wrSize, wrData, rdSize); err != nil {  //Setup I2C Struct.  Return if this fails.. Catastrophic Failure
            dcli.Printf("e"," Error: I2C Load Data Set Failed\n")
            return
        }

        //oci2c_disable()
        //i2cResetController()

        i2cMuxSet(I2Creg.Mux)   //Set the Mux Select

        isEna, _ := oci2c_is_enabled()
        if isEna == false {
            oci2c_enable(I2C_CLOCK_PRESCALE_100KHZ, 0x00)   //Enable
        } 

        //fmt.Printf(" Process I2C")
        err = oci2c_process()                           //Process I2C Transaction
        if err == nil {
            if rdSize > 0 {
                readData, _ = oci2c_get_buff_read_data()
            }
        } else {
            if ExecutingScanChain == 0 {
                dcli.Println("e"," Error: I2C Transaction Failed bus/mux/decimal addr", bus, mux, i2cAddr, "  wrsize/data=", wrSize, wrData," rdsize=", rdSize)
            }
        }
        return
}


func oci2c_cmd(cmd uint32, data byte) (err error) {
    WriteU32(I2Creg.DATA_REG, uint32(data)) 
    WriteU32(I2Creg.CMD_REG, cmd) 
    s := fmt.Sprintf(" send command 0x%02X with data 0x%02X", cmd, data)
    buffset(s)
    return
}


// Actions for state PRE_START - Handle special ops, if any, or else start a
// new message
func oci2c_pre_start() (err error) {
    I2Creg.State = STATE_START;
    return
}


// Actions for state START - ready to start a new message
func oci2c_start() (err error) {
    var data byte = 0

    data = byte(I2Creg.I2Caddr << 1)
    if I2Creg.wrSize == 0 {
        data = data | 0x01
    }
    oci2c_cmd(OCI2C_CMD_START, data);
    

    I2Creg.State = STATE_DATA;
    return
}


// Actions for state DATA - ready to transfer a data byte
func oci2c_data() (err error) {
    var stat uint32

    stat, err = ReadU32(I2Creg.STAT_REG)

    if stat & OCI2C_STAT_ARBLOST == OCI2C_STAT_ARBLOST  {
        // We lost the bus so abort the transfer.  The register definition says
        // the following about this bit:
        //
        //   This bit is set when the core lost arbitration.  Arbitration is
        //   lost when a STOP signal is detected, but not requested, or when
        //   master drives SDA high, but SDA is low.
        //
        err = fmt.Errorf("ERROR I2C BUS ARBITRATION LOST.  Stat Reg = %x\n", stat)
        //fmt.Printf("%s", err)
        buffset(err.Error())
        I2Creg.Error = -1;
        I2Creg.State = STATE_STOP;
    } else if I2Creg.cur_byte == 0 && (stat & OCI2C_STAT_NOACK == OCI2C_STAT_NOACK) {
        err = fmt.Errorf("ERROR NOACK Error on START.  Stat Reg = %x\n", stat)
        //fmt.Printf("%s", err)
        buffset(err.Error())
        I2Creg.Error = -2
        I2Creg.State = STATE_STOP
    } else if (I2Creg.wrSize > 0) && (I2Creg.cur_byte >= int(I2Creg.wrSize)) {   //write finished
         I2Creg.wrSize = 0
         I2Creg.cur_byte = 0
         if I2Creg.rdSize > 0 {
             I2Creg.State = STATE_PRE_START
         } else {
             I2Creg.State = STATE_STOP
         }
    } else if (I2Creg.wrSize > 0) {   //Write 
        // Send a WRITE command and advance to the next state
        oci2c_cmd(OCI2C_CMD_WRITE, byte(I2Creg.wrData[I2Creg.wrPointer]))
        I2Creg.State = STATE_WRITE
    } else if (I2Creg.wrSize == 0) && (I2Creg.cur_byte >= int(I2Creg.rdSize)) {   //read finished
        I2Creg.State = STATE_STOP;
    }  else if (I2Creg.wrSize == 0) && (I2Creg.rdSize > 0) { // read 
        // Send a READ command and advance to the next state
        var cmd uint32
        if I2Creg.cur_byte < int(I2Creg.rdSize -1) {
            cmd = OCI2C_CMD_READ
        } else {
            cmd = OCI2C_CMD_READ_LAST
        }
        oci2c_cmd(cmd, 0);
        I2Creg.State = STATE_READ;
     
    } 
    return
}



// Actions for state WRITE - waiting for device to acknowledge data
func oci2c_write() (err error) {
    var stat uint32

    // Check for acknowledgement of last WRITE
    stat, err = ReadU32(I2Creg.STAT_REG)
    if stat & OCI2C_STAT_NOACK == OCI2C_STAT_NOACK {
        err = fmt.Errorf("ERROR NOACK Error on WRITE.  Stat Reg = %x\n", stat)
        //fmt.Printf("%s", err)
        buffset(err.Error())
        I2Creg.Error = -1
        I2Creg.State = STATE_STOP
    } else {
        I2Creg.wrPointer = I2Creg.wrPointer+1
        I2Creg.cur_byte = I2Creg.cur_byte +1
        I2Creg.State = STATE_DATA
    }
    return
}

// Actions for state READ - waiting to receive data from device
func oci2c_read() (err error) {
    var data uint32

    data, err = ReadU32(I2Creg.DATA_REG)
    s := fmt.Sprintf(" RD DATA = %x", data)
    buffset(s)
    I2Creg.rdData = append(I2Creg.rdData, byte(data & 0xff))
    I2Creg.cur_byte = I2Creg.cur_byte +1
    I2Creg.rdPointer = I2Creg.rdPointer +1
    I2Creg.State = STATE_DATA;
    return
}


// Actions for state STOP - ready to send STOP command for previous sequence
func oci2c_stop() (err error) {
    // Send a STOP command
    oci2c_cmd(OCI2C_CMD_STOP, 0)

    // If is no error and there are more messages to process, go to the START
    // state.  Otherwise, this was the STOP to terminate the last message.
    //if I2Creg.Error == 0  && i2c->cur_msg < i2c->num_msg) {
    //    I2Creg.State = STATE_START;
    //} else {
        I2Creg.State = STATE_DONE
    //}
    return
}

// Actions for state DONE - transfer done
func oci2c_done() (err error) {
    // Acknowledge any outstanding interrupt
    oci2c_cmd(OCI2C_CMD_IACK, 0)
    I2Creg.State = STATE_DONE
    return
}


// Wait for an I2C transaction to complete.  For interrupt-driven mode, this
// will wait until the entire message chain is complete.  For polling mode,
// this will wait until the current command is complete.  Returns non-zero if
// the timeout expired.
func oci2c_wait() (err error) {
    var data32, i uint32 = 0, 0

    s := fmt.Sprintf(" oci2c_wait")
    buffset(s)
    for i=0; i<I2C_TIMEOUT_US; i++ {
        data32, err = ReadU32(I2Creg.STAT_REG)
        s = fmt.Sprintf(" DEBUGr TIP:status reg = %.02x.  TO=%d    i=%d", data32, I2C_TIMEOUT_US, i) 
        buffset(s)
        if data32 & OCI2C_STAT_TIP != OCI2C_STAT_TIP {
            break
        }
        time.Sleep(time.Duration(1) * time.Microsecond)
    } 

    if i >= I2C_TIMEOUT_US   { 
        err = fmt.Errorf("ERROR I2C write byte timeout waiting for TIP:status reg = %.02x.  TO=%d    i=%d\n", data32, I2C_TIMEOUT_US, i)
        //fmt.Printf("%s", err)
        buffset(err.Error())
        I2Creg.Error = -3
    } 
    s = fmt.Sprintf(" DEBUGr TIP:status reg = %.02x.  TO=%d    i=%d", data32, I2C_TIMEOUT_US, i) 
    buffset(s)
    return
}


func oci2c_process() (err error) {

    var data32 uint32 = 0
    //u8 stat;

    //if (i2c->errno == ETIMEDOUT || i2c->errno == EPROTO) {
    //    i2c->state = STATE_STOP;
    //    oci2c_stop(i2c);
    //    oci2c_done(i2c);
    //    return 0;
   // }

    defer func() {
        data32, _ = ReadU32(FPGA_SCRATCH_2_REG)
        if data32 == 0xDEBDEB99 {
            for i:=0; i<bufptr; i++ {
                fmt.Printf("%s", buffer[i]) 
            }
        }
        //Did we get a failure somewhere?  Set err return code
        if I2Creg.Error < 0 {
            err = fmt.Errorf("ERROR I2C Access Failed\n")
            //fmt.Printf("%s\n", err.Error())
            if data32 == 0xDEBDEB9A {
                for i:=0; i<bufptr; i++ {
                    fmt.Printf("%s", buffer[i]) 
                }
            }
        }
    } ()




    // Do actions for current state
    for 
    {
        for 
        {

            // Run the state machine until there is a transaction in progress that we
            // need to wait for.
            data32, err = ReadU32(I2Creg.STAT_REG)
            if data32 & OCI2C_STAT_TIP == OCI2C_STAT_TIP {
                break;
            } else {
                s := fmt.Sprintf(" TIP CLEAR")
                buffset(s)
            }
            switch (I2Creg.State) {
                case STATE_PRE_START:
                    s := fmt.Sprintf(" PreSTART")
                    buffset(s)
                    oci2c_pre_start();
                case STATE_START:
                    s := fmt.Sprintf(" START")
                    buffset(s)
                    oci2c_start();
                case STATE_DATA:
                    s := fmt.Sprintf(" Data")
                    buffset(s)
                    oci2c_data();
                case STATE_READ:
                    s := fmt.Sprintf(" Read")
                    buffset(s)
                    oci2c_read();
                case STATE_WRITE:
                    s := fmt.Sprintf(" Write")
                    buffset(s)
                    oci2c_write();
                case STATE_STOP:
                    s := fmt.Sprintf(" Stop")
                    buffset(s)
                    oci2c_stop();
                case STATE_DONE:
                    s := fmt.Sprintf(" Done")
                    buffset(s)
                    oci2c_done();
                    return
                case STATE_EXIT:
                    s := fmt.Sprintf(" Exit")
                    buffset(s)
                    return
            }
        } //for loop

        oci2c_wait()
        if I2Creg.Error < 0 {
            return
        }

    } //for loop

    return
}

