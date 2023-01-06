package tps53659

import (
    "fmt"
    "testing"
)


func TestReadVout(t *testing.T) {
    var tps TPS53659
    integer, dec, _ := tps.ReadVout("VRM_CAPRI_AVDD")
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
    var tps TPS53659
    integer, dec, _ := tps.ReadIout("VRM_CAPRI_DVDD")
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
    var tps TPS53659
    integer, dec, _ := tps.ReadIin("VRM_CAPRI_DVDD")
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
    var tps TPS53659
    integer, dec, _ := tps.ReadVin("VRM_CAPRI_DVDD")
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
    var tps TPS53659
    integer, dec, _ := tps.ReadVoutLn("VRM_CAPRI_DVDD")
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
    var tps TPS53659
    integer, dec, _ := tps.ReadTemp("VRM_CAPRI_DVDD")
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
    var tps TPS53659
    integer, dec, _ := tps.ReadPin("VRM_CAPRI_DVDD")
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
    var tps TPS53659
    integer, dec, _ := tps.ReadPout("VRM_CAPRI_DVDD")
    fmt.Printf("POUT: %d.%03d\n", integer, dec)
    if integer != 4 || dec != 937 {
        t.Error (
            "For", 0xC4,
            "expected", 4, 937,
            "got", integer, dec,
        )
    }
}

func TestSetMargin(t *testing.T) {
    var tps TPS53659
    pcts := []int{0, -3, 3}
    for _, pct := range(pcts) {
        err := tps.SetVMargin("VRM_CAPRI_DVDD", pct)
        if err != 0 {
            t.Error (
                "For", 0xC4,
                "expected", 0,
                "got", err,
            )
        } else {
            fmt.Println(pct, err)
        }
    }
}

func TestDispStatus(t *testing.T) {
    var tps TPS53659
    err := tps.DispStatus("VRM_CAPRI_DVDD")
    if err != 0 {
        t.Error (
            "DispStatus",
            "expected", 0,
            "got", err,
        )
    }

    err = tps.DispStatus("VRM_CAPRI_AVDD")
    if err != 0 {
        t.Error (
            "DispStatus",
            "expected", 0,
            "got", err,
        )
    }

}
