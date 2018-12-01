package eeprom

import (
    "fmt"
    "os"
//    "strconv"
    "time"
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
    entry{"Internal Use Area Offset",   			INT8,		1,		1,	[]byte{0}},
    entry{"Chassis Area Offset",   					INT8,		2,		1,	[]byte{0}},
    entry{"Board Info Offset",   					INT8,		3,		1,	[]byte{1}},
    entry{"Product Area Offset",     				INT8,		4,		1,	[]byte{0}},
    entry{"Multi-Record Area Offset",   			INT8,		5,		1,	[]byte{0}},
    entry{"PAD",  									INT8, 		6,		1,	[]byte{0}},
    entry{"Common Header Checksum",     			INT8,	 	7,		1,  []byte{0}},
    
    
    entry{"Board Info Format Version",				INT8, 		8,		1,  []byte{1}},
    entry{"Board Area Length",       				INT8,		9,		1,	[]byte{0xC}},
    entry{"Language Code",     						INT8,		10, 	1,  []byte{0x19}},
    entry{"Manufacturing Date/Time", 				INT8,		11, 	3,  []byte{0, 0, 0}},
    entry{"Manufacturing Type/Length", 				INT8,		14, 	1,  []byte{0xD5}},
    entry{"Manufacturer",     						STRING,		15, 	21, []byte{0x50, 0x45, 0x4E, 0x53, 
        0x41, 0x4E, 0x44, 0x4F, 0x20, 0x53, 0x59, 0x53, 0x54, 0x45, 0x4D, 0x53, 0x20, 0x49, 0x4E, 0x43, 0x2E}},
    entry{"Product Name Type/Length",     			INT8,		36, 	1,  []byte{0xD0}},
    entry{"Product Name",     						STRING,		37, 	10, []byte{0x4E, 0x41, 0x50, 0x4C, 
        0x45, 0x53, 0x20, 0x31, 0x30, 0x30}},
    entry{"Reserved",     							STRING,		47, 	6, 	[]byte{0x20, 0x20, 0x20, 0x20, 
        0x20, 0x20}},
    entry{"Serial Number Type/Length",     			INT8,		53, 	1,  []byte{0xCB}},
    entry{"Serial Number",     						STRING,		54, 	11, []byte{0x30, 0x30, 0x30, 0x30, 
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Part Number Type/Length",     			INT8,		65, 	1,  []byte{0xCD}},
    entry{"Part Number",     						STRING,		66, 	13, []byte{0x36, 0x38, 0x2D, 0x30, 
        0x30, 0x30, 0x33, 0x2D, 0x30, 0x32, 0x20, 0x30, 0x31}},
    entry{"FRU File ID Type/Length",     			INT8,		79, 	1,  []byte{0xC0}},
    entry{"Board ID Type/Length",     				INT8,		80, 	1,  []byte{4}},
    entry{"Board ID",     							INT8,		81, 	4,  []byte{1, 0 , 0, 0}},
    entry{"Engineering Change Level Type/Length",	INT8,		85, 	1,  []byte{0xC2}},
    entry{"Engineering Change Level",     			INT8,		86, 	2,  []byte{0, 0}},
    entry{"Number of MAC Address Type/Length",     	INT8,		88, 	1,  []byte{2}},
    entry{"Number of MAC Address",     				INT8,		89, 	2,  []byte{0x18, 0x0}},
    entry{"MAC Address Base Type/Length",     		INT8,		91, 	1,  []byte{6}},
    entry{"MAC Address Base",     					INT8,		92, 	6,  []byte{0, 0xAE, 0xCD, 0, 0, 0}},
    entry{"End of Field",				     		INT8,	 	98,		1,  []byte{0xC1}},
    entry{"PAD",     								INT8,		99, 	4,  []byte{0, 0, 0, 0}},
    entry{"Board Info Area Checksum",     			INT8,	 	103,	1,  []byte{0}},
}

var EepromTbl []entry
var brdInfoChk, cmnHeadChk uint

func init() {
    cardType := os.Getenv("CARD_TYPE")
    if cardType == "MTP" {
        EepromTbl = mtpTbl
    } else if cardType == "MTPS" {
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
//        if entry.Name == "Serial Number" {
//            dftArray := []byte{0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10}
//            if bytes.Equal(entry.Value, dftArray) {
//                cli.Println("i", "skip sn")
//                continue
//            }
//        } else if entry.Name == "Manufacturing Date" {
//            dftArray := []byte{0, 0, 0}
//            if bytes.Equal(entry.Value, dftArray) {
//                cli.Println("i", "skip date")
//                continue
//            }
//        } else if entry.Name == "MAC Address Base" {
//            dftArray := []byte{0, 0, 0, 0, 0, 0}
//            if bytes.Equal(entry.Value, dftArray) {
//            cli.Println("i", "skip mac")
//            continue
//            }
//        }
        
        if entry.Name == "Board Info Area Checksum" {
            entry.Value[0] = byte(0x100 - brdInfoChk % 0x100)
//            binary.Write(entry.Value, binary.LittleEndian, (0x100 - brdInfoChk % 0x100))
//            entry.Value = []byte(strconv.FormatUint(uint64(0x100 - brdInfoChk % 0x100), 16))
            
        } else if entry.Name == "Common Header Checksum" {
            entry.Value[0] = byte(0x100 - cmnHeadChk % 0x100)
        }
        
        if entry.DataType == STRING {
            data := make([]byte, entry.NumBytes)
            copy(data, entry.Value)
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

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    
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
                continue
            } else if entry.Name == "Serial Number" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, sn)
                continue
            } else if entry.Name == "Manufacturing Date/Time" {
                date, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, date)
                continue
            }
        }
        updateIntChk()
    }
    return
}

func updateIntChk() () {
    brdInfoChk = 0
    cmnHeadChk = 0
    for _, entry := range(EepromTbl) {
        if (entry.Offset > 7) && (entry.Offset < 103) {
//            brdInfoChk += entry.Value
            brdInfoChk += calcSum(entry)
        } else if (entry.Offset >= 0) && (entry.Offset < 7) {
//            intUseChk += entry.Value
            cmnHeadChk += calcSum(entry)
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
    
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    
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
                continue
            } else if entry.Name == "MAC Address Base" {
                mac, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "Manufacturing Date/Time" {
                date, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, date)
                continue
            }
        }
        updateIntChk()
    }
    return
}

//func UpdateDate(devName string, date []byte) (err int) {
////    if len(date) != 3 {
////        cli.Println("f", "Date format is invalid: ", date)
////        return
////    }
//    err = smbus.Open(devName)
//    if err != errType.SUCCESS {
//        return
//    }
//    defer smbus.Close()
//    
//    cardType := os.Getenv("CARD_TYPE")
//
//    if cardType == "NAPLES100" {
//        for _, entry := range(EepromTbl) {
//            if entry.Name == "Manufacturing Date" {
//                copy(entry.Value, date)
////                for i := 0; i < entry.NumBytes; i++ {
////                    entry.Value[i] = byte((date >> uint64(16 - i * 8)) & 0xFF)
////                    fmt.Printf("%d\n", entry.Value[i])
////                }
//                continue
//            } else if entry.Name == "MAC Address Base" {
//                mac, _ := readField(devName, entry.Offset, entry.NumBytes)
//                copy(entry.Value, mac)
//                continue
//            } else if entry.Name == "Serial Number" {
//                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
//                copy(entry.Value, sn)
//                continue
//            }
//        }
//        updateIntChk()
//    }
//    return
//}

func UpdateDate(devName string, str string) (err int) {
//    if len(date) != 3 {
//        cli.Println("f", "Date format is invalid: ", date)
//        return
//    }
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    
    cardType := os.Getenv("CARD_TYPE")

    if cardType == "NAPLES100" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "Manufacturing Date/Time" {
                const shortForm = "2006-01-02"
                date := fmt.Sprintf("%s%s%s%s%s%s", "20", string(str[4:6]), "-", string(str[0:2]), "-", string(str[2:4]))
            	start, _ := time.Parse(shortForm, "1996-01-01")
            	end, _ := time.Parse(shortForm, date)
            	difference := end.Sub(start)
            	data := make([]byte, 3)
            	data[0] = byte(int(difference.Minutes()) & 0xFF)
            	data[1] = byte((int(difference.Minutes()) >> 8) & 0xFF)
            	data[2] = byte((int(difference.Minutes()) >> 16) & 0xFF)
            	copy(entry.Value, data)
                continue
            } else if entry.Name == "MAC Address Base" {
                mac, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "Serial Number" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, sn)
                continue
            }
        }
        updateIntChk()
    }
    return
}

func DispEeprom(devName string, field string) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    var data []byte
    fmtStr := "%-45s%-20s"
    fmtDate := "%-45s0x%02X%02X%02X  %s"
    fmtMac := "%-45s%02X-%02X-%02X-%02X-%02X-%02X"
    fmtHex := "%-45s0x%-20X"
    var outStr string
    for _, entry := range(EepromTbl) {
        if(field == "SN") {
            if entry.Name != "Serial Number" {
                continue
            }
        } else if(field == "MAC") {
            if entry.Name != "MAC Address Base" {
                continue
            }
        } else if(entry.Name == "Reserved") {
            continue
        }
        data, err = readField(devName, entry.Offset, entry.NumBytes)
        if err != errType.SUCCESS {
            cli.Println("f", "Failed to read field at offset", entry.Offset, "number of bytes", entry.NumBytes)
            return
        }
        if entry.DataType == STRING {
            dataStr := string(data[:entry.NumBytes])
            outStr = fmt.Sprintf(fmtStr, entry.Name, dataStr)
        } else {
            if entry.Name == "Manufacturing Date/Time" {
                start := time.Date(1996, 1, 1, 0, 0, 0, 0, time.UTC)
                minutes := int((int(data[2]) * 0x10000) + (int(data[1]) * 0x100) + int(data[0]))
                now := start.Add(time.Minute * time.Duration(minutes))
                year, month, day := now.Date()
                date := fmt.Sprintf("%d/%d/%d", int(month), int(day), (int(year) % 100))
                outStr = fmt.Sprintf(fmtDate, entry.Name, data[2], data[1], data[0], date)
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

func DumpEeprom(devName string) (err int) {

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    var data []byte
    cardType := os.Getenv("CARD_TYPE")

    if cardType == "NAPLES100" {
        f, error := os.OpenFile("eeprom", os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
        if error != nil {
            cli.Println("e", "file create failed")
        }
        cli.Println("i", "dump FRU to file eeprom")
        for _, entry := range(EepromTbl) {
            data, err = readField(devName, entry.Offset, entry.NumBytes)
            if err != errType.SUCCESS {
                cli.Println("f", "Failed to read field at offset", entry.Offset, "number of bytes", entry.NumBytes)
                return
            }
            f.WriteString(string(data[:]))
        }
        f.Close()
    }
    return
}
