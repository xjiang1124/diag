package eeprom

import (
    "fmt"
    "os"

    "common/cli"
    "common/errType"
    "protocol/pmbus"
)

const(
    INT8 = 0
    INT16 = 1
    INT32 = 2
    INT64 = 3
    STRING = 4
)

// EEPROM entry data structure
type entry struct {
    Name     string
    DataType int
    Offset   int
    NumBytes int
    Value    []byte
}

var mtpTbl = []entry {
    entry{"NUM_BYTES",      STRING, 0,   4,  []byte("0256")},
    entry{"HW_MAJOR_REV",   STRING, 4,   2,  []byte("00")},
    entry{"HW_MINOR_REV",   STRING, 6,   4,  []byte("0100")},
    entry{"PRODUCT_NAME",   STRING, 10,  20, []byte("NIC MTP")},
    entry{"SERIAL_NUM",     STRING, 30,  20, []byte("1234567890")},
    entry{"COMPANY_NAME",   STRING, 50,  20, []byte("Pensando Systems Inc")},
    entry{"MFG_DEVIATION",  STRING, 70,  20, []byte("0")},
    entry{"MFG_BITS",       STRING, 90,  2,  []byte("00")},
    entry{"ENG_BITS",       STRING, 92,  2,  []byte("00")},
    entry{"MAC_ADDR",       STRING, 94,  12, []byte("AABBCCDDEEFF")},
    entry{"NUM_OF_MAC",     STRING, 106, 2,  []byte("00")},
}

var EepromTbl []entry

func init() {
    cardName := os.Getenv("CARD_NAME")
    if cardName == "MTP" {
        EepromTbl = mtpTbl
    } else {
        cli.Println("f", "Unsupported card: ", cardName)
    }
}

func writeField(devName string, offset int, numBytes int, data []byte) (err int) {
    var writeData byte

    if numBytes < len(data) {
        err = errType.INVALID_PARAM
        cli.Println("f", "data lenght more than number of bytes! numBytes:", numBytes, "data length:", len(data))
        return
    }
    for i := 0; i < numBytes; i++ {
        if i < len(data) {
            writeData = data[i]
        } else {
            writeData = 0
        }
        err = pmbus.WriteByte(devName, uint64(offset+i), writeData)
    }
    return
}

func readField(devName string, offset int, numBytes int) (data []byte, err int) {
    data = make([]byte, numBytes)

    for i := 0; i < numBytes; i++ {
        data[i], err = pmbus.ReadByte(devName, uint64(offset+i))
        if err != errType.SUCCESS {
            return
        }
    }
    return
}

func ProgEeprom(devName string) (err int) {
    for _, entry := range(EepromTbl) {
        err = writeField(devName, entry.Offset, entry.NumBytes, entry.Value)
        if err != errType.SUCCESS {
            return
        }
    }
    return
}

func UpdateMac(devName string, mac []byte) (err int) {
    if len(mac) != 12 {
        cli.Println("f", "Invalid mac length", mac, len(mac))
        err = errType.INVALID_PARAM
        return
    }

    for _, entry := range(EepromTbl) {
        if entry.Name == "MAC_ADDR" {
            copy(entry.Value, mac)
            break
        }
    }
    return
}

func DispEeprom(devName string) (err int) {
    var data []byte
    fmtStr := "%-20s%-20s"
    var outStr string
    for _, entry := range(EepromTbl) {
        data, err = readField(devName, entry.Offset, entry.NumBytes)
        if err != errType.SUCCESS {
            cli.Println("f", "Failed to read field at offset", entry.Offset, "number of bytes", entry.NumBytes)
            return
        }
        dataStr := string(data[:entry.NumBytes])
        outStr = fmt.Sprintf(fmtStr, entry.Name, dataStr)
        cli.Println("i", outStr)
    }
    return
}

