package lm75a

import (
    "fmt"
    "common/cli"
    "common/errType"
    "protocol/smbus"
)

const (

    LM75_TEMPERATURE_REG = 0
    LM75_CONFIG_REG = 1
    LM75_THYST_REG = 2
    LM75_TOS_REG = 3
    LM75_ID_REG = 4

)

func swap_uint16(a uint16) (b uint16) {
    b = ( uint16(a >> 8) | uint16(a << 8) )
    return
}


func ReadDevId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, LM75_ID_REG)
    return
}

func ReadTemp(devName string) (integer int64, dec int64, err int) {
    var data16 uint16

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    
    data16, err = smbus.ReadWord(devName, LM75_TEMPERATURE_REG)
    if err != errType.SUCCESS {
        return
    }
    data16 = swap_uint16(data16)

    if (data16 & 0x80) == 0x80{
        dec = 5
    }
    data16 = data16 >> 8
    integer = int64(data16)

    return
}

func DispStatus(devName string) (err int) {
    err = errType.SUCCESS

    degSym := fmt.Sprintf("(%cC)",0xB0)
    
    tmpStr := fmt.Sprintf("%-15s", devName+degSym)

    integer, dec, err := ReadTemp(devName)
    if err != errType.SUCCESS {
        return err
    }

    tmpStr = fmt.Sprintf("%s %d.%01d", tmpStr, integer, dec)
    cli.Println("i", tmpStr)

    return
}

