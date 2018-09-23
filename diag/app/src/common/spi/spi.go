// i2c.go specifies I2C wrapper for I2C library
package spi

import (
    //"fmt"
    //"config"
    "common/errType"
)

func SpiRead(offset uint32, data uint32) int {

    return errType.SUCCESS
}

func SpiWrite(offset uint32, data uint32) int {
    return errType.SUCCESS
}

func CpldRead(offset uint32, data uint32) int {
    return errType.SUCCESS
}

func CpldWrite(offset uint32, data uint32) int {
    return errType.SUCCESS
}

func MvlRegRead(offset uint32, data* uint32) int {
    return errType.SUCCESS
}

func MvlRegWrite(offset uint32, data uint32) int {
    return errType.SUCCESS
}
