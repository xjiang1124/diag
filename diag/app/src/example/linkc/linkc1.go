package main

import (
    "fmt"

    "common/errType"
)

// #cgo CFLAGS: -I../../../../lib/i2csim/
// #cgo LDFLAGS: /home/xguo2//workspace/psdiag/diag/app/pkg/linux_arm64/common/libi2csim.a
// #include <stdlib.h>
// #include "../../../../lib/i2csim/i2csim.h"
import "C"
import "unsafe"

func PalReadSim(devName string, offset uint64, numBytes uint64) (data []uint8, err int) {
    var pDevName *C.char = C.CString(devName)
    defer C.free(unsafe.Pointer(pDevName))
    var offsetC C.uint64
    var numBytesC C.uint64
    var retC C.int64
    err = errType.SUCCESS

// #ccccgo LDFLAGS: -li2csim
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

func main() {
    data, _ := PalReadSim("VRM_CAPRI_DVDD", 0x79, 1)
    fmt.Println("data:", data)
}
