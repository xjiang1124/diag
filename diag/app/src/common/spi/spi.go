// i2c.go specifies I2C wrapper for I2C library
package spi

import (
    //"fmt"
    //"config"
    "common/errType"
    "common/cli"
)

// #cgo CFLAGS: -I../../../../../include
// #cgo LDFLAGS: -lcpld
// #include <stdlib.h>
// #include "../../../../lib/capricpld/cpld.h"
import "C"
//import "unsafe"

func SpiRead(offset uint32, data uint32) int {

    return errType.SUCCESS
}

func SpiWrite(offset uint32, data uint32) int {
    return errType.SUCCESS
}

func CpldRead(offset uint32, data* uint32) {
    var rd C.int
    rd = C.Cpld_read(C.uchar(offset))
    *data = uint32(rd)
}

func CpldWrite(offset uint32, data uint32) (err int) {
    var retC C.int
    retC = C.Cpld_write(C.uchar(offset), C.uchar(data))
    if retC != 0 {
        cli.Println("e", "Failed to write CPLD")
    }
    err = int(retC)
    return
}

func MvlRegRead(offset uint32, data* uint32, phy uint32) (err int) {
    var retC C.int
    var rd C.ushort
    retC = C.Mdio_rd(C.uchar(offset), &rd, C.uchar(phy))
    if retC != 0 {
        cli.Println("e", "Failed to read Marvell register")
    }
    *data = uint32(rd)
    err = int(retC)
    return
}

func MvlRegWrite(offset uint32, data uint32, phy uint32) (err int) {
    var retC C.int
    retC = C.Mdio_wr(C.uchar(offset), C.ushort(data), C.uchar(phy))
    if retC != 0 {
        cli.Println("e", "Failed to write Marvell register")
    }
    err = int(retC)
    return
}

func MvlSmiRegRead(offset uint32, data* uint32, phy uint32) (err int) {
    var retC C.int
    var rd C.ushort
    retC = C.Mdio_smi_rd(C.uchar(offset), &rd, C.uchar(phy))
    if retC != 0 {
        cli.Println("e", "Failed to read Marvell smi register")
    }
    *data = uint32(rd)
    err = int(retC)
    return
}

func MvlSmiRegWrite(offset uint32, data uint32, phy uint32) (err int) {
    var retC C.int
    retC = C.Mdio_smi_wr(C.uchar(offset), C.ushort(data), C.uchar(phy))
    if retC != 0 {
        cli.Println("e", "Failed to write Marvell smi register")
    }
    err = int(retC)
    return
}
