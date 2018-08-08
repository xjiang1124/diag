package cpld

import (
    "hardware/hwinfo"
    "device/board" 
)

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
    data = 1
    return
}

func WriteReg(addr byte, data byte) (err int) {
    return
}

