package eeprom

import (
    "fmt"
    "os"
    "bytes"
//    "strconv"
    "time"
    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/smbusNew"
)

const(
    INT8 = 0
    INT16 = 1
    INT32 = 2
    INT64 = 3
    STRING = 4
)

var SnAllZero = []byte{0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
var SnAllF = []byte{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}

// EEPROM entry data structure
type entry struct {
    Name     string
    DataType int
    Offset   int
    NumBytes int
    Value    []byte
}

var MtpTbl = []entry {
    entry{"NUM_BYTES",      STRING, 0,   4,  []byte("0256")},
    entry{"HW_MAJOR_REV",   STRING, 4,   2,  []byte("00")},
    entry{"HW_MINOR_REV",   STRING, 6,   4,  []byte("0100")},
    entry{"PRODUCT_NAME",   STRING, 10,  20, []byte("NAPLES25 MTP Adapter")},
    entry{"SERIAL_NUM",     STRING, 30,  20, []byte("1234567890          ")},
    entry{"COMPANY_NAME",   STRING, 50,  20, []byte("Pensando Systems Inc")},
    entry{"MFG_DEVIATION",  STRING, 70,  20, []byte("0                   ")},
    entry{"MFG_BITS",       STRING, 90,  2,  []byte("00")},
    entry{"ENG_BITS",       STRING, 92,  2,  []byte("00")},
    entry{"MAC_ADDR",       STRING, 94,  12, []byte("AABBCCDDEEFF")},
    entry{"NUM_OF_MAC",     STRING, 106, 2,  []byte("00")},
}

var Naples25SwmAdapTbl = []entry {
    entry{"NUM_BYTES",      STRING, 0,   4,  []byte("0256")},
    entry{"HW_MAJOR_REV",   STRING, 4,   2,  []byte("01")},
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

var Naples100Tbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{1}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{1}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{1}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0xC}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0, 0, 0}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xD5}},
    entry{"Manufacturer",                           STRING,      15,       21,   []byte{0x50, 0x45, 0x4E, 0x53,
        0x41, 0x4E, 0x44, 0x4F, 0x20, 0x53, 0x59, 0x53, 0x54, 0x45, 0x4D, 0x53, 0x20, 0x49, 0x4E, 0x43, 0x2E}},
    entry{"Product Name Type/Length",               INT8,        36,       1,    []byte{0xD0}},
    entry{"Product Name",                           STRING,       37,       10,   []byte{0x4E, 0x41, 0x50, 0x4C,
        0x45, 0x53, 0x20, 0x31, 0x30, 0x30}},
    entry{"Reserved",                               STRING,      47,       6,    []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        53,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      54,       11,   []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Part Number Type/Length",                INT8,        65,       1,    []byte{0xCD}},
    entry{"Part Number",                            STRING,      66,       13,   []byte{0x36, 0x38, 0x2D, 0x30,
        0x30, 0x30, 0x33, 0x2D, 0x30, 0x32, 0x20, 0x30, 0x31}},
    entry{"FRU File ID Type/Length",                INT8,        79,       1,    []byte{0xC0}},
    entry{"Board ID Type/Length",                   INT8,        80,       1,    []byte{4}},
    entry{"Board ID",                               INT8,        81,       4,    []byte{1, 0 , 0, 0}},
    entry{"Engineering Change Level Type/Length",   INT8,        85,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        86,       2,    []byte{0, 0}},
    entry{"Number of MAC Address Type/Length",      INT8,        88,       1,    []byte{2}},
    entry{"Number of MAC Address",                  INT8,        89,       2,    []byte{0x18, 0x0}},
    entry{"MAC Address Base Type/Length",           INT8,        91,       1,    []byte{6}},
    entry{"MAC Address Base",                       INT8,        92,       6,    []byte{0, 0xAE, 0xCD, 0, 0, 0}},
    entry{"End of Field",                           INT8,        98,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,        99,       4,    []byte{0, 0, 0, 0}},
    entry{"Board Info Area Checksum",               INT8,        103,      1,    []byte{0}},
} 

var Naples100IBMTbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x0F}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,        15,       8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xDD}},
    entry{"Product Name",                           STRING,        24,      25,    []byte{0x44, 0x53, 0x43, 0x2D,
        0x31, 0x30, 0x30, 0x20, 0x32, 0x70, 0x20, 0x34, 0x30, 0x2F, 0x31, 0x30, 0x30, 0x47, 0x20, 0x51, 0x53, 
	0x46, 0x50, 0x32, 0x38}},
    entry{"Reserved",                               STRING,        49,       4,    []byte{0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        53,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,        54,       11,   []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Part Number Type/Length",                INT8,        65,       1,    []byte{0xD0}},
    entry{"Part Number",                            STRING,      66,       16,   []byte{0x44, 0x53, 0x43, 0x31,
        0x2D, 0x32, 0x51, 0x31, 0x30, 0x30, 0x2D, 0x38, 0x46, 0x31, 0x36, 0x50}},
    entry{"FRU File ID Type/Length",                INT8,        82,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,        83,       8,    []byte{0x30, 0x34, 0x2F, 0x31,
        0x30, 0x2F, 0x32, 0x30}},
    entry{"Board ID Type/Length",                   INT8,        91,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,        92,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,        96,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        97,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,        99,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       100,       2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       102,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       103,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       109,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,       110,      13,    []byte{0x36, 0x38, 0x2D, 0x30,
        0x30, 0x31, 0x33, 0x2D, 0x30, 0x31, 0x20, 0x30, 0x33}},
    entry{"End of Field",                           INT8,       123,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       124,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       127,       1,    []byte{0x00}},
} 
var OracleTbl = []entry {
    entry{"Class Code",                             INT8,        0,          3,    []byte{0x00, 0x80, 0x02}},
    entry{"PCI-SIG Vendor ID",                      INT8,        3,          2,    []byte{0xD8, 0x1D}},
    entry{"Serial Number",                          INT8,        5,          20,   []byte{0x78, 0x78, 0x78, 0x78, 0x78,
          0x78, 0x78, 0x78, 0x78, 0x78, 0x78, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Model Number",                           INT8,        25,         40,   []byte{0x36, 0x38, 0x2d, 0x78, 0x78,
          0x78, 0x78, 0x2d, 0x78, 0x78, 0x20, 0x78, 0x78, 0x20, 0x20, 0x50, 0x45, 0x4E, 0x53, 0x41, 0x4E, 0x44, 0x4F, 0x20, 
	  0x53, 0x59, 0x53, 0x54, 0x45, 0x4D, 0x53, 0x20, 0x49, 0x4E, 0x43, 0x2E, 0x20, 0x20, 0x20, 0x20}},
    entry{"Maximum Link Speed",                     INT8,        65,         1,    []byte{0x04}},
    entry{"Maximum Link Width",                     INT8,        66,         1,    []byte{0x0F}},
    entry{"Maximum Link Speed",                     INT8,        67,         1,    []byte{0x04}},
    entry{"Maximum Link Width",                     INT8,        68,         1,    []byte{0x08}},
    entry{"12V Power Rail Initial Power",           INT8,        69,         1,    []byte{0x32}},
    entry{"Reserved",                               INT8,        70,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        71,         1,    []byte{0x00}},
    entry{"12V Power Rail Maximum Power",           INT8,        72,         1,    []byte{0x32}},
    entry{"Reserved",                               INT8,        73,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        74,         1,    []byte{0x00}},
    entry{"Cap List Pointer",                       INT8,        75,         2,    []byte{0x50, 0x00}},
    entry{"",                                       INT8,        77,         1,    []byte{0x00}},
    entry{"",                                       INT8,        78,         1,    []byte{0x00}},
    entry{"",                                       INT8,        79,         1,    []byte{0x00}},
    entry{"VU Cap ID",                              INT8,        80,         1,    []byte{0xA2}},
    entry{"VU Cap ID",                              INT8,        81,         1,    []byte{0x00}},
    entry{"Next Cap address",                       INT8,        82,         1,    []byte{0x00}},
    entry{"Next Cap address",                       INT8,        83,         1,    []byte{0x00}},
    entry{"Sensor Type",                            INT8,        84,         1,    []byte{0x50}},
    entry{"Sensor Address",                         INT8,        85,         1,    []byte{0xEC}},
    entry{"Sensor #1 Address Offset",               INT8,        86,         1,    []byte{0x18}},
    entry{"Reserved",                               INT8,        87,         1,    []byte{0x17}},
    entry{"Warning Threshold - LSB",                INT8,        88,         1,    []byte{0x5F}},
    entry{"Warning Threshold - MSB",                INT8,        89,         1,    []byte{0x00}},
    entry{"OverTemp Threshold - LSB",               INT8,        90,         1,    []byte{0x69}},
    entry{"OverTemp Threshold - MSB",               INT8,        91,         1,    []byte{0x00}},
    entry{"PCIE Vendor ID - LSB",                   INT8,        92,         1,    []byte{0xD8}},
    entry{"PCIE Vendor ID - MSB",                   INT8,        93,         1,    []byte{0x1D}},
    entry{"PCIE Vendor ID - LSB",                   INT8,        94,         1,    []byte{0x02}},
    entry{"PCIE Vendor ID - MSB",                   INT8,        95,         1,    []byte{0x10}},
    entry{"PCIE Subsystem Vendor ID - LSB",         INT8,        96,         1,    []byte{0xD8}},
    entry{"PCIE Subsystem Vendor ID - MSB",         INT8,        97,         1,    []byte{0x1D}},
    entry{"PCIE Subsystem ID - LSB",                INT8,        98,         1,    []byte{0x09}},
    entry{"PCIE Subsystem ID - MSB",                INT8,        99,         1,    []byte{0x40}},
    entry{"PAD",                                    INT8,        100,        156,  []byte{0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }},
    entry{"Common Format Version",                  INT8,        256,        1,    []byte{1}},
    entry{"Internal Use Area Offset",               INT8,        257,        1,    []byte{0}},
    entry{"Chassis Area Offset",                    INT8,        258,        1,    []byte{0}},
    entry{"Board Info Offset",                      INT8,        259,        1,    []byte{1}},
    entry{"Product Area Offset",                    INT8,        260,        1,    []byte{0}},
    entry{"Multi-Record Area Offset",               INT8,        261,        1,    []byte{0}},
    entry{"PAD",                                    INT8,        262,        1,    []byte{0}},
    entry{"Common Header Checksum",                 INT8,        263,        1,    []byte{0}},
    entry{"Board Info Format Version",              INT8,        264,        1,    []byte{1}},
    entry{"Board Area Length",                      INT8,        265,        1,    []byte{0xC}},
    entry{"Language Code",                          INT8,        266,        1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        267,        3,    []byte{0, 0, 0}},
    entry{"Manufacturing Type/Length",              INT8,        270,        1,    []byte{0xD5}},
    entry{"Manufacturer",                           STRING,      271,        21,   []byte{0x50, 0x45, 0x4E, 0x53,
        0x41, 0x4E, 0x44, 0x4F, 0x20, 0x53, 0x59, 0x53, 0x54, 0x45, 0x4D, 0x53, 0x20, 0x49, 0x4E, 0x43, 0x2E}},
    entry{"Product Name Type/Length",               INT8,        292,        1,    []byte{0xD0}},
    entry{"Product Name",                           STRING,      293,        10,   []byte{0x4E, 0x41, 0x50, 0x4C,
        0x45, 0x53, 0x20, 0x31, 0x30, 0x30}},
    entry{"Reserved",                               STRING,      303,        6,    []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        309,        1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      310,        11,   []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Part Number Type/Length",                INT8,        321,        1,    []byte{0xCD}},
    entry{"Part Number",                            STRING,      322,        13,   []byte{0x36, 0x38, 0x2D, 0x30,
        0x30, 0x30, 0x33, 0x2D, 0x30, 0x32, 0x20, 0x30, 0x31}},
    entry{"FRU File ID Type/Length",                INT8,        335,        1,    []byte{0xC0}},
    entry{"Board ID Type/Length",                   INT8,        336,        1,    []byte{4}},
    entry{"Board ID",                               INT8,        337,        4,    []byte{1, 0 , 0, 0}},
    entry{"Engineering Change Level Type/Length",   INT8,        341,        1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        342,        2,    []byte{0, 0}},
    entry{"Number of MAC Address Type/Length",      INT8,        344,        1,    []byte{2}},
    entry{"Number of MAC Address",                  INT8,        345,        2,    []byte{0x18, 0x0}},
    entry{"MAC Address Base Type/Length",           INT8,        347,        1,    []byte{6}},
    entry{"MAC Address Base",                       INT8,        348,        6,    []byte{0, 0xAE, 0xCD, 0, 0, 0}},
    entry{"End of Field",                           INT8,        354,        1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,        355,        4,    []byte{0, 0, 0, 0}},
    entry{"Board Info Area Checksum",               INT8,        359,        1,    []byte{0}},
} 

/*
var HpeTbl = []entry {
    entry{"Board Info Format Version",              INT8,       128,        1,  []byte{1}},
    entry{"Board Area Length",                      INT8,       129,        1,  []byte{0xF}},
    entry{"Language Code",                          INT8,       130,        1,  []byte{0x19}},
    entry{"Manufacture Date/Time",                  INT8,       131,        3,  []byte{0, 0, 0}},
    entry{"Manufacturer Name Type/Length",          INT8,       134,        1,  []byte{0xC2}},
    entry{"Manufacturer",                           STRING,     135,        2,  []byte{0x48, 0x50}},
    entry{"Product Name Type/Length",               INT8,       137,        1,  []byte{0xF2}},
    entry{"Product Name",                           STRING,     138,        50, []byte{
            0x48, 0x50, 0x45, 0x20, 0x53, 0x6D, 0x61, 0x72, 0x74, 0x4E, 0x49, 0x43,
            0x20, 0x31, 0x30, 0x2F, 0x32, 0x35, 0x47, 0x62, 0x20, 0x32, 0x2D, 0x70,
            0x6F, 0x72, 0x74, 0x20, 0x36, 0x39, 0x31, 0x53, 0x46, 0x50, 0x32, 0x38,
            0x20, 0x41, 0x64, 0x61, 0x70, 0x74, 0x65, 0x72, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20}},
    entry{"PCA Serial Number Type/Length",          INT8,       188,        1,  []byte{0xCA}},
    entry{"HPE Serial Number",                      STRING,     189,        10, []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"PCA Product Number Type/Length",         INT8,       199,        1,  []byte{0xCA}},
    entry{"HPE Product Number",                     STRING,     200,        10, []byte{0x50, 0x31, 0x38, 0x36,
        0x36, 0x39, 0x2D, 0x30, 0x30, 0x31}},
    entry{"FRU File ID Type/Length",                INT8,       210,        1,  []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     211,        8,  []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"OEM Revision Type/Length",               INT8,       219,        1,  []byte{0x3}},
    entry{"HP OEM Record ID",                       INT8,       220,        1,  []byte{0xD2}},
    entry{"Revision Code",                          STRING,     221,        2,  []byte{0x30, 0x41}},
    entry{"Board ID Type/Length",                   INT8,       223,        1,  []byte{0x4}},
    entry{"Board ID",                               INT8,       224,        4,  []byte{0x2, 0x0, 0x0, 0x0}},
    entry{"Engineering Change Level Type/Length",   INT8,       228,        1,  []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       229,        2,  []byte{0x0, 0x0}},
    entry{"Number of MAC Address Type/Length",      INT8,       231,        1,  []byte{0x2}},
    entry{"Total Number of MAC Address",            INT8,       232,        2,  []byte{0x18, 0x0}},
    entry{"MAC Address Base Type/Length",           INT8,       234,        1,  []byte{0x6}},
    entry{"MAC Address Base",                       INT8,       235,        6,  []byte{0, 0xAE, 0xCD, 0, 0, 0}},
    entry{"End of Field",                           INT8,       241,        1,  []byte{0xC1}},
    entry{"PAD",                                    INT8,       242,        5,  []byte{0, 0, 0, 0, 0}},
    entry{"HPE Multi-Record Area Checksum",         INT8,       247,        1,  []byte{0}},
}
*/

var HpeTbl = []entry {
    entry{"Board Info Format Version",              INT8,       128,        1,  []byte{1}},
    entry{"Board Area Length",                      INT8,       129,        1,  []byte{0xF}},
    entry{"Language Code",                          INT8,       130,        1,  []byte{0x19}},
    entry{"Manufacturer Name Type/Length",          INT8,       131,        1,  []byte{0xC2}},
    entry{"Manufacturer",                           STRING,     132,        2,  []byte{0x48, 0x50}},
    entry{"Product Name Type/Length",               INT8,       134,        1,  []byte{0xF2}},
    entry{"Product Name",                           STRING,     135,        50, []byte{
            0x48, 0x50, 0x45, 0x20, 0x53, 0x6D, 0x61, 0x72, 0x74, 0x4E, 0x49, 0x43,
            0x20, 0x31, 0x30, 0x2F, 0x32, 0x35, 0x47, 0x62, 0x20, 0x32, 0x2D, 0x70,
            0x6F, 0x72, 0x74, 0x20, 0x36, 0x39, 0x31, 0x53, 0x46, 0x50, 0x32, 0x38,
            0x20, 0x41, 0x64, 0x61, 0x70, 0x74, 0x65, 0x72, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20}},
    entry{"PCA Serial Number Type/Length",          INT8,       185,        1,  []byte{0xCA}},
    entry{"HPE Serial Number",                      STRING,     186,        10, []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"PCA Product Number Type/Length",         INT8,       196,        1,  []byte{0xCA}},
    entry{"HPE Product Number",                     STRING,     197,        10, []byte{0x50, 0x31, 0x38, 0x36,
        0x36, 0x39, 0x2D, 0x30, 0x30, 0x31}},
    entry{"FRU File ID Type/Length",                INT8,       207,        1,  []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     208,        8,  []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"OEM Revision Type/Length",               INT8,       216,        1,  []byte{0x3}},
    entry{"HP OEM Record ID",                       INT8,       217,        1,  []byte{0xD2}},
    entry{"Revision Code",                          STRING,     218,        2,  []byte{0x30, 0x41}},
    entry{"Board ID Type/Length",                   INT8,       220,        1,  []byte{0x4}},
    entry{"Board ID",                               INT8,       221,        4,  []byte{0x2, 0x0, 0x0, 0x0}},
    entry{"Engineering Change Level Type/Length",   INT8,       225,        1,  []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       226,        2,  []byte{0x0, 0x0}},
    entry{"Number of MAC Address Type/Length",      INT8,       228,        1,  []byte{0x2}},
    entry{"Total Number of MAC Address",            INT8,       229,        2,  []byte{0x18, 0x0}},
    entry{"MAC Address Base Type/Length",           INT8,       231,        1,  []byte{0x6}},
    entry{"MAC Address Base",                       INT8,       232,        6,  []byte{0, 0xAE, 0xCD, 0, 0, 0}},
    entry{"End of Field",                           INT8,       238,        1,  []byte{0xC1}},
    entry{"PAD",                                    INT8,       239,        8,  []byte{0, 0, 0, 0, 0, 0, 0, 0}},
    entry{"HPE Multi-Record Area Checksum",         INT8,       247,        1,  []byte{0}},
}

var HpeTblOCP = []entry {
    entry{"Product Info Format Version",            INT8,        128,        1,    []byte{1}},
    entry{"Product Area Length",                    INT8,        129,        1,    []byte{0xA}},
    entry{"Language Code",                          INT8,        130,        1,    []byte{0x19}},
    entry{"Manufacturer Name Type/Length",          INT8,        131,        1,    []byte{0xC3}},
    entry{"Manufacturer",                           STRING,      132,        3,    []byte{0x48, 0x50, 0x45}},
    entry{"Product Name Type/Length",               INT8,        135,        1,    []byte{0xE3}},
    entry{"Product Name",                           STRING,      136,       35,    []byte{
        0x48, 0x50, 0x45, 0x20, 0x45, 0x53, 0x50, 0x20, 0x4E, 0x61, 0x70, 0x6C, 0x65, 0x73, 0x20, 0x44, 0x53, 
        0x43, 0x2D, 0x32, 0x35, 0x20, 0x32, 0x70, 0x20, 0x53, 0x46, 0x50, 0x32, 0x38, 0x20, 0x43, 0x61, 0x72, 0x64}},
    entry{"PCA Product Number Type/Length",         INT8,        171,        1,    []byte{0xCA}},
    entry{"HPE Product Number",                     STRING,      172,       10,    []byte{0x50, 0x32, 0x36, 0x39,
        0x36, 0x37, 0x2D, 0x42, 0x32, 31}},
    entry{"Product Version Type/Length",            INT8,        182,        1,    []byte{0xC2}},
    entry{"Product Version",                        STRING,      183,        2,    []byte{0x30, 0x30}},
    entry{"PCA Serial Number Type/Length",          INT8,        185,        1,    []byte{0xCA}},
    entry{"HPE Serial Number",                      STRING,      186,       10,    []byte{0x30, 0x30, 0x30, 0x30, 
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Asset Tag Type/Length",                  INT8,        196,        1,    []byte{0x00}},
    entry{"FRU File ID Type/Length",                INT8,        197,        1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,      198,        8,    []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"End of Field",                           INT8,        206,        1,    []byte{0xC1}},
    entry{"Product info Area Checksum",             INT8,        207,        1,    []byte{0x00}},
}


//Board Information Area Table
var HpeTblSWM = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{1}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{1}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x10}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{1}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0xF}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0, 0, 0}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xc8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x45, 0x4E, 0x53,
        0x41, 0x4E, 0x44, 0x4F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xEC}},
    entry{"Product Name",                           STRING,      24,      44,    []byte{0x50, 0x43, 0x41, 0x20, 
        0x50, 0x65, 0x6e, 0x73, 0x61, 0x6e, 0x64, 0x6f, 0x20, 0x44, 
        0x53, 0x50, 0x20, 0x44, 0x53, 0x43, 0x2d, 0x32, 0x35, 0x20, 
        0x31, 0x30, 0x2f, 0x32, 0x35, 0x47, 0x20, 0x32, 0x70, 0x20, 
        0x53, 0x46, 0x50, 0x32, 0x38, 0x20, 0x43, 0x61, 0x72, 0x64}},
    entry{"Serial Number Type/Length",              INT8,        68,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      69,      10,    []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Pad",                                    INT8,        79,       1,    []byte{0x00}},
    entry{"Part Number Type/Length",                INT8,        80,       1,    []byte{0xCD}},
    entry{"Part Number",                            STRING,      81,      13,    []byte{0x50, 0x32, 0x36, 0x39, 
        0x36, 0x38, 0x2d, 0x30, 0x30, 0x31, 0x00, 0x00, 0x00}},
    entry{"FRU File ID Type/Length",                INT8,        94,       1,    []byte{0xC8}},
    entry{"FRU File ID",                            INT8,        95,       8,    []byte{0x30, 0x36, 0x2F, 0x32, 
        0x34, 0x2F, 0x31, 0x39}},
    entry{"Board ID Type/Length",                   INT8,       103,       1,    []byte{4}},
    entry{"Board ID",                               INT8,       104,       4,    []byte{0x02, 0 , 0, 0}},
    entry{"Engineering Change Level Type/Length",   INT8,       108,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       109,       2,    []byte{0, 0}},
    entry{"Number of MAC Address Type/Length",      INT8,       111,       1,    []byte{2}},
    entry{"Number of MAC Address",                  INT8,       112,       2,    []byte{0x18, 0x0}},
    entry{"MAC Address Base Type/Length",           INT8,       114,       1,    []byte{6}},
    entry{"MAC Address Base",                       INT8,       115,       6,    []byte{0, 0xAE, 0xCD, 0, 0, 0}},
    entry{"End of Field",                           INT8,       121,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       122,       5,    []byte{0, 0, 0, 0, 0}},
    entry{"Board Info Area Checksum",               INT8,       127,       1,    []byte{0}},
} 


var HpeTblSWMext = []entry {
    entry{"Product Info Format Version",            INT8,        128,        1,    []byte{1}},
    entry{"Product Area Length",                    INT8,        129,        1,    []byte{0x0C}},
    entry{"Language Code",                          INT8,        130,        1,    []byte{0x19}},
    entry{"Manufacturer Name Type/Length",          INT8,        131,        1,    []byte{0xC3}},
    entry{"Manufacturer",                           STRING,      132,        3,    []byte{0x48, 0x50, 0x45}},
    entry{"Product Name Type/Length",               INT8,        135,        1,    []byte{0xEC}},
    entry{"Product Name",                           STRING,      136,       44,    []byte{
        0x50, 0x43, 0x41, 0x20, 0x50, 0x65, 0x6e, 0x73, 0x61, 0x6e, 
        0x64, 0x6f, 0x20, 0x44, 0x53, 0x50, 0x20, 0x44, 0x53, 0x43, 
        0x2d, 0x32, 0x35, 0x20, 0x31, 0x30, 0x2f, 0x32, 0x35, 0x47, 
        0x20, 0x32, 0x70, 0x20, 0x53, 0x46, 0x50, 0x32, 0x38, 0x20,
        0x43, 0x61, 0x72, 0x64}},
    entry{"PCA Product Number Type/Length",         INT8,        180,        1,    []byte{0xCA}},
    entry{"HPE Product Number",                     STRING,      181,       10,    []byte{0x50, 0x32, 0x36, 0x39,
        0x36, 0x38, 0x2D, 0x30, 0x30, 0x31}},
    entry{"Product Version Type/Length",            INT8,        191,        1,    []byte{0xC2}},
    entry{"Product Version",                        STRING,      192,        2,    []byte{0x30, 0x30}},
    entry{"PCA Serial Number Type/Length",          INT8,        194,        1,    []byte{0xCA}},
    entry{"HPE Serial Number",                      STRING,      195,       10,    []byte{0x30, 0x30, 0x30, 0x30, 
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Asset Tag Type/Length",                  INT8,        205,        1,    []byte{0xC0}},
    entry{"FRU File ID Type/Length",                INT8,        206,        1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,      207,        8,    []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"End of Field",                           INT8,        215,        1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,        216,        7,    []byte{0, 0, 0, 0, 0, 0, 0}},
    entry{"Product info Area Checksum",             INT8,        223,        1,    []byte{0x00}},
} 
 


var HpeAlomTblAll = []entry {
    //Common Header
    entry{"Common Format Version",                  INT8,         0,        1,    []byte{1}},
    entry{"Internal Use Area Offset",               INT8,         1,        1,    []byte{0}},
    entry{"Chassis Area Offset",                    INT8,         2,        1,    []byte{0}},
    entry{"Board Info Offset",                      INT8,         3,        1,    []byte{1}},
    entry{"Product Area Offset",                    INT8,         4,        1,    []byte{0x0d}},
    entry{"Multi-Record Area Offset",               INT8,         5,        1,    []byte{0x17}},
    entry{"PAD",                                    INT8,         6,        1,    []byte{0}},
    entry{"Common Header Checksum",                 INT8,         7,        1,    []byte{0}},

    //BIA
    entry{"Board Info Format Version",              INT8,         8,        1,    []byte{1}},
    entry{"Board Area Length",                      INT8,         9,        1,    []byte{0xC}},
    entry{"Language Code",                          INT8,        10,        1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,        3,    []byte{0, 0, 0}},
    entry{"Manufacturing Type/Length",              INT8,        14,        1,    []byte{0xCD}},
    entry{"Manufacturer",                           STRING,      15,       13,    []byte{0x50, 0x45, 0x4E, 0x53,
        0x41, 0x4E, 0x44, 0x4F, 0x20, 0x49, 0x4E, 0x43, 0x2E}},
    entry{"Product Name Type/Length",               INT8,        28,        1,    []byte{0xE6}},
    entry{"Product Name",                           STRING,      29,       38,    []byte{
        0x50, 0x43, 0x41, 0x20, 0x50, 0x65, 0x6e, 0x73, 0x61, 0x6e,
        0x64, 0x6f, 0x20, 0x44, 0x53, 0x50, 0x20, 0x66, 0x6f, 0x72, 
        0x20, 0x48, 0x50, 0x45, 0x20, 0x69, 0x4c, 0x4f, 0x20, 0x4d, 
        0x67, 0x6d, 0x74, 0x20, 0x41, 0x4c, 0x4f, 0x4d }},
    entry{"Serial Number Type/Length",              INT8,        67,        1,    []byte{0xCA}},
    entry{"Serial Number",                          STRING,      68,       10,    []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Part Number Type/Length",                INT8,        78,        1,    []byte{0xCA}},
    entry{"Part Number",                            STRING,      79,       10,    []byte{ 0x50, 0x32, 0x36, 0x39, 
        0x36, 0x39, 0x2d, 0x42, 0x32, 0x31 }},
    entry{"FRU File ID Type/Length",                INT8,        89,        1,    []byte{0xC8}},
    entry{"FRU File ID",                            STRING,      90,        8,    []byte{ 0x30, 0x31, 0x2f, 0x31, 
        0x33, 0x2f, 0x32, 0x30 }},
    entry{"End of Field",                           INT8,        98,        1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,        99,        4,    []byte{0, 0, 0, 0}},
    entry{"Board Info Area Checksum",               INT8,       103,        1,    []byte{0}},


    //PIA
    entry{"Product Info Format Version",            INT8,       104,        1,    []byte{1}},
    entry{"Product Area Length",                    INT8,       105,        1,    []byte{0xA}},
    entry{"Language Code",                          INT8,       106,        1,    []byte{0x19}},
    entry{"Manufacturer Name Type/Length",          INT8,       107,        1,    []byte{0xC3}},
    entry{"Manufacturer",                           STRING,     108,        3,    []byte{0x48, 0x50, 0x45}},
    entry{"Product Name Type/Length",               INT8,       111,        1,    []byte{0xE6}},
    entry{"Product Name",                           STRING,     112,        38,   []byte{
        0x50, 0x65, 0x6e, 0x73, 0x61, 0x6e, 0x64, 0x6f, 0x20, 0x44, 
        0x53, 0x50, 0x20, 0x66, 0x6f, 0x72, 0x20, 0x48, 0x50, 0x45, 
        0x20, 0x69, 0x4c, 0x4f, 0x20, 0x4d, 0x67, 0x6d, 0x74, 0x20,
        0x41, 0x4c, 0x4f, 0x4d, 0x20, 0x4d, 0x6f, 0x64 }},
    entry{"Product SKU Part Number Type/Length",    INT8,       150,        1,    []byte{0xCA}},
    entry{"Product SKU Part Number",                STRING,     151,       10,    []byte{ 0x50, 0x32, 0x36, 0x39,
        0x37, 0x31, 0x2d, 0x30, 0x30, 0x31 }},
    entry{"Product Version Type/Length",            INT8,       161,        1,    []byte{0xC2}},
    entry{"Product Version",                        STRING,     162,        2,    []byte{0x30, 0x30}},
    entry{"Product Serial Number Type/Length",      INT8,       164,        1,    []byte{0xCA}},
    entry{"PIA Serial Number",                          STRING,     165,       10,    []byte{0x30, 0x30, 0x30, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x30}},
    entry{"Asset Tag Type/Length",                  INT8,       175,        1,    []byte{0x00}},
    entry{"FRU File ID Type/Length",                INT8,       176,        1,    []byte{0x00}},
    entry{"End of Field",                           INT8,       177,        1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       178,        5,    []byte{0, 0, 0, 0, 0}},
    entry{"Product info Area Checksum",             INT8,       183,        1,    []byte{0}},
}

var EepromTbl []entry
var EepromExtTbl []entry
var CardType string
var brdInfoChk, productInfoChk, cmnHeadChk uint
var mraChk [7]uint
var mraHdrChk [7]uint

var HpeNaples uint
var HpeSwm uint
var HpeAlom bool
var HpeOcp uint
var Erase bool
var I2cAddr16 bool
var CustType string

func max(x, y int) (m int) {
    if x > y {
        return x
    } else {
        return y
    }
}

func init () {
    HpeNaples = 0
    HpeSwm = 0
    HpeAlom = false
    HpeOcp = 0
    I2cAddr16 = false
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
        misc.SleepInUSec(5000)    //atmel spec says max write time is 5ms
        if I2cAddr16 == true {
            err = smbusNew.I2C16WriteByte(devName, uint16(offset+i), writeData)
        } else {
            err = smbusNew.WriteByte(devName, uint64(offset+i), writeData)
        }
        if err != errType.SUCCESS {
            return
        }
    }
    return
}

func readField(devName string, offset int, numBytes int) (data []byte, err int) {
    data = make([]byte, numBytes)

    for i := 0; i < numBytes; i++ {
        if I2cAddr16 == true {
            data[i], err = smbusNew.I2C16ReadByte(devName, uint16(offset+i))
        } else {
            data[i], err = smbusNew.ReadByte(devName, uint64(offset+i))
        }
        if err != errType.SUCCESS {
            return
        }
    }
    return
}

func EraseEeprom(devName string, bus uint32, devAddr byte, numBytes int) (err int) {
    var eeData byte = 0xFF

    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

    if I2cAddr16 == false {
        if numBytes > 256 {
            cli.Printf("w", " Truncating down to 256 bytes due to eeprom size \n")
            numBytes = 256
        }
    }

    for i:=0; i<numBytes; i++ {
        misc.SleepInUSec(5000)    //atmel spec says max write time is 5ms
        if I2cAddr16 == true {
            err = smbusNew.I2C16WriteByte(devName, uint16(i), eeData)
        } else {
            err = smbusNew.WriteByte(devName, uint64(i), eeData)
        }
        if err != errType.SUCCESS {
            return
        }
    }
    misc.SleepInUSec(100000)
    return

}

func ProgEeprom(devName string, bus uint32, devAddr byte) (err int) {
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()
    is8g := 0
    for _, entry := range(EepromTbl) {
        if entry.Name == "Product Area Offset" {
            if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 {
                copy(entry.Value, []byte{0x10})
            }
        }
        if entry.Name == "Product Name" {
            
            if ((CardType == "NAPLES25")    ||
               (CardType == "NAPLES25OCP")) &&
               (HpeAlom != true)  {
                copy(entry.Value, []byte{0x4E, 0x41, 0x50, 0x4C, 0x45, 0x53, 0x20, 0x32, 0x35, 0x20})
            } else if CardType == "FORIO" {
                copy(entry.Value, []byte{0x46, 0x4F, 0x52, 0x49, 0x4F, 0x20, 0x38, 0x47, 0x42, 0x20})
            } else if CardType == "VOMERO" {
                copy(entry.Value, []byte{0x56, 0x4F, 0x4D, 0x45, 0x52, 0x4F, 0x20, 0x20, 0x20, 0x20})
            } 
        }

        if entry.Name == "Part Number"   &&
           ( (CardType == "NAPLES25")    ||
             (CardType == "NAPLES25SWM") ||
             (CardType == "NAPLES25OCP") ) {
            if entry.Value[6] == byte(0x38) {
                 is8g = 1
            }
        }
        if entry.Name == "Board ID" {
            if (CardType == "NAPLES25")    ||
               (CardType == "NAPLES25OCP") ||
               (CardType == "NAPLES25SWM") {
                if is8g == 1 {
                    copy(entry.Value, []byte{5, 0 , 0, 0})
                } else {
                    copy(entry.Value, []byte{2, 0 , 0, 0})
                }
            } else if CardType == "FORIO" {
                copy(entry.Value, []byte{4, 0 , 0, 0})
            } else if CardType == "VOMERO" {
                copy(entry.Value, []byte{6, 0 , 0, 0})
            }
        }

        if entry.Name == "Board Info Area Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - brdInfoChk % 0x100)
        } else if entry.Name == "Common Header Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - cmnHeadChk % 0x100)
        } else if entry.Name == "Product info Area Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - productInfoChk % 0x100)
        }

        err = writeField(devName, entry.Offset, entry.NumBytes, entry.Value)
        if err != errType.SUCCESS {
            cli.Println("e", "Program main FRU failed")
            return
        }
    }

    //Extended Table gets handled here
    //Default Extended Table is SWM card.  
    //Sub in fields for other products below and handle checksum for all extended table
    if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 {
        for _, entry := range(EepromExtTbl) {

            if entry.Name == "Product Name" {
                if (CardType == "NAPLES25OCP") && (HpeAlom != true)  {
                    copy(entry.Value, []byte{0x48, 0x50, 0x45, 0x20, 0x4F, 0x43, 
                        0x50, 0x20, 0x4E, 0x61, 0x70, 0x6C, 0x65, 0x73, 0x20, 0x44, 
                        0x53, 0x43, 0x2D, 0x32, 0x35, 0x20, 0x32, 0x70, 0x20, 0x53, 
                        0x46, 0x50, 0x32, 0x38, 0x20, 0x43, 0x61, 0x72, 0x64, 0x00})
                } 
            }

            if entry.Name == "HPE Product Number" {
                if (CardType == "NAPLES25OCP") && (HpeAlom != true)  {
                    copy(entry.Value, []byte{0x50, 0x31, 0x38, 0x36, 0x36, 0x39, 
                        0x2D, 0x30, 0x30, 0x31})
                } 
            }


            if entry.Name == "Product info Area Checksum" || entry.Name == "HPE Multi-Record Area Checksum" {
                updateIntChk()
                entry.Value[0] = byte(0x100 - productInfoChk % 0x100)
            }
            err = writeField(devName, entry.Offset, entry.NumBytes, entry.Value)
            if err != errType.SUCCESS {
                cli.Println("e", "Program extension FRU failed")
                return
            }
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

func UpdateMac(devName string, bus uint32, devAddr byte, mac []byte) (err int) {
//    CardType := os.Getenv("CARD_TYPE")

    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

    if CardType == "MTP" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "MAC_ADDR" {
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "SERIAL_NUM" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, sn)
                continue
            } else if entry.Name == "HW_MAJOR_REV" {
                major, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, major)
                continue
            }
        }
    } else {
        for _, entry := range(EepromTbl) {
            // For HPE ALOM, DO NOT COPY PART NUMBER.  PRINTED LABEL IS PIA P/N WHICH IS DIFFERENT THAN BIA P/N.
            // Keep default P/N for BIA 
            if HpeAlom != true {
                if entry.Name == "Part Number" {
                    pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, pn)
                    continue
                }
            }
            if entry.Name == "MAC Address Base" {
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "Serial Number" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, sn)
                continue
            } else if entry.Name == "Manufacturing Date/Time" {
                date, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, date)
                continue
            } else if entry.Name == "Product SKU Part Number" {
                pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, pn)
                continue
            }
        }

        if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 {
            for _, entry := range(EepromExtTbl) {
                if entry.Name == "MAC Address Base" {
                    copy(entry.Value, mac)
                    continue;
                } else if entry.Name == "Manufacture Date/Time" {
                    date, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, date)
                    continue
                } else if entry.Name == "HPE Serial Number" {
                    sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, sn)
                    continue
                } else if entry.Name == "Serial Number" {
                    sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, sn)
                    continue
                } else if entry.Name == "HPE Product Number" {
                    pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, pn)
                    continue
                } 
            }
        }

        updateIntChk()
    }
    return
}

func updateIntChk() () {
    brdInfoChk = 0
    productInfoChk = 0;
    cmnHeadChk = 0

    for i := 0; i< len(mraChk) ; i++ {
        mraChk[i] = 0;
        mraHdrChk[i] = 0;
    }

    for _, entry := range(EepromTbl) {
        if (entry.Offset > 7) && (entry.Offset < 103) {
            brdInfoChk += calcSum(entry)
        } else if (entry.Offset >= 0) && (entry.Offset < 7) {
            cmnHeadChk += calcSum(entry)
        }
    }
    if HpeOcp == 1 {
        for _, entry := range(EepromExtTbl) {
            if (entry.Offset > 127) && (entry.Offset < 207) {
                productInfoChk += calcSum(entry)
            }
        }
    }
    if HpeNaples == 1 {
        for _, entry := range(EepromExtTbl) {
            if (entry.Offset > 127) && (entry.Offset < 247) {
                productInfoChk += calcSum(entry)
            }
        }
    }
    if HpeSwm == 1 {
        brdInfoChk = 0
        productInfoChk = 0;
        cmnHeadChk = 0
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 7) && (entry.Offset < 127) {
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset >= 0) && (entry.Offset < 7) {
                cmnHeadChk += calcSum(entry)
            }
        }
        for _, entry := range(EepromExtTbl) {
            if (entry.Offset > 127) && (entry.Offset < 223) {
                productInfoChk += calcSum(entry)
            }
        }
    }

    if HpeAlom == true {
        //PIA Checksum (BIA is handled above in first EepromTbl checksum calculate)
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 103) && (entry.Offset < 183) {    
                productInfoChk += calcSum(entry)
            }
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

func FixNaples25HPEfru(devName string, bus uint32, devAddr byte) (err int) {
    var sn   []byte
    var mac  []byte
    var date []byte
    var pn   []byte
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

    for _, entry := range(EepromTbl) {
    if entry.Name == "Serial Number" {
            sn, _ = readField(devName, entry.Offset, entry.NumBytes)
            copy(entry.Value, sn)
            continue
        } else if entry.Name == "MAC Address Base" {
            mac, _ = readField(devName, entry.Offset, entry.NumBytes)
            copy(entry.Value, mac)
            continue
        } else if entry.Name == "Manufacturing Date/Time" {
            date, _ = readField(devName, entry.Offset, entry.NumBytes)
            copy(entry.Value, date)
            continue
        } else if entry.Name == "Part Number" {
            pn, _ = readField(devName, entry.Offset, entry.NumBytes)
            copy(entry.Value, pn)
            continue
        }
    }

    if HpeNaples == 1 {
        for _, entry := range(EepromExtTbl) {
            if entry.Name == "HPE Serial Number" {
                copy(entry.Value, sn)
                continue
            } else if entry.Name == "MAC Address Base" {
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "Manufacture Date/Time" {
                copy(entry.Value, date)
                continue
            } else if entry.Name == "HPE Product Number" {
                copy(entry.Value, pn)
                continue
            }
        }
    }

    updateIntChk()
    return
}

func UpdateSn(devName string, bus uint32, devAddr byte, sn []byte) (err int) {
    if len(sn) > 20 {
        cli.Println("f", "SN too long: ", sn)
        return
    }
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()
//    CardType := os.Getenv("CARD_TYPE")
    if CardType == "MTP" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "SERIAL_NUM" {
                copy(entry.Value, sn)
                continue
            } else if entry.Name == "MAC_ADDR" {
                mac, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "HW_MAJOR_REV" {
                major, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, major)
                continue
            }
        }
    } else {
        for _, entry := range(EepromTbl) {
            // For HPE ALOM, DO NOT COPY PART NUMBER.  PRINTED LABEL IS PIA P/N WHICH IS DIFFERENT THAN BIA P/N.
            // Keep default P/N from default fru table BIA 
            if HpeAlom != true {
                if entry.Name == "Part Number" {
                    pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, pn)
                    continue
                }
            }
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
            } else if entry.Name == "Product SKU Part Number" {
                pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, pn)
                continue
            }
        }

        if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 {
            for _, entry := range(EepromExtTbl) {
                if entry.Name == "HPE Serial Number" {
                    copy(entry.Value, sn)
                    continue
                } else if entry.Name == "Serial Number" {
                    copy(entry.Value, sn)
                    continue
                } else if entry.Name == "MAC Address Base" {
                    mac, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, mac)
                    continue
                } else if entry.Name == "Manufacture Date/Time" {
                    date, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, date)
                    continue
                } else if entry.Name == "HPE Product Number" {
                    pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, pn)
                    continue
                } 
            }
        }

        updateIntChk()
    }
    return
}

func UpdatePn(devName string, bus uint32, devAddr byte, pn []byte) (err int) {
    if len(pn) > 13 {
        cli.Println("f", "SN too long: ", pn)
        return
    }

    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

//    CardType := os.Getenv("CARD_TYPE")
    if CardType == "MTP" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "Part Number" {
                copy(entry.Value, pn)
                break
            }
        }
    } else {
        for _, entry := range(EepromTbl) {
            // For HPE ALOM, DO NOT COPY PART NUMBER.  PRINTED LABEL IS PIA P/N WHICH IS DIFFERENT THAN BIA P/N.
            // Keep default P/N for BIA 
            if HpeAlom != true {
                if entry.Name == "Part Number" {
                    copy(entry.Value, pn)
                    continue
                }
            }
            if entry.Name == "Serial Number" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
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
             } else if entry.Name == "Product SKU Part Number" {
                copy(entry.Value, pn)
                continue
             }
        }

        if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 {
            for _, entry := range(EepromExtTbl) {
                if entry.Name == "MAC Address Base" {
                    mac, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, mac)
                    continue
                } else if entry.Name == "Manufacture Date/Time" {
                    date, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, date)
                    continue
                } else if entry.Name == "HPE Serial Number" {
                    sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, sn)
                    continue
                } else if entry.Name == "Serial Number" {
                    sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, sn)
                    continue
                } else if entry.Name == "HPE Product Number" {
                    copy(entry.Value, pn)
                    continue
                }
            }
        }

        updateIntChk()
    }
    return
}

func UpdateDate(devName string, bus uint32, devAddr byte, str string) (err int) {
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

//    CardType := os.Getenv("CARD_TYPE")
    if CardType == "MTP" {
        cli.Println("e", "This feature does not support MTP!")
        err = errType.FAIL
        return
    }

    data := make([]byte, 3)
    for _, entry := range(EepromTbl) {
        // For HPE ALOM, DO NOT COPY PART NUMBER.  PRINTED LABEL IS PRODUCT INFORMATION AREA P/N WHICH IS DIFFERENT 
        // THAN BOARD INFORMATION AREA P/N. Keep default P/N for BIA 
        if HpeAlom != true {
            if entry.Name == "Part Number" {
                pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, pn)
                continue
            }
        }
        if entry.Name == "Manufacturing Date/Time" {
            const shortForm = "2006-01-02"
            date := fmt.Sprintf("%s%s%s%s%s%s", "20", string(str[4:6]), "-", string(str[0:2]), "-", string(str[2:4]))
            start, _ := time.Parse(shortForm, "1996-01-01")
            end, _ := time.Parse(shortForm, date)
            difference := end.Sub(start)
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
        } else if entry.Name == "Product SKU Part Number" {
            pn, _ := readField(devName, entry.Offset, entry.NumBytes)
            copy(entry.Value, pn)
            continue
        }
    }

    if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 {
    for _, entry := range(EepromExtTbl) {
            if entry.Name == "Manufacture Date/Time" {
                copy(entry.Value, data)
                continue
            } else if entry.Name == "MAC Address Base" {
                mac, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "HPE Serial Number" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, sn)
                continue
            } else if entry.Name == "Serial Number" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, sn)
                continue
            } else if entry.Name == "HPE Product Number" {
                pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, pn)
                continue
            } 
        }
    }

    updateIntChk()
    return
}

func UpdateMajor(devName string, bus uint32, devAddr byte, major []byte) (err int) {

    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

    if CardType == "MTP" {
        for _, entry := range(EepromTbl) {
            if entry.Name == "HW_MAJOR_REV" {
                copy(entry.Value, major)
                continue
            } else if entry.Name == "MAC_ADDR" {
                mac, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, mac)
                continue
            } else if entry.Name == "SERIAL_NUM" {
                sn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, sn)
                continue
            }
        }
    }

    return
}

func DispEeprom(devName string, bus uint32, devAddr byte, field string) (err int) {
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()
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
        } else if(field == "PN") {
            if entry.Name != "Part Number" {
                continue
            }
        } else if(entry.Name == "Reserved") {
            continue
        } /*else if (entry.Name == "Serial Number" || entry.Name == "Part Number") && (HpeNaples == 1) {
            continue
        }*/
        data, err = readField(devName, entry.Offset, entry.NumBytes)
        if err != errType.SUCCESS {
            cli.Println("f", "Failed to read field at offset", entry.Offset, "number of bytes", entry.NumBytes)
            return
        }
        if(field == "SN") {
            if(bytes.Equal(SnAllZero, data) || bytes.Equal(SnAllF, data)) {
                data, err = readField(devName, HpeTbl[9].Offset, HpeTbl[9].NumBytes)
                dataStr := string(data[:HpeTbl[9].NumBytes])
                outStr = fmt.Sprintf(fmtStr, HpeTbl[9].Name, dataStr)
                cli.Println("i", outStr)
                return
            }
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
                date := fmt.Sprintf("%02d/%02d/%02d", int(month), int(day), (int(year) % 100))
                outStr = fmt.Sprintf(fmtDate, entry.Name, data[2], data[1], data[0], date)
            } else if entry.Name == "MAC Address Base" {
                outStr = fmt.Sprintf(fmtMac, entry.Name, data[0], data[1], data[2], data[3], data[4], data[5])
            } else {
                outStr = fmt.Sprintf(fmtHex, entry.Name, data)
            }
        }
        cli.Println("i", outStr)
    }

    if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 && field == "ALL" {
        fmt.Println()
        for _, entry := range(EepromExtTbl) {
            data, err = readField(devName, entry.Offset, entry.NumBytes)
            if err != errType.SUCCESS {
                cli.Println("f", "Failed to read field at offset", entry.Offset, "number of bytes", entry.NumBytes)
                return
            }
            if entry.DataType == STRING {
                dataStr := string(data[:entry.NumBytes])
                outStr = fmt.Sprintf(fmtStr, entry.Name, dataStr)
            } else {
                if entry.Name == "Manufacture Date/Time" {
                    start := time.Date(1996, 1, 1, 0, 0, 0, 0, time.UTC)
                    minutes := int((int(data[2]) * 0x10000) + (int(data[1]) * 0x100) + int(data[0]))
                    now := start.Add(time.Minute * time.Duration(minutes))
                    year, month, day := now.Date()
                    date := fmt.Sprintf("%02d/%02d/%02d", int(month), int(day), (int(year) % 100))
                    outStr = fmt.Sprintf(fmtDate, entry.Name, data[2], data[1], data[0], date)
                } else if entry.Name == "MAC Address Base" {
                    outStr = fmt.Sprintf(fmtMac, entry.Name, data[0], data[1], data[2], data[3], data[4], data[5])
                } else {
                    outStr = fmt.Sprintf(fmtHex, entry.Name, data)
                }
            }
            cli.Println("i", outStr)
        }
    }

    return
}

func DumpEeprom(devName string, bus uint32, devAddr byte, numBytes int) (err int) {

    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()
    var data []byte

    f, error := os.OpenFile("eeprom", os.O_CREATE|os.O_WRONLY, 0600)
    if error != nil {
        cli.Println("e", "file create failed")
    }
    cli.Println("i", "dump FRU to file eeprom")
    for i := 0; i < numBytes; i++ {
        data, err = readField(devName, i, 1)
        cli.Printf("d", "Offset=0x%x, data=0x%x\n", i, data)
        if err != errType.SUCCESS {
            cli.Println("f", "Failed to read field at offset", i)
            return
        }
        f.WriteString(string(data[:]))
    }

    f.Close()
    return
}
