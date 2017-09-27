package pcf85263a

import (
    "common/cli"
    "common/errType"
    "common/i2c"
    "common/misc"
    "hardware/pcf85263aReg"
)


func ReadTime(devName string) (year byte, month byte, day byte, hour byte, minute byte, second byte, err int) {
    data, err := i2c.Read(devName, pcf85263aReg.YEARS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    year = data[0]
    year = (year & 0xF) + (year >> 4) *10

    data, err = i2c.Read(devName, pcf85263aReg.MONTHS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    month = data[0]
    month = (month & 0xF) + ((month >> 4) & 1) * 10

    data, err = i2c.Read(devName, pcf85263aReg.DAYS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    day = data[0]
    day = (day & 0xF) + ((day >> 4) & 3) * 10

    data, err = i2c.Read(devName, pcf85263aReg.HOURS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    hour = data[0]
    hour = (hour & 0xF) + ((hour >> 4) & 3) * 10

    data, err = i2c.Read(devName, pcf85263aReg.MINUTES, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    minute = data[0]
    minute = (minute & 0xF) + ((minute >> 4) & 7) * 10

    data, err = i2c.Read(devName, pcf85263aReg.SECONDS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    second = data[0]
    second = (second & 0xF) + ((second >> 4) & 7) * 10

    return
}
