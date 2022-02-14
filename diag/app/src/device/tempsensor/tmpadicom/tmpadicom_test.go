package tmpadicom

import (
    //"fmt"
    "testing"
)

type TestVector struct {
    channel byte
    integer int64
    dec int64
    err int
}

var testTbl = []TestVector {
    TestVector {0, 35, 1250, 0,},
    TestVector {1, 69, 1875, 0,},
    TestVector {2, -9, 625,  0,},
}


func TestReadVout(t *testing.T) {
    for _, testItem := range(testTbl) {
        integer, dec, err := ReadTemp("TEMP_SENSOR", testItem.channel)
        if integer != testItem.integer || dec != testItem.dec || err != 0 {
               t.Error (
                   "\n",
                   "Expected err, integer, dec", testItem.err, testItem.integer, testItem.dec,
                   "\n",
                   "Received err, integer, dec", err, integer, dec,
               )
           }
    }
}

func TestReadDevId(t *testing.T) {
    id, err := ReadDevId("TEMP_SENSOR")
    if id != DEV_ID_V || err != 0 {
        t.Error (
            "\n",
            "Expected ID, err", DEV_ID_V, 0,
            "\n",
            "Received ID, err", id, err,
        )
    }
}

func TestReadMfgId(t *testing.T) {
    id, err := ReadMfgId("TEMP_SENSOR")
    if id != MFG_ID_V || err != 0 {
        t.Error (
            "\n",
            "Expected ID, err", MFG_ID_V, 0,
            "\n",
            "Received ID, err", id, err,
        )
    }
}
func TestDispTemp(t *testing.T) {
    err := DispTemp("TEMP_SENSOR")
    if err != 0 {
        t.Error (
            "\n",
            "Expected err", 0,
            "Received err", err,
        )
    }
}
