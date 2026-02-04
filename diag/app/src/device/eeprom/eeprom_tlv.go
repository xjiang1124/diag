package eeprom

import (
	"fmt"
	"os"
	"strings"
    "strconv"
	"hash/crc32"
    "common/errType"
    "common/cli"
    "common/misc"
    //"protocol/smbusNew"
    "device/fpga/liparifpga"
    "hardware/i2cinfo"
    "protocol/smbusNew"
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
	//extension fields
	chassis_type       = byte(0x50)
	board_type         = byte(0x51)
	sub_type           = byte(0x52)
	pcba_part_number   = byte(0x53)
	pcba_serial_number = byte(0x54)
    hw_maj_rev         = byte(0x55)
    hw_min_rev         = byte(0x56)
    mfg_deviation      = byte(0x57)
    mfg_bits           = byte(0x58)
    eng_bits           = byte(0x59)
    //tail
	vendor_extension   = byte(0xfd)
	crc_32             = byte(0xfe)
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
    "HW_MAJOR_REV":   hw_maj_rev,
    "HW_MINOR_REV":   hw_min_rev,
    "MFG_DEVIATION":  mfg_deviation,
    "MFG_BITS":     mfg_bits,
    "ENG_BITS":     eng_bits,
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
    "    HW_Maj_Rev (HW major revision)\n",
    "    HW_Min_Rev (HW minor revision)\n",
    "    MFG_Dev (Manufacturer deviation)\n",
    "    Mfg_Bits (Manufacturer bits)\n",
    "    Eng_bits (Engineering bits)\n",
}

/*
 * def specific EepromTlvs without tlv ID string, for given card types
 * different card type may have various TLV entries
 */
var LipariCpuTlvs = []tlvEntry {
    //tlvEntry{ tlv_id_str,        STRING,    0,    8,   []byte(TlvInfoId)},
    //tlvEntry{ tlv_hdr_ver,       INT8,      8,    1,   TlvHdrVer},
    //all TLVs big endian
    //tlvEntry{ total_length,      INT8,      9,    2,   []byte{0x00, 0x00}},
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
    //tlvEntry{ total_length,      INT8,      9,    2,   []byte{0x0, 0x00}},
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

/*
 * MTP: MATERA
 */
var MtpMateraMbTlvs = []tlvEntry {
    //tlvEntry{ tlv_id_str,        STRING,    0,    8,   []byte(TlvInfoId)},
    //tlvEntry{ tlv_hdr_ver,       INT8,      8,    1,   TlvHdrVer},
    //all TLVs big endian
    //
    //          TypeCode         DataType  Offset Len Value
    //tlvEntry{ total_length,    INT8,     9,     2,  []byte{0x00, 0x00}},
    tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"MATERA MB"
            0x4d, 0x41, 0x54, 0x45, 0x52, 0x41, 0x20, 0x4d,
            0x42, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}},
    tlvEntry{ part_number,       STRING,   33,  35,   []byte{
            0x36, 0x38, 0x2D, 0x30, 0x30, 0x33, 0x32, 0x2D,
            0x30, 0x31, 0x20, 0x30, 0x30, 0x31, 0x20, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00}},
    tlvEntry{ serial_number,     STRING,   70,  20,   []byte{
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ base_mac_addr,     INT8,     92,   6,   []byte{
            0x00, 0xAE, 0xCD, 0x00, 0x00, 0x00}},
    tlvEntry{ manufacture_date,  STRING,   100,  19,   []byte("04/12/2023 00:00:00")},
    tlvEntry{ num_mac_addr,      INT16,    121,   2,   []byte{0x01, 0x00}},
    tlvEntry{ manufacturer,      STRING,   125,  20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ vendor,            STRING,  147,  20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ hw_maj_rev,        STRING,  169,   2,   []byte{0x30, 0x30}}, //"00"
    tlvEntry{ hw_min_rev,        STRING,  173,   4,   []byte{0x30, 0x31, 0x30, 0x30}}, //"0100"
    tlvEntry{ mfg_deviation,     STRING,  179,  20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ mfg_bits,          STRING,  201,   2,   []byte{0x00, 0x00}},
    tlvEntry{ eng_bits,          STRING,  205,   2,   []byte{0x00, 0x00}},
    tlvEntry{ crc_32,             INT8,   209,   4,   []byte{0x00, 0x00, 0x00, 0x00}},
}

var MtpPanareaMbProductName = tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"PANAREA MB"
            0x50, 0x41, 0x4E, 0x41, 0x52, 0x45, 0x41, 0x20,
            0x4d, 0x42, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}}

var MtpPonzaMbProductName = tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"PONZA MB"
            0x50, 0x4F, 0x4E, 0x5A, 0x41, 0x20, 0x4D, 0x42,
            0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}}

var MtpMateraIobTlvs = []tlvEntry {
    //tlvEntry{ tlv_id_str,        STRING,    0,    8,   []byte(TlvInfoId)},
    //tlvEntry{ tlv_hdr_ver,       INT8,      8,    1,   TlvHdrVer},
    //all TLVs big endian
    //
    //          TypeCode         DataType  Offset Len Value
    //tlvEntry{ total_length,    INT8,     9,     2,  []byte{0x00, 0x00}},
    tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"MATERA IOB"
            0x4d, 0x41, 0x54, 0x45, 0x52, 0x41, 0x20, 0x49,
            0x4f, 0x42, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}},
    tlvEntry{ part_number,       STRING,   33,  35,   []byte{
            0x36, 0x38, 0x2D, 0x30, 0x30, 0x33, 0x32, 0x2D,
            0x30, 0x31, 0x20, 0x30, 0x30, 0x31, 0x20, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00}},
    tlvEntry{ serial_number,     STRING,   70,  20,   []byte{
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ base_mac_addr,     INT8,     92,   6,   []byte{
            0x00, 0xAE, 0xCD, 0x00, 0x00, 0x00}},
    tlvEntry{ manufacture_date,  STRING,   100,  19,   []byte("04/12/2023 00:00:00")},
    tlvEntry{ num_mac_addr,      INT16,    121,   2,   []byte{0x01, 0x00}},
    tlvEntry{ manufacturer,      STRING,   125,  20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ vendor,            STRING,  147,  20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ hw_maj_rev,        STRING,  169,   2,   []byte{0x30, 0x30}}, //"00"
    tlvEntry{ hw_min_rev,        STRING,  173,   4,   []byte{0x30, 0x31, 0x30, 0x30}}, //"0100"
    tlvEntry{ mfg_deviation,     STRING,  179,  20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ mfg_bits,          STRING,  201,   2,   []byte{0x00, 0x00}},
    tlvEntry{ eng_bits,          STRING,  205,   2,   []byte{0x00, 0x00}},
    tlvEntry{ crc_32,             INT8,   209,   4,   []byte{0x00, 0x00, 0x00, 0x00}},
}

var MtpPanareaIobProductName = tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"PANAREA IOB"
            0x50, 0x41, 0x4E, 0x41, 0x52, 0x45, 0x41, 0x20,
            0x49, 0x4f, 0x42, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}}

var MtpPonzaIobProductName = tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"PONZA MB"
            0x50, 0x4F, 0x4E, 0x5A, 0x41, 0x20, 0x49, 0x4f,
            0x42, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}}

var MtpMateraFpicTlvs = []tlvEntry {
    //tlvEntry{ tlv_id_str,        STRING,    0,    8,   []byte(TlvInfoId)},
    //tlvEntry{ tlv_hdr_ver,       INT8,      8,    1,   TlvHdrVer},
    //all TLVs big endian
    //
    //          TypeCode         DataType  Offset Len Value
    //tlvEntry{ total_length,    INT8,     9,     2,  []byte{0x00, 167}},
    tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"MATERA FPIC"
            0x4d, 0x41, 0x54, 0x45, 0x52, 0x41, 0x20, 0x46,
            0x50, 0x49, 0x43, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}},
    tlvEntry{ part_number,       STRING,   33,  35,   []byte{
            0x36, 0x38, 0x2D, 0x30, 0x30, 0x33, 0x32, 0x2D,
            0x30, 0x31, 0x20, 0x30, 0x30, 0x31, 0x20, 0x20,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00}},
    tlvEntry{ serial_number,     STRING,   70,  20,   []byte{
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ base_mac_addr,     INT8,     92,   6,   []byte{
            0x00, 0xAE, 0xCD, 0x00, 0x00, 0x00}},
    tlvEntry{ manufacture_date,  STRING,   100,  19,  []byte("04/12/2023 00:00:00")},
    tlvEntry{ num_mac_addr,      INT16,    121,  2,   []byte{0x01, 0x00}},
    tlvEntry{ manufacturer,      STRING,   125, 20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ vendor,            STRING,   147,  20,  []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ hw_maj_rev,        STRING,  169,   2,   []byte{0x30, 0x30}}, //"00"
    tlvEntry{ hw_min_rev,        STRING,  173,   4,   []byte{0x30, 0x31, 0x30, 0x30}}, //"0100"
    tlvEntry{ mfg_deviation,     STRING,  179,  20,   []byte{
            0x41, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00}},
    tlvEntry{ mfg_bits,          STRING,  201,   2,   []byte{0x00, 0x00}},
    tlvEntry{ eng_bits,          STRING,  205,   2,   []byte{0x00, 0x00}},
    tlvEntry{ crc_32,             INT8,   209,   4,   []byte{0x00, 0x00, 0x00, 0x00}},
}

var MtpPanareaFpicProductName = tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"PANAREA FPIC"
            0x50, 0x41, 0x4E, 0x41, 0x52, 0x45, 0x41, 0x20,
            0x46, 0x50, 0x49, 0x43, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}}

var MtpPonzaFpicProductName = tlvEntry{ product_name,      STRING,   11,  20,   []byte{
            //"PANAREA FPIC"
            0x50, 0x4F, 0x4E, 0x5A, 0x41, 0x20, 0x20, 0x20,
            0x46, 0x50, 0x49, 0x43, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x20, 0x20}}

type cardDevPn struct {
    cardTyp     string
    devName     string
    partNum     string
}

//Add PNs to table of cards with TLV format
var CardTypesTlv = []cardDevPn{
    //LIPARI
    cardDevPn{"LIPARI",      "SYSTEM",      PN_LIPARI       },
    cardDevPn{"LIPARI",      "FRU",         PN_LIPARI_CPUBRD},
    cardDevPn{"LIPARI",      "FRU_CPUBRD",  PN_LIPARI_CPUBRD},
    cardDevPn{"LIPARI",      "FRU_SWITCH",  PN_LIPARI_SWITCH},
    cardDevPn{"LIPARI",      "FRU_BMC",     PN_LIPARI_BMC   },
    //MTP_MATERA
    cardDevPn{"MTP_MATERA",  "FRU",         PN_MTP_MATERA_FRU},
    cardDevPn{"MTP_MATERA",  "MB",          PN_MTP_MATERA_MB},
    cardDevPn{"MTP_MATERA",  "IOBL",        PN_MTP_MATERA_IOB},
    cardDevPn{"MTP_MATERA",  "IOBR",        PN_MTP_MATERA_IOB},
    cardDevPn{"MTP_MATERA",  "FPIC",        PN_MTP_MATERA_FPIC},
    //MTP_PANAREA
    cardDevPn{"MTP_PANAREA", "FRU",         PN_MTP_PANAREA_FRU},
    cardDevPn{"MTP_PANAREA", "MB",          PN_MTP_PANAREA_MB},
    cardDevPn{"MTP_PANAREA", "IOBL",        PN_MTP_PANAREA_IOB},
    cardDevPn{"MTP_PANAREA", "IOBR",        PN_MTP_PANAREA_IOB},
    cardDevPn{"MTP_PANAREA", "FPIC",        PN_MTP_PANAREA_FPIC},
    //MTP_PONZA
    cardDevPn{"MTP_PONZA", "FRU",           PN_MTP_PONZA_FRU},
    cardDevPn{"MTP_PONZA", "MB",            PN_MTP_PONZA_MB},
    cardDevPn{"MTP_PONZA", "IOBL",          PN_MTP_PONZA_IOB},
    cardDevPn{"MTP_PONZA", "IOBR",          PN_MTP_PONZA_IOB},
    cardDevPn{"MTP_PONZA", "FPIC",          PN_MTP_PONZA_FPIC},
}

type fpgaOffsetW struct {
    cardTyp        string
    devName        string
    OffsetWidth    int    //number of bytes
}

var FpgaOffsetWidth = []fpgaOffsetW{
    //LIPARI
    fpgaOffsetW{"LIPARI", "FRU",        1},
    fpgaOffsetW{"LIPARI", "FRU_CPUBRD", 1},
    fpgaOffsetW{"LIPARI", "FRU_SWITCH", 2},
}

/**********************************
 *    PUBLIC FUNCTIONS FOR TLV    *
 **********************************/

func CardInListTlv(dev string) (found bool, minPN string) {
    found = false
    //return true if card type is in the list of cards with tlv-format eeprom
    var cardtyp string = CardType
    for _, card := range(CardTypesTlv) {
        if (cardtyp == card.cardTyp) {
            found = true
            if (dev == card.devName) {
                minPN = card.partNum
                return
            }
        }
    }

    return
}

func ProgTlvs(devName string, sn string, pn string, sn2 string, pn2 string,
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
        cli.Println("e", "Failed to program to FRU. Card not supported.")
        err = errType.FAIL
        return
    }

    //Updates the byte data slice with specified data
    err = updateTlvs(sn, pn, sn2, pn2, mac, date)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to program to FRU. Update failed.")
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
    found, _ := CardInListAccessViaFpga(devName)
    if found == true { // access fru via FPGA
        err = writeTlvsViaFpga(devName)
    } else { // access FRU via smbus
        err = writeTlvsViaSmbus(devName)
    }

    cli.Println("i", "EEPROM updated!")
    return
}

func ProgTlvField(devName string, field string, value string) (err int) {
    found, _ := CardInListAccessViaFpga(devName)
    if found == true { // access fru via FPGA
        err = ProgTlvFieldFpga(devName, field, value)
    } else { // access FRU via smbus
        err = ProgTlvFieldSmbus(devName, field, value)
    }
    return
}

func ProgTlvFieldSmbus(devName string, field string, value string) (err int) {
    err = errType.SUCCESS

    if field == "ALL" {
        cli.Println("e", "updating all fields, should not reach here!!!")
        err = errType.FAIL
        return
    }

    tlvCode := FieldTlvCode[field] //invalid field
    if tlvCode == 0 {
        cli.Println("e", fieldUsage)
        return errType.FAIL
    }

    TlvData = []byte{}
    var tmpData byte

    //readout the TLV hdr TlvStart = TlvHdrLen + TlvVerBytes + TlvTotalLenBytes
    for i := 0; i < int(TlvStart); i++ {
        tmpData, err = readByteSmbus(devName, i)
        TlvData = append(TlvData, tmpData)
    }

    totalLen := (int(TlvData[TlvTotalLenOffset]) << 8) + int(TlvData[TlvTotalLenOffset+1])
    //total EEPROM size < 2048 bytes
    if totalLen >= 2037 { // exclude 11 bytes TLV hdr
        cli.Println("i", "Wrong Total Length:", totalLen)
        err = errType.FAIL
        return
    }

    //read out TLV contents
    for i := int(TlvStart); i < int(TlvStart) + totalLen; i++ {
        tmpData, err = readByteSmbus(devName, i)
        TlvData = append(TlvData, tmpData)
    }

    // update the tlv in field
    err = updateTlvField(tlvCode, value)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to program to FRU. Update failed.")
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
    writeTlvsViaSmbus(devName)
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

    i2cFMap, errFMap := i2cinfo.GetI2cInfo(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "Failed to obtain I2C FPGA mapping of", devName)
        return
    }
    strArr := strings.Split(i2cFMap.HubName, "_")
    tmp, _ := strconv.Atoi(strArr[0])
    bus := uint32(tmp)
    tmp, _ = strconv.Atoi(strArr[1])
    mux := uint32(tmp)
    i2cAddr := uint32(i2cFMap.DevAddr)
    i2cOffsetlen := getFpgaOffsetWidth(devName)
    if i2cOffsetlen == -1 {
        return errType.FAIL
    }

    // check tlv hdr
    wrData := []byte{}
    for i:=0; i<i2cOffsetlen; i++ {
        wrData = append(wrData, byte(0x00))
    }
    rdData, errFpga := liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)),
                                             wrData, uint32(TlvHdrLen))
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
    totalLen := (int(rdData[1]) << 8) + int(rdData[2]) //big endian
    // total EEPROM size < 2048 bytes
    if totalLen >= 2037 || totalLen <= int(TlvStart) {
        cli.Println("i", "Wrong Total Length:", totalLen)
        return errType.FAIL
    }

    // read out all TLVs
    wrData[i2cOffsetlen-1] = TlvStart    //TlvTotalLenOffset + 2
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)),
                                            wrData, uint32(totalLen))
    TlvData = append(TlvData, rdData...)

    // update the tlv in field
    err = updateTlvField(tlvCode, value)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to program to FRU. Update failed.")
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
    writeTlvsViaFpga(devName)

    cli.Println("i", "EEPROM updated!")
    return
}

func DisplayTlvs(devName string, field string, fpo bool) (err int){
    found, _ := CardInListAccessViaFpga(devName)
    if found == true { // access fru via FPGA
        err = DisplayTlvFpga(devName, field, fpo)
    } else { // access FRU via smbus
        err = DisplayTlvSmbus(devName, field, fpo)
    }
    return
}

func DisplayTlvSmbus(devName string, field string, fpo bool) (err int){
    err = errType.SUCCESS

    TlvData = []byte{}
    var tmpData byte

    //readout the TLV hdr TlvStart = TlvHdrLen + TlvVerBytes + TlvTotalLenBytes
    for i := 0; i < int(TlvStart); i++ {
        tmpData, err = readByteSmbus(devName, i)
        TlvData = append(TlvData, tmpData)
    }

    //display TLV hdr
    var start int = 0
    var outputStr string
    var tlvTitle string = "TLV ID String"
    tlvIdStr := string(TlvData[start : start+int(TlvHdrLen)])
    outputStr = fmt.Sprintf("%-20s\t\t%s", tlvTitle, tlvIdStr)
    cli.Println("i", outputStr)
    start += int(TlvHdrLen)

    tlvTitle = "TLV Hdr Version"
    outputStr = fmt.Sprintf("%-20s\t\t%d", tlvTitle, int(TlvData[start]))
    cli.Println("i", outputStr)
    start += int(TlvVerBytes)

    tlvTitle = "TLV Total Length"
    totalLen := (int(TlvData[start]) << 8) + int(TlvData[start+1]) //big endian, 2 bytes
    cli.Println("i", fmt.Sprintf("%-20s\t\t%d", tlvTitle, totalLen))
    start += int(TlvTotalLenBytes)

    //total EEPROM size < 2048 bytes
    if totalLen >= 2037 { // exclude 11 bytes TLV hdr
        cli.Println("i", "Wrong Total Length:", totalLen)
        err = errType.FAIL
        return
    }

    //read out TLV contents
    for i := start; i < start + totalLen; i++ {
        tmpData, err = readByteSmbus(devName, i)
        TlvData = append(TlvData, tmpData)
    }

    //display TLV fields
    for {
        if start >= (totalLen + int(TlvStart)) {
            if field != "ALL" {
                cli.Println("e", "TLV field", field, "is not found in dev", devName)
                err = errType.FAIL
                return
            }
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

func DisplayTlvFpga(devName string, field string, fpo bool) (err int){

    i2cFMap, errFMap := i2cinfo.GetI2cInfo(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
        return
    }
    strArr := strings.Split(i2cFMap.HubName, "_")
    tmp, _ := strconv.Atoi(strArr[0])
    bus := uint32(tmp)
    tmp, _ = strconv.Atoi(strArr[1])
    mux := uint32(tmp)
    i2cAddr := uint32(i2cFMap.DevAddr)
    i2cOffsetlen := getFpgaOffsetWidth(devName)
    if i2cOffsetlen == -1 {
        err = errType.FAIL
        return
    }

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
    //cli.Println("i", "/
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
    // Note: TlvHdrVersion Len = 1
    outputStr = fmt.Sprintf("%-20s\t\t%d", tlvTitle, TlvData[start])
    cli.Println("i", outputStr)
    start += int(TlvVerBytes)

    // TLV total_length (2-bytes)
    wrData[i2cOffsetlen-1] = TlvTotalLenOffset
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, 2)
    totalLen := (int(rdData[0]) << 8) + int(rdData[1]) //big endian
    tlvTitle = "TLV Total Length"
    cli.Println("i", fmt.Sprintf("%-20s\t\t%d", tlvTitle, totalLen))
    TlvData = append(TlvData, rdData...)
    start += int(TlvTotalLenBytes)

    // total EEPROM size < 2048 bytes
    if totalLen >= 2037 { // exclude 11 bytes TLV hdr
        cli.Println("i", "Wrong Total Length:", totalLen)
        err = errType.FAIL
        return
    }

    // read out all TLVs
    wrData[i2cOffsetlen-1] = TlvTotalLenOffset + 2
    rdData = []byte{}
    rdData, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)),
                                            wrData, uint32(totalLen))
    TlvData = append(TlvData, rdData...)
    // debug
    //cli.Println("i", "TLV whole contents:", TlvData)

    for {
        if start >= (totalLen + int(TlvStart)) {
            if field != "ALL" {
                cli.Println("e", "TLV field", field, "is not found in dev", devName)
                err = errType.FAIL
                return
            }
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

func DumpEepromTlvs(devName string, numBytes int, fname string, toFile bool) (output []byte, err int) { 
    var f *os.File
    var err_ error

    rdData := []byte{}
    found, _ := CardInListAccessViaFpga(devName)

    if found == true { //access eeprom via fpga
        i2cFMap, errFMap := i2cinfo.GetI2cInfo(devName)
        if errFMap != errType.SUCCESS {
            cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
            return
        }
        strArr := strings.Split(i2cFMap.HubName, "_")
        tmp, _ := strconv.Atoi(strArr[0])
        bus := uint32(tmp)
        tmp, _ = strconv.Atoi(strArr[1])
        mux := uint32(tmp)
        i2cAddr := uint32(i2cFMap.DevAddr)
        i2cOffsetlen := getFpgaOffsetWidth(devName)
        if i2cOffsetlen == -1 {
            err = errType.FAIL
            return
        }

        wrData := []byte{}
        for i:=0; i<i2cOffsetlen; i++ {
            wrData = append(wrData, byte(0x00))
        }
        rdData, err_ = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData,
                                              uint32(numBytes))
        if err_ != nil {
            cli.Println("e", "DumpEepromTlvFpga() - Failed to read I2C FPGA: dev bus mux i2cAddr offset",
                        devName, bus, mux, i2cAddr, i2cOffsetlen)
            return nil, -1
        }
    } else { // access eeprom via smbus
        var tmpData byte
        for i := 0; i < numBytes; i++ {
            tmpData, err = readByteSmbus(devName, i)
            rdData = append(rdData, tmpData)
        }
    }

    if toFile == true {
        f, err_ = os.OpenFile(fname, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0600)
        if err_ != nil {
            cli.Println("e", "file create failed. Filename:", fname)
            return nil, -1
        }
        f.WriteString(string(rdData[:]))
        f.Close()
        cli.Println("i", "EEPROM: dumped", numBytes, "bytes to file", fname)
    }

    return rdData, err
}

func EraseEepromTlv(devName string, numBytes int) (err int) {
    err = errType.SUCCESS

    if numBytes > 256 {
        cli.Println("i", "Truncating down to 256 bytes due to eeprom size.")
        numBytes = 256
    }

    found, _ := CardInListAccessViaFpga(devName)
    if found == true {
        err = EraseEepromTlvFpga(devName, numBytes)
    } else {
        err = EraseEepromTlvSmbus(devName, numBytes)
    }

    return
}

func EraseEepromTlvSmbus(devName string, numBytes int) (err int) {
    err = errType.SUCCESS

    var val byte = 0xFF
    for i := 0; i < numBytes; i++ {
        // delay for writing
        misc.SleepInUSec(10000)
        err = writeByteSmbus(devName, i, val)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to erase FRU at offset", i)
            err = errType.FAIL
            return
        }
    }

    return
}

func EraseEepromTlvFpga(devName string, numBytes int) (err int) {
    err = errType.SUCCESS

    i2cFMap, errFMap := i2cinfo.GetI2cInfo(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
        err = errType.FAIL
        return
    }
    strArr := strings.Split(i2cFMap.HubName, "_")
    tmp, _ := strconv.Atoi(strArr[0])
    bus := uint32(tmp)
    tmp, _ = strconv.Atoi(strArr[1])
    mux := uint32(tmp)
    i2cAddr := uint32(i2cFMap.DevAddr)
    i2cOffsetlen := getFpgaOffsetWidth(devName)
    if i2cOffsetlen == -1 {
        err = errType.FAIL
        return
    }

    wrData := []byte{}
    for i:=0; i<=i2cOffsetlen; i++ {
        wrData = append(wrData, byte(0x00))
    }

    var errFpga error
    for k:=0; k<numBytes; k++ {
        for t:=0; t<i2cOffsetlen; t++ {
            wrData[t] = byte((k>>uint(8*(i2cOffsetlen-t-1))) & 0xFF)
        }
        wrData[i2cOffsetlen] = 0xFF
        _, errFpga = liparifpga.I2c_access(bus, mux, i2cAddr, uint32(len(wrData)), wrData, 0)
        if errFpga != nil {
            cli.Println("e", "Failed to erase (write 0xFF) EEPROM through I2C FPGA:",
                        "dev bus mux i2cAddr i2cOffsetlen",
                        devName, bus, mux, i2cAddr, i2cOffsetlen)
            err = errType.FAIL
            return
        }
        // delay for writing
        misc.SleepInUSec(10000)
    }

    return
}

func VerifyFruTlvs(devName string) (err int){
    err = errType.SUCCESS

    found, _ := CardInListAccessViaFpga(devName)
    if found == true {
        cli.Println("i", "It will be implemented to verify TLV EEPROM accessing via FPGA...")
        return
    }

    TlvData = []byte{}
    var tmpData byte

    //readout the TLV hdr TlvStart = TlvHdrLen + TlvVerBytes + TlvTotalLenBytes
    for i := 0; i < int(TlvStart); i++ {
        tmpData, err = readByteSmbus(devName, i)
        TlvData = append(TlvData, tmpData)
    }

    var start int = 0
    //verify TLV ID String
    tlvIdStr := string(TlvData[start : start+int(TlvHdrLen)])
    if tlvIdStr != TlvInfoId {
        cli.Println("e", "Failed to verify TlvInfoId! Expected:", TlvInfoId, "Readout:", tlvIdStr)
        err = errType.FAIL
        return
    }
    start += int(TlvHdrLen) + int(TlvVerBytes) //skip TLV Hdr version

    //verify TLV Total Length
    totalLen := (int(TlvData[start]) << 8) + int(TlvData[start+1]) //big endian, 2 bytes
    //total EEPROM size < 2048 bytes
    if totalLen <= 0 || totalLen >= 2037 { // exclude 11 bytes TLV hdr
        cli.Println("i", "Failed to verify Total Length:", totalLen)
        err = errType.FAIL
        return
    }
    start += int(TlvTotalLenBytes)

    //read out TLV contents
    for i := start; i < start + totalLen; i++ {
        tmpData, err = readByteSmbus(devName, i)
        TlvData = append(TlvData, tmpData)
    }

    //Claculate expexted check sums
    var cksum uint32
    cksum, err = CalcCrc32()
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to verify: error in calculating expected CRC32")
        return
    }

    //verify TLV fields
    for {
        if start >= (totalLen + int(TlvStart)) {
            break
        }

        tlvName := getTlvName(TlvData[start])
        if tlvName == "Unknown" {
            cli.Println("e", "Failed to verify TLV code:", tlvName)
            err = errType.FAIL
            return
        }
        if tlvName == "CRC-32" {
            if int(TlvData[start+1]) != 4 {
                cli.Println("e", "Failed to verify CRC-32: expected length 4, read out length",
                            int(TlvData[start+1]))
                err = errType.FAIL
                return
            }
            var rdCksum uint32 = uint32(TlvData[start+2])<<24 + uint32(TlvData[start+3])<<16 + uint32(TlvData[start+4])<<8 + uint32(TlvData[start+5])
            if rdCksum != cksum {
                cli.Println("e", "Failed to verify CRC-32:")
                cli.Println("e", fmt.Sprintf("Expected CRC-32: 0x%02X 0x%02X 0x%02X 0x%02X",
                            (cksum&0xFF000000)>>24, (cksum&0xFF0000)>>16,
                            (cksum&0xFF00)>>8, cksum&0xFF))
                cli.Println("e", fmt.Sprintf("Read out CRC-32: 0x%02X 0x%02X 0x%02X 0x%02X",
                            TlvData[start+2], TlvData[start+3], TlvData[start+4], TlvData[start+5]))
                err = errType.FAIL
                return
            }
        }
        start += 2 + int(TlvData[start+1])
    }

    err = errType.SUCCESS
    cli.Println("i", "Successfully verified TLV Header/Code/CRC-32")
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
    //cli.Println("d", "Number of entries in EepromTlvs:", len(EepromTlvs))
    for i:=0; i<len(EepromTlvs); i++ {
        TlvData = append(TlvData, EepromTlvs[i].TypeCode)
        TlvData = append(TlvData, EepromTlvs[i].Length)
        total_length += int(EepromTlvs[i].Length) + 2
        TlvData = append(TlvData, EepromTlvs[i].Value...)
        TlvInfo = append(TlvInfo, tlvEntry{EepromTlvs[i].TypeCode, EepromTlvs[i].DataType,
                         EepromTlvs[i].Offset, EepromTlvs[i].Length, EepromTlvs[i].Value})
        //debug
        //cli.Println("d", getTlvName(EepromTlvs[i].TypeCode), "\t",
        //            EepromTlvs[i].Length, "\t", EepromTlvs[i].Value)
        //cli.Println("d", getTlvName(TlvInfo[i].TypeCode), "\t", TlvInfo[i].Length,
        //            "\t", TlvInfo[i].Value)
        //cli.Println("d", "total_length =", total_length)
    }

    TlvData[TlvTotalLenOffset] = byte((total_length>>8)&0xFF)
    TlvData[TlvTotalLenOffset+1] = byte(total_length&0xFF)
    // debug
    //cli.Println("d", "Total Length:", "\t",
    //            TlvData[TlvTotalLenOffset]<<8 + TlvData[TlvTotalLenOffset+1])

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
            //tempStr += fmt.Sprintf("0x") //don't display hex prefix "0x" for mfg scripts
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
            cli.Println("i", fmt.Sprintf("%-20s\t\t0x%02X 0x%02X 0x%02X 0x%02X",
                        getTlvName(TlvData[start]),
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
        //debug
        //cli.Println("d", "updateTlvs():", getTlvName(TlvInfo[i].TypeCode), "offset =",
        //            int(TlvInfo[i].Offset), "len =", TlvInfo[i].Length)
        //cli.Println("d", TlvInfo[i].Value)
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

func readByteSmbus(devName string, offset int) (tmpData byte, err int) {
    err = errType.SUCCESS

    //Opens smbus connection
    i2cSmbus, errSmbus := i2cinfo.GetI2cInfo(devName)
    if errSmbus != errType.SUCCESS {
        cli.Println("e", "Failed to obtain smbus info for dev", devName)
        return
    }
    err = smbusNew.Open(devName, i2cSmbus.Bus, i2cSmbus.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open smbus: dev", devName,
                    "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
        return
    }
    defer smbusNew.Close()

    if (i2cSmbus.Flag == i2cinfo.FLAG_16BIT_EEPROM) {
        tmpData, err = smbusNew.I2C16ReadByte(devName, uint16(offset))
    } else {
        tmpData, err = smbusNew.ReadByte(devName, uint64(offset))
    }
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to read from FRU at offset", offset)
        return
    }
    return
}

func writeByteSmbus(devName string, offset int, val byte) (err int) {
    err = errType.SUCCESS

    //Opens smbus connection
    i2cSmbus, errSmbus := i2cinfo.GetI2cInfo(devName)
    if errSmbus != errType.SUCCESS {
        cli.Println("e", "Failed to obtain smbus info for dev", devName)
        return
    }
    err = smbusNew.Open(devName, i2cSmbus.Bus, i2cSmbus.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open smbus: dev", devName,
                    "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
        return
    }
    defer smbusNew.Close()

    if (i2cSmbus.Flag == i2cinfo.FLAG_16BIT_EEPROM) {
        err = smbusNew.I2C16WriteByte(devName, uint16(offset), val)
    } else {
        err = smbusNew.WriteByte(devName, uint64(offset), val)
    }
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write FRU at offset", offset, "with value", val)
    }
    return
}

func writeTlvsViaSmbus(devName string) (err int) {
    err = errType.SUCCESS

    //Opens smbus connection
    i2cSmbus, errSmbus := i2cinfo.GetI2cInfo(devName)
    if errSmbus != errType.SUCCESS {
        cli.Println("e", "Failed to obtain smbus info for dev", devName)
        return
    }
    err = smbusNew.Open(devName, i2cSmbus.Bus, i2cSmbus.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open smbus: dev", devName,
                    "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
        return
    }
    defer smbusNew.Close()

    for k:=0; k<len(TlvData); k++ {
        misc.SleepInUSec(10000) // delay for writing
        if (i2cSmbus.Flag == i2cinfo.FLAG_16BIT_EEPROM) {
            err = smbusNew.I2C16WriteByte(devName, uint16(k), TlvData[k])
        } else {
            err = smbusNew.WriteByte(devName, uint64(k), TlvData[k])
        }
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to write to FRU at offset", k)
            return err
        }
    }
    return
}

func writeTlvsViaFpga(devName string) (err int) {
    err = errType.SUCCESS
    i2cFMap, errFMap := i2cinfo.GetI2cInfo(devName)
    if errFMap != errType.SUCCESS {
        cli.Println("e", "smbus not available and failed to obtain I2C FPGA mapping of", devName)
        err = errType.FAIL
        return
    }
    strArr := strings.Split(i2cFMap.HubName, "_")
    tmp, _ := strconv.Atoi(strArr[0])
    bus := uint32(tmp)
    tmp, _ = strconv.Atoi(strArr[1])
    mux := uint32(tmp)
    i2cAddr := uint32(i2cFMap.DevAddr)
    i2cOffsetlen := getFpgaOffsetWidth(devName)
    if i2cOffsetlen == -1 {
        err = errType.FAIL
        return
    }

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
    case  hw_maj_rev:
        Name = "HW_MAJOR_REV"
    case  hw_min_rev:
        Name = "HW_MINOR_REV"
    case  mfg_deviation:
        Name = "MFG Deviation"
    case  mfg_bits:
        Name = "MFG BITS"
    case  eng_bits:
        Name = "Eng BITS"
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

func getFpgaOffsetWidth(dev string) (width int) {

    var cardtyp string = os.Getenv("CARD_TYPE")
    for _, t := range(FpgaOffsetWidth) {
        if (cardtyp == t.cardTyp) && (dev == t.devName) {
            return t.OffsetWidth
        }
    }

    cli.Println("e", "Unsupported FRU access via FPGA upon CARD_TYPE", cardtyp, "DevName", dev)
    return -1
}
