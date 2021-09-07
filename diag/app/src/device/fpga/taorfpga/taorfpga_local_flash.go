/* 
 Generating the image  4m42.349644611s  time   //CLK=1, 8 byte read   50us delay to get read data...   all flash
 File fastread.hex generated

 */

package taorfpga

import (
    "fmt"
    "os"
    "bufio"
    "strings"
    "time"
)

const GOLDFW = "primary"
const MAINFW = "secondary"
const ALLFLASH = "allflash"


/*
 * Description of a single Erase region
 */
type flash_region struct {
  offset            uint32
  region_size       uint32
  number_of_sectors  uint32
  sector_size        uint32
} 
//MICRON = //16777216 addresses bytes (128Mb), 256 64K sectors
var flag_region_info flash_region

const STS_REG_BUSY  uint32 = 0x01
const STS_REG_WE    uint32 = 0x02
const STS_REG_BP0   uint32 = 0x04
const STS_REG_BP1   uint32 = 0x08
const STS_REG_BP2   uint32 = 0x10
const STS_REG_TBP   uint32 = 0x20
const STS_REG_SP    uint32 = 0x40
const STS_REG_SRP   uint32 = 0x80

//delays are in us
const WRITE_SR_DEALY        int = 1500
const PAGE_WR_DELAY         int = 1800 
const SUBSECTOR_ERASE_DELAY int = 400000
const SECTOR_ERASE_DELAY    int = 1000000
const CHIP_ERASE_DELAY      int = 1000000

const FLASH_SECTOR_SIZE    uint32 = 0x10000




/*
const D1_CFG_FLASH_CTRL_REG        uint64 = 0x200   0
const D1_CFG_FLASH_BAUD_RATE_REG   uint64 = 0x204   1   
const D1_CFG_FLASH_CS_DELAY_REG    uint64 = 0x208   2
const D1_CFG_FLASH_READ_CAPTURE_REG uint64 = 0x20c  3
const D1_CFG_FLASH_PROTOCOL_REG    uint64 = 0x210   4
const D1_CFG_FLASH_READ_INST_REG   uint64 = 0x214   5
const D1_CFG_FLASH_WRITE_INST_REG  uint64 = 0x218   6
const D1_CFG_FLASH_CMD_SET_REG     uint64 = 0x21c   7
const D1_CFG_FLASH_CMD_CTRL_REG    uint64 = 0x220   8
const D1_CFG_FLASH_CMD_ADDR_REG    uint64 = 0x224   9
const D1_CFG_FLASH_WDATA0_REG      uint64 = 0x228   A
const D1_CFG_FLASH_WDATA1_REG      uint64 = 0x22c   B
const D1_CFG_FLASH_RDATA0_REG      uint64 = 0x230   C
const D1_CFG_FLASH_RDATA1_REG      uint64 = 0x234   D
*/

//func FlashInitInfo() {
func init () {
    //16777216 addresses (128Mb), 256 erasable sectors respectively.  Sector Size = 64K  SubSector Size = 4K
    flag_region_info.region_size = uint32(0x1000000)  //16MB - 128Mb
    flag_region_info.sector_size = FLASH_SECTOR_SIZE
    flag_region_info.number_of_sectors = flag_region_info.region_size / flag_region_info.sector_size
    flag_region_info.offset = 0
}

func AddrDecipher(region string) (addr uint32, maxSize uint32, err error) {

    if region == GOLDFW {
        addr = 0x00
        maxSize = 0x800000
    } else if region == MAINFW {
        addr = 0x800000
        maxSize = 0x800000
    } else if region == ALLFLASH {
        addr = 0x00
        maxSize = 0x1000000
    } else {
        err = fmt.Errorf(" ERROR.  Flash Partition is invalid.  You entered %s.  It needs to be primary, secondary, or allflash\n", region)
        fmt.Printf("%s", err)
        return

    }
    return
}


func FlashGenerateImageFromFlash(region string, filename string) (err error) {
    var addr, maxSize uint32
    var rd_data64 uint64 = 0
    var i int = 0
    flashData := []byte{}

    addr, maxSize, err =  AddrDecipher(region) 
    if err != nil {
        return
    }

    f, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
     }

    defer f.Close()


    for i=int(addr); i<int(addr + maxSize); i = i+8 {
        if (i%0x20000) == 0 {
            fmt.Printf("%.08x\n", uint32(i))
        }
        rd_data64, err = FlashReadEightBytes(uint32(i)) 
        if err != nil {
            fmt.Printf(" ERROR: Flash Read Failed\n")
            return
        }
        flashData = append(flashData, byte(rd_data64 & 0xff) )
        flashData = append(flashData, byte((rd_data64 & 0xff00)>>8) )
        flashData = append(flashData, byte((rd_data64 & 0xff0000)>>16) )
        flashData = append(flashData, byte((rd_data64 & 0xff000000)>>24) )
        flashData = append(flashData, byte((rd_data64 & 0xff00000000)>>32) )
        flashData = append(flashData, byte((rd_data64 & 0xff0000000000)>>40) )
        flashData = append(flashData, byte((rd_data64 & 0xff000000000000)>>48) )
        flashData = append(flashData, byte((rd_data64 & 0xff00000000000000)>>56) )
    }

    f.WriteString(string(flashData[:]))
    return
}

func swap(data uint8) (data8 uint8) {
    var i, j uint8 
    for i = 0; i < 8; i++ {
	j = 7-i;
	data8 |= ((data >> j) & 0x1) << i;
    }
    return
}

func FlashBitSwapImage(infile string, outfile string) (err error) {
    inF_Data  := []byte{}
    inF, err := os.Open(infile)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", infile, err)
        return
    }
    outF, err := os.OpenFile(outfile, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", outfile, err)
        return
    }
    defer func() { 
        inF.Close()
        outF.Close()
    } ()

    scanner := bufio.NewScanner(inF)
    scanner.Split(bufio.ScanBytes)

    for scanner.Scan() {
        b := scanner.Bytes()
        data8 := swap(b[0])
        inF_Data = append(inF_Data, data8)
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        return
    }

    outF.WriteString(string(inF_Data[:]))

    return
}

func FlashWriteImage(region string, filename string) (err error) {
    var i int = 0
    var addr, maxSize uint32
    var data64 uint64
    var blank_data uint64 = 0xFFFFFFFFFFFFFFFF
    var skipped_writes int = 0
    var data8  uint8
    data := []byte{}

    addr, maxSize, err =  AddrDecipher(region) 
    if err != nil {
        return
    }

    if (addr % flag_region_info.sector_size) != 0 {
        fmt.Printf(" ERROR.  Address must be 64K aligned.  You entered addr\n", addr)
        return
    }
    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    fmt.Printf(" Writing Image %s starting at addr=0x%x\n", filename, addr)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    if strings.Contains(filename, "rpd")==true || strings.Contains(filename, "RPD")==true {
        fmt.Printf(" RPD FILE:  BIT SWAP ENABLED\n")
    } else {
        fmt.Printf(" BIN FILE:  BIT SWAP DISABLED\n")
    }

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        if strings.Contains(filename, "rpd")==true || strings.Contains(filename, "RPD")==true {
            data8 = swap(b[0])
            data = append(data, data8)
        } else {
            data = append(data, b[0])
        }
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        return
    }
    if len(data) > int(maxSize) {
        err = fmt.Errorf(" ERROR.  File Size is greater than flash programmable region size.  Bytes Scanned from file=%d.  Flash region size=%d\n", len(data), maxSize)
        fmt.Printf("%s", err)
        return
    }
    if len(data) % 8 != 0 {
        err = fmt.Errorf(" ERROR.  File Size must be a multiple of 8 (i.e. 8388608, 4194304, etc)\n")
        fmt.Printf("%s", err)
        return
    }

    //Disable software WP in the status register
    if region == GOLDFW {
        err = FlashWriteStatusReg(0x00)   //Clear the software lock 
        if err != nil {
            return
        }
        time.Sleep(time.Duration(50) * time.Millisecond)  
    } 
    

    fmt.Printf(" INFO: Flash Start Addr=0x%.06x\n", addr)
    fmt.Printf(" Erasing/Programming each Sector")
    for i=0;i<len(data); i+=8 {

        if (uint32(i) % flag_region_info.sector_size) == 0 {
            //fmt.Printf("0x%x  ", uint32(i) + addr)
            fmt.Printf(".")
            err = FlashEraseSector((uint32(i) + addr))
            if err != nil {
                return
            }
        }
        data64 = data64 + uint64(data[i])
        data64 = data64 + uint64(data[i + 1])<<8
        data64 = data64 + uint64(data[i + 2])<<16
        data64 = data64 + uint64(data[i + 3])<<24
        data64 = data64 + uint64(data[i + 4])<<32
        data64 = data64 + uint64(data[i + 5])<<40
        data64 = data64 + uint64(data[i + 6])<<48
        data64 = data64 + uint64(data[i + 7])<<56
        if data64 != blank_data {
            err = FlashWriteEightBytes(data64, (uint32(i) + addr) )
            if err != nil {
                return
            }
        } else {
            skipped_writes++
        }
        data64 = 0
        
    }



    fmt.Printf("\n")
    fmt.Printf(" Skipped writes = %d... bytes=0x%x\n", skipped_writes, (skipped_writes * 8))

    //if region == GOLDFW {
    //    fmt.Printf(" Enabling software controlled flash write protect\n")
    //    err = FlashWriteStatusReg(0x60)   //Lock bottom half, sectors[127:0].   bytes[7fffff:0]
    //    if err != nil {
    //        return
    //    }
    //} 
     
    return
}


func FlashVerifyImage(region string, filename string) (err error) {
    var i int = 0
    var addr, maxSize uint32
    var rd_data64 uint64
    var wr_data64 uint64 
    var data8  uint8
    data := []byte{}

    addr, maxSize, err =  AddrDecipher(region) 
    if err != nil {
        return
    }

    if (addr % flag_region_info.sector_size) != 0 {
        err = fmt.Errorf(" ERROR.  Address must be 64K aligned.  You entered addr\n", addr)
        fmt.Printf("%s", err)
        return
    }

    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    fmt.Printf(" Verifying Image %s starting at addr=0x%x\n", filename, addr)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        if strings.Contains(filename, "rpd")==true || strings.Contains(filename, "RPD")==true {
            data8 = swap(b[0])
            data = append(data, data8)
        } else {
            data = append(data, b[0])
        }
    }
    if err = scanner.Err(); err != nil {
        fmt.Println(err)
        return
    }
    if len(data) > int(maxSize) {
        err = fmt.Errorf(" ERROR.  File Size is greater than flash programmable region size.  Bytes Scanned from file=%d.  Flash region size=%d\n", len(data), maxSize)
        fmt.Printf("%s", err)
        return
    }

    for i=0;i<len(data); i+=8 {

        if (uint32(i) % flag_region_info.sector_size) == 0 {
            fmt.Printf(".")
        }
        rd_data64, err = FlashReadEightBytes((uint32(i) + addr)) 
        if err != nil {
            err = fmt.Errorf(" ERROR: Flash Read Failed\n")
            fmt.Printf("%s", err)
            return
        }
        wr_data64 = wr_data64 + uint64(data[i])
        wr_data64 = wr_data64 + uint64(data[i + 1])<<8
        wr_data64 = wr_data64 + uint64(data[i + 2])<<16
        wr_data64 = wr_data64 + uint64(data[i + 3])<<24
        wr_data64 = wr_data64 + uint64(data[i + 4])<<32
        wr_data64 = wr_data64 + uint64(data[i + 5])<<40
        wr_data64 = wr_data64 + uint64(data[i + 6])<<48
        wr_data64 = wr_data64 + uint64(data[i + 7])<<56

        if rd_data64 != wr_data64 {
            err = fmt.Errorf(" Error: Flash Miscompare at address 0x%x:  WR 0x%.08x%.08x   RD 0x%.08x%.08x\n", (uint32(i) + addr), uint32(wr_data64>>32), uint32(wr_data64 & 0xFFFFFFFF), uint32(rd_data64>>32), uint32(rd_data64 & 0xFFFFFFFF))
            fmt.Printf("%s", err)
            fmt.Printf("Verification failed\n")
            return
        }
        wr_data64 = 0
    }
    fmt.Printf("\nVerification passed\n")
    return
}


//Check if the flash is busy before executing erase or write
func FlashPollBusyMicroSec(timeout_ms int) (sr_reg uint32, err int) {
    var errGo error
    sr_reg, _ = FlashReadStatusReg() 
    for i:=0; i<timeout_ms; i++ {
        sr_reg, errGo = FlashReadStatusReg() 
        if errGo != nil {
            fmt.Printf("[ERROR] FlashPollBusyMicroSec-> Read Status Failed\n")
            err = 1
            return
        }
        if sr_reg & STS_REG_BUSY != STS_REG_BUSY {
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)
    } 
    err = 1
    return 
}

//Check if the flash is busy before executing erase or write
func FlashPollBusy(timeout_ms int) (sr_reg uint32, err int) {
    var errGo error
    sr_reg, _ = FlashReadStatusReg() 
    for i:=0; i<timeout_ms; i++ {
        sr_reg, errGo = FlashReadStatusReg() 
        if errGo != nil {
            fmt.Printf("[ERROR] FlashPollBusyMicroSec-> Read Status Failed\n")
            err = 1
            return
        }
        if sr_reg & STS_REG_BUSY != STS_REG_BUSY {
            return
        }
        time.Sleep(time.Duration(1) * time.Millisecond)
    } 
    err = 1
    return 
}

func FlashCheckWriteEnable() (err error) {
    var sr_reg uint32
    for i:=0; i< 500; i++ {
        sr_reg, _ := FlashReadStatusReg() 
        if sr_reg & STS_REG_WE == STS_REG_WE {
            return
        }
        time.Sleep(time.Duration(1) * time.Millisecond)  //Sleep 1ms
    }
    err = fmt.Errorf("ERROR: FlashCheckWriteEnable.  Write Enable is not set: Status Reg=%.02x\n", sr_reg)
    fmt.Printf("%s", err)
    return 
}

func FlashPollCmdComplete() (err error) {
    var data32 uint32
    for i:=0; i< 500; i++ {
        data32, _ = TaorReadU32(1, D1_CFG_FLASH_CMD_CTRL_REG)
        if (data32 & 0x1) == 0 {
            //fmt.Printf(" %d", i)
            return
        }
        time.Sleep(time.Duration(1) * time.Millisecond)  //Sleep 1ms
    }
    err = fmt.Errorf("ERROR: Polling flash cmd complete failed.  CMD REG=%x\n", data32)
    fmt.Printf("%s", err)
    return 
}


func FlashPollCmdCompleteForReads() (err error) {
    var data32 uint32

    data32, _ = TaorReadU32(1, D1_CFG_FLASH_CMD_CTRL_REG)
    if data32 & 0x80000000 == 0x80000000 {    //fpga 800b-07272021 added the ability to pull for read done instead of using arbitrary delays
                                              //if bit31 in CMD_CTRL_REG is set, it supports polling BIT1
        for i:=0; i< 1000; i++ {
            data32, _ = TaorReadU32(1, D1_CFG_FLASH_CMD_CTRL_REG)
            if data32 & 0x2 != 0x2 {
                return
            }
        }
    } else { 
        for i:=0; i< 500; i++ {
            data32, _ = TaorReadU32(1, D1_CFG_FLASH_CMD_CTRL_REG)
            if (data32 & 0x1) == 0 {
                //fmt.Printf(" %d", i)
                time.Sleep(time.Duration(50) * time.Microsecond)  
                return
            }
            time.Sleep(time.Duration(1) * time.Millisecond)  //Sleep 1ms
        }
    }
    err = fmt.Errorf("ERROR: Polling flash cmd complete failed.  CMD REG=%x\n", data32)
    fmt.Printf("%s", err)
    return 
}


func FlashReadDevIDReg() (data32 uint32, err error) {
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00000389F)   //Opcode 0x9F ,  READ BIT[11],  RD SIZE[12:15] = 3 BYTES
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 
    
    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    /*
    for i:=0; i< 500; i++ {
        data32, _ := TaorReadU32(1, D1_CFG_FLASH_RDATA0_REG)
        if data32 != 0xFF {
            fmt.Printf("I=%d  data32=%x\n", i, data32)
            break
        }
        time.Sleep(time.Duration(1) * time.Microsecond)  //Sleep 1us
    }*/

    //data32, err = TaorReadU32(1, D1_CFG_FLASH_RDATA0_REG)
    time.Sleep(time.Duration(25) * time.Microsecond)  
    data32, err = TaorReadU32(1, D1_CFG_FLASH_RDATA0_REG)

    return
}


func FlashReadStatusReg() (data32 uint32, err error) {
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00001805)    //Opcode 0x05 ,  READ BIT[11],  RD SIZE[12:15] = 1 BYTE
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 

    if err = FlashPollCmdComplete(); err != nil {
        return
    }
    time.Sleep(time.Duration(100) * time.Microsecond)  

    data32, err = TaorReadU32(1, D1_CFG_FLASH_RDATA0_REG)

    return
}

func FlashWriteStatusReg(data32 uint32) (err error) {

    FlashWriteEnable()
    //err = FlashCheckWriteEnable() 
    //if err != nil {
    //    return
    //}

    err = TaorWriteU32(1, D1_CFG_FLASH_WDATA0_REG, (data32 & 0xFF)) 
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00001001)  //Op Code 0x01, 0 ADDR BYTES[10:8]. WRITE 1 BYTE[12:15]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1)

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    sr_reg, rc := FlashPollBusyMicroSec(WRITE_SR_DEALY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: FlashWriteStatusReg.  Timeout Waiting Write to complete.  Delay = %d.   Status Reg=%.02x\n", WRITE_SR_DEALY, sr_reg)
       fmt.Printf("%s", err)
    }

    return
}

func FlashWriteEnable() (err error) {
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00000006)     //Opcode 0x06
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 
    //Why does Intel have us writing a 1 to write data reg after transaction starts?? Bug on their part?
    //err = TaorWriteU32(1, D1_CFG_FLASH_WDATA0_REG,   0x1) 

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    return
}


//4K Erase
func FlashErase4kSubSector(addr uint32) (err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashEraseSector.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }

    FlashWriteEnable()
    err = FlashCheckWriteEnable() 
    if err != nil {
        return
    }

    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00000320) //Opcode 0x20 ,  3 ADDR BYTES[10:8]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr) 
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    sr_reg, rc := FlashPollBusyMicroSec(SUBSECTOR_ERASE_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: FlashEraseSector.  Timeout Waiting for Secor Erase to Compelte.  Delay = %d.   Status Reg=%.02x\n", SUBSECTOR_ERASE_DELAY, sr_reg)
       fmt.Printf("%s", err)
    }

    return
}

//32K Erase
func FlashEraseHalfSector(addr uint32) (err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashEraseHalfSector.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }

    FlashWriteEnable()
    err = FlashCheckWriteEnable() 
    if err != nil {
        return
    }

    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00000352) //Opcode 0x52 ,  3 ADDR BYTES[10:8]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr) 
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    sr_reg, rc := FlashPollBusyMicroSec(SECTOR_ERASE_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: FlashEraseSector.  Timeout Waiting for Half Sector Erase to Compelte.  Delay = %d.   Status Reg=%.02x\n", SECTOR_ERASE_DELAY, sr_reg)
       fmt.Printf("%s", err)
    }
    return
}

//64K Erase
func FlashEraseSector(addr uint32) (err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashEraseSector.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }

    FlashWriteEnable()
    err = FlashCheckWriteEnable() 
    if err != nil {
        return
    }

    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x000003D8)  //Opcode 0xD8 ,  3 ADDR BYTES[10:8]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr) 
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    sr_reg, rc := FlashPollBusyMicroSec(SECTOR_ERASE_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: FlashEraseSector.  Timeout Waiting for Sector Erase to Compelte.  Delay = %d.   Status Reg=%.02x\n", SECTOR_ERASE_DELAY, sr_reg)
       fmt.Printf("%s", err)
    }
    return
}




func FlashReadByte(addr uint32) (data32 uint32, err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashReadByte.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }

    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00001B03)  //Op Code 0x03, 3 ADDR BYTES[10:8], DATA READ BIT[11], READ 1 BYTE[12:15]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr)
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 

    if err = FlashPollCmdCompleteForReads(); err != nil {
        return
    }
    data32, err = TaorReadU32(1, D1_CFG_FLASH_RDATA0_REG)
    data32 = data32 & 0xFF
    return
}


func FlashReadFourBytes(addr uint32) (data32 uint32, err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashReadFourBytes.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00004B03)  //Op Code 0x03, 3 ADDR BYTES[10:8], DATA READ BIT[11], READ 4 BYTES[12:15]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr)
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 

    if err = FlashPollCmdCompleteForReads(); err != nil {
        return
    }
    data32, err = TaorReadU32(1, D1_CFG_FLASH_RDATA0_REG)
    return
}


func FlashReadEightBytes(addr uint32) (data64 uint64, err error) {
    var data32 uint32
    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashReadFourBytes.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00008B03)  //Op Code 0x03, 3 ADDR BYTES[10:8], DATA READ BIT[11], READ 8 BYTES[12:15]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr)
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1) 

    if err = FlashPollCmdCompleteForReads(); err != nil {
        return
    }
    data32, err = TaorReadU32(1, D1_CFG_FLASH_RDATA0_REG)
    data64 = data64 | uint64(data32)
    data32, err = TaorReadU32(1, D1_CFG_FLASH_RDATA1_REG)
    data64 = data64 | uint64(data32)<<32
    return
}


func FlashWriteByte(data32 uint32, addr uint32) (err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashWriteByte.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }


    FlashWriteEnable()
    //err = FlashCheckWriteEnable() 
    //if err != nil {
    //    return
    //}

    err = TaorWriteU32(1, D1_CFG_FLASH_WDATA0_REG, (data32 & 0xFF)) 
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr)
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00001302)  //Op Code 0x02, 3 ADDR BYTES[10:8]. WRITE 1 BYTE[12:15]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1)

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    sr_reg, rc := FlashPollBusyMicroSec(PAGE_WR_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: FlashEraseSector.  Timeout Waiting for Secor Erase to Compelte.  Delay = %d.   Status Reg=%.02x\n", PAGE_WR_DELAY, sr_reg)
       fmt.Printf("%s", err)
    }

    return
}


func FlashWriteFourBytes(data32 uint32, addr uint32) (err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashWriteFourBytes.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }


    FlashWriteEnable()
    //err = FlashCheckWriteEnable() 
    //if err != nil {
    //    return
    //}

    err = TaorWriteU32(1, D1_CFG_FLASH_WDATA0_REG, data32) 
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr)
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00004302)  //Op Code 0x02, 3 ADDR BYTES[10:8]. WRITE 4 BYTE[12:15]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1)

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    sr_reg, rc := FlashPollBusyMicroSec(PAGE_WR_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: FlashEraseSector.  Timeout Waiting for Secor Erase to Compelte.  Delay = %d.   Status Reg=%.02x\n", PAGE_WR_DELAY, sr_reg)
       fmt.Printf("%s", err)
    }

    return
}

func FlashWriteEightBytes(data64 uint64, addr uint32) (err error) {

    if addr > flag_region_info.region_size {
        err = fmt.Errorf("ERROR: FlashWriteFourBytes.  Address passed (0x%x) is greather than flash size - %x\n", addr, flag_region_info.region_size)
        fmt.Printf("%s", err)
        return
    }


    FlashWriteEnable()
    //err = FlashCheckWriteEnable() 
    //if err != nil {
    //    return
    //}

    err = TaorWriteU32(1, D1_CFG_FLASH_WDATA0_REG, uint32(data64 & 0xFFFFFFFF)) 
    err = TaorWriteU32(1, D1_CFG_FLASH_WDATA1_REG, uint32(data64 >> 32)) 
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_ADDR_REG, addr)
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_SET_REG, 0x00008302)  //Op Code 0x02, 3 ADDR BYTES[10:8]. WRITE 8 BYTE[12:15]
    err = TaorWriteU32(1, D1_CFG_FLASH_CMD_CTRL_REG, 0x1)

    if err = FlashPollCmdComplete(); err != nil {
        return
    }

    sr_reg, rc := FlashPollBusyMicroSec(PAGE_WR_DELAY)
    if rc != 0 {
       err = fmt.Errorf("ERROR: FlashEraseSector.  Timeout Waiting for Secor Erase to Compelte.  Delay = %d.   Status Reg=%.02x\n", PAGE_WR_DELAY, sr_reg)
       fmt.Printf("%s", err)
    }

    return
}





/* 
 
//Register access commands

//Applicable for all flashes

int read_device_id(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x0000489F);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
	return IORD(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xc);
}
int read_status_register(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00001805);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
	return IORD(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xc);
}
int read_flag_status_register(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00001870);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
	return IORD(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xc);
}
void write_enable(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00000006);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xA,1);
}

void enter_4byte_addressing_mode(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x000000B7);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xA,1);
}
void clear_flag_status_register(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00000050);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xA,1);
}
 
 
//for micron flash to enter quad SPI mode
void write_evcr_quad(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00001061);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xA,0x0000005f);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
}
//for micron flash to enter dual SPI mode
void write_evcr_dual(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00001061);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xA,0x0000009f);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
}

//Erase Commands//
void erase_sector_cypress(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x000003D8);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x9,0x00000000);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
}
void erase_sector_micron(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00000420);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x9,0x00000000);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
} 
 
 
//Read Memory Commands

int read_memory(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x4,0x00000000);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x0,0x00000101);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x5,0x00000003);
	return IORD(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_MEM_BASE,0x00000000);
}
int read_memory_3byte(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x4,0x00000000);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x0,0x00000001);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x5,0x00000003);
	return IORD(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_MEM_BASE,0x00000000);
} 
 
 
//Page Program Commands

//4byte addr page program
void write_memory(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x4,0x00000000);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x0,0x00000101);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x6,0x00007002);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_MEM_BASE,0x00000000,0xabcd1234);
}
void write_memory_3byte(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x4,0x00000000);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x0,0x00000001);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x6,0x00000502);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_MEM_BASE,0x00000000,0xabcd1234);
}
 
//Sector Protection Commands 
//Applicable for micron flash only

void write_register_for_sector_unprotect_micron(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00001001);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xA,0x00000000);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
}

//Sector 0 of memory array is protected; (TB-BP3-BP2-BP1-BP0:1-0-0-0-1)
void write_status_register_for_block_protect_micron(){
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x7,0x00001001);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0xA,0x0000007c);
	IOWR(INTEL_GENERIC_SERIAL_FLASH_INTERFACE_TOP_0_AVL_CSR_BASE,0x8,0x1);
} 
*/



