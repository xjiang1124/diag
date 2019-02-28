package pcf85263a

import (
    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/i2c_c"
    "protocol/smbus"
)

func ReadTime_C(devName string) (year byte, month byte, day byte, hour byte, minute byte, second byte, err int) {
    data, err := i2c_c.Read(devName, YEARS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    year = data[0]
    year = (year & 0xF) + (year >> 4) *10

    data, err = i2c_c.Read(devName, MONTHS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    month = data[0]
    month = (month & 0xF) + ((month >> 4) & 1) * 10

    data, err = i2c_c.Read(devName, DAYS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    day = data[0]
    day = (day & 0xF) + ((day >> 4) & 3) * 10

    data, err = i2c_c.Read(devName, HOURS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    hour = data[0]
    hour = (hour & 0xF) + ((hour >> 4) & 3) * 10

    data, err = i2c_c.Read(devName, MINUTES, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    minute = data[0]
    minute = (minute & 0xF) + ((minute >> 4) & 7) * 10

    data, err = i2c_c.Read(devName, SECONDS, misc.ONE_BYTE)
    if err != errType.SUCCESS {
        cli.Println("d", "failed to read RTC data")
    }
    second = data[0]
    second = (second & 0xF) + ((second >> 4) & 7) * 10

    return
}

func ReadTime(devName string) (year byte, month byte, day byte, hour byte, minute byte, second byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err := smbus.ReadByte(devName, YEARS)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }
    year = data
    year = (year & 0xF) + (year >> 4) *10

    data, err = smbus.ReadByte(devName, MONTHS)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }
    month = data
    month = (month & 0xF) + ((month >> 4) & 1) * 10

    data, err = smbus.ReadByte(devName, DAYS)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }
    day = data
    day = (day & 0xF) + ((day >> 4) & 3) * 10

    data, err = smbus.ReadByte(devName, HOURS)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }
    hour = data
    hour = (hour & 0xF) + ((hour >> 4) & 3) * 10

    data, err = smbus.ReadByte(devName, MINUTES)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }
    minute = data
    minute = (minute & 0xF) + ((minute >> 4) & 7) * 10

    data, err = smbus.ReadByte(devName, SECONDS)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }
    second = data
    second = (second & 0xF) + ((second >> 4) & 7) * 10

    return
}

func DispTime(devName string) (err int) {
    year, month, day, hour, minute, second, err := ReadTime(devName)

    if err != errType.SUCCESS {
        return
    }

    cli.Printf("i", "RTC current time: %02d/%02d/%02d(m/d/n) %02d:%02d:%02d(h:m:s)\n", month, day, year, hour, minute, second)

    return
}

func SetTime(devName string, year byte, month byte, day byte, hour byte, minute byte, second byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    year = byte(misc.GetOnes(int(year)) | (misc.GetTens(int(year)) << 4))
    err = smbus.WriteByte(devName, YEARS, year)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }

    month = byte(misc.GetOnes(int(month)) | (misc.GetTens(int(month)) << 4))
    err = smbus.WriteByte(devName, MONTHS, month)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }

    day = byte(misc.GetOnes(int(day)) | (misc.GetTens(int(day)) << 4))
    err = smbus.WriteByte(devName, DAYS, day)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }

    hour = byte(misc.GetOnes(int(hour)) | (misc.GetTens(int(hour)) << 4))
    err = smbus.WriteByte(devName, HOURS, hour)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }

    minute = byte(misc.GetOnes(int(minute)) | (misc.GetTens(int(minute)) << 4))
    err = smbus.WriteByte(devName, MINUTES, minute)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }

    second = byte(misc.GetOnes(int(second)) | (misc.GetTens(int(second)) << 4))
    second = second | 0x80
    err = smbus.WriteByte(devName, SECONDS, second)
    if err != errType.SUCCESS {
        cli.Println("e", "failed to read RTC data")
    }

    return
}
