package eeprom

import (
    "fmt"
    "bytes"
    "time"
    "strconv"
    "strings"
    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/smbusNew"
)

//New card PNs can be added here
const (
    //General purpose constants
    MAX_BYTES           int = 512
    MRA_HDR_LEN         int = 5
    CHDR_LEN            int = 8
    BRD_INFO_AREA_LEN   int = 6
    OFFSET_NORM_FACTOR  int = 8
    ZERO_START          int = 0
    DELAYED_START       int = 256
    SHORT_FORM          string = "2006-01-02"

    //Attribute constants
    MAC_LEN             int = 12
    MFG_DATE_LEN        int = 3

    //Profinfo data structure constants
    FIELD_NUM_NONE      int = 0xFFFF
    FIELD_NUM_SN_3      int = 3
    FIELD_NUM_PN_4      int = 4
    FIELD_NUM_PN_10     int = 10
    FIELD_NUM_MAC_9     int = 9

    //Field types; Area field number vs absolute byte offset
    FIELD_TYPE_NUM      int = 0
    FIELD_TYPE_BYTE     int = 1

    //FRU area definition
    AREA_TYPE_BOARD_INFO    int = 0
    AREA_TYPE_PRDT_INFO     int = 1
    AREA_TYPE_MRA_E1        int = 0xE1
    AREA_TYPE_MRA_E2        int = 0xE2
    AREA_TYPE_MRA_E6        int = 0xE6
    AREA_TYPE_MRA_C1        int = 0xC6

    //Supported board PNs
    IBM_PN      string = "68-0028"
    PEN_PN      string = "68-0021"

    //TEST
    TEST_PN     string = "68-1337"
)

type progInfo struct {
    fieldType   int
    areaCode    int
    sn          int
    pn          int
    mac         int
}

type updateInfo struct {
    tbl  []entry
    info []progInfo
}

type card struct {
    Name     string
    pn      string
}

type entryinfo struct {
	Name     string
	DataType int
	Offset   int
	NumBytes int
}

//Part number and data location maps
var CardDataInfo = map[string]updateInfo{
    IBM_PN: updateInfo{OrtanoIBMTbl, []progInfo{progInfo{FIELD_TYPE_NUM, 
                                                        AREA_TYPE_BOARD_INFO,  
                                                        FIELD_NUM_SN_3, 
                                                        FIELD_NUM_PN_10, 
                                                        FIELD_NUM_MAC_9}}},
    PEN_PN: updateInfo{OrtanoPensandoTbl, []progInfo{progInfo{FIELD_TYPE_NUM, 
                                                        AREA_TYPE_BOARD_INFO, 
                                                        FIELD_NUM_SN_3, 
                                                        FIELD_NUM_PN_10, 
                                                        FIELD_NUM_MAC_9}}},
    //ONLY TEST; NOT REAL!
    TEST_PN:updateInfo{Lacona32DELLTbl, []progInfo{progInfo{FIELD_TYPE_NUM, 
        AREA_TYPE_BOARD_INFO, FIELD_NUM_SN_3, FIELD_NUM_PN_4, FIELD_NUM_MAC_9},
                                                   progInfo{FIELD_TYPE_NUM, 
        AREA_TYPE_BOARD_INFO, FIELD_NUM_NONE, FIELD_NUM_PN_10, FIELD_NUM_NONE}}},
}

//Add PNs to table of accepted cards
var CardTypes = []card{
    card{"ORTANO-IBM", IBM_PN},
    card{"ORTANO-PEN", PEN_PN},
                      }

//Data structure slices
var Data    []byte
var DataRaw []byte
var Info    []entryinfo

//==============================================================================
//                     G E N E R I C     F U N C T I O N S
//==============================================================================

func convertToByteTbl(pn string) (err int){
    //Writes all entries of EepromTbl into new slices
    //Checks and sets EepromTbl based on the input part number
    found, partNum := CardInList(pn)
    if found == true {
        EepromTbl = CardDataInfo[partNum].tbl
    } else {
        cli.Println("e", "ERROR: Card type not supported; failed to set EepromTbl")
        err = errType.FAIL
        return
    }
    //Writes tabl into data and info slices
    for i:=0;i<len(EepromTbl);i++ {
        Data = append(Data, EepromTbl[i].Value...)
        Info = append(Info, entryinfo{EepromTbl[i].Name, EepromTbl[i].DataType, EepromTbl[i].Offset, EepromTbl[i].NumBytes})
    }
    return
}

func checkCHdrStart() (int) {
    //Checks first 3 bytes for Oracle card . Oracle FRU has fixed starting bytes
    var OracleOrtano = []byte{0x00, 0x80, 0x02} //Oracle Ortano signature
    var chkSlice []byte
    for i:=0;i<3;i++ {
        chkSlice = append(chkSlice, Data[i])
    }
    if bytes.Equal(chkSlice, OracleOrtano) {
        return DELAYED_START
    }
    return ZERO_START
}

func getOffsetsCHdr(start int) (boardInfoOff int, productInfoOff int, multiRecordOff int) {
    //Reads and returns area starting byte offsets
    if Data[start+1] != 0x00 || Data[start+2] != 0x00 {
        fmt.Printf("ERROR: common header Internal Use Area Offset and Chassis Area Offset not supported.\n")
        return
    }
    boardInfoOff = (int(Data[start+3]) * OFFSET_NORM_FACTOR)
    productInfoOff = (int(Data[start+4]) * OFFSET_NORM_FACTOR)
    multiRecordOff = (int(Data[start+5]) * OFFSET_NORM_FACTOR)
    return
}

func findFieldOffset(start int, end int, fieldNum int) (fieldOff int, fieldLen int, err int) {
    //WARNING: Function only works for board info area and product info area!
    //Multi Info Area does not have type/length field
    //Finds the offset annd length of a field based on the field offset
    if fieldNum < 1 {
        cli.Println("e", "ERROR: Invalid number of field.")
        err = errType.INVALID_PARAM
        return
    }
    //Checks if fieldNum > number of fields
    var len, totalNumberFields int
    for i:=start+BRD_INFO_AREA_LEN;i<end-1;i+=len+1 {
        len = int(Data[i] & 0x3F)
        totalNumberFields++
    }
    if totalNumberFields < fieldNum {
        cli.Printf("e", "ERROR: Field %d does not exist.", fieldNum)
        err = errType.FAIL
        return
    }
    //Finds field at offset
    var totalFields int = 0
    for i:=start+BRD_INFO_AREA_LEN;i<end-1;i+=fieldLen+1 {
        if totalFields == fieldNum {
            break
        }
        fieldOff = i+1
        fieldLen = int(Data[i] & 0x3F)
        totalFields+=1
    }
    return
}

func findPn(start int, end int) (pn string, err int) {
    //Returns part number or assembly number and converts byte data to string
    var pnBytes []byte
    partNumOff, partNumLen, err := findFieldOffset(start, end, FIELD_NUM_PN_4)
    if err != errType.SUCCESS {
        cli.Println("e", "ERROR: Failed to find part number offset.")
        return
    }
    pnBytes = Data[partNumOff:partNumOff+partNumLen]
    partNum := string(pnBytes) //full PN
    found, pn := CardInList(partNum)
    if (found == true) && (err == errType.SUCCESS) {
        return 
    }
    partNumOff, partNumLen, err = findFieldOffset(start, end, FIELD_NUM_PN_10)
    pnBytes = Data[partNumOff:partNumOff+partNumLen]
    partNum = string(pnBytes)
    found, pn = CardInList(partNum)
    if (found == true) && (err == errType.SUCCESS) {
        return 
    } else {
        cli.Println("i", "Assembly number not found")
        err = errType.FAIL
        return
    }
}

func findPnBlind() (pn string, err int) {
    dataString := string(DataRaw[:])
    for _, card := range CardTypes {
        if strings.Contains(dataString, card.pn) {
            pn = card.pn
            return
        }
    }
    err = errType.PN_NOT_SUPPORT
    return
}

//unused function
func writeToTbl() {
    //Writes the values in Data back to EepromTbl
    for i:=0;i<len(EepromTbl);i++ {
        dataOffset := EepromTbl[i].Offset
        dataLen := EepromTbl[i].NumBytes
        EepromTbl[i].Value = Data[dataOffset:(dataOffset+dataLen)]
    }
}

//==============================================================================
//                  C H E C K     S U M     F U N C T I O N S
//==============================================================================

func chkSum(start int, length int) (chkSum byte) {
    //Generic Checksum function; returns checksum byte
    var sum uint
    for i:=0;i<length;i++ {
        sum += uint(Data[start+i])
    }
    chkSum = byte(0x100 - sum % 0x100)
    return
}


func mraChkSum(start int, mraOff int) (recordChkSum [][2]uint, mraHdrChkSum [][2]uint) {
    //Checks and returns multi-record area check sum with associated offsets
    var recordLen, recordStrt, recordChkSumOff, rHdrChkSumOff int 
    for i:=start+mraOff;i<len(Data);i++ {
        recordLen = int(Data[start+mraOff + 2])
        recordChkSumOff = start+mraOff + 3
        rHdrChkSumOff = start+mraOff + 4
        recordStrt = start+mraOff + 5
        recordChkSum=append(recordChkSum, [2]uint{uint(recordChkSumOff), uint(chkSum(recordStrt, recordLen))})
        mraHdrChkSum=append(mraHdrChkSum, [2]uint{uint(rHdrChkSumOff), uint(chkSum(start+mraOff, MRA_HDR_LEN))})
        mraOff += (recordLen + MRA_HDR_LEN)
        if Data[start+mraOff + 1] == 0x82 {
            break
        }
    }
    return
}

func updateChkSum() {
    //Function to update all checksums
    //Offset and length variables
    var cHdrStrt int = checkCHdrStart()
    var boardInfoAreaOff, productInfoAreaOff, multiRecordAreaOff int = getOffsetsCHdr(cHdrStrt)
    var boardInfoAreaLen int = int(Data[cHdrStrt+boardInfoAreaOff + 1]) * OFFSET_NORM_FACTOR
    var productInfoAreaLen int = int(Data[cHdrStrt+productInfoAreaOff + 1]) * OFFSET_NORM_FACTOR 
    //Check sum variable initialization
    var cHdrChkSum, boardInfoAreaChkSum, productInfoChkSum byte
    //Product and multi-record area Checksums calculated
    cHdrChkSum = chkSum(cHdrStrt, CHDR_LEN)
    boardInfoAreaChkSum = chkSum(cHdrStrt + boardInfoAreaOff, boardInfoAreaLen - 1)
    //Updates common header and board info area Checksums
    Data[cHdrStrt + CHDR_LEN - 1] = cHdrChkSum
    Data[cHdrStrt + boardInfoAreaOff + boardInfoAreaLen - 1] = boardInfoAreaChkSum
    //Product info area checksum and update
    if productInfoAreaOff != 0 {
        productInfoChkSum = chkSum(cHdrStrt + productInfoAreaOff, productInfoAreaLen - 1)
        Data[cHdrStrt + productInfoAreaOff + productInfoAreaLen - 1] = productInfoChkSum
    }
    //If the multi record area is present, finds and updates multi record area checksums here
    if multiRecordAreaOff != 0 {
        recordChkSum, mraHdrChkSum := mraChkSum(cHdrStrt, cHdrStrt + multiRecordAreaOff)
        for _, pair := range(recordChkSum) {
            Data[int(pair[0])] = byte(pair[1])
        }
        for _, pair := range(mraHdrChkSum) {
            Data[int(pair[0])] = byte(pair[1])
        }
    }
}

func updateFields(sn string, pn string, mac string, date string) (err int) {
    //Updates serial number, part number, MAC address, and date in Data
    var snOff, snLen, pnOff, pnLen, macOff, macLen, dateOff, dateLen int

    //Checks PN validity and sets card type
    found, minPN := CardInList(pn)
    if found != true {
        cli.Printf("e", "ERROR: Card part number not supported")
        return errType.FAIL
    }
    card := CardDataInfo[minPN]

    //Initial failure condition
    if (sn == "") || (pn == "") || (mac == "") || (date == "") {
        cli.Printf("e", "ERROR: Must have values for serial number, part number, MAC address, and date.\n")
        err = errType.INVALID_PARAM
        return 
    }

    //Converts MAC address to byte
    macByte := make([]byte, 6)
    data, _ := strconv.ParseUint(mac, 16, 64)
    macByte[0] = byte(data >> 40 & 0xFF)
    macByte[1] = byte(data >> 32 & 0xFF)
    macByte[2] = byte(data >> 24 & 0xFF)
    macByte[3] = byte(data >> 16 & 0xFF)
    macByte[4] = byte(data >> 8 & 0xFF)
    macByte[5] = byte(data & 0xFF)

    //Converts date into 3 hex values (month, day, year)
    var dateByte []byte
    month, day, year := date[:2], date[2:4], date[4:]
    formatDate := fmt.Sprintf("20%s-%s-%s", year, month, day)
    timeStart, _ := time.Parse(SHORT_FORM, "1996-01-01")
    timeEnd, _ := time.Parse(SHORT_FORM, formatDate)
    difference := timeEnd.Sub(timeStart)
    dateByte = append(dateByte, byte(int(difference.Minutes()) & 0xFF)) 
    dateByte = append(dateByte, byte((int(difference.Minutes()) >> 8) & 0xFF))
    dateByte = append(dateByte, byte((int(difference.Minutes()) >> 16) & 0xFF))
    
    //Converts SN and PN to byte & declares offset/length variables
    snByte := []byte(sn)
    pnByte := []byte(pn)

    //Find offset/Len of SN/PN/MAC/Date of each progInfo entry
    start := checkCHdrStart()
    boardInfoOffset, _, _ := getOffsetsCHdr(start)
    boardInfoLen := int(Data[start+boardInfoOffset+1]) * OFFSET_NORM_FACTOR
    //Loops through card.info slice and updates each field
    for _, entry := range(card.info) {
        //SN, PN, MAC, and DATE offsets and locations
        //If NONE is found, provious offset and length will retain. Same field will be retained.
        //Same field will be updated.
        if entry.fieldType == FIELD_TYPE_BYTE {
            if entry.sn != FIELD_NUM_NONE {
                snOff = entry.sn
                snLen = len(sn)
            }
            if entry.pn != FIELD_NUM_NONE {
                pnOff = entry.pn
                pnLen = len(pn)
            }
            if entry.mac != FIELD_NUM_NONE {
                macOff = entry.mac
                macLen = MAC_LEN
            }
        } else {
            if entry.sn != FIELD_NUM_NONE {
                snInt := entry.sn
                snOff, snLen, err = findFieldOffset(start+boardInfoOffset, start+boardInfoOffset+boardInfoLen, snInt)
            }
            if entry.pn != FIELD_NUM_NONE {
                pnInt := entry.pn
                pnOff, pnLen, err = findFieldOffset(start+boardInfoOffset, start+boardInfoOffset+boardInfoLen, pnInt)
            }
            if entry.mac != FIELD_NUM_NONE {
                macInt := entry.mac
                macOff, macLen, err = findFieldOffset(start+boardInfoOffset, start+boardInfoOffset+boardInfoLen, macInt)
            }
        }

        //Sets date offset and length
        dateOff, dateLen = start+boardInfoOffset+MFG_DATE_LEN, MFG_DATE_LEN

        //Returns error if previous step for finding offset and lengths fail
        if err != errType.SUCCESS {
            cli.Println("e", "ERROR: Failed to find correct offsets and field lengths.")
            return
        }

        //Error return if any of the update fields are empty
        var errField string
        if snOff == 0 {
            errField = "Serial Number"
            err = errType.FAIL
            cli.Printf("e", "ERROR: Specified update field empty; check card info slice/field: %s", errField)
            return
        } else if pnOff == 0 {
            errField = "Part Number"
            err = errType.FAIL
            cli.Printf("e", "ERROR: Specified update field empty; check card info slice/field: %s", errField)
            return
        } else if pnOff == 0 {
            errField = "MAC Address"
            err= errType.FAIL
            cli.Printf("e", "ERROR: Specified update field empty; check card info slice/field: %s", errField)
            return
        }

        //Returns error if string longer than specified value
        if (len(sn) > snLen) || (len(pn) > pnLen) || (len(mac) != MAC_LEN) || (len(date) != (MFG_DATE_LEN*2)) {
            err = errType.INVALID_PARAM
            var errorOutput string
            if len(date) != (2*MFG_DATE_LEN) {
                errorOutput += " date"
            } else if len(sn) > snLen {
                errorOutput += " serial number"
            } else if len(pn) > pnLen {
                errorOutput += " assembly number"
            } else if len(mac) != MAC_LEN {
                errorOutput += " MAC address"
            }
            cli.Printf("e", "ERROR: Input fields differ from specified lengths. Affected field(s):%s", errorOutput)
            return
        }

        //Pads values if less than FRU specified length
        if entry.fieldType != FIELD_TYPE_BYTE {
            if (len(sn) < snLen) {
                for i:=len(snByte);i<snLen;i++ {
                    snByte=append(snByte, 0x20)
                }
            } else if (len(pnByte) < pnLen) {
                for i:=len(pnByte);i<pnLen;i++ {
                    pnByte=append(pnByte, 0x20)
                }
            }
        }

        //Update Data slice (byte)
        var incrementVar int = 0
        for offset:=0;offset<len(Data);offset++ {
            if offset == dateOff {
                for i:=offset;i<offset+dateLen;i++ {
                    Data[i]=dateByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            } else if offset == snOff {
                for i:=offset;i<offset+snLen;i++ {
                    Data[i]=snByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            } else if offset == pnOff {
                for i:=offset;i<offset+pnLen;i++ {
                    Data[i]=pnByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            } else if offset == macOff {
                for i:=offset;i<offset+macLen;i++ {
                    Data[i]=macByte[incrementVar]
                    incrementVar++
                }
                incrementVar = 0
            }
        }
    }
    return
}

//==============================================================================
//                  F R U    A C T I O N    F U N C T I O N S
//==============================================================================

func writeToFRU(devName string) (err int) {
    //Writes values in Data directly to FRU
    //Checks Data length vs Max number of bytes
    if len(Data) > MAX_BYTES {
        err = errType.FAIL
        cli.Printf("e", "ERROR: Data larger than Maximum Bytes by %d offsets", MAX_BYTES-len(Data))
        return
    }
    //Writes to FRU
    for i:=0;i<len(Data);i++ {
        misc.SleepInUSec(5000) //delay for writing
        if I2cAddr16 == true {
            err = smbusNew.I2C16WriteByte(devName, uint16(i), Data[i])
        } else {
            err = smbusNew.WriteByte(devName, uint64(i), Data[i])
        }
        if err != errType.SUCCESS {
            cli.Printf("e", "ERROR: Failed to write to FRU at offset %d", i)
            return err
        }
    }
    return
}

func readFromFruBlind(devName string) (err int) {
    var fruData byte

    for i:=0;i<MAX_BYTES;i++ {
        fruData, err =readOffset(devName, i)
        DataRaw = append(DataRaw, fruData)
        if err != errType.SUCCESS {
            return
        }
    }
    return
}

func readFromFru(devName string) (err int) {
    //Reads values from FRU and uploads into Data slice
    var sliceLen int
    var fruData byte
    
    //Fills Data slice with 0xFF temporarily
    for i:=0;i<MAX_BYTES;i++ {
        Data = append(Data, 0xFF)
    }

    // Calculate FRU table size based on IPMI headers
    //Checks header for variables
    for i:=0;i<6;i++ {
        fruData, err = readOffset(devName, i)
        Data[i] = fruData
    }
    start := checkCHdrStart()
    for i:=start;i<start+6;i++ {
        fruData, err =readOffset(devName, i)
        Data[i] = fruData
    }
    boardInfoOff, productInfoOff, mraInfoOff := getOffsetsCHdr(start)

    boardInfoByte, _ := readOffset(devName, start+boardInfoOff + 1)
    boardInfoLen := int(boardInfoByte) * OFFSET_NORM_FACTOR

    productInfoByte, _ := readOffset(devName, start+productInfoOff + 1)
    productInfoLen := int(productInfoByte) * OFFSET_NORM_FACTOR

    //Checks and sets the slice length
    if mraInfoOff != 0 {
        sliceLen += start+mraInfoOff
        for i:=start+mraInfoOff;i<MAX_BYTES;i++ {
            endOfList, _ := readOffset(devName, start+mraInfoOff + 1)
            recordLen, _ := readOffset(devName, start+mraInfoOff + 2)
            sliceLen += MRA_HDR_LEN + int(recordLen)
            mraInfoOff += MRA_HDR_LEN + int(recordLen)
            if endOfList == 0x82 {
                break
            }
        }
    } else if productInfoOff != 0 {
        sliceLen = start+productInfoOff + productInfoLen
    } else if boardInfoOff != 0 {
        sliceLen = start+boardInfoOff + boardInfoLen
    }

    //Clears Data slice
    Data = nil

    //Reads data from FRU and fills the Data slice
    for i:=0;i<sliceLen;i++ {
        fruData, err = readOffset(devName, i)
        Data = append(Data, fruData)
        if err != errType.SUCCESS {
            cli.Printf("e", "ERROR: Failed to read from FRU at offset %s", i)
            return
        }
    }
    return
}

func readOffset(devName string, offset int) (data byte, err int) {
    //Generic FRU reading function
    if I2cAddr16 == true {
        data, err = smbusNew.I2C16ReadByte(devName, uint16(offset))
    } else {
        data, err = smbusNew.ReadByte(devName, uint64(offset))
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to read from FRU at offset %d\n", offset)
        return
    }
    return
}

//==============================================================================
//                      P U B L I C     F U N C T I O N S
//==============================================================================

func CardInList(partNum string) (found bool, minPN string) {
    //Looks through supported card slice and returns true if card number is present
    for _, card := range(CardTypes) {
        if card.pn == partNum[:len(card.pn)] {
            found = true
            minPN = card.pn
            return
        }
    }
    return
}

func DisplayData(devName string, bus uint32, devAddr byte, field string, fpo bool) (err int){
    //Displays data of EEPROM
    //Formatting
    var outputString string
    var cardPN string
    var dataValue []byte

    fmtStr  := "%-45s%-20s"
    fmtDate := "%-45s0x%02X%02X%02X  %s"
    fmtMac  := "%-45s%02X-%02X-%02X-%02X-%02X-%02X"
    fmtHex  := "%-45s0x%-20X"

    //Opens connection
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

    //Reads data from FRU and puts into Data slice
    if fpo == true {
        err = readFromFruBlind(devName)
        if err != errType.SUCCESS {
            return
        }

        cardPN, err = findPnBlind()
        if err != errType.SUCCESS {
            return
        }

    } else {
        err = readFromFru(devName)
        if err != errType.SUCCESS {
            return
        }

        //Finds PN on card and sets EepromTbl
        start := checkCHdrStart()
        boardInfoOffset, _, _ := getOffsetsCHdr(start)
        boardInfoLen := int(Data[start+boardInfoOffset+1]) * OFFSET_NORM_FACTOR
        cardPN, err = findPn(start+boardInfoOffset, start+boardInfoOffset+boardInfoLen)
    }
    if (err == errType.SUCCESS) {
        EepromTbl=CardDataInfo[cardPN].tbl
    } else {
        err = errType.PN_NOT_SUPPORT
        return
    }

    //Displays info
    for i:=0;i<len(EepromTbl);i++ {
        dataName := EepromTbl[i].Name
        dataOffset := EepromTbl[i].Offset
        dataLen := EepromTbl[i].NumBytes
        dataType := EepromTbl[i].DataType
        if fpo == true {
            dataValue = DataRaw[dataOffset:(dataOffset+dataLen)]
        } else {
            dataValue = Data[dataOffset:(dataOffset+dataLen)]
        }
        //Checks for the field
        if field != "ALL" {
            if field == "SN" {
                if dataName != "Serial Number" {
                    continue
                }
            } else if field == "MAC" {
                if dataName != "MAC Address Base" {
                    continue
                }
            } else if field == "PN" {
                if dataName != "Assembly Number" {
                    continue
                }
            } else if field == "DATE" {
                if dataName != "Manufacturing Date/Time" {
                    continue
                }
            }
        }
        //Formats and displays FRU value
        if dataType == STRING {
            dataString := string(dataValue)
            outputString = fmt.Sprintf(fmtStr, dataName, dataString)
        } else {
            if dataName == "Manufacturing Date/Time" {
                start := time.Date(1996, 1, 1, 0, 0, 0, 0, time.UTC)
                minutes := int((int(dataValue[2]) * 0x10000) + 
                    (int(dataValue[1]) * 0x100) + int(dataValue[0]))
                now := start.Add(time.Minute * time.Duration(minutes))
                year, month, day := now.Date()
                date := fmt.Sprintf("%02d/%02d/%02d", 
                    int(month), 
                    int(day), 
                    (int(year) % 100))
                outputString = fmt.Sprintf(fmtDate, dataName, 
                    dataValue[2], dataValue[1], dataValue[0], 
                    date)
            } else if dataName == "MAC Address Base" {
                outputString = fmt.Sprintf(fmtMac, dataName, 
                    dataValue[0],
                    dataValue[1],
                    dataValue[2],
                    dataValue[3],
                    dataValue[4],
                    dataValue[5],)
            } else if dataName == "Class Code" {
                outputString = fmt.Sprintf("%-45s0x%02X%02X%02X", dataName,
                dataValue[2], dataValue[1], dataValue[0]) 
            } else if dataName == "PCI-SIG Vendor ID" {
                outputString = fmt.Sprintf("%-45s0x%02X%02X", dataName, 
                dataValue[1], dataValue[0])
            } else if dataName == "Cap List Pointer" {
                outputString = fmt.Sprint("%-45s0x%02X%02X", dataName, dataValue[1], dataValue[0])
            } else {
                outputString = fmt.Sprintf(fmtHex, dataName, dataValue)
            }
        }
        cli.Println("i", outputString)
    }
    return
}

func ProgData(devName string, bus uint32, devAddr byte, sn string, pn string, mac string, date string) (err int){
    //Creates data slice of EEPROM table, updates data and checksums, and writes to FRU
    //Opens connections
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()
    //Initiates the entries
    err = convertToByteTbl(pn)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Card not supported.")
        err = errType.FAIL
        return 
    }
    //Updates the byte data slice with specified data
    err = updateFields(sn, pn, mac, date)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Update failed.")
        err = errType.FAIL
        return 
    }
    //Updates check sums
    updateChkSum()
    //Writes data table to FRU
    err = writeToFRU(devName)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Write failed.")
        err = errType.FAIL
        return 
    }
    cli.Println("i", "EEPROM updated.")
    return
}
