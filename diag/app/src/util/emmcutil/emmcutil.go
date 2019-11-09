package main

import (
    "flag"

    "common/cli"
    "common/errType"
    "device/emmc"
)

func main() {
    testPtr     := flag.Bool  ("test", false,  "Perform eMMC test")
    fileSizePtr := flag.String("size", "1",    "Test file size in MB")
    countPtr    := flag.Int   ("count", 0,      "Test count")

    flag.Parse() // Scan the arguments list 

    if *testPtr == true {
        err := emmc.EmmcTest(*fileSizePtr, *countPtr)
        if err != errType.SUCCESS {
            cli.Println("i", "eMMC test failed!")
        } else {
            cli.Println("i", "eMMC test passed")
        }
    }
}
