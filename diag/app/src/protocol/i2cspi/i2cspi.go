package i2cspi

import (
    //"protocol/i2cPtcl"
)

const (
    CONFIG   = 1
    IO       = 2
    CLR_INTR = 3
)

var cmdSwRst     []byte
var cmdWrDis     []byte
var cmdWrEn      []byte
var cmdEn4BAddr  []byte
var cmdRdSts     []byte
var cmdRdFlashId []byte
var cmdRd256B    []byte

func init() {
    cmdSwRst    = []byte{0x02, 0x66, 0x99}
    cmdWrDis    = []byte{0x02, 0x01, 0xEC}
    cmdWrEn     = []byte{0x02, 0x01, 0x6C}
    cmdEn4BAddr = []byte{0x02, 0xB7}
    cmdRdSts    = []byte{0x02, 0x7E, 0xFF}

    cmdRdFlashId = make([]byte, 22)
    cmdRd256B = make([]byte, 258)

    cmdRdFlashId[0] = 0x02
    cmdRdFlashId[1] = 0x9E
    for i := 2; i < 22; i++ {
        cmdRdFlashId[i] = 0xFF
    }

    cmdRd256B[0] = 0x02
    cmdRd256B[1] = 0x13
    for i := 2; i < 258; i++ {
        cmdRd256B[i] = 0xFF
    }
}

