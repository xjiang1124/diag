package tps544b25

import (
    "testing"
)

func TestDispStatus(t *testing.T) {
    var tps TPS544B25
    err := tps.DispStatus("VDDQ_DDR")
    if err != 0 {
        t.Error (
            "DispStatus",
            "expected", 0,
            "got", err,
        )
    }
}
