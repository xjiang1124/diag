package tps53659

import (
    "fmt"
    "testing"
)

func TestReadWord(t *testing.T) {
    integer, dec := ReadVout(2, 0xC4, 0)
    fmt.Printf("VOUT: %d.%3d\n", integer, dec)
    if integer != 0 || dec != 800 {
        t.Error (
            "For", 0xC4,
            "expected", 0, 800,
            "got", integer, dec,
        )
    }
}
