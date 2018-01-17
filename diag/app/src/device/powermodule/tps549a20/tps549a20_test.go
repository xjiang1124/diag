package tps549a20

import (
    "testing"
)

func TestDispStatus(t *testing.T) {
    var tps TPS549A20
    err := tps.DispStatus("VRM_HBM")
    if err != 0 {
        t.Error (
            "DispStatus",
            "expected", 0,
            "got", err,
        )
    }

    err = tps.DispStatus("VRM_ARM")
    if err != 0 {
        t.Error (
            "DispStatus",
            "expected", 0,
            "got", err,
        )
    }

}
