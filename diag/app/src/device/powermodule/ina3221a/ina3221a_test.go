package ina3221a

import (
    "fmt"
    "testing"
)

// READ_VIN
// --------
// P12V         i2c-2 0x43 0x2      = 12V
// P3V3         i2c-2 0x43 0x4      = 3.3V
// VDD_DDR      i2c-2 0x43 0x6      = 0.71V
// VDD_075_PCIE i2c-2 0x42 0x2      = 0.75V
// VDD_12_MX    i2c-2 0x42 0x4      = 12V
// VDD_12_PCIE  i2c-2 0x42 0x6      = 12V
// P1V8_NIC     i2c-2 0x41 0x2      = 1.8V
// VDDQ         i2c-2 0x41 0x4      = 1.1V
// VDD_075_MX   i2c-2 0x41 0x6      = 0.75V

// READ_IIN
// --------
// P12V         i2c-2 0x43 0x1 / 0.002 ohm
// P3V3         i2c-2 0x43 0x3 / 0.02 ohm
// VDD_DDR      i2c-2 0x43 0x5 / 0.005 ohm
// VDD_075_PCIE i2c-2 0x42 0x1 / 0.005 ohm
// VDD_12_MX    i2c-2 0x42 0x3 / 0.005 ohm
// VDD_12_PCIE  i2c-2 0x42 0x5 / 0.005 ohm
// P1V8_NIC     i2c-2 0x41 0x1 / 0.02 ohm
// VDDQ         i2c-2 0x41 0x3 / 0.1 ohm
// VDD_075_MX   i2c-2 0x41 0x5 / 0.005 ohm

func testReadCh2Vout(t *testing.T) {
    var ina INA3221A
    integer, dec, err := ina.ReadVout("P3V3")
    fmt.Printf("VOUT: %d.%3d\n", integer, dec)
}

func testReadCh2Iout(t *testing.T) {
    var ina INA3221A
    integer, dec, err := ina.ReadIout("P3V3")
    fmt.Printf("IOUT: %d.%3d\n", integer, dec)
}

func testReadCh2Pout(t *testing.T) {
    var ina INA3221A
    integer, dec, err := ina.ReadIout("P3V3")
    fmt.Printf("POUT: %d.%3d\n", integer, dec)
}

func testReadMFRID(t *testing.T) {
    var ina INA3221A
    data, err := ina.ReadMFRID("ISENSE_1")
    fmt.Printf("ISENSE_1 MFR ID: %d\n", data)
    data, err := ina.ReadMFRID("ISENSE_2")
    fmt.Printf("ISENSE_2 MFR ID: %d\n", data)
    data, err := ina.ReadMFRID("ISENSE_3")
    fmt.Printf("ISENSE_3 MFR ID: %d\n", data)
}

func testReadDieID(t *testing.T) {
    var ina INA3221A
    data, err := ina.ReadDieID("ISENSE_1")
    fmt.Printf("ISENSE_1 Die ID: %d\n", data)
    data, err := ina.ReadDieID("ISENSE_2")
    fmt.Printf("ISENSE_2 Die ID: %d\n", data)
    data, err := ina.ReadDieID("ISENSE_3")
    fmt.Printf("ISENSE_3 Die ID: %d\n", data)
}