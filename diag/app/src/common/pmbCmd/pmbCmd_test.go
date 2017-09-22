package pmbCmd

import (
    //"fmt"
    "testing"

    "common/errType"
)

func TestReadByte(t *testing.T) {
    var data byte
    data, err := ReadByte("VRM_CAPRI_DVDD", 0xAD)
    if data != 0x59  || err != errType.SUCCESS {
        t.Error (
            "offset", 0xad,
            "expect", 0x59, 0,
            "Received", data, err,
        )
    }
}

func TestReadWord(t *testing.T) {
    var data uint16
    data, err := ReadWord("VRM_CAPRI_DVDD", 0x20)
    if data != 0x27  || err != errType.SUCCESS {
        t.Error (
            "offset", 0x20,
            "expect", 0x27, 0,
            "Received", data, err,
        )
    }

    data, err = ReadWord("VRM_CAPRI_DVDD", 0x89)
    if data != 0xD14F  || err != errType.SUCCESS {
        t.Error (
            "offset", 0x89,
            "expect", 0xD14F, 0,
            "Received", data, err,
        )
    }

}
