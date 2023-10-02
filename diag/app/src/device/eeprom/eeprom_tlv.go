package eeprom

import (
	"fmt"
	"os"
	//"strconv"
	"strings"
    "strconv"
	//"time"
	"hash/crc32"
    "common/errType"
    "common/cli"
    "common/misc"
    //"protocol/smbusNew"
    "device/fpga/liparifpga"
    "hardware/i2cinfo"
)

// EEPROM TLVs Type Codes
const (
	product_name       = byte(0x21)
	part_number        = byte(0x22)
	serial_number      = byte(0x23)
	base_mac_addr      = byte(0x24)
	manufacture_date   = byte(0x25)
	device_version     = byte(0x26)
	label_revision     = byte(0x27)
	platform_name      = byte(0x28)
	onie_version       = byte(0x29)
	num_mac_addr       = byte(0x2a)
	manufacturer       = byte(0x2b)
	country_code       = byte(0x2c)
	vendor             = byte(0x2d)
	diag_version       = byte(0x2e)
	service_tag        = byte(0x2f)
	vendor_extension   = byte(0xfd)
	crc_32             = byte(0xfe)
	//extension fields
	chassis_type       = byte(0x50)
	board_type         = byte(0x51)
	sub_type           = byte(0x52)
	pcba_part_number   = byte(0x53)
	pcba_serial_number = byte(0x54)
)

var TlvInfoId = "TlvInfo" + string(0x00)
var TlvHdrVer uint8 = 0x01
var TlvHdrLen uint8 = 8
var TlvVerBytes uint8 = 1
var TlvTotalLenBytes uint8 = 2
var TlvTotalLenOffset uint8 = 9
var TlvStart uint8 = TlvHdrLen + TlvVerBytes + TlvTotalLenBytes

// EEPROM entry data structure
type tlvEntry struct {
    TypeCode    byte
    DataType    int
    Offset      int
    Length      byte
    Value       []byte
}


// define EepromTlvs to replace eeprom.EepromTbl & .EepromExtTbl
var EepromTlvs []tlvEntry
var TlvInfo []tlvEntry
var TlvData []byte

var FieldTlvCode = map[string]byte {
    "PRODUCT":      product_name,
    "PN":           part_number,
    "SN":           serial_number,
    "MAC":          base_mac_addr,
    "DATE":         manufacture_date,
    "TIME":         manufacture_date,
    "DEVVER":       device_version,
    "LABELREV":     label_revision,
    "PLATFORM":     platform_name,
    "ONIEVER":      onie_version,
    "NUMMAC":       num_mac_addr,
    "MFG":          manufacturer,
    "COUNTRY":      country_code,
    "VENDOR":       vendor,
    "DIAGVER":      diag_version,
    "SERVICETAG":   service_tag,
    "PCBPN":        pcba_part_number,
    "PCBSN":        pcba_serial_number,
}
var fieldUsage = []string {
    "-field supports the following options (case insensitive):\n",
    "    All (display all fields)\n",
    "    Product (product name)\n",
    "    PN (system part number)\n",
    "    SN (system serial number)\n",
    "    MAC (base mac address)\n",
    "    Date (MFG date/time)\n",
    "    Time (the same as Date)\n",
    "    DevVer (device version)\n",
//    "    LabelRev (label revision)\n",
    "    Platform (platform name)\n",
    "    ONIEver (ONIE version)\n",
    "    numMac (number of mac addr)\n",
    "    MFG (manufacturer name)\n",
    "    country (2-letter country code)\n",
    "    Vendor (vendor name)\n",
    "    DiagVer (diag version)\n",
    "    ServiceTag (service tag)\n",
    "    PcbPN (pcba part number)\n",
    "    PcbSN (pcba serial number)\n",
}

/*
 * def specific EepromTlvs for given card types
 * different card type may have various TLV entries
 */
var LipariCpuTlvs = []tlvEntry {
    //tlvEntry{ tlv_id_str,        STRING,    0,    8,   []byte(TlvInfoId)},
    //tlvEntry{ tlv_hdr_ver,       INT8,      8,    1,   TlvHdrVer},
    //all TLVs big endian
    //tlvEntry{ total_length,      INT8,      9,    2,   []byte{0x00, 212}},
    tlvEntry{ product_name,      STRING,   11,  45,   []byte{
            0x44, 0x53, 0x53, 0x2d, 0x32, 0x38, 0x34, 0x30,
            0x30, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20}},
    tlvEntry{ part_number,       STRING,   58,  15,   []byte{
            0x36, 0x38, 0x2D, 0x30, 0x30, 0x33, 0x32, 0x2D,
            0x30, 0x31, 0x20, 0x30, 0x30, 0x31, 0x20}},
    tlvEntry{ serial_number,     STRING,   75,  12,   []byte{
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ base_mac_addr,     INT8,     89,   6,   []byte{
            0x00, 0xAE, 0xCD, 0x00, 0x00, 0x00}},
    tlvEntry{ manufacture_date,  STRING,   97,  19,   []byte("04/12/2023 00:00:00")},
    tlvEntry{ device_version,    INT8,    118,   1,   []byte{0x00}},
    //tlvEntry{ label_revision }
    tlvEntry{ platform_name,     STRING,  121,  15,   []byte("Lipari Switch  ")},
    tlvEntry{ onie_version,      STRING,  138,   8,   []byte("00.00.00")},
    tlvEntry{ num_mac_addr,      INT16,   148,   2,   []byte{0x01, 0x00}},
    tlvEntry{ manufacturer,      STRING,  152,   8,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00}},
    // ISO 3166-1 alpha-2 code: US
    tlvEntry{ country_code,      STRING,  162,   2,   []byte("US")},
    tlvEntry{ vendor,            STRING,  166,   8,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ diag_version,      STRING,  176,   5,   []byte("00.00")},
    tlvEntry{ service_tag,       STRING,  183,   1,   []byte{0x00}},
    tlvEntry{ pcba_part_number,  STRING,  186,  15,   []byte{
            0x37, 0x33, 0x2D, 0x30, 0x30, 0x36, 0x38, 0x2D,
            0x30, 0x31, 0x20, 0x30, 0x30, 0x31, 0x20}},
    tlvEntry{ pcba_serial_number,STRING,  203,  12,   []byte{
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ crc_32,             INT8,   217,   4,   []byte{0x00, 0x00, 0x00, 0x00}},
}

var LipariSwitchTlvs = []tlvEntry {
    //tlvEntry{ tlv_id_str,        STRING,    0,    8,   []byte(TlvInfoId)},
    //tlvEntry{ tlv_hdr_ver,       INT8,      8,    1,   TlvHdrVer},
    // TLVs big endian
    //tlvEntry{ total_length,      INT8,      9,    2,   []byte{0x0, 212}},
    tlvEntry{ product_name,      STRING,   11,  45,   []byte{
            0x44, 0x53, 0x53, 0x2d, 0x32, 0x38, 0x34, 0x30,
            0x30, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20, 0x20}},
    tlvEntry{ part_number,       STRING,   58,  15,   []byte{
            0x36, 0x38, 0x2D, 0x30, 0x30, 0x33, 0x32, 0x2D,
            0x30, 0x31, 0x20, 0x30, 0x30, 0x31, 0x20}},
    tlvEntry{ serial_number,     STRING,   75,  12,   []byte{
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ base_mac_addr,     INT8,     89,   6,   []byte{
            0x00, 0xAE, 0xCD, 0x00, 0x00, 0x00}},
    tlvEntry{ manufacture_date,  STRING,   97,  19,   []byte("04/12/2023 00:00:00")},
    tlvEntry{ device_version,    INT8,    118,   1,   []byte{0x00}},
    //tlvEntry{ label_revision }
    tlvEntry{ platform_name,     STRING,  121,  15,   []byte("Lipari Switch  ")},
    tlvEntry{ onie_version,      STRING,  138,   8,   []byte("00.00.00")},
    tlvEntry{ num_mac_addr,      INT16,   148,   2,   []byte{0x01, 0x00}},
    tlvEntry{ manufacturer,      STRING,  152,   8,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00}},
    // ISO 3166-1 alpha-2 code: US
    tlvEntry{ country_code,      STRING,  162,   2,   []byte("US")},
    tlvEntry{ vendor,            STRING,  166,   8,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ diag_version,      STRING,  176,   5,   []byte("00.00")},
    tlvEntry{ service_tag,       STRING,  183,   1,   []byte{0x00}},
    tlvEntry{ pcba_part_number,  STRING,  186,  15,   []byte{    //73-0067-01
            0x37, 0x33, 0x2D, 0x30, 0x30, 0x36, 0x37, 0x2D,
            0x30, 0x31, 0x20, 0x30, 0x30, 0x31, 0x20}},
    tlvEntry{ pcba_serial_number,STRING,  203,  12,   []byte{
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ crc_32,             INT8,   217,   4,   []byte{0x00, 0x00, 0x00, 0x00}},
}


type cardDevPn struct {
    cardTyp     string
    devName     string
    partNum     string
}

//Add PNs to table of cards with TLV format
var CardTypesTlv = []cardDevPn{
    cardDevPn{"LIPARI",  "SYSTEM",   PN_LIPARI       },
    cardDevPn{"LIPARI",  "FRU",      PN_LIPARI_CPUBRD},
    cardDevPn{"LIPARI",  "CPU",      PN_LIPARI_CPUBRD},
    cardDevPn{"LIPARI",  "SWITCH",   PN_LIPARI_SWITCH},
    cardDevPn{"LIPARI",  "BMC",      PN_LIPARI_BMC   },
}


/**********************************
 *    PUBLIC FUNCTIONS FOR TLV    *
 **********************************/

func CardInListTlv(dev string) (found bool, minPN string) {
    found = false

    //return true if card number is in the list of card types using tlv eeprom format
    var cardtyp string = os.Getenv("CARD_TYPE")
    for _, card := range(CardTypesTlv) {
        if strings.Contains(cardtyp, card.cardTyp) {
            found = true
            if strings.Contains(dev, card.devName) {
                minPN = card.partNum
                //cli.Println("i", "TLV-based EEPROM: Card_Type", cardtyp, "devName", dev, "PN", minPN)
                return
            }
        }
    }

    return
}

func ProgTlvFpga(devName string, sn string, pn string, sn2 string, pn2 string,
                 mac string, date string) (err int) {

    if (sn == "") || (pn == "") || (mac == "") || (date == "") {
        cli.Println("e", "ERROR: Must have values for serial number, part number, MAC address, and date.")
        err = errType.INVALID_PARAM
        return
    }
    //no read from FRU, use default values with update of input sn/sn2/pn/pn2/mac/date
    // debug
    cli.Println("i", "Update SN  :", sn)
    cli.Println("i", "Update PN  :", pn)
    cli.Println("i", fmt.Sprintf("BaseMacAddr: 0x%02X:%02X:%02X:%02X:%02X:%02X",
                                 mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]))
    cli.Println("i", "MFG Date   :", date)
    if sn2 != "" {
        cli.Println("i", "Update SN2 :", sn2)
    }
    if pn2 != "" {
        cli.Println("i", "Update PN2 :", pn2)
    }

    //Initiates the entries with default values, store in eeprom.Data
    err = convertTlvToBytes()
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Card not supported.")
        err = errType.FAIL
        return
    }

    //Updates the byte data slice with specified data
    err = updateTlvs(sn, pn, sn2, pn2, mac, date)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Update failed.")
        err = errType.FAIL
        return
    }

    //Claculate and updates check sums
    var cksum uint32
    cksum, err = CalcCrc32()
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to calculate CRC32")
        return
    }

    updateTlvCrc32(cksum)
    cli.Println("i", "CRC32 is updated")

    //Writes data table to FRU
    writeTlvToFru(devName)

    cli.Println("i", "EEPROM updated!")
    return
}

func ProgTlvFieldFpga(devName string, field string, value string) (err int) {
    err = errType.SUCCESS

    if field == "ALL" {
        cli.Println("e", "updating all fields, should not reach here!!!")
        err = errType.FAIL
        return
    }

    tlvCode := FieldTlvCode[field]
    if tlvCode == 0 {
        cli.Println("e", fieldUsage)
        return errType.FAIL
    }

    i2cFMap, errFMap := i2cinfo.GetI2cFpgaMap(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
        return
    }
    bus := i2cFMap.Bus
    mux := i2cFMap.Mux
    i2cAddr := i2cFMap.I2cAddr
    i2cOffsetlen := i2cFMap.OffsetLen

    // check tlv hdr
    wrData := []byte{}
    for i:=0; i<i2cOffsetlen; i++ {
        wrData = append(wrData, byte(0x00))
    }
    rdData, errFpga := liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, uint32(TlvHdrLen))
    if errFpga != nil {
        cli.Println("e", "ProgTlvFieldFpga - Failed to read I2C FPGA: dev bus mux i2cAddr offset",
                    devName, bus, mux, i2cAddr, i2cOffsetlen)
        return errType.FAIL
    }
    tlvInfoIdBytes := []byte(TlvInfoId)
    for i:=0; i<int(TlvHdrLen); i++ {
        if rdData[i] != tlvInfoIdBytes[i] {
            cli.Println("e", devName, "TLV-format EEPROM has wrong ID string:", string(rdData))
            return errType.FAIL
        }
    }
    TlvData = append(TlvData, rdData...)

    // TLV hdr version and totalLen
    wrData[i2cOffsetlen-1] = TlvHdrLen
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, 3)
    TlvData = append(TlvData, rdData...)
    totalLen := (int(rdData[1]) << 8) + int(rdData[2])    // big endian
    // total EEPROM size < 2048 bytes
    if totalLen >= 2037 || totalLen <= int(TlvStart) {
        cli.Println("i", "Wrong Total Length:", totalLen)
        return errType.FAIL
    }

    // read out all TLVs
    wrData[i2cOffsetlen-1] = TlvStart    //TlvTotalLenOffset + 2
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, uint32(totalLen))
    TlvData = append(TlvData, rdData...)

    // update the tlv in field
    err = updateTlvField(tlvCode, value)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR: Failed to program to FRU. Update failed.")
        return errType.FAIL
    }

    //Claculate and updates check sums
    var cksum uint32
    cksum, err = CalcCrc32()
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to calculate CRC32")
        return
    }

    updateTlvCrc32(cksum)
    cli.Println("i", "CRC32 is updated")

    //Writes data table to FRU
    writeTlvToFru(devName)

    cli.Println("i", "EEPROM updated!")
    return
}

func DisplayTlvFpga(devName string, field string, fpo bool) (err int){

    i2cFMap, errFMap := i2cinfo.GetI2cFpgaMap(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
        return
    }
    bus := i2cFMap.Bus
    mux := i2cFMap.Mux
    i2cAddr := i2cFMap.I2cAddr
    i2cOffsetlen := i2cFMap.OffsetLen

    TlvData = []byte{}

    // Checks TLV ID string "TlvInfo"
    // API I2c_access() need to write offset address before read at the offset
    wrData := []byte{}
    for i:=0; i<i2cOffsetlen; i++ {
        wrData = append(wrData, byte(0x00))
    }
    rdData, errFpga := liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, uint32(TlvHdrLen))
    if errFpga != nil {
        cli.Println("e", "DisplayTlvFpga - Failed to read I2C FPGA: dev bus mux i2cAddr offset",
                    devName, bus, mux, i2cAddr, i2cOffsetlen)
        return
    }
    // debug
    //cli.Println("i", "debugging: tlvIdStr =", rdData)
    var outputStr string
    var tlvTitle string = "TLV ID String"
    tlvIdStr := string(rdData)
    outputStr = fmt.Sprintf("%-20s\t\t%s", tlvTitle, tlvIdStr)
    cli.Println("i", outputStr)

    tlvInfoIdBytes := []byte(TlvInfoId)
    for i:=0; i<int(TlvHdrLen); i++ {
        if rdData[i] != tlvInfoIdBytes[i] {
            cli.Println("e", devName, "TLV-format EEPROM has wrong ID string:", tlvIdStr)
            err = errType.FAIL
            return
        }
    }
    TlvData = append(TlvData, rdData...)
    start := int(TlvHdrLen)

    // TLV hdr version
    wrData[i2cOffsetlen-1] = TlvHdrLen
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, 1)
    TlvData = append(TlvData, rdData...)
    tlvTitle = "TLV Hdr Version"
    // Note: TlvHdrLen = 1
    outputStr = fmt.Sprintf("%-20s\t\t%d", tlvTitle, TlvData[start])
    cli.Println("i", outputStr)
    start += 1

    // TLV total_length (2-bytes)
    wrData[i2cOffsetlen-1] = TlvTotalLenOffset
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, 2)
    totalLen := (int(rdData[0]) << 8) + int(rdData[1])    // big endian
    tlvTitle = "TLV Total Length"
    cli.Println("i", fmt.Sprintf("%-20s\t\t%d", tlvTitle, totalLen))
    TlvData = append(TlvData, rdData...)
    start += 2

    // total EEPROM size < 2048 bytes
    if totalLen >= 2037 {
        cli.Println("i", "Wrong Total Length:", totalLen)
        err = errType.FAIL
        return
    }

    // read out all TLVs
    wrData[i2cOffsetlen-1] = TlvTotalLenOffset + 2
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, uint32(totalLen))
    TlvData = append(TlvData, rdData...)
    // debug
    //cli.Println("i", "TLV whole contents:", TlvData)

    for {
        if start >= (totalLen + int(TlvTotalLenOffset) + 2) {
            break
        }

        if field != "ALL" {
            if int(FieldTlvCode[field]) == 0 {    //input field does not support
                cli.Println("e", fieldUsage)
                return errType.FAIL
            } else if (FieldTlvCode[field] != TlvData[start]) {
                start += 2 + int(TlvData[start+1])
                continue
            } else {
                dispTlvField(start)
                return errType.SUCCESS
            }
        }

        dispTlvField(start)
        start += 2 + int(TlvData[start+1])
    }

    err = errType.SUCCESS
    return
}

func DumpEepromTlvFpga(devName string, numBytes int) (err int) {

    i2cFMap, errFMap := i2cinfo.GetI2cFpgaMap(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
        return
    }
    bus := i2cFMap.Bus
    mux := i2cFMap.Mux
    i2cAddr := i2cFMap.I2cAddr
    i2cOffsetlen := i2cFMap.OffsetLen

    if Smbus {
        // smbus available, should not reach here!
        cli.Println("e", "smbus is ready, should not reach here!")
        return
    }

    f, error := os.OpenFile("eeprom", os.O_CREATE|os.O_WRONLY, 0600)
    if error != nil {
        cli.Println("e", "file create failed")
    }
    cli.Println("i", "dump FRU to file \"./eeprom\"")

    wrData := []byte{}
    for i:=0; i<i2cOffsetlen; i++ {
        wrData = append(wrData, byte(0x00))
    }
    rdData, errFpga := liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, uint32(numBytes))
    if errFpga != nil {
        cli.Println("e", "DumpEepromTlvFpga() - Failed to read I2C FPGA: dev bus mux i2cAddr offset",
                    devName, bus, mux, i2cAddr, i2cOffsetlen)
        return
    }
    //debug
    cli.Println("i", rdData)
    f.WriteString(string(rdData[:]))

    f.Close()
    return
}


/***************************
 *    GENERIC FUNCTIONS    *
 ***************************/

func convertTlvToBytes() (err int){
    //Writes all entries of EepromTlvs into new slices
    //Checks and sets EepromTlvs based on the input part number

    // header
    TlvData = append(TlvData, []byte(TlvInfoId)...)
    TlvData = append(TlvData, byte(TlvHdrVer))
    TlvData = append(TlvData, []byte{0x0, 0x0}...)

    var total_length int = 0
    // debug
    //cli.Println("i", "convertTlvToBytes(): Number of entries in EepromTlvs is", len(EepromTlvs))
    for i:=0; i<len(EepromTlvs); i++ {
        TlvData = append(TlvData, EepromTlvs[i].TypeCode)
        TlvData = append(TlvData, EepromTlvs[i].Length)
        total_length += int(EepromTlvs[i].Length) + 2
        //debug
        //cli.Println("i", "total_length =", total_length)
        TlvData = append(TlvData, EepromTlvs[i].Value...)
        TlvInfo = append(TlvInfo, tlvEntry{EepromTlvs[i].TypeCode, EepromTlvs[i].DataType,
                         EepromTlvs[i].Offset, EepromTlvs[i].Length, EepromTlvs[i].Value})
        // Debug
        //cli.Println("i", getTlvName(EepromTlvs[i].TypeCode), "\t", EepromTlvs[i].Length, "\t", EepromTlvs[i].Value)
        //cli.Println("i", getTlvName(TlvInfo[i].TypeCode), "\t", TlvInfo[i].Length, "\t", TlvInfo[i].Value)
    }

    TlvData[TlvTotalLenOffset] = byte((total_length>>8)&0xFF)
    TlvData[TlvTotalLenOffset+1] = byte(total_length&0xFF)
    // debug
    //cli.Println("i", "Total Length:", "\t\t", TlvData[TlvTotalLenOffset]<<8 + TlvData[TlvTotalLenOffset+1])

    return
}

func dispTlvField(start int) (err int) {
    err = errType.SUCCESS
    var tempStr string
    if TlvData[start] == num_mac_addr {    // 2-bytes
            if TlvData[start+1] != 2 {
                err = errType.FAIL
                cli.Println("e", getTlvName(TlvData[start]), "lenght is not 2 bytes!")
                return
            }
            cli.Println("i", fmt.Sprintf("%-20s\t\t0x%02X 0x%02X (%d)", getTlvName(TlvData[start]),
                        TlvData[start+2], TlvData[start+3],
                        int(TlvData[start+2])<<8 + int(TlvData[start+3])))
    } else if TlvData[start] == base_mac_addr {    // 6-byte
            if TlvData[start+1] != 6 {
                err = errType.FAIL
                cli.Println("e", getTlvName(TlvData[start]), "lenght is not 6 bytes!")
                return
            }
            tempStr += fmt.Sprintf("0x")
            for j:=start+2; j<start+1+int(TlvData[start+1]); j++ {
                tempStr += fmt.Sprintf("%02X:", TlvData[j])
            }
            tempStr += fmt.Sprintf("%02X", TlvData[start+1+int(TlvData[start+1])])
            cli.Println("i", fmt.Sprintf("%-20s\t\t%s", getTlvName(TlvData[start]), tempStr))
    } else if TlvData[start] == device_version {    // single byte
            if TlvData[start+1] != 1 {
                err = errType.FAIL
                cli.Println("e", getTlvName(TlvData[start]), "lenght is not 1 byte!")
                return
            }
            cli.Println("i", fmt.Sprintf("%-20s\t\t%d", getTlvName(TlvData[start]), TlvData[start+2]))
    } else if TlvData[start] == crc_32 {    // 4-byte
            cli.Println("i", fmt.Sprintf("%-20s\t\t0x%02X 0x%02X 0x%02X 0x%02X", getTlvName(TlvData[start]),
                        TlvData[start+2], TlvData[start+3], TlvData[start+4], TlvData[start+5]))
    } else {
            cli.Println("i", fmt.Sprintf("%-20s\t\t%s", getTlvName(TlvData[start]),
                        TlvData[start+2:start+2+int(TlvData[start+1])]))
    }

    return
}

func updateTlvs(sn string, pn string, sn2 string, pn2 string, mac string, date string) (err int) {
    //sn/sn2 length 15; pn/pn2 length 12
    //base_mac_addr 6 byte, input is string "xxxxxxxxxxxx"
    //MFG Data/Time: string, len 19, format "MM/DD/YYYY HH:NN:SS"

    snByte   := []byte(sn)
    pnByte   := []byte(pn)
    sn2Byte  := []byte(sn2)
    pn2Byte  := []byte(pn2)
    dateByte := []byte(date)

    macByte := make([]byte, 6)
    data, _ := strconv.ParseUint(mac, 16, 64)
    macByte[0] = byte(data >> 40 & 0xFF)
    macByte[1] = byte(data >> 32 & 0xFF)
    macByte[2] = byte(data >> 24 & 0xFF)
    macByte[3] = byte(data >> 16 & 0xFF)
    macByte[4] = byte(data >> 8 & 0xFF)
    macByte[5] = byte(data & 0xFF)

    for i:=0; i<len(TlvInfo); i++ {
        switch TlvInfo[i].TypeCode {
        case part_number:         //pn
            updateTlvValue(int(TlvInfo[i].Offset)+2, len(pnByte), TlvInfo[i].Length, pnByte)
        case serial_number:       //sn
            updateTlvValue(int(TlvInfo[i].Offset)+2, len(snByte), TlvInfo[i].Length, snByte)
        case base_mac_addr:       //mac
            updateTlvValue(int(TlvInfo[i].Offset)+2, len(macByte), TlvInfo[i].Length, macByte)
        case manufacture_date:    //date
            updateTlvValue(int(TlvInfo[i].Offset)+2, len(dateByte), TlvInfo[i].Length, dateByte)
        case pcba_part_number:    //pn2
            updateTlvValue(int(TlvInfo[i].Offset)+2, len(pn2Byte), TlvInfo[i].Length, pn2Byte)
        case pcba_serial_number:  //sn2
            updateTlvValue(int(TlvInfo[i].Offset)+2, len(sn2Byte), TlvInfo[i].Length, sn2Byte)
        default:
            continue
        }
    }

    return
}

func updateTlvField(tlvCode byte, value string) (err int) {
    err = errType.SUCCESS

    start := int(TlvStart)
    var valBytes = []byte{}
    for {
        if start >= len(TlvData) {
            break;
        }

        if TlvData[start] == tlvCode {
            dTyp, _ := getTlvDatatyp(tlvCode)
            if tlvCode == base_mac_addr {
                data, _ := strconv.ParseUint(value, 16, 64)
                valBytes = append(valBytes, byte(data >> 40 & 0xFF))
                valBytes = append(valBytes, byte(data >> 32 & 0xFF))
                valBytes = append(valBytes, byte(data >> 24 & 0xFF))
                valBytes = append(valBytes, byte(data >> 16 & 0xFF))
                valBytes = append(valBytes, byte(data >> 8 & 0xFF))
                valBytes = append(valBytes, byte(data & 0xFF))
            } else if (dTyp==INT16) {
                data, _ := strconv.ParseUint(value, 10, 16)
                valBytes = append(valBytes, byte(data >> 8 & 0xFF))
                valBytes = append(valBytes, byte(data & 0xFF))
            } else if (dTyp==INT8) {
                data, _ := strconv.ParseUint(value, 10, 8)
                valBytes = append(valBytes, byte(data & 0xFF))
            } else {  // STRING, etc.
                valBytes = []byte(value)
            }

            cli.Println("i", "Update Field:", getTlvName(tlvCode), valBytes)
            updateTlvValue(start+2, len(valBytes), TlvData[start+1], valBytes)
            return errType.SUCCESS
        }
        start += int(TlvData[start+1]) + 2
    }

    cli.Println("e", "The input field to be updated is not found!")
    cli.Println("i", fieldUsage)
    return errType.FAIL
}

func updateTlvValue(offset int, inputLen int, specLen byte, newVal []byte) {
    if inputLen <= int(specLen) {
        for j:=0; j<inputLen; j++ {
            TlvData[offset+j] = newVal[j]
        }
        offset += inputLen
        for k:=0; k<int(specLen)-inputLen; k++ {
            TlvData[offset+k] = 0x0
        }
    } else {
        for j:=0; j<int(specLen); j++ {
            TlvData[offset+j] = newVal[j]
        }
    }
}

func CalcCrc32() (cksum uint32, err int) {

    if TlvInfoId != string(TlvData[0:8]) {
        cli.Println("e", "Invalid: EEPROM is not in TLV format!")
        err = errType.FAIL
        return
    }

    cksum = crc32.ChecksumIEEE(TlvData[0:len(TlvData)-4])
    return
}

func updateTlvCrc32(cksum uint32) {
    l := len(TlvData)
    TlvData[l-4] = byte((cksum>>24)&0xFF)
    TlvData[l-3] = byte((cksum>>16)&0xFF)
    TlvData[l-2] = byte((cksum>>8)&0xFF)
    TlvData[l-1] = byte(cksum&0xFF)
    //debug
    dbgStr := fmt.Sprintf("CRC32: 0x%02X 0x%02X 0x%02X 0x%02X",
              TlvData[l-4], TlvData[l-3], TlvData[l-2], TlvData[l-1])
    cli.Println("i", dbgStr)
}

func writeTlvToFru(devName string) (err int) {
    err = errType.SUCCESS
    i2cFMap, errFMap := i2cinfo.GetI2cFpgaMap(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
        err = errType.FAIL
        return
    }
    bus := i2cFMap.Bus
    mux := i2cFMap.Mux
    i2cAddr := i2cFMap.I2cAddr
    i2cOffsetlen := i2cFMap.OffsetLen

    wrData := []byte{}
    for i:=0; i<=i2cOffsetlen; i++ {
        wrData = append(wrData, byte(0x00))
    }

    var errFpga error
    for k:=0; k<len(TlvData); k++ {
        for t:=0; t<i2cOffsetlen; t++ {
            wrData[t] = byte((k>>uint(8*(i2cOffsetlen-t-1))) & 0xFF)
        }
        wrData[i2cOffsetlen] = TlvData[k]
        _, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, 0)
        if errFpga != nil {
            cli.Println("e", "Failed to write EEPROM through I2C FPGA: dev bus mux i2cAddr i2cOffsetlen",
                        devName, bus, mux, i2cAddr, i2cOffsetlen)
            err = errType.FAIL
            return
        }
        // delay for writing
        misc.SleepInUSec(10000)
    }

    return
}


func getTlvName(tlvcode byte) (Name string) {
    switch tlvcode {
    case product_name:
        Name = "Product Name"
    case part_number:
        Name = "Part Number"
    case serial_number:
        Name = "Serial Number"
    case base_mac_addr:
        Name = "MAC Address Base"
    case manufacture_date:
        Name = "MFG Date/Time"
    case device_version:
        Name = "Device Version"
    case label_revision:
        Name = "Label Revision"
    case platform_name:
        Name = "Platform Name"
    case onie_version:
        Name = "ONIE Version"
    case num_mac_addr:
        Name = "Number of MAC Addr"
    case manufacturer:
        Name = "Manufacturer"
    case country_code:
        Name = "Country Code"
    case vendor:
        Name = "Vendor Name"
    case diag_version:
        Name = "Diag Version"
    case service_tag:
        Name = "Service Tag"
    case vendor_extension:
        Name = "Vendor Extension"
    case pcba_part_number:
        Name = "PCBA Part Number"
    case pcba_serial_number:
        Name = "PCBA Serial Number"
    case crc_32:
        Name = "CRC-32"
    default:
        Name = "Unknown"
    }

    return
}

func getTlvDatatyp(tlvcode byte) (typ int, err int) {
    err = errType.SUCCESS
    switch tlvcode {
    case base_mac_addr:
    case device_version:
    case crc_32:
        typ = INT8
    case num_mac_addr:
        typ = INT16
    default:
        typ = STRING
    }

    return
}

