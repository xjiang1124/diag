package pex8716

import (
    "common/cli"
    "common/errType"
    "protocol/i2cPtcl"
)

func Open(devName string) (err int) {
    err = i2cPtcl.Open(devName)
    return
}

func Close() {
    i2cPtcl.Close()
}

func Read(regAddr uint32, access_mode byte, port byte, byte_enable byte) (data uint32, err int) {
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

func Write(regAddr uint32, data uint32, access_mode byte, port byte, byte_enable byte) (err int) {
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

    cmdBuf[4] = byte(data & 0xFF)
    cmdBuf[5] = byte((data>>8) & 0xFF)
    cmdBuf[6] = byte((data>>16) & 0xFF)
    cmdBuf[7] = byte((data>>24) & 0xFF)

    err = i2cPtcl.Write(cmdBuf)
    if err != errType.SUCCESS {
        cli.Printf("e", "PEX read failed. Write command failure 0x%x\n", cmdBuf)
        return
    }

    return
}


