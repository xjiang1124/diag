package cardinfo

import (
    "fmt"
    "testing"

    "common/errType"
)

func TestReadVout(t *testing.T) {
    fmt.Println(Cardinfo)
    cardType := "ORTANO2"
    err, asicType := GetAsicType(cardType)
    if err != errType.SUCCESS {
        fmt.Println("Failed!")
    } else {
        fmt.Println(cardType, asicType)
    }

    cardType := "ORTANO2A"
    err, asicType := GetAsicType(cardType)
    if err != errType.SUCCESS {
        fmt.Println("Failed!")
    } else {
        fmt.Println(cardType, asicType)
    }

    cardType = "ORTANO3"
    err, asicType = GetAsicType(cardType)
    if err != errType.SUCCESS {
        fmt.Println("Failed!")
    } else {
        fmt.Println(cardType, asicType)
    }

    cardType = "ORTANO2"
    err, asicType = GetCtrlType(cardType)
    if err != errType.SUCCESS {
        fmt.Println("Failed!")
    } else {
        fmt.Println(cardType, asicType)
    }

    cardType = "LACONA32"
    err, asicType = GetCtrlType(cardType)
    if err != errType.SUCCESS {
        fmt.Println("Failed!")
    } else {
        fmt.Println(cardType, asicType)
    }

    cardType = "LACONA"
    err, asicType = GetCtrlType(cardType)
    if err != errType.SUCCESS {
        fmt.Println("Failed!")
    } else {
        fmt.Println(cardType, asicType)
    }

}

