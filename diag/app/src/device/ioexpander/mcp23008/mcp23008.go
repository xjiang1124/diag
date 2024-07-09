package mcp23008

import (
    "fmt"
    "common/errType"

    "common/cli"
    "protocol/smbusNew"
    "hardware/i2cinfo"
)

//MCP23008: I2C
//MCP23S08: SPI
//Reg Data in byte
const (
    //RegName        Offset
    IODIR   uint = 0x00
    IPOL    uint = 0x01
    GPINTEN uint = 0x02
    DEFVAL  uint = 0x03
    INTCON  uint = 0x04
    IOCON   uint = 0x05
    GPPU    uint = 0x06
    INTF    uint = 0x07
    INTCAP  uint = 0x08
    GPIO    uint = 0x09
    OLAT    uint = 0x0A
)

var regName = [...]string {
    IODIR:   "IODIR",
    IPOL:    "IPOL",
    GPINTEN: "GPINTEN",
    DEFVAL:  "DEFVAL",
    INTCON:  "INTCON",
    IOCON:   "IOCON",
    GPPU:    "GPPU",
    INTF:    "INTF",
    INTCAP:  "INTCAP",
    GPIO:    "GPIO",
    OLAT:    "OLAT",
}

func ReadByteSmbus(devName string, offset uint) (Data byte, err int) {
    err = errType.SUCCESS
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
    defer smbusNew.Close()

    Data, err = smbusNew.ReadByte(devName, uint64(offset))
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read from %s at offset 0x%02x", devName, offset))
        return
    }

    return
}

func WriteByteSmbus(devName string, offset uint, val byte) (err int) {
    err = errType.SUCCESS

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
    defer smbusNew.Close()

    err = smbusNew.WriteByte(devName, uint64(offset), val)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write", devName, " at offset", offset, "with value", val)
    }
    return
}


func DispStatus(devName string) (err int) {
    err = errType.SUCCESS
    var data byte
    var errSmbus int

    for r := IODIR; r < OLAT; r++ {
        data, errSmbus = ReadByteSmbus(devName, r)
        if errSmbus != errType.SUCCESS {
            cli.Println("e", fmt.Sprintf("MCP23008: Reg[%s (0x%02x)] reading failed!", regName[r], r))
            err = errSmbus
        }
        cli.Println("i", fmt.Sprintf("MCP23008: Reg[%s (0x%02x)] = 0x%02x", regName[r], r, data))
    }

    return
}

