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
    LM75_ID_REG = 7

    LM75_ID_EXPECTED = 0xA0
    LM75_ID_MASK     = 0xF0
    LM75_TEMPERATURE_MASK     = 0xFF80

)


func smbus_read8(devName string, address uint8) (data8 uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    
    data8, err = smbus.ReadByte(devName, uint64(address))
    if err != errType.SUCCESS {
        cli.Println("e", " i2cTest:  Read Dev ID Failed")
        return
    }
    smbus.Close()
    return
}

func smbus_read16(devName string, address uint8) (data16 uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    data16, err = smbus.ReadWord(devName, uint64(address))
    if err != errType.SUCCESS {
        cli.Println("e", " i2cTest:  Read Dev ID Failed")
        return
    }
    smbus.Close()
    return
}


func swap_uint16(a uint16) (b uint16) {
    b = ( uint16(a >> 8) | uint16(a << 8) )
    return
}

func I2cTest(devName string) (err int) {
    var id byte 
    var data16 uint16
    var temp_mask uint16 = uint16(LM75_TEMPERATURE_MASK)

    id, err = smbus_read8(devName, LM75_ID_REG)
    if err != errType.SUCCESS {
        cli.Printf("e", " i2cTest:  Read reg-0x%x failed\n", LM75_ID_REG)
        return
    }

    if id & LM75_ID_MASK != LM75_ID_EXPECTED {
        cli.Printf("e", " LM75 ID is incorrect.  Expect 0xA0 in the upper nibble.  Read 0x%x\n", id)
        err = errType.FAIL
        return
    }
    
    data16, err = smbus_read16(devName, LM75_TEMPERATURE_REG)
    if err != errType.SUCCESS {
        cli.Printf("e", " i2cTest:  Read reg-0x%x failed\n", LM75_TEMPERATURE_REG)
        return
    }
    data16 = swap_uint16(data16)
    if (data16 & (^(temp_mask))) != 0x00 {
        cli.Printf("e", " LM75 Register %d is incorrect.  Expect Lower 7 bits to be 0.  Read 0x%x\n", LM75_TEMPERATURE_REG, data16)
        err = errType.FAIL
        return
    }

    return
}


func ReadDevId(devName string) (id byte, err int) {
    id, err = smbus_read8(devName, LM75_ID_REG)
    if err != errType.SUCCESS {
        cli.Printf("e", " i2cTest:  Read reg-0x%x failed\n", LM75_ID_REG)
        return
    }
    return
}

func ReadTemp(devName string) (integer int64, dec int64, err int) {
    var data16 uint16
    var data8 int8
    var udata8 uint8

    data16, err = smbus_read16(devName, LM75_TEMPERATURE_REG)
    if err != errType.SUCCESS {
        cli.Printf("e", " i2cTest:  Read reg-0x%x failed\n", LM75_TEMPERATURE_REG)
        return
    }

    data16 = swap_uint16(data16)

    if (data16 & 0x80) == 0x80{
        dec = 5
    }

    udata8 = uint8(data16 >> 8)
    //is it negative   check if msb is set?   Ugly code due to golang strict casting and rules
    if udata8 & 0x80 == 0x80{
        udata8 = udata8 & 0x7F    //mask sign bit
        udata8 = 0x80 - udata8    //two's complement
        data8 = 0 - int8(udata8)  //make it negative
    } else {
        data8 = int8(udata8)
    }

    integer = int64(data8)

    return
}

func GetTemperature(devName string) (temperatures []float64, err int) {
    dig, frac, err := ReadTemp(devName)
    if err != errType.SUCCESS {
        temperatures = append(temperatures, 2989)
        
    } else {
        temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    }
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

