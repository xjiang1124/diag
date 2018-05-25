package pex8716

import (
    "common/cli"
    "common/misc"
)

func pexLpbkConfig(port byte) (err int) {
    var data uint32
    //dataBuf := make([]byte, REG_WIDTH)
    pattern0 := uint32(0x11223344)
    pattern1 := uint32(0x55667788)
    pattern2 := uint32(0x11223344)
    pattern3 := uint32(0x55667788)

    //clear 0x224 bit10
    data, _ = ReadReg(PHYSICALTEST0, ACC_MODE_TP, port, BYTE_EN_ALL)
    data &= 0xFFFFFBFF
    WriteReg(PHYSICALTEST0, data, ACC_MODE_TP, port, BYTE_EN_ALL)

    //write pattern to register
    WriteReg(TESTPATTERN0, pattern0, ACC_MODE_TP, port, BYTE_EN_ALL)
    WriteReg(TESTPATTERN1, pattern1, ACC_MODE_TP, port, BYTE_EN_ALL)
    WriteReg(TESTPATTERN2, pattern2, ACC_MODE_TP, port, BYTE_EN_ALL)
    WriteReg(TESTPATTERN3, pattern3, ACC_MODE_TP, port, BYTE_EN_ALL)

    //write reg 0x208, set bit[24, 25] 0x10, clear [28, 29]
    data, _ = ReadReg(PORTCONTROL, ACC_MODE_TP, port, BYTE_EN_ALL)
    data &= 0xCEFFFFFF
    data |= 0x2FFFFFFF
    WriteReg(PORTCONTROL, data, ACC_MODE_TP, port, BYTE_EN_ALL)

    //set reg 0x230 port 0 master lpbk
    data, _ = ReadReg(PORTCOMMAND, ACC_MODE_TP, port, BYTE_EN_ALL)
    //dataBuf[0] = 0
    //dataBuf[0] |= 1
    //dataBuf[1] = 0
    //dataBuf[2] = 0
    //dataBuf[3] = 0

    // ??? - right?
    data = 1
    WriteReg(PORTCOMMAND, data, ACC_MODE_TP, port, BYTE_EN_ALL)

    //read back to make sure lpbk is ready
    var i uint = 0
    for ; i < 10; i++ {
        data, _ = ReadReg(PORTCOMMAND, ACC_MODE_TP, port, BYTE_EN_ALL)
        if data & 0x8 == 0 {
            break
        }
    }
    if i == 10 {
        cli.Println("Port lpbk master state is not ready")
    }
    return
}

func pexTestStart(port byte) (err int) {
    //write reg 0x228 to set parallel lpbk, enable generator
    //dataBuf[2] = 0x2
    //dataBuf[3] = 0xFF
    //err = WriteReg(PHYSICALTEST1, dataBuf)
    data := uint32(0xFF0200)
    WriteReg(PHYSICALTEST1, data, ACC_MODE_TP, port, BYTE_EN_ALL)
    return
}

func pexTestStop(port byte) (err int) {
    var data uint32
    err = WriteReg(PHYSICALTEST1, data, ACC_MODE_TP, port, BYTE_EN_ALL)
    return
}

func pexTestCheck(port byte) (err int) {
    var data uint32
    dataBuf := make([]byte, REG_WIDTH)
//    err = ReadReg(DIAGDATAQUAD0, dataBuf)
    for i:=0; i< 8; i++ {
        dataBuf[3] = (byte)(i % 4)
        WriteReg(DIAGDATAQUAD0 + (uint32)((i/4)*4), misc.BytesToU32(dataBuf, 4), ACC_MODE_TP, port, BYTE_EN_ALL)
        data, _ = ReadReg(DIAGDATAQUAD0 + (uint32)((i/4)*4), ACC_MODE_TP, port, BYTE_EN_ALL)
        dataBuf = misc.U32ToBytes(data)
        if dataBuf[3] & 0x80 == 0 {
            cli.Println("Serdes", i, "UTP is not sync")
            continue
        }
        if dataBuf[2] != 0 {
            cli.Println("Serdes", i, "error, expected", dataBuf[0], "actual", dataBuf[1])
        } else {
            cli.Println("Serdes", i, "UTP passed!")
        }
    }
    return
}

func pexTestCleanup(port byte) (err int) {
    WriteReg(PHYSICALTEST1, 0, ACC_MODE_TP, port, BYTE_EN_ALL)
    return
}

func UTPTest(port byte, duration int) {
    pexLpbkConfig(port)
    pexTestStart(port)
    misc.SleepInSec(duration)
    pexTestStop(port)
    pexTestCheck(port)
    pexTestCleanup(port)
}


