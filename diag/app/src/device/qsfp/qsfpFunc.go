package qsfp

import (
    "common/errType"
    "protocol/smbus"
)

func ReadBytes(devName string, offset uint64, numBytes uint64) (data []byte, err int) {
    var i uint64

    data = make([]byte, numBytes)

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    for i = 0; i < numBytes; i++ {
        data[i], err = smbus.ReadByte(devName, offset+i)
        if err != errType.SUCCESS {
            return
        }
    }

    return
}

func ReadBytesUpper(devName string, offset uint64, numBytes uint64, page byte) (data []byte, err int) {
//    err = smbus.Open(devName)
//    if err != errType.SUCCESS {
//        return
//    }
//    defer smbus.Close()
//
//    err = smbus.WriteByte(devName, 127, page)
//    if err != errType.SUCCESS {
//        return
//    }

    data, err = ReadBytes(devName, offset, numBytes)
    if err != errType.SUCCESS {
        return
    }

    return
}

func GetFieldInfo(qsfpTbl []qsfpPage_t, field string) (fieldInfo qsfpPage_t, err int) {
    for _, fieldInfo = range(qsfpTbl) {
        if fieldInfo.name == field {
            return
        }
    }
    err = errType.INVALID_PARAM
    return
}

func ReadField(devName string, field string) (data []byte, err int) {
    fieldInfo, err := GetFieldInfo(lowerPage, field)
    if err != errType.SUCCESS {
        return
    }

    data, err = ReadBytes(devName, fieldInfo.offset, fieldInfo.numBytes)
    return
}

func ReadFieldUpper(devName string, field string, page byte) (data []byte, err int) {
    var upperTbl []qsfpPage_t

    if page == 0 {
        upperTbl = upperPage00
    } else {
        err = errType.INVALID_PARAM
        return
    }

    fieldInfo, err := GetFieldInfo(upperTbl, field)
    if err != errType.SUCCESS {
        return
    }

    data, err = ReadBytesUpper(devName, fieldInfo.offset, fieldInfo.numBytes, page)
    return
}

func ReadId(devName string) (id byte, err int) {
    data, err := ReadFieldUpper(devName, "ID", 0)
    id = data[0]
    return
}

func LaserEnDis(devName string, enDis int) (err int) {
    var data byte

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    if enDis == ENABLE {
        data = 0x0
    } else {
        data =0xF
    }

    err = smbus.WriteByte(devName, 0x86, data)
    if err != errType.SUCCESS {
        return
    }

    return
}

func LaserEnable(devName string) (err int) {
    err = LaserEnDis(devName, ENABLE)
    return
}

func LaserDisable(devName string) (err int) {
    err = LaserEnDis(devName, DISABLE)
    return
}
