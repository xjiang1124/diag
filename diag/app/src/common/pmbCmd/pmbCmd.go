// pmb.go specifies PMBus commands implementations
package pmbCmd

import (
    //"fmt"

    "common/errType"
    //"common/i2c"
    "common/i2c"
    "common/misc"
)

func ReadByte(devName string, regAddr uint64) (data byte, err int) {
    dataArray, err := i2c.Read(devName, regAddr, misc.ONE_BYTE)
    data = dataArray[0]
    return
}

func WriteByte(devName string, regAddr uint64, data byte) (err int) {
    var dataArr = []byte{data}
    err = i2c.Write(devName, regAddr, dataArr, misc.ONE_BYTE)
    return
}

func ReadWord(devName string, regAddr uint64) (data uint16, err int) {
    byteArray, err := i2c.Read(devName, regAddr, misc.TWO_BYTE)
    if err != errType.SUCCESS {
        return
    }

    data = misc.BytesToU16(byteArray, misc.TWO_BYTE)
    return
}

func WriteWord(devName string, regAddr uint64, data uint16) (err int) {
    dataArr := misc.U16ToBytes(data)
    err = i2c.Write(devName, regAddr, dataArr, misc.TWO_BYTE)
    return

    return errType.SUCCESS
}

func SendByte(devName string, regAddr uint64, data byte) int {
    return errType.SUCCESS
}

