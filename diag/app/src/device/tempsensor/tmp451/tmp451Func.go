package tmp451

import (
    "fmt"

    "common/cli"
    "common/errType"
    "protocol/smbus"
)


func I2cTest(devname string) (err int) {
    var id byte 
    var data8, temp8 uint8
    //var temp_mask uint16 = uint16(LM75_TEMPERATURE_MASK)

    err = smbus.Open(devname)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devname, MANUFACTURING_ID_RD)
    if err != errType.SUCCESS {
        cli.Println("e", " i2cTest:  Read Dev ID Failed")
        return
    }

    if id != MANUFACTURING_ID_VALUE {
        cli.Printf("e", " TMP451 ID is incorrect.  Expect 0x%.02x   Read 0x%x\n", MANUFACTURING_ID_VALUE, id)
        err = errType.FAIL
        return
    }

    data8, err = smbus.ReadByte(devname, LOCAL_HIGH_LIMIT_RD)
    if err != errType.SUCCESS {
        cli.Printf("e", " i2c Read Byte:  Read reg-0x%x failed", LOCAL_HIGH_LIMIT_RD)
        return
    }
    err = smbus.WriteByte(devname, LOCAL_HIGH_LIMIT_WR, (data8+1))
    if err != errType.SUCCESS {
        cli.Println("e", " i2c Write Byte:  Read reg-0x%x failed")
        return
    }
    temp8, err = smbus.ReadByte(devname, LOCAL_HIGH_LIMIT_RD)
    if err != errType.SUCCESS {
        cli.Printf("e", " i2c Read Byte:  Read reg-0x%x failed", LOCAL_HIGH_LIMIT_RD)
        return
    }
    if (data8 + 1) != temp8 {
        cli.Printf("e", " TMP451 LOCAL HIGH LIMIT.  Expect 0x%.02x   Read 0x%x\n", (data8 + 1), temp8)
        err = errType.FAIL
        return
    }
    err = smbus.WriteByte(devname, LOCAL_HIGH_LIMIT_WR, data8)
    if err != errType.SUCCESS {
        cli.Println("e", " i2c Write Byte:  Read reg-0x%x failed")
        return
    }
    return
}


func ReadMfgId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, MANUFACTURING_ID_RD)
    return
}

/* On Taormina, remote sensor is not hooked up */
func ReadTemp(devName string, channel byte) (integer int64, dec int64, err int) {
    var tempHighAddr uint64
    var tempLowAddr uint64
    var decimal float64
    var config_reg, tempHighByte, tempLowByte byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    config_reg, err = smbus.ReadByte(devName, CONFIG_RD)
    if err != errType.SUCCESS {
        return
    }

    switch channel {
    case LOCAL_TEMP:
        tempHighAddr = LOCAL_TEMP_HIGH_RD
        tempLowAddr = LOCAL_TEMP_LOW_RD
    case REMOTE_TEMP:
        tempHighAddr = REMOTE_TEMP_HIGH_RD
        tempLowAddr = REMOTE_TEMP_LOW_RD
    default:
        err = errType.INVALID_PARAM
        return
    }

    tempLowByte, err = smbus.ReadByte(devName, tempLowAddr)
    if err != errType.SUCCESS {
        return
    }

    tempHighByte, err = smbus.ReadByte(devName, tempHighAddr)
    if err != errType.SUCCESS {
        return
    }

    if (config_reg & CONFIG_RANGE_BIT) == CONFIG_RANGE_BIT {
        integer = int64(tempHighByte) - 64
    } else {
        integer = int64(tempHighByte)

    }

    //DEC IS .0625 * (BITS[7:4] >> 4)
    decimal = float64(tempLowByte>>4) * 0.0625 * 1000
    dec = int64(decimal) 


    return
}


func GetTemperature(devName string) (temperatures []float64, err int) {
    dig, frac, err := ReadTemp(devName, LOCAL_TEMP)
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

    integer, dec, err := ReadTemp(devName, LOCAL_TEMP)
    if err != errType.SUCCESS {
        return err
    }

    tmpStr = fmt.Sprintf("%s %d.%01d", tmpStr, integer, dec)
    cli.Println("i", tmpStr)

    return
}


