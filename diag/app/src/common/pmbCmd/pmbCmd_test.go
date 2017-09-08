package pmbCmd

import (
    "fmt"
    "testing"
)

func TestReadWord(t *testing.T) {
    var data uint32
    ReadWord(2, 0xC4, 0x20, &data)
    fmt.Printf("0x%x\n", data)
}
