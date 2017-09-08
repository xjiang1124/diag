package tps53659

import (
    "fmt"
    "testing"
)

func TestReadVout(t *testing.T) {
    integer, dec, _ := ReadVout(2, 0xC4, 0)
    fmt.Printf("VOUT: %d.%3d\n", integer, dec)
    if integer != 0 || dec != 800 {
        t.Error (
            "For", 0xC4,
            "expected", 0, 800,
            "got", integer, dec,
        )
    }
}

func TestReadIout(t *testing.T) {
    integer, dec, _ := ReadIout(2, 0xC4, 0)
    fmt.Printf("IOUT: %d.%3d\n", integer, dec)
    if integer != 4 || dec != 765 {
        t.Error (
            "For", 0xC4,
            "expected", 4, 765,
            "got", integer, dec,
        )
    }
}

func TestReadIin(t *testing.T) {
    integer, dec, _ := ReadIin(2, 0xC4, 0)
    fmt.Printf("IIN: %d.%3d\n", integer, dec)
    if integer != 5 || dec != 234 {
        t.Error (
            "For", 0xC4,
            "expected", 5, 234,
            "got", integer, dec,
        )
    }
}

func TestReadVin(t *testing.T) {
    integer, dec, _ := ReadVin(2, 0xC4, 0)
    fmt.Printf("VIN: %d.%3d\n", integer, dec)
    if integer != 10 || dec != 250 {
        t.Error (
            "For", 0xC4,
            "expected", 10, 250,
            "got", integer, dec,
        )
    }
}

func TestReadVoutLn(t *testing.T) {
    integer, dec, _ := ReadVoutLn(2, 0xC4, 0)
    fmt.Printf("VOUT_LN: %d.%3d\n", integer, dec)
    if integer != 4 || dec != 890 {
        t.Error (
            "For", 0xC4,
            "expected", 4, 890,
            "got", integer, dec,
        )
    }
}

func TestReadTemp(t *testing.T) {
    integer, dec, _ := ReadTemp(2, 0xC4, 0)
    fmt.Printf("TEMP: %d.%3d\n", integer, dec)
    if integer != 5 || dec != 203 {
        t.Error (
            "For", 0xC4,
            "expected", 5, 203,
            "got", integer, dec,
        )
    }
}

func TestReadPin(t *testing.T) {
    integer, dec, _ := ReadPin(2, 0xC4, 0)
    fmt.Printf("PIN: %d.%03d\n", integer, dec)
    if integer != 5 || dec != 78 {
        t.Error (
            "For", 0xC4,
            "expected", 5, 78,
            "got", integer, dec,
        )
    }
}

func TestReadPout(t *testing.T) {
    integer, dec, _ := ReadPout(2, 0xC4, 0)
    fmt.Printf("POUT: %d.%03d\n", integer, dec)
    if integer != 4 || dec != 937 {
        t.Error (
            "For", 0xC4,
            "expected", 4, 937,
            "got", integer, dec,
        )
    }
}
