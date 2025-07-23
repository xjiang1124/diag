package smbus

import (
    "github.com/go-smbus"

    "common/errType"
    "common/cli"
    "config"
    "hardware/i2cinfo"
)


type I2cInfo struct {
    devName string
    smb *smbusdev.SMBus
    vrmInfo i2cinfo.I2cInfo
}

var smbInfo I2cInfo

func init () {
    //smbInfo.smb = smbusdev.New()
}

func Open(devName string) (err int) {
    var errgo error

    //cli.Println("d", smbInfo)
    if (config.SmbusMode == config.DISABLE) {
        return
    }
    smbInfo.smb = smbusdev.New()

    if smbInfo.devName != "" {
        err = errType.SMB_INF_BUSY
        return
    }
    smbInfo.vrmInfo, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return err
    }

    errgo = smbInfo.smb.Open(uint(smbInfo.vrmInfo.Bus), smbInfo.vrmInfo.DevAddr)
    if errgo != nil {
        cli.Println("e", errgo)
        err = errType.SMB_OPEN_FAIL
        return
    }
    smbInfo.devName = devName
    //cli.Println("d", smbInfo)
    return
}

func Close() (err int) {
    if (config.SmbusMode == config.DISABLE) {
        return
    }

    errgo := smbInfo.smb.Bus_close()
    //errgo = smbInfo.smb.Bus_close()
    if errgo != nil {
        cli.Println("e", errgo)
        err = errType.SMB_CLOSE_FAIL
        return
    }
    smbInfo.devName = ""
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
        cli.Println("e", "I2C ERROR Dev=", smbInfo.devName," @ Offset=", regAddr, "  Errno=", errgo)
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
        cli.Println("f", "I2C ERROR Dev=", smbInfo.devName," @ Offset=", regAddr, "  Errno=", errgo)
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
        cli.Println("f", "I2C ERROR Dev=", smbInfo.devName," @ Offset=", regAddr, "  Errno=", errgo)
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
 * ReadBlock
 * Read block smbus command. LSB is at highest byte. MSB is at byte[0]
 */
func Readi2cBlock(devName string, regAddr uint64, buf []byte) (byteCnt int, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    byteCnt, errgo := smbInfo.smb.Read_i2c_block_data(byte(regAddr), buf)
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
 * Writei2cBlock
 * Write block smbus command. LSB is at highest byte. MSB is at byte[0]
 */
func Writei2cBlock(devName string, regAddr uint64, buf []byte) (byteCnt int, err int) {
    if smbInfo.devName != devName {
        err = errType.SMB_INF_INVALID
        return
    }
    byteCnt, errgo := smbInfo.smb.Write_i2c_block_data(byte(regAddr), buf)
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
