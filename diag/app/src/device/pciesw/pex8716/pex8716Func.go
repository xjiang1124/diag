package pex8716

import (
    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/i2cPtcl"
)

const (
    REG_WIDTH = 4
    MAX_RETRY = 10
    DLY_USEC  = 1000
    BYTE_EN_ALL = 0xFF
)

const (
    ACC_MODE_TP  = 0
    ACC_MODE_NT  = 1
    ACC_MODE_NTV = 2
)

const (
    EEP_OP_WR  = 0x2
    EEP_OP_RD  = 0x3
    EEP_OP_RST_WR_EN = 0x4
    EEP_OP_SET_WR_EN = 0x6

    EEP_EN_ADDR_WTH_OW = 1
    EEP_ADDR_WTH_1B = 1
    EEP_ADDR_WTH_2B = 2
    EEP_ADDR_WTH_3B = 3
)

func Open(devName string) (err int) {
    err = i2cPtcl.Open(devName)
    return
}

func Close() {
    i2cPtcl.Close()
}

func ReadReg(regAddr uint32, access_mode byte, port byte, byte_enable byte) (data uint32, err int) {
    cli.Printf("d", "am=0x%x, p=0x%x, be=0x%x\n", access_mode, port, byte_enable)
    cmdBuf := make([]byte, 4)
    var dataBuf []byte

    if regAddr > 0xFFF {
        cli.Printf("e", "Invalid register address 0x%x\n", regAddr)
        err = errType.INVALID_PARAM
        return
    }

    cmdBuf[0] = 0x4

    cmdBuf[1] = (access_mode & 0x3) << 4
    cmdBuf[1] = cmdBuf[1] | ((port & 0x6) >> 1)

    cmdBuf[2] = (port & 1) << 7
    cmdBuf[2] = cmdBuf[2] | ((byte_enable & 0xF) << 2)
    cmdBuf[2] = cmdBuf[2] | byte((regAddr & 0xFFF) >> 10)
    //cli.Printf("d", "addr=0x%x\n", byte((regAddr & 0xFFF) >> 10))

    cmdBuf[3] = byte((regAddr & 0x3FF) >> 2)

    for i := 0; i < 4; i++ {
        cli.Printf("d", "cmdBuf[%d]=0x%x\n", i, cmdBuf[i])
    }

    err = i2cPtcl.Write(cmdBuf)
    if err != errType.SUCCESS {
        cli.Printf("e", "PEX read failed. Write command failure 0x%x\n", cmdBuf)
        return
    }
    dataBuf, err = i2cPtcl.Read(4)
    if err != errType.SUCCESS {
        cli.Printf("e", "PEX read failed. Read command failure 0x%x\n", cmdBuf)
        return
    }
    data = uint32(dataBuf[0]) << 24 | uint32(dataBuf[1]) << 16 |
           uint32(dataBuf[2]) << 8 | uint32(dataBuf[3])

    return
}

func WriteReg(regAddr uint32, data uint32, access_mode byte, port byte, byte_enable byte) (err int) {
    cmdBuf := make([]byte, 8)

    if regAddr > 0xFFF {
        cli.Printf("e", "Invalid register address 0x%x\n", regAddr)
        err = errType.INVALID_PARAM
        return
    }

    cmdBuf[0] = 0x3

    cmdBuf[1] = (access_mode & 0x3) << 4
    cmdBuf[1] = cmdBuf[1] | ((port & 0x6) >> 1)

    cmdBuf[2] = (port & 1) << 7
    cmdBuf[2] = cmdBuf[2] | ((byte_enable & 0xF) << 2)
    cmdBuf[2] = cmdBuf[2] | byte((regAddr & 0xFFF) >> 10)

    cmdBuf[3] = byte((regAddr & 0x3FF) >> 2)

    cmdBuf[7] = byte(data & 0xFF)
    cmdBuf[6] = byte((data>>8) & 0xFF)
    cmdBuf[5] = byte((data>>16) & 0xFF)
    cmdBuf[4] = byte((data>>24) & 0xFF)

    err = i2cPtcl.Write(cmdBuf)
    if err != errType.SUCCESS {
        cli.Printf("e", "PEX read failed. Write command failure 0x%x\n", cmdBuf)
    }

    return
}

/**
 * Read one DWORD (4-byte) from EEPROM
 */
func ReadEepDw(offset uint32, port byte) (data uint32, err int) {
    var stsCtrlData uint32
    var flag uint32

    // Do not support over 32KB for now
    if offset >= 0x7FFF {
        cli.Printf("e", "EEPROM offset can ot exceed 0x7FFF, received: 0x%x\n", offset)
        err = errType.INVALID_PARAM
        return
    }

    // Compose control data
    stsCtrlData = (offset >> 2) & 0x1FFF
    stsCtrlData = stsCtrlData | (EEP_OP_RD << 13)
    stsCtrlData = stsCtrlData | EEP_EN_ADDR_WTH_OW << 21
    stsCtrlData = stsCtrlData | EEP_ADDR_WTH_2B << 22
    cli.Printf("d", "stsCtrlData=0x%x\n", stsCtrlData)

    err = WriteReg(REG_EEP_STS_CTRL, stsCtrlData, ACC_MODE_TP, port, 0xF)
    if err != errType.SUCCESS {
        cli.Printf("e", "Faild to write; addr=0x%x, data=0x%x\n", REG_EEP_STS_CTRL, stsCtrlData)
        return
    }

    // Check done flag
    for i := 0; i < MAX_RETRY; i++ {
        cli.Println("d", "Wait for EEP done", i)
        data, err = ReadReg(REG_EEP_STS_CTRL, ACC_MODE_TP, port, 0xF)
        if err != errType.SUCCESS {
            cli.Printf("e", "Faild to read; addr=0x%x\n", REG_EEP_STS_CTRL)
            return
        }
        flag = (data >> 18) & 1
        if flag == 0 {
            break
        }
        misc.SleepInUSec(1000)
    }

    if flag != 0 {
        cli.Println("e", "PEX EEP read timeout!")
        err = errType.TIMEOUT
        return
    }

    data, err = ReadReg(REG_EEP_BUF, ACC_MODE_TP, port, 0xF)
    if err != errType.SUCCESS {
        cli.Printf("e", "Faild to write; addr=0x%x, data=0x%x\n", REG_EEP_STS_CTRL, stsCtrlData)
    }
    return

}

/**
 * Read one DWORD (4-byte) from EEPROM
 */
func WriteEepDw(offset uint32, port byte, data uint32) (err int) {
    var stsCtrlData uint32
    var flag uint32

    // Do not support over 32KB for now
    if offset >= 0x7FFF {
        cli.Printf("e", "EEPROM offset can ot exceed 0x7FFF, received: 0x%x\n", offset)
        err = errType.INVALID_PARAM
        return
    }

    // Write data to buffer register
    err = WriteReg(REG_EEP_BUF, data, ACC_MODE_TP, port, 0xF)
    if err != errType.SUCCESS {
        cli.Printf("e", "Faild to write; addr=0x%x, data=0x%x\n", REG_EEP_BUF, data)
        return
    }

    // Write Enable latch + enable 2-byte addressing: 0x00A0C000
    stsCtrlData = EEP_EN_ADDR_WTH_OW << 21
    stsCtrlData = stsCtrlData | EEP_ADDR_WTH_2B << 22
    stsCtrlData = stsCtrlData | EEP_OP_SET_WR_EN << 13
    cli.Printf("d", "P0: stsCtrl=0x%x\n", stsCtrlData)

    err = WriteReg(REG_EEP_STS_CTRL, stsCtrlData, ACC_MODE_TP, port, 0xF)
    if err != errType.SUCCESS {
        cli.Printf("e", "Faild to write; addr=0x%x, data=0x%x\n", REG_EEP_STS_CTRL, stsCtrlData)
        return
    }

    // Compose control data
    stsCtrlData = (offset >> 2) & 0x1FFF
    stsCtrlData = stsCtrlData | EEP_EN_ADDR_WTH_OW << 21
    stsCtrlData = stsCtrlData | EEP_ADDR_WTH_2B << 22
    stsCtrlData = stsCtrlData | (EEP_OP_WR << 13)

    cli.Printf("d", "P1: stsCtrlData=0x%x\n", stsCtrlData)

    err = WriteReg(REG_EEP_STS_CTRL, stsCtrlData, ACC_MODE_TP, port, 0xF)
    if err != errType.SUCCESS {
        cli.Printf("e", "Faild to write; addr=0x%x, data=0x%x\n", REG_EEP_STS_CTRL, stsCtrlData)
        return
    }

    // Check done flag
    for i := 0; i < MAX_RETRY; i++ {
        cli.Println("d", "Wait for EEP done", i)
        data, err = ReadReg(REG_EEP_STS_CTRL, ACC_MODE_TP, port, 0xF)
        if err != errType.SUCCESS {
            cli.Printf("e", "Faild to read; addr=0x%x\n", REG_EEP_STS_CTRL)
            return
        }
        flag = (data >> 18) & 1
        if flag == 0 {
            break
        }
        misc.SleepInUSec(1000)
    }

    if flag != 0 {
        cli.Println("e", "PEX EEP read timeout!")
        err = errType.TIMEOUT
        return
    }

    // Reset write enable
    stsCtrlData = EEP_EN_ADDR_WTH_OW << 21
    stsCtrlData = stsCtrlData | EEP_ADDR_WTH_2B << 22
    stsCtrlData = stsCtrlData | EEP_OP_RST_WR_EN << 13
    cli.Printf("d", "P2: stsCtrl=0x%x\n", stsCtrlData)

    err = WriteReg(REG_EEP_STS_CTRL, stsCtrlData, ACC_MODE_TP, port, 0xF)
    if err != errType.SUCCESS {
        cli.Printf("e", "Faild to write; addr=0x%x, data=0x%x\n", REG_EEP_STS_CTRL, stsCtrlData)
    }
    return

}



