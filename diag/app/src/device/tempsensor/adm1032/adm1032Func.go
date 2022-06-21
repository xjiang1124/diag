package adm1032

import (
    "fmt"

    "common/cli"
    "common/errType"
    "protocol/smbus"
    "time"
)

func ReadMfgId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, MFG_ID)
    return
}

func ReadDevId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, DIE_ID)
    return
}

func ReadTemp(devName string, channel byte) (integer int64, dec int64, err int) {
    var try byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    try = 0
    for { 
        lowByte, err := smbus.ReadByte(devName, STATUS)
        if err != errType.SUCCESS {
            return integer, dec, err
        }
        if  (lowByte & 0x80) == 0  {
            break;
        } else if  try > 2 {
            fmt.Printf("temp sensor ADM1032 is busy")
            return integer, dec, errType.INVALID_PARAM
        }
        try = try + 1
        time.Sleep(100 * time.Millisecond) 
    }
    switch channel {
    case LOCAL_TEMP:
        lowByte, err := smbus.ReadByte(devName, LOCAL_TEMP_REG)
        if err != errType.SUCCESS {
            return integer, dec, err
        }
        integer = int64(lowByte)
        dec = 0
    case REMOTE_TEMP:
        lowByte, err := smbus.ReadByte(devName, REMOTE_TEMP_HIGH)
        if err != errType.SUCCESS {
            return integer, dec, err
        }
        integer = int64(lowByte)

        lowByte, err = smbus.ReadByte(devName, REMOTE_TEMP_LOW)
        if err != errType.SUCCESS {
            return integer, dec, err
        }
        dec = int64((lowByte & 0xf0) >> 4)
        dec = (dec * 625) / 10
    default:
        err = errType.INVALID_PARAM
        return
    }
    return
}

func DispStatus(devName string) (err int) {
    err = errType.SUCCESS

    degSym := fmt.Sprintf("(%cC)",0xB0)
    tempTitle := []string {"LOCAL", "REMOTE",}
    var titleStr string
    for _, title := range(tempTitle) {
        tmpStr := fmt.Sprintf("%-20s", title+degSym)
        titleStr = titleStr + tmpStr
    }
    cli.Println("i", titleStr)

    var outStr string
    for i:=0; i<MAX_CHANNEL; i++ {
        integer, dec, err := ReadTemp(devName, byte(i))
        if err != errType.SUCCESS {
            return err
        }
        tmpStr := fmt.Sprintf("%d.%04d", integer, dec)
        tmpStr = fmt.Sprintf("%-20s", tmpStr)
        outStr = outStr + tmpStr
    }
    cli.Println("i", outStr)

    return
}
