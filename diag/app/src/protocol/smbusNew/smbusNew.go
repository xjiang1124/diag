package smbusNew

import (
    "github.com/go-smbus"

    "common/errType"
    "common/cli"
)


type SmbInfo struct {
    devName string
    bus uint32
    devAddr byte
    smb *smbusdev.SMBus
}

var smbInfo SmbInfo

func init () {
    //smbInfo.smb = smbusdev.New()
}

func Open(devName string, bus uint32, devAddr byte) (err int) {
    var errgo error

    if smbInfo.smb != nil {
        cli.Println("e", "SMB bus already opened!", smbInfo)
        return errType.SMB_OPEN_FAIL
    }

    smbInfo.smb = smbusdev.New()

    if smbInfo.devName != "" {
        err = errType.SMB_INF_BUSY
        return
    }

    errgo = smbInfo.smb.Open(uint(bus), devAddr)
    if errgo != nil {
        cli.Println("e", errgo)
        err = errType.SMB_OPEN_FAIL
        return
    }
    smbInfo.devName = devName
    smbInfo.bus = bus
    smbInfo.devAddr = devAddr
    //cli.Println("d", smbInfo)
    return
}

func Close() (err int) {
    errgo := smbInfo.smb.Bus_close()
    if errgo != nil {
        cli.Println("e", errgo)
        err = errType.SMB_CLOSE_FAIL
        return
    }
    smbInfo.devName = ""
    smbInfo.bus = 0
    smbInfo.devAddr = 0
    smbInfo.smb = nil
    return
}

func ReadByte(devName string, regAddr uint64) (data byte, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    data, errgo := smbInfo.smb.Read_byte_data(byte(regAddr))
    if errgo != nil {
        cli.Println("e", errgo)
        err = errType.SMB_READ_FAIL
        return
    }
    return
}

func WriteByte(devName string, regAddr uint64, data byte) (err int) {
    if smbInfo.devName != devName {
        cli.Println("e", "Invalid device name:", devName)
        err = errType.SMB_INF_INVALID
        return
    }
    errgo := smbInfo.smb.Write_byte_data(byte(regAddr), data)
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }
    return
}

func ReadWord(devName string, regAddr uint64) (data uint16, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    data, errgo := smbInfo.smb.Read_word_data(byte(regAddr))
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_READ_FAIL
        return
    }
    return
}

func WriteWord(devName string, regAddr uint64, data uint16) (err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    errgo := smbInfo.smb.Write_word_data(byte(regAddr), data)
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }
    return
}

func SendByte(devName string, data byte) (err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    errgo := smbInfo.smb.Write_byte(data)
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }
    return
}

func ReceiveByte(devName string) (data byte, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    data, errgo := smbInfo.smb.Read_byte()
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }
    return
}

/**
 * ReadBlock
 * Read block smbus command. LSB is at highest byte. MSB is at byte[0]
 */
func ReadBlock(devName string, regAddr uint64, buf []byte) (byteCnt int, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    byteCnt, errgo := smbInfo.smb.Read_block_data(byte(regAddr), buf)
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_READ_FAIL
        return
    }
    return byteCnt, err
}

/**
 * WriteBlock
 * Write block smbus command. LSB is at highest byte. MSB is at byte[0]
 */
func WriteBlock(devName string, regAddr uint64, buf []byte) (byteCnt int, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    byteCnt, errgo := smbInfo.smb.Write_block_data(byte(regAddr), buf)
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_READ_FAIL
        return
    }
    return byteCnt, err
}
/**
 * WriteBlock
 * Write block smbus command. LSB is at highest byte. MSB is at byte[0]
 */
func ProcessCall(devName string, cmd uint64, buf []byte) (data []byte, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    data, errgo := smbInfo.smb.Block_process_call(byte(cmd), buf)
    if errgo != nil {
        cli.Println("f", errgo)
        err = errType.SMB_READ_FAIL
        return
    }
    return
}

//=============================================
//
// This section is to implement 16-bit internal addressing
// 
// I2C Tools steps as following
// # write to 0x0000. First 0x00 is the register offset, second 0x00 is the first byte of DATA,
// # but chip interprets that as the 2nd byte of the address.
// i2cset -y 0 0x50 0x00 0x00 0x01 0x02 0x03 i
// i2cset -y 0 0x50 0x00 0x0a 0xFF 0xFE 0xFD i
// 
// # write address 0x0000 to the chip, sets the address counter
// i2cset -y 0 0x50 0x00 0x00
// 
// # each read command returns a byte and advances the counter
// i2cget -y 0 0x50 # returns 0x01
// i2cget -y 0 0x50 # returns 0x02
// i2cget -y 0 0x50 # returns 0x03
// 
// 
// # repeat the process to read address 0x000A
// i2cset -y 0 0x50 0x00 0x0a
// i2cget -y 0 0x50 # returns 0xFF
// i2cget -y 0 0x50 # returns 0xFE
// i2cget -y 0 0x50 # returns 0xFD
//
//=============================================

func I2C16WriteByte(devName string, offset uint16, data byte) (err int) {
    wData := make([]byte, 2)
    wData[0] = byte(offset & 0xFF)
    wData[1] = data
    wOffset := byte((offset& 0xFF00) >> 8)

    _, errgo := smbInfo.smb.Write_i2c_block_data(wOffset, wData)
    if errgo != nil {
        cli.Println("f", "I2C WR ERROR Dev=", smbInfo.devName," @ Offset=", offset, "  Errno=", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }

    return
}

func I2C16ReadByte(devName string, offset uint16) (data byte, err int) {
    wData := make([]byte, 1)
    wData[0] = byte(offset & 0xFF)
    wOffset := byte((offset& 0xFF00) >> 8)

    _, errgo := smbInfo.smb.Write_i2c_block_data(wOffset, wData)
    if errgo != nil {
        cli.Println("f", "I2C RD ERROR Dev=", smbInfo.devName, "@ Offset=", offset, "  Errno=", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }

    data, err = ReceiveByte(devName)
    return
}

func I2C16WriteBlock(devName string, offset uint16, buf []byte) (err int) {
    wData := make([]byte, 1)
    wData[0] = byte(offset & 0xFF)
    wData = append(wData, buf...)
    wOffset := byte((offset& 0xFF00) >> 8)

    _, errgo := smbInfo.smb.Write_i2c_block_data(wOffset, wData)
    if errgo != nil {
        cli.Println("f", errgo)
        cli.Println("f", "I2C WR BLK ERROR Dev=", smbInfo.devName," @ Offset=", offset, "  Errno=", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }
    return
}

func I2C16ReadBlock(devName string, offset uint16, buf []byte) (byteCnt int, err int) {
    var i int
    wData := make([]byte, 1)
    wData[0] = byte(offset & 0xFF)
    wOffset := byte((offset& 0xFF00) >> 8)

    _, errgo := smbInfo.smb.Write_i2c_block_data(wOffset, wData)
    if errgo != nil {
        cli.Println("f", "I2C RD BLK ERROR Dev=", smbInfo.devName, "@ Offset=", offset, "  Errno=", errgo)
        err = errType.SMB_WRITE_FAIL
        return
    }

    for i = 0; i < len(buf); i++ {
        data, err := ReceiveByte(devName)
        if err != errType.SUCCESS {
            break
        }
        buf[i] = data
    }
    byteCnt = i

    return
}
