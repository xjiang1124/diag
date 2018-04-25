// i2c.go specifies I2C wrapper for I2C library
package spi

import (
    //"fmt"
    "config"
    "common/errType"
)

func SpiRead(offset uint32, data uint32) int {

    return errType.Success
}

func SpiWrite(offset uint32, data uint32) int {
    return errType.Success
}

func CpldRead(offset uint32, data uint32) int {
    return errType.Success
}

func CpldWrite(offset uint32, data uint32) int {
    return errType.Success
}

func MvlRegRead(offset uint32, data* uint32) int {
    return errType.Success
}

func MvlRegWrite(offset uint32, data uint32) int {
    return errType.Success
}
