package adt7462

import (
    "os"
    "fmt"
    "time"
    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/smbus"
    //"hardware/hwinfo"
)

const (
    // FAN TACH index
    FAN_1_INLET  = 0x00
    FAN_1_OUTLET = 0x01
    FAN_2_INLET  = 0x02
    FAN_2_OUTLET = 0x03
    FAN_3_INLET  = 0x04
    FAN_3_OUTLET = 0x05
    FAN_4_INLET  = 0x06
    FAN_4_OUTLET = 0x07
    NUM_FAN      = 8

    // Temp sensor index
    LOCAL_TEMP    = 0x00
    REMOTE_1_TEMP = 0x01
    REMOTE_2_TEMP = 0x02
    REMOTE_3_TEMP = 0x03
    NUM_TEMP      = 4

    // PWM control
    FAN_1_PWM = 0x00
    FAN_2_PWM = 0x01
    FAN_3_PWM = 0x02
    FAN_4_PWM = 0x03
    NUM_PWM   = 3
)

type config struct {
    regAddr uint64
    startBit uint
    numBits uint
    val byte
}

var configTbl = []config {
    {PIN_CONF_1,      0, 8, 0x7F}, // Disable VID; Select TACH1-5, enable D1/3 --- default
    {PIN_CONF_2,      7, 1, 0x1},  // Select TACH6 --- default
    {PIN_CONF_3,      2, 2, 0x0},  // Select vBATT --- default
    {PIN_CONF_4,      2, 2, 0x3},  // Select PWM1/2 --- default
    {CONFIG_2,        2, 1, 0x1},  // High frequence mode
    {PWM1_CONFIG,     5, 3, 0x7},  // PWM1 manual mode
    {PWM2_CONFIG,     5, 3, 0x7},  // PWM2 manual mode
    {PWM3_CONFIG,     5, 3, 0x7},  // PWM3 manual mode
    {PWM4_CONFIG,     5, 3, 0x4},  // PWM4 manual mode
    {TACH_ENABLE,     0, 8, 0x3F}, // Enable all TACHs
    {PWM1_TO_PWM4_MAX,0, 8, 0xFF}, // MAX speed setting
    {DIGITAL_MASK,    7, 1, 0x1},  // Mask Chassis Intrustiion Alert
}
var pwmConfigTbl = []config {
    {PWM1_DUTY_CYCLE, 0, 8, 0x80}, // PWM1 initial duty cycle
    {PWM2_DUTY_CYCLE, 0, 8, 0x80}, // PWM2 initial duty cycle
    {PWM3_DUTY_CYCLE, 0, 8, 0x80}, // PWM3 initial duty cycle
}


func I2cTest(devName string) (err int) {
    var backup, data8 uint8
    patterns := []uint8{ 0xAA, 0x55 }
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    backup, err = smbus.ReadByte(devName, PWM1_MIN)
    if err != errType.SUCCESS {
        return
    }

    for i:=0; i<len(patterns); i++ {
        err = smbus.WriteByte(devName, PWM1_MIN, patterns[i])
        if err != errType.SUCCESS {
            return
        }

        data8, err = smbus.ReadByte(devName, PWM1_MIN)
        if err != errType.SUCCESS {
            return
        }

        if patterns[i] != data8 {
            err = errType.FAIL
            cli.Printf("e", "Device-%s Register 0x%x:  Wrote 0x%.04x   Read 0x%.04x\n", devName, PWM1_MIN, (patterns[i]), data8)
            return
        }
    }

    err = smbus.WriteByte(devName, PWM1_MIN, backup)
    if err != errType.SUCCESS {
        return
    }
    
    return
}


func ReadReg(devName string, addr uint32) (data byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = smbus.ReadByte(devName, uint64(addr))
    if err != errType.SUCCESS {
        return
    }
    return
}

func WriteReg(devName string, addr uint32, data byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    err = smbus.WriteByte(devName, uint64(addr), data)
    if err != errType.SUCCESS {
        return
    }
    return
}

func DumpReg(devName string) (err int) {
    var data byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    for _, entry := range(FAN_REGISTERS) {
        data, err = smbus.ReadByte(devName, entry.Address)
        if err != errType.SUCCESS {
            return
        }
        cli.Printf("i", "%-20s [%.02x] = %.02x\n", entry.Name, entry.Address, data)
    }
    return
}


func Setup(devName string) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    var data byte
    for _, config := range(configTbl) {
        data, err = smbus.ReadByte(devName, config.regAddr)
        if err != errType.SUCCESS {
            return
        }

        data, err = misc.SetBits8(data, config.val, config.startBit, config.numBits)
        if err != errType.SUCCESS {
            return
        }

        err = smbus.WriteByte(devName, config.regAddr, data)
        if err != errType.SUCCESS {
            return
        }
    }

    //============================
    // Enable to start working
    data, err = smbus.ReadByte(devName, CONFIG_1)
    if err != errType.SUCCESS {
        return
    }

    if (data & 0x80) == 0 {
        cli.Println("f", "Device ", devName, "not ready!")
        err = errType.FAIL
        return
    }

    data, err = misc.SetBits8(data, 1, 5, 1)
    if err != errType.SUCCESS {
        return
    }

    err = smbus.WriteByte(devName, CONFIG_1, data)
    if err != errType.SUCCESS {
        return
    }

    //============================
    for _, config := range(pwmConfigTbl) {
        data, err = smbus.ReadByte(devName, config.regAddr)
        if err != errType.SUCCESS {
            return
        }

        data, err = misc.SetBits8(data, config.val, config.startBit, config.numBits)
        if err != errType.SUCCESS {
            return
        }

        err = smbus.WriteByte(devName, config.regAddr, data)
        if err != errType.SUCCESS {
            return
        }
    }

    cli.Println("i", "Fan initialized")
    return
}

/*
    FanIdx  Tach
    0       fan_1_inlet
    1       fan_1_outlet
    2       fan_2_inlet
    3       fan_2_outlet
    4       fan_3_inlet
    5       fan_3_outlet
    6       7
    7       8
 */
func GetFanSpeed(devName string, fanIdx uint64) (rpm uint64, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    var tachLsbReg uint64
    var tachMsbReg uint64
    var tachLsb byte
    var tachMsb byte
    var temp uint64

    if fanIdx > FAN_4_OUTLET {
        err = errType.SUCCESS
        return
    }

    // TACH 1- 4
    if fanIdx <= 3 {
        tachLsbReg = TACH1_VALUE_LSB + (fanIdx * 2)
        tachMsbReg = TACH1_VALUE_MSB + (fanIdx * 2)
    } else { // TACH 5-8
        tachLsbReg = TACH1_VALUE_LSB + (fanIdx * 2) + 2
        tachMsbReg = TACH1_VALUE_MSB + (fanIdx * 2) + 2
    }

    tachLsb, err = smbus.ReadByte(devName, tachLsbReg)
    if err != errType.SUCCESS {
        cli.Println("f", "Failed to get tach LSB", devName)
    }
    tachMsb, err = smbus.ReadByte(devName, tachMsbReg)
    if err != errType.SUCCESS {
        cli.Println("f", "Failed to get tach MSB", devName)
    }

    // Calculate rpm
    // 9k*60/tach
    temp = (uint64(tachMsb) << 8) | uint64(tachLsb)
    if temp != 0 {
        rpm = 90000*60/temp 
        // if rpm < 100 {
        //    rpm = 0
        // }
    } else {
        rpm = 0
    }
    return
}

/*
    FanIdx  PWM
    0       fan_1: pwm1
    1       fan_2: pwm2
    2       fan_3: pwm3
    3       pwm4

    pct: fan speed percentage: 0-100
 */
func SetFanSpeed(devName string, pwmIdx uint64, pct uint64) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    var pwmReg uint64
    var pwmVal uint64
    var pwmVal_rd byte 

    if pwmIdx > FAN_4_PWM {
        err = errType.SUCCESS
        return
    }

    if pct > 100 {
        err = errType.SUCCESS
        return
    }

    pwmReg = PWM1_DUTY_CYCLE + pwmIdx
    pwmVal = (pct * 255) / 100
    if pct > 0 && byte(pwmVal) == 0 {
        pwmVal = 0xFF
    }

    //cli.Printf("i", "Reg: 0x%x, value0x%x\n", pwmReg, byte(pwmVal))
    for i:=0; i < 3; i++ {
        err = smbus.WriteByte(devName, pwmReg, byte(pwmVal))
        if err != errType.SUCCESS {
            cli.Println("e", "failed to set pwm register")
        }
        time.Sleep(time.Duration(5) * time.Millisecond)
        pwmVal_rd, err = smbus.ReadByte(devName, pwmReg)
        if err != errType.SUCCESS {
            cli.Println("e", "failed to read pwm register")
        }
        if pwmVal_rd == byte(pwmVal) {
            return
        }
        time.Sleep(time.Duration(500) * time.Millisecond)
    }
    cli.Printf("e", "%d: pwm reg value is not expected, read: 0x%x expected: 0x%x\n", pwmIdx, pwmVal_rd, byte(pwmVal))
    return
}

/*
    tempIdx     temp sensor
    0           local
    1           remote 1
    2           remote 2
    3           remote 3
 */
func GetTemp(devName string, tempIdx uint64) (integer int, frac int,  err int) {
    var tempLsbReg uint64
    var tempMsbReg uint64
    var tempLsb byte
    var tempMsb byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    tempLsbReg = LOCAL_TEMP_VALUE_LSB + tempIdx * 2
    tempMsbReg = LOCAL_TEMP_VALUE_MSB + tempIdx * 2

    //cli.Printf("i", "Lsb: 0x%x, Msb: 0x%x\n", tempLsbReg, tempMsbReg)
    tempLsb, err = smbus.ReadByte(devName, tempLsbReg)
    tempMsb, err = smbus.ReadByte(devName, tempMsbReg)

    integer = -64 + int(tempMsb)
    frac = 25 * int(tempLsb >> 6)

    return
}

func GetTemperature(devName string) (temperatures []float64, err int) {
    dig, frac, err := GetTemp(devName, 0)
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    return
}

func DispStatus(devName string) (err int) {


    cardType := os.Getenv("CARD_TYPE")
        if cardType == "TAORMINA" {
        var fmtStr = "%-19s"
        var fmtNameStr = "%-20s"
        var outStr string
        var outStrTemp string
        var integer int
        var frac int
        var data byte
        var rpm [8]uint64

        //TACH_ENABLE            [07] = 3f
        data, err = ReadReg(devName, TACH_ENABLE) 
        if err != errType.SUCCESS {
            cli.Println("f", "Failed register read to device ", devName)
            return
        }
        //If tach enable is zero, part isn't initialized...   
        if data == 0x00 {
            err = Setup(devName)
            if err != errType.SUCCESS {
                cli.Println("f", "Setup of ", devName, " Failed")
                return
            }
            misc.SleepInSec(2)
        }
        // Fan speed
        titles := []string {"FAN1 Inlet/Outlet", "FAN2 Inlet/Outlet", "FAN3 Inlet/Outlet", "Local Temp"}
        outStr = fmt.Sprintf(fmtNameStr, "NAME")
        for _, title := range(titles) {
            outStr = outStr + fmt.Sprintf(fmtStr, title)
        }
        cli.Println("i", "=================================")
        cli.Println("i", outStr)

        outStr = fmt.Sprintf(fmtNameStr, devName)

        for i := 0; i < NUM_FAN; i++ {
            rpm[i], err = GetFanSpeed(devName, uint64(i))
            if err != errType.SUCCESS {
                cli.Println("f", "Failed to get fan speed!", i, err)
                return
            }
        }
        for i := 0; i < 6; i+=2 {
            outStrTemp = fmt.Sprintf("%d / %d", rpm[i], rpm[i+1])
            outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        }
        // Temp
        integer, frac, err = GetTemp(devName, 0)
        if err != errType.SUCCESS {
            cli.Println("f", "Failed to get temp!", err)
            return
        }
        outStrTemp = fmt.Sprintf("%d.%02d", integer, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        cli.Println("i", outStr)


    } else {
        var fmtDig string = "%d"
        var fmtDigFrac string = "%d.%02d"
        var fmtStr = "%-15s"
        var fmtNameStr = "%-20s"
        var outStr string
        var outStrTemp string
        var rpm uint64
        var integer int
        var frac int
        // Fan speed
        titles := []string {"FAN1-Inlet", "FAN1-Outlet", "FAN2-Inlet", "FAN2-Outlet",
                              "FAN3-Inlet", "FAN3-Outlet", "FAN4-Inlet", "FAN4-Outlet"}
        outStr = fmt.Sprintf(fmtNameStr, "NAME")
        for _, title := range(titles) {
            outStr = outStr + fmt.Sprintf(fmtStr, title)
        }
        cli.Println("i", "=================================")
        cli.Println("i", outStr)

        outStr = fmt.Sprintf(fmtNameStr, devName)

        for i := 0; i < NUM_FAN; i++ {
            rpm, err = GetFanSpeed(devName, uint64(i))
            if err != errType.SUCCESS {
                cli.Println("f", "Failed to get fan speed!", i, err)
                return
            }
            if rpm == 65535 {
                rpm = 0
            }
            outStrTemp = fmt.Sprintf(fmtDig, rpm)
            outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        }
        cli.Println("i", outStr)

        // Temp
        vrmTitle := []string {"Local", "Outlet", "Inlet-1", "Inlet-2"}
        outStr = fmt.Sprintf(fmtNameStr, "NAME")
        for _, title := range(vrmTitle) {
            outStr = outStr + fmt.Sprintf(fmtStr, title)
        }
        cli.Println("i", "--------------------")
        cli.Println("i", outStr)

        outStr = fmt.Sprintf(fmtNameStr, devName)

        for i := 0; i < NUM_TEMP; i++ {
            integer, frac, err = GetTemp(devName, uint64(i))
            if err != errType.SUCCESS {
                cli.Println("f", "Failed to get temp!", i, err)
                return
            }
            outStrTemp = fmt.Sprintf(fmtDigFrac, integer, frac)
            outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        }
        cli.Println("i", outStr+"\n")
    }
    return
}

