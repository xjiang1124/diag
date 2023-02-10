package main

import (
    "common/spi"
)

func CpldWrite(offset uint32, data uint32) {
    spi.CpldWrite(offset, data)
}