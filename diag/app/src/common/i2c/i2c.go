// i2c.go specifies I2C wrapper for I2C library
package i2c

import (
    //"fmt"

    "config"
    "common/errType"
    //"hardware/vrmsim"
)

// #cgo CFLAGS: -I../../../../lib/
// #cgo LDFLAGS: -li2csim
// #include <stdlib.h>
// #include "../../../../lib/i2csim/i2csim.h"
import "C"
import "unsafe"

func Read(devName string, offset uint64, numBytes uint64) (data []byte, err int) {
    if config.SimMode == 1 {
        return PalReadSim(devName, offset, numBytes)
    }
    return data, errType.SUCCESS
}

func Write(i2cIdx uint32, devAddr uint32, offset uint32, data []byte, numBytes uint32) int {
    return errType.SUCCESS
}

func PalReadSim(devName string, offset uint64, numBytes uint64) (data []uint8, err int) {
    var pDevName *C.char = C.CString(devName)
    defer C.free(unsafe.Pointer(pDevName))
    var offsetC C.uint64
    var numBytesC C.uint64
    err = errType.SUCCESS

    offsetC = C.uint64(offset)
    numBytesC = C.uint64(numBytes)

    // Maximum number of byte is 16
    rd := [16]C.char{0, 0, 0, 0}

    if numBytes > 16 {
        return data, errType.INVALID_PARAM
    }

    C.pal_i2c_read(pDevName, offsetC, &rd[0], numBytesC)
    data = C.GoBytes(unsafe.Pointer(&rd[0]), C.int(numBytesC))

    return data, err
}


