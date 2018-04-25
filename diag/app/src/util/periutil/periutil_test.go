package main

import (
    "flag"
    "os"
	"testing"
)

func TestMain(m *testing.M) {
    flag.Parse()
    ret := m.Run()
    os.Exit(ret)
	//go func() {
    //    os.Exit(m.Run())
	//}
}
