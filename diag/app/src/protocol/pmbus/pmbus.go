// pmb.go specifies PMBus commands implementations
package pmbus

import (
    //"fmt"


    "common/errType"
    "protocol/i2c"
    "common/misc"
    "protocol/smbus"
    "config"
)

func ReadByte(devName string, regAddr uint64) (data byte, err int) {
    if config.SmbusMode == config.DISABLE {
        dataArray, err1 := i2c.Read(devName, regAddr, misc.ONE_BYTE)
        data = dataArray[0]
        err = err1
    } else {
        data, err = smbus.ReadByte(devName, regAddr)
    }
    return
}

func WriteByte(devName string, regAddr uint64, data byte) (err int) {
    if config.SmbusMode == config.DISABLE {
        var dataArr = []byte{data}
        err = i2c.Write(devName, regAddr, dataArr, misc.ONE_BYTE)
    } else {
        err = smbus.WriteByte(devName, regAddr, data)
    }
    return
}

func ReadWord(devName string, regAddr uint64) (data uint16, err int) {
    if config.SmbusMode == config.DISABLE {
        byteArray, err1 := i2c.Read(devName, regAddr, misc.TWO_BYTE)
        err = err1
        if err != errType.SUCCESS {
            return
        }
        data = misc.BytesToU16(byteArray, misc.TWO_BYTE)
    } else {
        data, err = smbus.ReadWord(devName, regAddr)
    }

    return
}

func WriteWord(devName string, regAddr uint64, data uint16) (err int) {
    if config.SmbusMode == config.DISABLE {
        dataArr := misc.U16ToBytes(data)
        err = i2c.Write(devName, regAddr, dataArr, misc.TWO_BYTE)
    } else {
        err = smbus.WriteWord(devName, regAddr, data)
    }

    return
}

func SendByte(devName string, cmd byte) (err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        err = smbus.SendByte(devName, cmd)
    }
    return

}

func ReadBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    if config.SmbusMode == config.DISABLE {
        _, err1 := i2c.Read(devName, regAddr, misc.ONE_BYTE)
        err = err1
    } else {
        byteCnt, err = smbus.ReadBlock(devName, regAddr, dataBuf)
    }
    return
}

func WriteBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    if config.SmbusMode == config.DISABLE {
        err1 := i2c.Write(devName, regAddr, dataBuf, misc.ONE_BYTE)
        err = err1
    } else {
        byteCnt, err = smbus.WriteBlock(devName, regAddr, dataBuf)
    }
    return
}

func Open(devName string) (err int) {
    //cli.Println("d", smbInfo)
    if (config.SmbusMode == config.DISABLE) {
        return
    }
    err = smbus.Open(devName)
    return
}

func Close() (err int) {
    if (config.SmbusMode == config.DISABLE) {
        return
    }

    err = smbus.Close()
    return err
}
