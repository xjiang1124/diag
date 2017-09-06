// i2c.go specifies I2C wrapper for I2C library
package i2c

import (
    "common/errType"
)

func Read(devNameString string, offset uint32, data []byte, numBytes uint32) uint32 {
    return errType.Success
}

func Write(devNameString string, offset uint32, data []byte, numBytes uint32) uint32 {
    return errType.Success
}
