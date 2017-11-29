package cli

import (
    //"fmt"
    "testing"
)

func TestPrintf(t *testing.T) {
    err := Printf("i", "%s %s", "string1", "string2")
    if err != nil {
        t.Error (
            err,
        )
    }
    err = Printf("i", "digitals %d 0x%x", 15, 134)
    if err != nil {
        t.Error (
            err,
        )
    }

}
