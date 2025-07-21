package rc22308

import (
    "fmt"
    "common/errType"

    "common/cli"
    "protocol/smbus"
)

const (
    VENDOR_ID     byte = 0x0
    DEVICE_ID     byte = 0x2
    DEVICE_REV    byte = 0x4
    DEVICE_PGM    byte = 0x6
    DEVICE_CNFG   byte = 0x8
    MISC_CNFG     byte = 0xC
    MISC_CTRL     byte = 0x14
    STARTUP_STS   byte = 0x20
    DEVICE_STS    byte = 0x24
)


func readByteData(devName string, offset byte) (Data byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }

    Data, err = smbus.ReadByte(devName, uint64(offset))
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read from %s at offset 0x%02X", devName, offset))
    }
    smbus.Close()
    return
}

func readWordData(devName string, offset byte) (Data uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }

    Data, err = smbus.ReadWord(devName, uint64(offset))
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read from %s at offset 0x%02X", devName, offset))
    }
    smbus.Close()
    return
}

func readBlockData(devName string, offset byte, dataBuf []byte) (bytecnt int, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    // RC22308 uses plain I2C block read/write
    bytecnt, err = smbus.Readi2cBlock(devName, uint64(offset), dataBuf)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read from %s at offset 0x%02X", devName, offset))
    }
    smbus.Close()
    return
}

func writePageRegister(devName string, page byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    // the page register is at offset 0xFC, this 4-byte register must be written
    // in a signel-burst write transaction
    // RC22308 uses plain I2C block read/write
    page_buf := make([]byte, 4)
    page_buf[3] = page
    _, err = smbus.Writei2cBlock(devName, 0xFC, page_buf)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to write to %s at offset 0xFC", devName))
    }
    smbus.Close()
    return
}

// word
func ReadVendorID(devName string) (err int) {
    vendor_id, err := readWordData(devName, VENDOR_ID)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read VENDOR_ID @ 0x%02X for dev %s", VENDOR_ID, devName))
    } else {
        fmt.Printf("VENDOR_ID: 0x%04x\n", vendor_id)
    }
    return
}

//word
func ReadDevID(devName string) (err int) {
    dev_id, err := readWordData(devName, DEVICE_ID)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read DEVICE_ID @ 0x%02X for dev %s", DEVICE_ID, devName))
    } else {
        fmt.Printf("DEVICE_ID: 0x%04x\n", dev_id)
    }
    return
}

//word
func ReadDevRev(devName string) (err int) {
    dev_rev, err := readWordData(devName, DEVICE_REV)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read DEVICE_REV @ 0x%02X for dev %s", DEVICE_REV, devName))
    } else {
        fmt.Printf("DEVICE_REV: 0x%04x\n", dev_rev)
    }
    return
}

//word
func ReadDevPgm(devName string) (err int) {
    dev_pgm, err := readWordData(devName, DEVICE_PGM)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read DEVICE_PGM @ 0x%02X for dev %s", DEVICE_PGM, devName))
    } else {
        fmt.Printf("DEVICE_PGM: 0x%04x\n", dev_pgm)
    }
    return
}

//4 byte
func ReadDevCnfg(devName string) (err int) {
    dev_cnfg := make([]byte, 4)
    err = errType.SUCCESS
    _, err = readBlockData(devName, DEVICE_CNFG, dev_cnfg)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read DEVICE_CNFG @ 0x%02X for dev %s", DEVICE_CNFG, devName))
    } else {
        value := uint32(dev_cnfg[0]) << 24 | uint32(dev_cnfg[1]) << 16 | uint32(dev_cnfg[2]) << 8 | uint32(dev_cnfg[3])
        fmt.Printf("DEVICE_CNFG: 0x%08x\n", value)
    }
    return
}

//byte
func ReadMiscCnfg(devName string) (err int) {
    misc_cnfg, err := readByteData(devName, MISC_CNFG)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read MISC_CNFG @ 0x%02X for dev %s", MISC_CNFG, devName))
    } else {
        fmt.Printf("MISC_CNFG: 0x%02x\n", misc_cnfg)
    }
    return
}

//byte
func ReadMiscCtrl(devName string) (err int) {
    misc_ctrl, err := readByteData(devName, MISC_CTRL)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read MISC_CTRL @ 0x%02X for dev %s", MISC_CTRL, devName))
    } else {
        fmt.Printf("MISC_CTRL: 0x%02x\n", misc_ctrl)
    }
    return
}

//word
func ReadStartupSts(devName string) (err int) {
    startup_sts, err := readWordData(devName, STARTUP_STS)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read STARTUP_STS @ 0x%02X for dev %s", STARTUP_STS, devName))
    } else {
        fmt.Printf("STARTUP_STS: 0x%04x\n", startup_sts)
    }
    return
}

//4 byte
func ReadDevSts(devName string) (err int) {
    dev_sts := make([]byte, 4)
    err = errType.SUCCESS
    _, err = readBlockData(devName, DEVICE_STS, dev_sts)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read DEVICE_STS @ 0x%02X for dev %s", DEVICE_STS, devName))
    } else {
        value := uint32(dev_sts[0]) << 24 | uint32(dev_sts[1]) << 16 | uint32(dev_sts[2]) << 8 | uint32(dev_sts[3])
        fmt.Printf("DEVICE_STS: 0x%08x\n", value)
    }
    return
}

func DispStatus(devName string) (err int) {
    err = writePageRegister(devName, 0x0)
    if err != errType.SUCCESS {
        return
    }
    ReadVendorID(devName)
    ReadDevID(devName)
    ReadDevRev(devName)
    ReadDevPgm(devName)
    ReadDevCnfg(devName)
    ReadMiscCnfg(devName)
    ReadMiscCtrl(devName)
    ReadStartupSts(devName)
    ReadDevSts(devName)
    return
}
