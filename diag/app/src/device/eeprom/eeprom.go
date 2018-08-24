package eeprom

import (
    "fmt"
    "os"
    "strconv"
    "bytes"
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
    entry{"Common Format Version",      			INT8,		0,		1,	[]byte{1}},
    entry{"Internal Use Area Offset",   			INT8,		1,		1,	[]byte{0xC}},
    entry{"Chassis Area Offset",   					INT8,		2,		1,	[]byte{0}},
    entry{"Board Info Offset",   					INT8,		3,		1,	[]byte{0}},
    entry{"Product Area Offset",     				INT8,		4,		1,	[]byte{0}},
    entry{"Multi-Record Area Offset",   			INT8,		5,		1,	[]byte{0}},
    entry{"PAD",  									INT8, 		6,		1,	[]byte{0}},
    entry{"Common Header Checksum",     			INT8,	 	7,		1,  []byte{0xF2}},
    
    
    entry{"Board Info Format Version",				INT8, 		8,		1,  []byte{1}},
    entry{"Board Area Length",       				INT8,		9,		1,	[]byte{0xA}},
    entry{"Language Code",     						INT8,		10, 	1,  []byte{0}},
    entry{"FRU File ID Type/Length",     			INT8,		11, 	1,  []byte{2}},
    entry{"FRU File ID",     						INT8,		12, 	1,  []byte{2}},
    entry{"Product Name Type/Length",     			INT8,		13, 	1,  []byte{0xC}},
    entry{"Product Name",     						STRING,		14, 	10, []byte{0x10, 0x10, 0x10, 0x10, 
        0x10, 0x10, 0x10, 0x10, 0x10, 0x10}},
    entry{"Part Number Type/Length",     			INT8,		24, 	1,  []byte{0x10}},
    entry{"Part Number",     						STRING,		25, 	13, []byte{0x16, 0x18, 0x0D, 0x38, 
        0x38, 0x38, 0x38, 0x0D, 0x38, 0x38, 0x00, 0x38, 0x38}},
    entry{"Serial Number Type/Length",     			INT8,		38, 	1,  []byte{0xE}},
    entry{"Serial Number",     						STRING,		39, 	11, []byte{0x10, 0x10, 0x10, 0x10, 
        0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10}},
    entry{"Manufacturer Type/Length",     			INT8,		50, 	1,  []byte{0x1A}},
    entry{"Manufacturer",     						STRING,		51, 	21, []byte{0x30, 0x25, 0x2E, 0x33, 
        0x25, 0x2E, 0x24, 0x2F, 0x00, 0x33, 0x39, 0x33, 0x34, 0x25, 0x2D, 0x33, 0x00, 0x29, 0x2E, 0x23, 0x0E}},
    entry{"Manufacturing Date Type/Length", 		INT8,		72, 	1,  []byte{9}},
    entry{"Manufacturing Date", 					INT8,		73, 	3,  []byte{0, 0, 0}},
    entry{"SKU Type/Length",     					INT8,		76, 	1,  []byte{0xD}},
    entry{"SKU",     								INT8,		77, 	4,  []byte{0, 0, 0, 0}},
    entry{"Engineering Change Level Type/Length",	INT8,		81, 	1,  []byte{0xE}},
    entry{"Engineering Change Level",     			INT8,		82, 	1,  []byte{1}},
    entry{"Vendor IANA Type/Length",     			INT8,		83, 	1,  []byte{0xE}},
    entry{"Vendor IANA",     						INT8,		84, 	4,  []byte{0, 0, 0, 0x12}},
    entry{"PAD",     								INT8,		88, 	1,  []byte{0}},
    entry{"Board Info Area Checksum",     			INT8,	 	89,		1,  []byte{0}},


    entry{"Internal Use Area Format Version",     	INT8,		96, 	1,  []byte{1}},
    entry{"Internal Use Area Length",     			INT8,		97, 	1,  []byte{2}},
    entry{"Format Revision",     					INT8,		98, 	1,  []byte{1}},
    entry{"Board ID",     							INT8,		99, 	4,  []byte{0, 0, 0, 1}},
    entry{"Number of MAC Address",     				INT8,		103, 	2,  []byte{0, 0x18}},
    entry{"MAC Address Base",     					INT8,		106, 	6,  []byte{0, 0, 0, 0, 0, 0}},
    entry{"PAD",     								INT8,		112, 	1,  []byte{0}},
    entry{"Internal Use Area Checksum",     		INT8,	 	120,	1,  []byte{0}},
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

func max(x, y int) (m int) {
    if x > y {
        return x
    } else {
        return y
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
        if entry.Name == "Serial Number" {
            dftArray := []byte{0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10}
            if bytes.Equal(entry.Value, dftArray) {
                cli.Println("i", "skip sn")
                continue
            }
        } else if entry.Name == "Manufacturing Date" {
            dftArray := []byte{0, 0, 0}
            if bytes.Equal(entry.Value, dftArray) {
                cli.Println("i", "skip date")
                continue
            }
        } else if entry.Name == "MAC Address Base" {
            dftArray := []byte{0, 0, 0, 0, 0, 0}
            if bytes.Equal(entry.Value, dftArray) {
            cli.Println("i", "skip mac")
            continue
            }
        }
        
        if entry.Name == "Board Info Area Checksum" {
            entry.Value[0] = byte(0x100 - brdInfoChk % 0x100)
//            binary.Write(entry.Value, binary.LittleEndian, (0x100 - brdInfoChk % 0x100))
//            entry.Value = []byte(strconv.FormatUint(uint64(0x100 - brdInfoChk % 0x100), 16))
            
        } else if entry.Name == "Internal Use Area Checksum" {
            entry.Value[0] = byte(0x100 - intUseChk % 0x100)
        }
        
        if entry.DataType == STRING {
            data := make([]byte, entry.NumBytes)
            copy(data, entry.Value)
            for i := 0; i < entry.NumBytes; i++ {
                data[i] += 0x20
            }
            cli.Println("i", "program " + entry.Name + " value " + string(data) + " len ", len(entry.Value))
        } else {
            outStr := fmt.Sprintf("%s 0x%x len %d", entry.Name, entry.Value, len(entry.Value))
            cli.Println("i", outStr)
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

func UpdateMac(devName string, mac []byte) (err int) {
    cardType := os.Getenv("CARD_TYPE")
    if cardType == "MTP" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "MAC_ADDR" {
                copy(entry.Value, mac)
//                for i := 0; i < entry.NumBytes; i++ {
//                    entry.Value[i] = byte((mac >> uint64(48 - i * 8)) & 0xFF)
//                }
                break
            }
        }
    } else if cardType == "NAPLES100" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "MAC Address Base" {
                copy(entry.Value, mac)
//                for i := 0; i < entry.NumBytes; i++ {
//                    entry.Value[i] = byte((mac >> uint64(40 - i * 8)) & 0xFF)
//                    cli.Println("i", "mac ", i, " ", entry.Value[i], "  ", (mac >> uint64(40 - i * 8)) & 0xFF)
//                }
                break
            }
        }
        updateIntChk()
    }
    return
}

func updateIntChk() () {
    for _, entry := range(EepromTbl) {
        if (entry.Offset > 7) && (entry.Offset < 89) {
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
                for i := 0; i < entry.NumBytes; i++ {
                    sn[i] -= 0x20
                }
                copy(entry.Value, sn)
                break
            }
        }
        updateIntChk()
    }
    return
}

func UpdateDate(devName string, date []byte) (err int) {
//    if len(date) != 3 {
//        cli.Println("f", "Date format is invalid: ", date)
//        return
//    }

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "NAPLES100" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "Manufacturing Date" {
                copy(entry.Value, date)
//                for i := 0; i < entry.NumBytes; i++ {
//                    entry.Value[i] = byte((date >> uint64(16 - i * 8)) & 0xFF)
//                    fmt.Printf("%d\n", entry.Value[i])
//                }
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
    fmtStr := "%-45s%-20s"
    fmtDate := "%-45s%02s/%02s/%02s"
    fmtMac := "%-45s%02x-%02x-%02x-%02x-%02x-%02x"
    fmtHex := "%-45s0x%-20x"
    var outStr string
    for _, entry := range(EepromTbl) {
        data, err = readField(devName, entry.Offset, entry.NumBytes)
        if err != errType.SUCCESS {
            cli.Println("f", "Failed to read field at offset", entry.Offset, "number of bytes", entry.NumBytes)
            return
        }
        if entry.DataType == STRING {
                for i := 0; i < entry.NumBytes; i++ {
                    data[i] += 0x20
                }
            dataStr := string(data[:entry.NumBytes])
            outStr = fmt.Sprintf(fmtStr, entry.Name, dataStr)
        } else {
            if entry.Name == "Manufacturing Date" {
                outStr = fmt.Sprintf(fmtDate, entry.Name, strconv.Itoa(int(data[0])), strconv.Itoa(int(data[1])), strconv.Itoa(int(data[2])))
            } else if entry.Name == "MAC Address Base" {
                outStr = fmt.Sprintf(fmtMac, entry.Name, data[0], data[1], data[2], data[3], data[4], data[5])
            } else {
                outStr = fmt.Sprintf(fmtHex, entry.Name, data)
            }
        }

        cli.Println("i", outStr)
    }
    return
}

