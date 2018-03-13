package adt7462

import (
    "fmt"

    "common/cli"
    "common/dmutex"
    "common/errType"
    "common/misc"
    "protocol/smbus"
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
    NUM_PWM   = 4
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
    {TACH_ENABLE,     0, 8, 0xFF}, // Enable all TACHs
    {PWM1_TO_PWM4_MAX,0, 8, 0xFF}, // MAX speed setting
}
var pwmConfigTbl = []config {
    {PWM1_DUTY_CYCLE, 0, 8, 0x80}, // PWM1 initial duty cycle
    {PWM2_DUTY_CYCLE, 0, 8, 0x80}, // PWM2 initial duty cycle
    {PWM3_DUTY_CYCLE, 0, 8, 0x80}, // PWM3 initial duty cycle
}

func Setup(devName string) (err int) {
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

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
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

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
        tachLsbReg = TACH1_VALUE_LSB + fanIdx * 2
        tachMsbReg = TACH1_VALUE_MSB + fanIdx * 2
    } else { // TACH 5-8
        tachLsbReg = TACH1_VALUE_LSB + fanIdx * 2 + 2
        tachMsbReg = TACH1_VALUE_MSB + fanIdx * 2 + 2
    }

    tachLsb, err = smbus.ReadByte(devName, tachLsbReg)
    tachMsb, err = smbus.ReadByte(devName, tachMsbReg)

    // Calculate rpm
    // 9k*60/tach
    temp = (uint64(tachMsb) << 8) | uint64(tachLsb)
    rpm = 90000*60/temp
    if rpm < 100 {
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
    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

    var pwmReg uint64
    var pwmVal uint64

    if pwmIdx > FAN_4_PWM {
        err = errType.SUCCESS
        return
    }

    if pct > 100 {
        err = errType.SUCCESS
        return
    }

    pwmReg = PWM1_DUTY_CYCLE + pwmIdx
    pwmVal = pct * 100 / 39
    if pct > 0 && byte(pwmVal) == 0 {
        pwmVal = 0xFF
    }

    cli.Printf("i", "Reg: 0x%x, value0x%x\n", pwmReg, byte(pwmVal))
    err = smbus.WriteByte(devName, pwmReg, byte(pwmVal))
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

    err = dmutex.Lock(devName)
    if err != errType.SUCCESS {
        return
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    defer dmutex.Unlock(devName)

    tempLsbReg = LOCAL_TEMP_VALUE_LSB + tempIdx * 2
    tempMsbReg = LOCAL_TEMP_VALUE_MSB + tempIdx * 2

    //cli.Printf("i", "Lsb: 0x%x, Msb: 0x%x\n", tempLsbReg, tempMsbReg)
    tempLsb, err = smbus.ReadByte(devName, tempLsbReg)
    tempMsb, err = smbus.ReadByte(devName, tempMsbReg)

    integer = -64 + int(tempMsb)
    frac = 25 * int(tempLsb >> 6)

    return
}

func DispStatus(devName string) (err int) {
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
    vrmTitle := []string {"Local", "Remote-1", "Remote-2", "Remote-3"}
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
    return
}

