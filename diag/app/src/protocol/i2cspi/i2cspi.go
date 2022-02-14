package i2cspi

import (
    "bufio"
    "encoding/binary"
    "fmt"
    "os"

    "common/dcli"
    "common/errType"
    "common/misc"
    "protocol/i2cPtcl"
)

const (
    CONFIG   = 1
    IO       = 2
    CLR_INTR = 3

    STS_UNLOCK = 0x20
    STS_LOCK   = 0xEC
)

const (
    MFG_ID_MICRON = 0x20
    MFG_ID_MXIC   = 0xC2
)


var pageSize = 0x100
var sectorSize = 0x10000

// SPI commands
var cmdMuxSel    = []byte{0x01, 0x03}
var cmdDpramLpbk = []byte{0x01, 0xFF}
var cmdUnlock    = []byte{0x02, 0x01, 0x20}
var cmdLock      = []byte{0x02, 0x01, 0xEC}
var cmdWrEn      = []byte{0x02, 0x06}
var cmdSwRst     = []byte{0x02, 0x99}
var cmdWr        = []byte{0x02, 0x12}
var cmdRd        = []byte{0x02, 0x13}

var cmdRdSts     = []byte{0x02, 0x05, 0xFF}
var cmdRdFlag    = []byte{0x02, 0x70, 0xFF}
var cmdRdNonVolCfg = []byte{0x02, 0xB5, 0xFF, 0xFF}
var cmdRdVolCfg  = []byte{0x02, 0x85, 0xFF}
var cmdClrFlag   = []byte{0x02, 0x50}

var cmdEn4BAddr  = []byte{0x02, 0xB7}
var cmdErase     = []byte{0x02, 0xDC}

var cmdRdId      []byte
var cmdRd256B    []byte

type spiStsT struct {
    name     string
    cmd      []byte
    numBytes int
}

var spiSts = []spiStsT {
    spiStsT {
        "Status Register",
        cmdRdSts,
        1,
    },
    spiStsT {
        "Flag Status Register",
        cmdRdFlag,
        1,
    },
    spiStsT {
        "Non-Volatile Configuration Register",
        cmdRdNonVolCfg,
        2,
    },
    spiStsT {
        "Volatile Configuration Register",
        cmdRdVolCfg,
        1,
    },
}

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
    cmdRdId[1] = 0x9F
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

func printHexData(data []byte) {
    for i:=0; i<len(data); i++ {
        fmt.Printf("0x%02X ", data[i])
        if (i+1)%16 == 0 {
            fmt.Printf("\n")
        }
    }
    fmt.Printf("\n")

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

/**
 * Send a write command and wait for status to clear
 */
func SpiWrCmdWait(cmd []byte, waitInUSec int) (err int) {
    err = BusWrite(cmd)
    if err != errType.SUCCESS {
        dcli.Println("e", "BusWrite failed!")
        return
    }

    err = checkWrDone(waitInUSec)
    return
}

/**
 * Send a read command and return bytes required
 */
func SpiRdCmd(cmd []byte, numBytes int) (data []byte, err int) {
    err = BusWrite(cmd)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadFlagSts: failed to write cmdRdFlag")
        return
    }

    data, err = BusRead(uint64(numBytes+1))
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiReadFlagSts: failed to BusRead")
        return
    }

    data = data[1:numBytes+1]
    return

}

func SpiWritePage(addr uint32, data []byte) (err int) {
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

    err = checkWrDone(200)
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

func SpiEraseSector(addr uint32) (err int) {
    addrSlice := addrToSlice(addr)

    err = BusWrite(cmdErase, addrSlice)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiEraseSector: failed to write cmdErase")
        return
    }

    err = checkWrDone(150000)
    return
}

func SpiWriteStatusReg(data byte) (err int) {
    wrData := make([]byte, 3)
    wrData[0] = 0x02
    wrData[1] = 0x01
    wrData[2] = data

    err = SpiWrCmdWait(wrData, 8000)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to write status register")
        return
    }
    return
}

func SpiReadFlagSts() (data byte, err int) {
    rdData, err := SpiRdCmd(cmdRdFlag, 1)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to read Flag Status")
        return
    }

    data = rdData[0]
    return
}

func SpiReadSts() (data byte, err int) {
    rdData, err := SpiRdCmd(cmdRdSts, 1)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to read Status register")
        return
    }

    data = rdData[0]
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
func checkWrDone(waitInUSec int) (err int) {
    var flag byte
    var sts byte
    var i int

    maxIte := 20
    wrDone := false

    for i=0; i<maxIte; i++ {
        misc.SleepInUSec(waitInUSec)

        //flag, err = SpiReadFlagSts()
        //if err != errType.SUCCESS {
        //    dcli.Println("e", "Failed to read flag status")
        //    return
        //}

        sts, err = SpiReadSts()
        if err != errType.SUCCESS {
            dcli.Println("e", "Failed to read status register")
            return
        }
        sts1 := sts & 1

        //if (flag == 0x81) {
        //if (flag == 0x81) && (sts1 == 0) {
        if (sts1 == 0) {
            wrDone = true
            break
        }
        //dcli.Printf("i", "Flag Status: 0x%02x; Status: 0x%02x\n", flag, sts)
    }

    if wrDone == false {
        err = errType.FAIL
        dcli.Println("e", "Prog/Erase time out")
        dcli.Printf("i", "Ite: %d; Flag Status Post: 0x%02x; Status Post: 0x%02x\n", i, flag, sts)
    }
    //dcli.Printf("i", "Flag Status Post: 0x%02x; Status Post: 0x%02x\n", flag, sts)
    return
}

func SpiShowAllSts() (err int) {
    var data []byte
    var spists spiStsT
    for i:=0; i<len(spiSts); i++ {
        spists = spiSts[i]
        data, err = SpiRdCmd(spists.cmd, spists.numBytes)
        if err != errType.SUCCESS {
            dcli.Printf("e", "Failed to read status: %s\n", spists.name)
            break
        }

        dcli.Printf("i", "=== %s ===\n", spists.name)
        for j:=0; j<len(data); j++ {
            dcli.Printf("i", "REG[%d] = 0x%x\n", j, data[j])
        }
    }
    return
}

/**
 * Read binary file
 */
func ReadFileBin(filename string) (data []byte, err int) {
    file, errgo := os.Open(filename)
    if errgo != nil {
        dcli.Println("e", errgo)
        return nil, errType.FAIL
    }
    defer file.Close()

    stats, statsErr := file.Stat()
    if statsErr != nil {
        dcli.Println("e", statsErr)
        return nil, errType.FAIL
    }

    var size int64 = stats.Size()
    data = make([]byte, size)

    bufr := bufio.NewReader(file)
    _, errgo = bufr.Read(data)
    if errgo != nil {
        dcli.Println("e", errgo)
        return nil, errType.FAIL
    }

    return data, err
}


/**
 * Read write binary file
 */
func WriteFileBin(filename string, data []byte) (err int) {
    file, errgo := os.OpenFile(filename, os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0755)
    if errgo != nil {
        dcli.Println("e", errgo)
        return errType.FAIL
    }
    defer file.Close()

    for i:=0; i<len(data); i++ {
        errgo := binary.Write(file, binary.LittleEndian, data[i])
        if errgo != nil {
            dcli.Println("e", errgo)
            err = errType.FAIL
            return
        }
    }

    return
}

/**
 * SPI program
 */
func SpiProgram(imageType string, filename string, startAddr uint32) (err int) {
    var sizeLimit uint32

    switch imageType {
    case "GOLDFW":
        startAddr = 0x00400000
        sizeLimit = 0x03c00000
    case "TESTFW":
        startAddr = 0x00000000
        //sizeLimit = 0x00080000 // 512KB
        sizeLimit = 0x00100000 // 1MB
    default:
        dcli.Println("e", "Unsupport image type:", imageType)
        err = errType.FAIL
        return
    }

    // Address has to be 64KB aligned for now
    if startAddr != startAddr&(^uint32(0xFFFF)) {
        dcli.Printf("e", "Start address must be 64KB aligned! Got 0x%x\n", startAddr)
        err = errType.FAIL
        return
    }

    dcli.Printf("i", "startAddr=0x%x, sizeLimit=0x%x\n", startAddr, sizeLimit)

    // Check file size
    fi, errgo := os.Stat(filename);
    if errgo != nil {
        dcli.Println("e", errgo)
        return errType.FAIL
    }
    fileSize := fi.Size()
    if uint32(fileSize) > sizeLimit {
        dcli.Println("e", "Invalid file size:", fileSize, "File size limite:", sizeLimit)
        err = errType.FAIL
        return
    }

    // Read data from file
    data, err := ReadFileBin(filename)
    if err != errType.SUCCESS {
        return
    }
    dcli.Printf("i", "File size: 0x%x\n", len(data))

    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable MUX SEL")
        return
    }

    // Clear status bits in Flag Status Register
    err = BusWrite(cmdClrFlag)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable MUX SEL")
        return
    }

    // SPI reset
    //err = BusWrite(cmdSwRst)
    //if err != errType.SUCCESS {
    //    dcli.Println("e", "cmdSwRst Failed")
    //    return
    //}

    // SPI WR enable
    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiEraseSector: failed to write cmdWrEn")
        return
    }
    misc.SleepInUSec(10)

    // Enable writing to the status register and unlock the lock the sector 1023:0
    err = SpiWriteStatusReg(STS_UNLOCK)
    if err != errType.SUCCESS {
        return
    }

    // Enable 4-byte addressing
    err = BusWrite(cmdEn4BAddr)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to enable 4-byte addressing")
        return
    }

    // Erase flash before write
    for addr:= startAddr; addr<startAddr+uint32(fileSize); addr=addr+uint32(sectorSize) {
        err = BusWrite(cmdWrEn)
        if err != errType.SUCCESS {
            dcli.Println("e", "cmdWrEn failed")
            return
        }
        misc.SleepInUSec(10)

        if addr%0x100000 == 0 {
            dcli.Printf("i", "Erasing addr 0x%08x\n", addr)
        }
        err = SpiEraseSector(addr)
        if err != errType.SUCCESS {
            dcli.Printf("e", "Abort erase at address 0x%08x\n", addr)
            return
        }
    }

    dcli.Println("i", "Done erasing. Startging programming")
    // Program image by page
    for addr:= startAddr; addr<startAddr+uint32(fileSize); addr=addr+uint32(pageSize) {
        err = BusWrite(cmdWrEn)
        if err != errType.SUCCESS {
            dcli.Println("e", "cmdWrEn failed")
            return
        }
        misc.SleepInUSec(10)

        if addr%0x100000 == 0 {
            dcli.Printf("i", "Programming addr 0x%08x\n", addr)
        }
        err = SpiWritePage(addr, data[addr-startAddr:addr-startAddr+uint32(pageSize)])
        if err != errType.SUCCESS {
            dcli.Printf("e", "Abort page write at address 0x%08x\n", addr)
            return
        }
    }

    // SPI WR enable
    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiEraseSector: failed to write cmdWrEn")
        return
    }
    misc.SleepInUSec(10)

    // Enable writing to the status register and unlock the lock the sector 1023:0
    err = SpiWriteStatusReg(STS_LOCK)
    if err != errType.SUCCESS {
        return
    }

    dcli.Println("i", "Image program done")
    return
}


/**
 * SPI dump flash content to a data file
 */
func SpiDump(imageType string, filename string, startAddr uint32, fileSize uint32) (err int) {
    var sizeLimit uint32
    var rdData []byte

    switch imageType {
    case "GOLDFW":
        startAddr = 0x00400000
        sizeLimit = 0x03c00000
    case "TESTFW":
        startAddr = 0x00000000
        //sizeLimit = 0x00080000 // 512KB
        sizeLimit = 0x00100000 // 1MB
    default:
        dcli.Println("e", "Unsupport image type:", imageType)
        err = errType.FAIL
        return
    }

    // Address has to be 64KB aligned for now
    if startAddr != startAddr&(^uint32(0xFFFF)) {
        dcli.Printf("e", "Start address must be 64KB aligned! Got 0x%x\n", startAddr)
        err = errType.FAIL
        return
    }

    dcli.Printf("i", "startAddr=0x%x, sizeLimit=0x%x\n", startAddr, sizeLimit)

    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiDump: Failed to enable MUX SEL")
        return
    }

    // Enable 4-byte addressing
    err = BusWrite(cmdEn4BAddr)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to enable 4-byte addressing")
        return
    }

    // read by page
    for addr:= startAddr; addr<startAddr+uint32(fileSize); addr=addr+uint32(pageSize) {
        if addr%0x100000 == 0 {
            dcli.Printf("i", "Reading addr 0x%08x\n", addr)
        }

        rdData, err = SpiReadPage(addr)
        if err != errType.SUCCESS {
            dcli.Printf("e", "Abort page write at address 0x%08x\n", addr)
            return
        }
        err = WriteFileBin(filename, rdData)
        if err != errType.SUCCESS {
            return
        }
    }

    dcli.Printf("i", "Flash image dump to %s\n", filename)
    return
}


//======================================================
// Test suite
func NewTest(bus uint32, devAddr byte) *Test {
    var t Test
    t.bus = bus
    t.devAddr = devAddr
    return &t

}

func (t *Test) TestDpramLpbk() (err int) {
    // Generate 256B random data
    cmd := make([]byte, 1)
    cmd[0] = 0x02
    data := misc.GenRandByteSlice(pageSize)
    //data := make([]byte, 256)

    err = BusWrite(cmdDpramLpbk)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to set DPRAM loopback")
        return
    }

    //err = SpiWritePage(0x01020304, data)
    err = BusWrite(cmd, data)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage failed")
        return
    }

    dataRd, err := BusRead(uint64(pageSize))
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage failed")
        return
    }

    for i:=0; i<pageSize; i++ {
        if data[i] != dataRd[i] {
            dcli.Printf("e", "Mismatch! data[%d]=0x%02x; dataRd[%d]=0x%02x\n", i, data[i], i, dataRd[i+5])
            err = errType.FAIL
        }
    }

    if err == errType.SUCCESS {
        dcli.Println("i", "Read back verification passed")
    }

    return
}

func (t *Test) TestDpramLpbkRead(numBytes int) (err int) {
    data, err := BusRead(uint64(numBytes))
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage failed")
        return
    }

    dcli.Println("i", "=== Read Data ===")
    printHexData(data)

    return
}

func (t *Test) TestDpramLpbkWrite(numBytes int) (err int) {
    // Generate 256B random data
    cmd := make([]byte, 1)
    cmd[0] = 0x02
    data := misc.GenRandByteSlice(numBytes)

    err = BusWrite(cmdDpramLpbk)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to set DPRAM loopback")
        return
    }

    //err = SpiWritePage(0x01020304, data)
    err = BusWrite(cmd, data)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage failed")
        return
    }

    dcli.Println("i", "=== Write Data ===")
    printHexData(data)
    return
}

func (t *Test) TestReadPage(addr uint32) (err int) {
    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "ReadPage failed!")
        return
    }

    // Enable 4-byte addressing
    err = BusWrite(cmdEn4BAddr)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to unlock")
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
    printHexData(data)
    return
}

func (t *Test) TestEraseSector(addr uint32) (err int) {
    // Enable MUX SEL and disable WP pin
    err = BusWrite(cmdMuxSel)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable MUX SEL")
        return
    }

    // Clear status bits in Flag Status Register
    err = BusWrite(cmdClrFlag)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable MUX SEL")
        return
    }

    // Enable 4-byte addressing
    err = BusWrite(cmdEn4BAddr)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to unlock")
        return
    }

    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiEraseSector: failed to write cmdWrEn")
        return
    }

    // Enable writing to the status register and unlock the lock the sector 1023:0
    err = SpiWriteStatusReg(STS_UNLOCK)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to unlock")
        return
    }

    SpiShowAllSts()

    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiEraseSector: failed to write cmdWrEn")
        return
    }

    err = SpiEraseSector(addr)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to erase block")
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

    // Clear status bits in Flag Status Register
    err = BusWrite(cmdClrFlag)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable MUX SEL")
        return
    }

    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage: failed to write cmdWrEn")
        return
    }

    // Enable writing to the status register and unlock the lock the sector 1023:0
    err = SpiWriteStatusReg(STS_UNLOCK)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to unlock")
        return
    }

    // Enable 4-byte addressing
    err = BusWrite(cmdEn4BAddr)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to unlock")
        return
    }

    err = BusWrite(cmdWrEn)
    if err != errType.SUCCESS {
        dcli.Println("e", "SpiWritePage: failed to write cmdWrEn")
        return
    }

    err = SpiWritePage(addr, data)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to write page")
        return
    }

    // Read QSPI page
    dataRd, err := SpiReadPage(addr)
    if err != errType.SUCCESS {
        dcli.Println("e", "TestWriteReadPage: Failed to enable read page")
        return
    }

    for i:=0; i<pageSize; i++ {
        if data[i] != dataRd[i] {
            dcli.Printf("e", "Mismatch! data[%d]=0x%02x; dataRd[%d]=0x%02x\n", i, data[i], i, dataRd[i])
            err = errType.FAIL
        }
    }
    if err == 0 {
        dcli.Println("i", "Read back verification passed")
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
    //err = BusWrite(cmdSwRst)
    //if err != errType.SUCCESS {
    //    dcli.Println("e", "ReadPage failed!")
    //    return
    //}

    // Read QSPI ID
    data, err := ReadId()
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

/**
 * Show values of all status/configuration registers
 */
func (t *Test) TestShowSts() (err int) {
    err = SpiShowAllSts()
    return
}

