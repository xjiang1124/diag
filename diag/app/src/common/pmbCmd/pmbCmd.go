// pmb.go specifies PMBus commands implementations
package pmbCmd

import (
    "fmt"

    "common/errType"
    "common/i2c"
    "common/misc"
)

func ReadByte(i2cIdx uint32, devAddr uint32, regAddr uint32, dataPtr *uint32) int {
    byteArray := make([]byte, 4)

    retVal := i2c.Read(i2cIdx, devAddr, regAddr, byteArray, 1)
    if retVal != errType.Success {
        return retVal
    }

    misc.BytesToU32(dataPtr, byteArray)
    fmt.Println(byteArray)
    return errType.Success

    return errType.Success
}

func WriteByte(i2cIdx uint32, devAddr uint32, regAddr uint32, data uint32) int {
    return errType.Success
}

func ReadWord(i2cIdx uint32, devAddr uint32, regAddr uint32, dataPtr *uint32) int {
    byteArray := make([]byte, 4)

    retVal := i2c.Read(i2cIdx, devAddr, regAddr, byteArray, 2)
    if retVal != errType.Success {
        return retVal
    }

    misc.BytesToU32(dataPtr, byteArray)
    fmt.Println(byteArray)
    return errType.Success
}

func WriteWord(i2cIdx uint32, devAddr uint32, regAddr uint32, data uint32) int {
    return errType.Success
}

func SendByte(i2cIdx uint32, devAddr uint32, regAddr uint32, data uint32) int {
    return errType.Success
}

