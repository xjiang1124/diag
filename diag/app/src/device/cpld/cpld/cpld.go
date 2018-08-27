package cpld

import (
    "hardware/hwinfo"
    "device/board" 
    "common/cli"
)

// #cgo CFLAGS: -I../../../../../include
// #cgo LDFLAGS: -lspi
// #include <stdlib.h>
// #include "cType.h"
// #include "../../../../../lib/spi_userspace/spi.h"
import "C"
//import "unsafe"


const (
    MDIO_ACC_ENA	= 0x1
    MDIO_RD_ENA		= 0x2
    MDIO_WR_ENA		= 0x4
)

func ReadMdio(phy byte, addr byte) (data uint16, err int) {
    var dataLo, dataHi byte
    t := hwinfo.CpldInfo.(*Naples100info.Naples100Cpld_T)
    WriteReg(byte(t.ESW_MDIO_CTRL_HIGH), addr)
    WriteReg(byte(t.ESW_MDIO_CTRL_LOW), ((phy << 3) | MDIO_RD_ENA | MDIO_ACC_ENA))
    WriteReg(byte(t.ESW_MDIO_CTRL_LOW), 0)
    dataLo, err = ReadReg(byte(t.ESW_MDIO_DATA_LOW))
    dataHi, err = ReadReg(byte(t.ESW_MDIO_DATA_HIGH))
    data = uint16(dataHi << 8 | dataLo)
    
    return
}

func WriteMdio(phy byte, addr byte, data uint16) (err int) {
    t := hwinfo.CpldInfo.(*Naples100info.Naples100Cpld_T)
    WriteReg(byte(t.ESW_MDIO_CTRL_HIGH), addr)
    WriteReg(byte(t.ESW_MDIO_DATA_LOW), byte((data >> 8) & 0xFF))
    WriteReg(byte(t.ESW_MDIO_DATA_HIGH), byte(data & 0xFF))
    WriteReg(byte(t.ESW_MDIO_CTRL_LOW), ((phy << 3) | MDIO_WR_ENA | MDIO_ACC_ENA))
    WriteReg(byte(t.ESW_MDIO_CTRL_LOW), 0)
 
    return
}

func ReadReg(addr byte) (data byte, err int) {
    var retC C.int
    var rd C.uchar
    retC = C.CpldRd(C.uchar(addr), &rd)
    if retC != 0 {
        cli.Println("e", "Failed to read CPLD")
    }
    data = byte(rd)
    err = int(retC)
    return
}

func WriteReg(addr byte, data byte) (err int) {
    var retC C.int
    retC = C.CpldWr(C.uchar(addr), C.uchar(data))
    if retC != 0 {
        cli.Println("e", "Failed to write CPLD")
    }
    err = int(retC)
    return
}

