package ad7997

import (
    "fmt"
    "testing"
)

func testReadCh2Vout(t *testing.T) {
    var ina INA3221A
    integer, dec, err := ina.ReadVout("P12V_AUX")
    fmt.Printf("VOUT: %d.%3d\n", integer, dec)
}

func testReadCh2Iout(t *testing.T) {
    var ina INA3221A
    integer, dec, err := ina.ReadIout("P12V_AUX")
    fmt.Printf("IOUT: %d.%3d\n", integer, dec)
}

func testReadCh2Pout(t *testing.T) {
    var ina INA3221A
    integer, dec, err := ina.ReadIout("P12V_AUX")
    fmt.Printf("POUT: %d.%3d\n", integer, dec)
}
