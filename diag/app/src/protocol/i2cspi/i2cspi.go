package i2cspi

import (
    "fmt"

    "common/dcli"
    "common/errType"
    "common/misc"
    "protocol/i2cPtcl"
)

const (
    CONFIG   = 1
    IO       = 2
    CLR_INTR = 3
)

var pageSize = 256

// SPI commands
var cmdMuxSel    = []byte{0x01, 0x03}
var cmdDpramLpbk = []byte{0x01, 0xFF}
var cmdUnlock    = []byte{0x02, 0x01, 0x6C}
var cmdLock      = []byte{0x02, 0x01, 0xEC}
var cmdWrEn      = []byte{0x02, 0x06}
var cmdSwRst     = []byte{0x02, 0x06, 0x99}
var cmdWr        = []byte{0x02, 0x12}
var cmdRd        = []byte{0x02, 0x13}
var cmdRdSts     = []byte{0x02, 0x05, 0xFF}
var cmdRdFlag    = []byte{0x02, 0x70, 0xFF}
var cmdEn4BAddr  = []byte{0x02, 0xB7}
var cmdErase     = []byte{0x02, 0xDC}

var cmdRdId      []byte
var cmdRd256B    []byte

// Test struct
type Test struct {
    bus     uint32
    devAddr byte
}

//=========================================
func init() {
    // Initialize read commands which needs multiple of FFs
    cmdRdId =   make([]byte, 22)
    cmdRd256B = make([]byte, 258)

    cmdRdId[0] = 0x02
    cmdRdId[1] = 0x9E
    for i := 2; i < 22; i++ {
        cmdRdId[i] = 0xFF
    }

    cmdRd256B[0] = 0x02
    cmdRd256B[1] = 0x13
    for i := 2; i < 258; i++ {
        cmdRd256B[i] = 0xFF
    }
}

func addrToSlice(addr uint32) (addrSlice []byte) {
    addrSlice = make([]byte, 4)
    for i:=0; i<4; i++ {
        addrSlice[3-i] = byte((addr >> uint32(i*8)) & 0xFF)
    }
    return
}

func Open(devName string, bus uint32, devAddr byte) (err int) {
    err = i2cPtcl.Open(devName, bus, devAddr)
    return
}

func Close() {
    i2cPtcl.Close()
}

func BusWrite(datas ...[]byte) (err int) {
    var writeData []byte

    for _, data := range datas {
        writeData = misc.ByteSliceAppend(writeData, data)
    }
    err = i2cPtcl.Write(writeData)
    return
}

func BusRead(numBytes uint64) (data []byte, err int) {
    data, err = i2cPtcl.Read(numBytes)
    return
}

func SpiWritePage(addr uint32, data []byte) (err int) {
    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage: failed to write cmdWrEn")
        return
    }

    addrSlice := addrToSlice(addr)

    // Data have to be page size
    if len(data) != pageSize {
        dcli.Println("e", "SpiWritePage: Data has to be 256-byte page size! Got", len(data))
        err = errType.FAIL
        return
    }

    err = BusWrite(cmdWr, addrSlice, data)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage: BusWrite failed!")
        return
    }

    _, err = checkWrDone()
    return
}

func SpiReadPage(addr uint32) (data []byte, err int) {
    addrSlice := addrToSlice(addr)

    dataDummy := make([]byte, pageSize)
    for i:=0; i< len(dataDummy); i++ {
        dataDummy[i] = 0xFF
    }

    err = BusWrite(cmdRd, addrSlice, dataDummy)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadPage failed!")
        return
    }

    // 256 + 5 bytes
    data, err = BusRead(261)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadPage failed!")
    }

    data = data[5:]

    return
}

func SpiEraseBlock(addr uint32) (err int) {
    addrSlice := addrToSlice(addr)

    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiEraseBlock: failed to write cmdWrEn")
        return
    }

    err = BusWrite(cmdErase, addrSlice)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiEraseBlock: failed to write cmdErase")
        return
    }

    _, err = checkWrDone()
    return
}

func SpiReadFlagSts() (data byte, err int) {
    err = BusWrite(cmdRdFlag)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadFlagSts: failed to write cmdRdFlag")
        return
    }

    retData, err := BusRead(2)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadFlagSts: failed to BusRead")
        return
    }

    data = retData[1]
    return
}

func SpiReadSts() (data byte, err int) {
    err = BusWrite(cmdRdSts)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadFlagSts: failed to write cmdRdFlag")
        return
    }

    retData, err := BusRead(2)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadFlagSts: failed to BusRead")
        return
    }

    data = retData[1]
    return
}

func ReadId() (retData []byte, err int) {
    err = BusWrite(cmdRdId)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadId failed!")
        return
    }

    data, err := BusRead(21)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadId failed!")
        return
    }

    retData = data[1:]

    return
}

/**
 * Check Write/program/erase progress
 * return: false: operation in progress; true: operation done
 */
func checkWrDone() (wrDone bool, err int) {
    //misc.SleepInSec(1)
    var flag byte
    var sts byte
    maxIte := 10
    wrDone = false
    for i:=0; i<maxIte; i++ {
        flag, err = SpiReadFlagSts()
        if err != errType.SUCCESS {
            dcli.Println("e", "Failed to read flag status")
            return
        }

        sts, err = SpiReadFlagSts()
        if err != errType.SUCCESS {
            dcli.Println("e", "Failed to read status register")
            return
        }
        sts1 := sts & 1

        if (flag == 0x81) && (sts1 == 1) {
            dcli.Println("i", "Write page done")
            wrDone = true
            break
        }
        misc.SleepInUSec(5000)
        dcli.Printf("i", "Flag Status Post: 0x%02x; Status Post: 0x%02x\n", flag, sts)
    }

    if wrDone == false {
        err = errType.FAIL
        dcli.Println("e", "TestWriteReadPage: Write page time out")
    }
    return
}

func NewTest(bus uint32, devAddr byte) *Test {
    var t Test
    t.bus = bus
    t.devAddr = devAddr
    return &t

}

func (t *Test) TestDpramLpbk() (err int) {
    // Generate 256B random data
    data := misc.GenRandByteSlice(pageSize)

    err = BusWrite(cmdDpramLpbk)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to set DPRAM loopback")
        return
    }

    err = SpiWritePage(0x01020304, data)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage failed")
        return
    }
    return

    dataRd, err := BusRead(uint64(pageSize+5))
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage failed")
        return
    }
    //dcli.Println("d", dataRd)

    // Check read back data
    dcli.Println("i", "Address Bytes")
    for i:=0; i<4; i++ {
        dcli.Printf("i", "Addr[%d] = 0x%02x\n", i, dataRd[i+1])
    }

    for i:=0; i<pageSize; i++ {
        if data[i] != dataRd[i+5] {
            dcli.Printf("e", "Mismatch! data[%d]=0x%02x; dataRd[%d]=0x%02x\n", i, data[i], i, dataRd[i+5])
            err = errType.FAIL
        }
    }

    if err == errType.SUCCESS {
        dcli.Println("i", "Read back verification passed")
    }

    return
}

func (t *Test) TestReadPage(addr uint32) (err int) {
    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadPage failed!")
        return
    }

    // Read QSPI page
    data, err := SpiReadPage(addr)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadPage failed!")
        return
    }

    // Print out data
    dcli.Println("i", "=== Printing Read Data ===")
    for i:=0; i<len(data); i++ {
        fmt.Printf("0x%02X ", data[i])
        if (i+1)%16 == 0 {
            fmt.Printf("\n")
        }
    }
    fmt.Printf("\n")

    return
}

func (t *Test) TestEraseBlock(addr uint32) (err int) {
    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable MUX SEL")
        return
    }

    // Enable writing to the status register and unlock the lock the sector 1023:0
    err = BusWrite(cmdUnlock)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to unlock")
        return
    }

    err = SpiEraseBlock(addr)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to erase block")
        return
    }

    // Ddisable writing to the status register and 
    // lock the lock the sector 1023:0 and enable write protect pin 
    err = BusWrite(cmdLock)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to disable write")
        return
    }

    return
}

func (t *Test) TestWritePage(addr uint32) (err int) {
    // Generate 256B random data
    data := misc.GenRandByteSlice(pageSize)

    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable MUX SEL")
        return
    }

    // Enable writing to the status register and unlock the lock the sector 1023:0
    err = BusWrite(cmdUnlock)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to unlock")
        return
    }

    flag, err := SpiReadFlagSts()
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to read flag status")
        return
    }
    dcli.Printf("i", "Flag Status Pre: 0x%02x\n", flag)

    err = SpiWritePage(addr, data)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to write page")
        return
    }

    // Read QSPI page
    //dataRd, err := SpiReadPage(addr)
    //if err != errType.SUCCESS {
    //    dcli.Println("e", "TestWriteReadPage: Failed to enable read page")
    //    return
    //}

    //for i:=0; i<pageSize; i++ {
    //    if data[i] != dataRd[i] {
    //        dcli.Printf("e", "Mismatch! data[%d]=0x%02x; dataRd[%d]=0x%02x\n", i, data[i], i, dataRd[i])
    //        err = errType.FAIL
    //    }
    //}

    // Ddisable writing to the status register and 
    // lock the lock the sector 1023:0 and enable write protect pin 
    err1 := BusWrite(cmdLock)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to disable write")
        err = err1
        return
    }

    return
}

func (t *Test) TestReadId() (err int) {
    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadPage failed!")
        return
    }

    // QSPI reset
    err = BusWrite(cmdSwRst)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadPage failed!")
        return
    }

    // Read QSPI ID
    data, err := ReadId()
    err = BusWrite(cmdRdId)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadPage failed!")
        return
    }

    // Print ID
    dcli.Println("i", "=== SPI ID ===")
    for i:=0; i<20; i++ {
        fmt.Printf("0x%02X ", data[i])
    }
    fmt.Printf("\n")

    return
}

