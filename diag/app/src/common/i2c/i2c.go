// i2c.go specifies I2C wrapper for I2C library
package i2c

import (
    //"fmt"

    "config"
    "common/errType"
    //"hardware/vrmsim"
)

// #cgo CFLAGS: -I../../../../lib/
// #cgo LDFLAGS: -li2c -li2csim
// #include <stdlib.h>
// #include "../../../../lib/i2csim/i2csim.h"
import "C"
import "unsafe"

func Read(devName string, offset uint64, numBytes uint64) (data []byte, err int) {
    if config.PalSimEnable == config.ENABLE {
        return PalReadSim(devName, offset, numBytes)
    }
    return data, errType.SUCCESS
}

// #ccccgo LDFLAGS: ${SRCDIR}/../../../pkg/linux_arm64/common/libi2csim.a
// #ccccgo LDFLAGS: /home/xguo2//workspace/psdiag/diag/app/pkg/linux_arm64/common/libi2csim.a
func Write(devName string, offset uint64, data []byte, numBytes uint64) int {
    if config.PalSimEnable == config.ENABLE {
        return PalWriteSim(devName, offset, numBytes, data)
    }
    return errType.SUCCESS
}

func PalReadSim(devName string, offset uint64, numBytes uint64) (data []uint8, err int) {
    var pDevName *C.char = C.CString(devName)
    defer C.free(unsafe.Pointer(pDevName))
    var offsetC C.uint64
    var numBytesC C.uint64
    var retC C.int64
    err = errType.SUCCESS

    offsetC = C.uint64(offset)
    numBytesC = C.uint64(numBytes)

    // Maximum number of byte is 16
    rd := [16]C.char{0, 0, 0, 0}

    if numBytes > 16 {
        return data, errType.INVALID_PARAM
    }

    retC = C.pal_i2c_read(pDevName, offsetC, &rd[0], numBytesC)
    data = C.GoBytes(unsafe.Pointer(&rd[0]), C.int(numBytesC))

    if retC != 0 {
        err = errType.I2C_RD_FAIL
    }

    return data, err
}

func PalWriteSim(devName string, offset uint64, numBytes uint64, data []uint8) (err int) {
    var pDevName *C.char = C.CString(devName)
    defer C.free(unsafe.Pointer(pDevName))
    var offsetC C.uint64
    var numBytesC C.uint64
    var retC C.int64
    err = errType.SUCCESS

    offsetC = C.uint64(offset)
    numBytesC = C.uint64(numBytes)

    rd := [16]C.char{0, 0, 0, 0}

    if numBytes > 16 {
        return errType.INVALID_PARAM
    }

    var i uint64
    for i = 0; i < numBytes; i++ {
        rd[i] = C.char(data[i])
    }

    retC = C.pal_i2c_write(pDevName, offsetC, &rd[0], numBytesC)

    if retC != 0 {
        err = errType.I2C_RD_FAIL
    }

    return err
}
