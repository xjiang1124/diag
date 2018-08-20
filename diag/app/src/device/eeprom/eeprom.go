package eeprom

import (
    "fmt"
    "os"

    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/smbus"
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
    entry{"PRODUCT_NAME",   STRING, 10,  20, []byte("NIC MTP             ")},
    entry{"SERIAL_NUM",     STRING, 30,  20, []byte("1234567890          ")},
    entry{"COMPANY_NAME",   STRING, 50,  20, []byte("Pensando Systems Inc")},
    entry{"MFG_DEVIATION",  STRING, 70,  20, []byte("0                   ")},
    entry{"MFG_BITS",       STRING, 90,  2,  []byte("00")},
    entry{"ENG_BITS",       STRING, 92,  2,  []byte("00")},
    entry{"MAC_ADDR",       STRING, 94,  12, []byte("AABBCCDDEEFF")},
    entry{"NUM_OF_MAC",     STRING, 106, 2,  []byte("00")},
}

var naples100Tbl = []entry {
    entry{"Common Format Version",      			STRING,		0,		1,	[]byte("1")},
    entry{"Internal Use Area Offset",   			STRING,		1,		1,	[]byte("C")},
    entry{"Chassis Area Offset",   					STRING,		2,		1,	[]byte("0")},
    entry{"Board Info Offset",   					STRING,		3,		1,	[]byte("0")},
    entry{"Product Area Offset",     				STRING,		4,		1,	[]byte("0")},
    entry{"Multi-Record Area Offset",   			STRING,		5,		1,	[]byte("0")},
    entry{"PAD",  									STRING, 	6,		1,	[]byte("0")},
    entry{"Common Header Checksum",     			STRING, 	7,		1,  []byte("F2")},
    
    
    entry{"Board Info Format Version",				STRING, 	8,		1,  []byte("1")},
    entry{"Board Area Length",       				STRING,		9,		1,	[]byte("A")},
    entry{"Language Code",     						STRING,		10, 	1,  []byte("0")},
    entry{"FRU File ID Type/Length",     			STRING,		11, 	1,  []byte("2")},
    entry{"FRU File ID",     						STRING,		12, 	1,  []byte("2")},
    entry{"Product Name Type/Length",     			STRING,		13, 	1,  []byte("C")},
    entry{"Product Name",     						STRING,		14, 	10, []byte("00000000000000000000")},
    entry{"Part Number Type/Length",     			STRING,		24, 	1,  []byte("10")},
    entry{"Part Number",     						STRING,		25, 	13, []byte("16180D101010130D1011002110")},
    entry{"Serial Number Type/Length",     			STRING,		38, 	1,  []byte("E")},
    entry{"Serial Number",     						STRING,		39, 	11, []byte("00000000000")},
    entry{"Manufacturer Type/Length",     			STRING,		50, 	1,  []byte("1A")},
    entry{"Manufacturer",     						STRING,		51, 	21, []byte("PENSANDO SYSTEMS INC.")},
    entry{"Manufacturing Date Type/Length", 		STRING,		72, 	1,  []byte("9")},
    entry{"Manufacturing Date", 					STRING,		73, 	3,  []byte("000000")},
    entry{"SKU Type/Length",     					STRING,		76, 	1,  []byte("D")},
    entry{"SKU",     								STRING,		77, 	4,  []byte("00000000")},
    entry{"Engineering Change Level Type/Length",	STRING,		81, 	1,  []byte("E")},
    entry{"Engineering Change Level",     			STRING,		82, 	1,  []byte("1")},
    entry{"Vendor IANA Type/Length",     			STRING,		83, 	1,  []byte("E")},
    entry{"Vendor IANA",     						STRING,		84, 	4,  []byte("12")},
    entry{"PAD",     								STRING,		88, 	1,  []byte("0")},
    entry{"Board Info Area Checksum",     			STRING, 	89,		1,  []byte("0")},


    entry{"Internal Use Area Format Version",     	STRING,		96, 	1,  []byte("1")},
    entry{"Internal Use Area Length",     			STRING,		97, 	1,  []byte("2")},
    entry{"Format Revision",     					STRING,		98, 	1,  []byte("1")},
    entry{"Board ID",     							STRING,		99, 	4,  []byte("00000001")},
    entry{"Number of MAC Address",     				STRING,		103, 	2,  []byte("18")},
    entry{"MAC Address Base",     					STRING,		106, 	6,  []byte("000000000000")},
    entry{"PAD",     								STRING,		112, 	1,  []byte("0")},
    entry{"Internal Use Area Checksum",     		STRING, 	120,	1,  []byte("0")},
}

var EepromTbl []entry
var brdInfoChk, intUseChk uint

func init() {
    cardType := os.Getenv("CARD_TYPE")
    if cardType == "MTP" {
        EepromTbl = mtpTbl
    } else if cardType == "NAPLES100" {
        EepromTbl = naples100Tbl
    } else {
        cli.Println("e", "Unsupported card:", cardType)
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
        //cli.Printf("d", "offset=0x%x, data=0x%x\n",offset+i, writeData)
        misc.SleepInUSec(2000)
        err = smbus.WriteByte(devName, uint64(offset+i), writeData)
    }
    return
}

func readField(devName string, offset int, numBytes int) (data []byte, err int) {
    data = make([]byte, numBytes)

    for i := 0; i < numBytes; i++ {
        data[i], err = smbus.ReadByte(devName, uint64(offset+i))
        if err != errType.SUCCESS {
            return
        }
    }
    return
}

func ProgEeprom(devName string) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    for _, entry := range(EepromTbl) {
        if entry.Name == "Board Info Area Checksum" {
            entry.Value[0] = byte(0x100 - brdInfoChk % 0x100)
        } else if entry.Name == "Internal Use Area Checksum" {
            entry.Value[0] = byte(0x100 - intUseChk % 0x100)
        }
        err = writeField(devName, entry.Offset, entry.NumBytes, entry.Value)
        if err != errType.SUCCESS {
            return
        }
    }
    return
}

func UpdateMacMtp(devName string, mac []byte) (err int) {
    for _, entry := range(EepromTbl) {
        if entry.Name == "MAC_ADDR" {
            copy(entry.Value, mac)
            break
        }
    }
    return
}

func UpdateMac(devName string, mac uint64) (err int) {
    cardType := os.Getenv("CARD_TYPE")
    if cardType == "MTP" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "MAC_ADDR" {
//                copy(entry.Value, mac)
                for i := 0; i < entry.NumBytes; i++ {
                    entry.Value[i] = byte((mac >> uint64(48 - i * 8)) & 0xFF)
                }
                break
            }
        }
    } else if cardType == "NAPLES100" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "MAC Address Base" {
//                copy(entry.Value, mac)
                for i := 0; i < entry.NumBytes; i++ {
                    entry.Value[i] = byte((mac >> uint64(48 - i * 8)) & 0xFF)
                }
                break
            }
        }
        updateIntChk()
    }
    return
}

func updateIntChk() () {
    for _, entry := range(EepromTbl) {
        if (entry.Offset < 7) && (entry.Offset < 89) {
//            brdInfoChk += entry.Value
            brdInfoChk += calcSum(entry)
        } else if (entry.Offset > 95) && (entry.Offset < 120) {
//            intUseChk += entry.Value
            intUseChk += calcSum(entry)
        }
    }
}

func calcSum(item entry) (chkSum uint) {
    chkSum = 0
    for i := 0; i < item.NumBytes; i++ {
        chkSum += uint(item.Value[i])
    }
    return
}

func UpdateSn(devName string, sn []byte) (err int) {
    if len(sn) > 20 {
        cli.Println("f", "SN too long: ", sn)
        return
    }

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "MTP" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "SERIAL_NUM" {
                copy(entry.Value, sn)
                break
            }
        }
    } else if cardType == "NAPLES100" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "Serial Number" {
                copy(entry.Value, sn)
                break
            }
        }
        updateIntChk()
    }
    return
}

func UpdateDate(devName string, date []byte) (err int) {
    if len(date) != 6 {
        cli.Println("f", "Date format is invalid: ", date)
        return
    }

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "NAPLES100" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "Manufacturing Date" {
                copy(entry.Value, date)
                break
            }
        }
        updateIntChk()
    }
    return
}

func DispEeprom(devName string) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

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

