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
    dataArray, err := i2c.Read(devName, regAddr, 1)
    data = dataArray[0]
    return
}

func WriteByte(devName string, regAddr uint64, data byte) int {
    return errType.SUCCESS
}

func ReadWord(devName string, regAddr uint64) (data uint16, err int) {
    //fmt.Printf("0x%x\n", regAddr)
    byteArray, err := i2c.Read(devName, regAddr, 2)
    //_, err = i2c1.Read(devName, regAddr, 2)
    if err != errType.SUCCESS {
        return data, err
    }

    data = misc.BytesToU16(byteArray)
    return data, errType.SUCCESS
}

func WriteWord(devName string, regAddr uint64, data uint16) (err int) {
    return errType.SUCCESS
}

func SendByte(devName string, regAddr uint64, data byte) int {
    return errType.SUCCESS
}

