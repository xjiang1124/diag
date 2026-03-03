package eeprom

import (
    "fmt"
    "os"
    "bytes"
    "strings"
    "time"
    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/smbusNew"
    "device/fpga/materafpga"
    "device/sucuart"
    "hardware/i2cinfo"
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

var MtpTurboTbl = []entry {
    entry{"NUM_BYTES",      STRING, 0,   4,  []byte("0256")},
    entry{"HW_MAJOR_REV",   STRING, 4,   2,  []byte("00")},
    entry{"HW_MINOR_REV",   STRING, 6,   4,  []byte("0100")},
    entry{"PRODUCT_NAME",   STRING, 10,  20, []byte("TURBO NIC MTP")},
    entry{"SERIAL_NUM",     STRING, 30,  20, []byte("1234567890          ")},
    entry{"COMPANY_NAME",   STRING, 50,  20, []byte("Pensando Systems Inc")},
    entry{"MFG_DEVIATION",  STRING, 70,  20, []byte("0                   ")},
    entry{"MFG_BITS",       STRING, 90,  2,  []byte("00")},
    entry{"ENG_BITS",       STRING, 92,  2,  []byte("00")},
    entry{"MAC_ADDR",       STRING, 94,  12, []byte("AABBCCDDEEFF")},
    entry{"NUM_OF_MAC",     STRING, 106, 2,  []byte("00")},
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
    entry{"Serial Number",                          STRING,      54,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
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
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      24,      25,    []byte{0x44, 0x53, 0x43, 0x2D,
        0x31, 0x30, 0x30, 0x20, 0x32, 0x70, 0x20, 0x34, 0x30, 0x2F, 0x31, 0x30, 0x30, 0x47, 0x20, 0x51, 0x53, 
    0x46, 0x50, 0x32, 0x38}},
    entry{"PAD",                                    STRING,      49,      15,    []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        64,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      65,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        76,       1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      77,       16,   []byte{0x44, 0x53, 0x43, 0x31,
        0x2D, 0x32, 0x51, 0x31, 0x30, 0x30, 0x2D, 0x38, 0x46, 0x31, 0x36, 0x50}},
    entry{"PAD",                                    STRING,      93,        9,    []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,       102,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     103,       8,    []byte{0x30, 0x34, 0x2F, 0x31,
        0x30, 0x2F, 0x32, 0x30}},
    entry{"Board ID Type/Length",                   INT8,       111,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       112,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       116,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       117,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       119,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       120,       2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       122,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       123,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       129,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,     130,      13,    []byte{0x36, 0x38, 0x2D, 0x30,
        0x30, 0x31, 0x33, 0x2D, 0x30, 0x31, 0x20, 0x30, 0x33}}, 
    entry{"End of Field",                           INT8,       143,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       144,       7,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       151,       1,    []byte{0x00}},
} 

var Naples100HPETbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x10}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x0F}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x45, 0x4E, 0x53,
        0x41, 0x4E, 0x44, 0x4F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xEC}},
    entry{"Product Name",                           STRING,      24,       44,   []byte{
        0x50, 0x43, 0x41, 0x20, 0x44, 0x53, 0x50, 0x20, 0x44, 0x53, 
        0x43, 0x31, 0x30, 0x30, 0x20, 0x45, 0x6e, 0x74, 0x20, 0x31, 
        0x30, 0x30, 0x47, 0x20, 0x32, 0x70, 0x20, 0x51, 0x53, 0x46, 
        0x50, 0x32, 0x38, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        68,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      69,       10,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"PAD",                                    INT8,        79,       1,    []byte{0x00}},
    entry{"Part Number Type/Length",                INT8,        80,       1,    []byte{0xCD}},
    entry{"Part Number",                            STRING,      81,       10,   []byte{0x50, 0x33, 0x37, 0x36,
        0x39, 0x32, 0x2D, 0x30, 0x30, 0x31}},
    entry{"PAD",                                    INT8,        91,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"FRU File ID Type/Length",                INT8,        94,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,      95,       8,    []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"Board ID Type/Length",                   INT8,       103,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       104,       4,    []byte{0x02, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       108,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       109,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       111,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       112,       2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       114,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       115,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"End of Field",                           INT8,       121,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       122,       5,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00}},
    entry{"Board Info Area Checksum",               INT8,       127,       1,    []byte{0x00}},

    entry{"Product Info Format Version",            INT8,       128,       1,    []byte{0x01}},
    entry{"Product Area lenth",                     INT8,       129,       1,    []byte{0x0B}},
    entry{"Language Code",                          INT8,       130,       1,    []byte{0x19}},
    entry{"Manufacturer Name Type/Length",          INT8,       131,       1,    []byte{0xC3}},
    entry{"Manufacturer",                           STRING,     132,       3,    []byte{0x48, 0x50, 0x45}},
    entry{"Product Name Type/Length",               INT8,       135,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,     136,       40,   []byte{
        0x50, 0x65, 0x6e, 0x73, 0x61, 0x6e, 0x64, 0x6f, 0x20, 0x44, 
        0x53, 0x50, 0x20, 0x44, 0x53, 0x43, 0x2d, 0x31, 0x30, 0x30, 
        0x20, 0x45, 0x6e, 0x74, 0x20, 0x31, 0x30, 0x30, 0x47, 0x62, 
        0x20, 0x43, 0x61, 0x72, 0x64, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"PCA Product Number Type/Length",         INT8,       176,       1,    []byte{0xCA}},
    entry{"Product Number",                         STRING,     177,       10,   []byte{0x50, 0x33, 0x37, 0x36,
        0x39, 0x30, 0x2D, 0x42, 0x32, 0x31}},
    entry{"Product Version Type/Length",            INT8,       187,       1,    []byte{0xC2}},
    entry{"Product Version",                        STRING,     188,       2,    []byte{0x30, 0x41}},
    entry{"PCA Serial Number Type/Length",          INT8,       190,       1,    []byte{0xCA}},
    entry{"Serial Number",                          STRING,     191,       10,   []byte{0x35, 0x55, 0x50, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Asset Tag Type/Length",                  INT8,       201,       1,    []byte{0xC0}},
    entry{"Fru File ID Type/Length",                INT8,       202,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     203,       8,    []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"End of Field",                           INT8,       211,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       212,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Product info Area Checksum",             INT8,       215,       1,    []byte{0x00}},
} 


var Naples100HPECLOUDTbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x10}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x0F}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x45, 0x4E, 0x53,
        0x41, 0x4E, 0x44, 0x4F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xF0}},
    entry{"Product Name",                           STRING,      24,       48,   []byte{
        0x50, 0x43, 0x41, 0x20, 0x44, 0x53, 0x50, 0x20, 0x44, 0x53, 
        0x43, 0x31, 0x30, 0x30, 0x20, 0x43, 0x6c, 0x64, 0x2d, 0x53, 
        0x50, 0x20, 0x32, 0x70, 0x20, 0x51, 0x53, 0x46, 0x50, 0x32, 
        0x38, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        72,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      73,       10,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"PAD",                                    INT8,        83,       1,    []byte{0x00}},
    entry{"Part Number Type/Length",                INT8,        84,       1,    []byte{0xCD}},
    entry{"Part Number",                            STRING,      85,       10,   []byte{0x50, 0x34, 0x31, 0x38, 
        0x35, 0x34, 0x2d, 0x30, 0x30, 0x31}},
    entry{"PAD",                                    INT8,        95,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"FRU File ID Type/Length",                INT8,        98,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,      99,       8,    []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"Board ID Type/Length",                   INT8,       107,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       108,       4,    []byte{0x02, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       112,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       113,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       115,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       116,       2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       118,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       119,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"End of Field",                           INT8,       125,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       126,       1,    []byte{0x00}},
    entry{"Board Info Area Checksum",               INT8,       127,       1,    []byte{0x00}},

    entry{"Product Info Format Version",            INT8,       128,       1,    []byte{0x01}},
    entry{"Product Area lenth",                     INT8,       129,       1,    []byte{0x0C}},
    entry{"Language Code",                          INT8,       130,       1,    []byte{0x19}},
    entry{"Manufacturer Name Type/Length",          INT8,       131,       1,    []byte{0xC3}},
    entry{"Manufacturer",                           STRING,     132,       3,    []byte{0x48, 0x50, 0x45}},
    entry{"Product Name Type/Length",               INT8,       135,       1,    []byte{0xEC}},
    entry{"Product Name",                           STRING,     136,       44,   []byte{
        0x50, 0x65, 0x6e, 0x73, 0x61, 0x6e, 0x64, 0x6f, 0x20, 0x44, 
        0x53, 0x50, 0x20, 0x44, 0x53, 0x43, 0x2d, 0x31, 0x30, 0x30, 
        0x20, 0x43, 0x6c, 0x64, 0x2d, 0x53, 0x50, 0x20, 0x31, 0x30, 
        0x30, 0x47, 0x62, 0x20, 0x43, 0x61, 0x72, 0x64, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20 }},
    entry{"PCA Product Number Type/Length",         INT8,       180,       1,    []byte{0xCA}},
    entry{"Product Number",                         STRING,     181,       10,   []byte{0x50, 0x34, 0x31, 0x38, 0x35, 0x32, 0x2d, 0x42, 0x32, 0x31}},
    entry{"Product Version Type/Length",            INT8,       191,       1,    []byte{0xC2}},
    entry{"Product Version",                        STRING,     192,       2,    []byte{0x30, 0x41}},
    entry{"PCA Serial Number Type/Length",          INT8,       194,       1,    []byte{0xCA}},
    entry{"Serial Number",                          STRING,     195,       10,   []byte{0x35, 0x55, 0x50, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Asset Tag Type/Length",                  INT8,       205,       1,    []byte{0xC0}},
    entry{"Fru File ID Type/Length",                INT8,       206,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     207,       8,    []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"End of Field",                           INT8,       215,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       216,       7,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00}},
    entry{"Product info Area Checksum",             INT8,       223,       1,    []byte{0x00}},
}


var Naples100DELLTbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      24,      40,    []byte{
        0x44, 0x53, 0x43, 0x2d, 0x31, 0x30, 0x30, 0x2c, 0x32, 0x78, 
        0x51, 0x53, 0x46, 0x50, 0x32, 0x38, 0x2c, 0x38, 0x67, 0x52, 
        0x41, 0x4d, 0x2c, 0x31, 0x36, 0x47, 0x65, 0x4d, 0x4d, 0x43, 
        0x2c, 0x44, 0x65, 0x6c, 0x6c, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        64,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      65,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        76,       1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      77,       25,   []byte{
        0x44, 0x53, 0x43, 0x31, 0x2d, 0x32, 0x51, 0x31, 0x30, 0x30, 
        0x2d, 0x38, 0x46, 0x31, 0x36, 0x50, 0x2d, 0x44, 0x20, 0x20, 
        0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,       102,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     103,       8,    []byte{0x30, 0x37, 0x2f, 0x32, 
        0x33, 0x2f, 0x32, 0x31}},
    entry{"Board ID Type/Length",                   INT8,       111,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       112,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       116,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       117,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       119,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       120,       2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       122,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       123,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       129,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,     130,      13,    []byte{0x36, 0x38, 0x2d, 0x30, 
        0x30, 0x32, 0x34, 0x2d, 0x30, 0x31, 0x20, 0x30, 0x30}},
    entry{"End of Field",                           INT8,       143,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       144,       7,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       151,       1,    []byte{0x00}},
}



var Vomero2Tbl = []entry {
    entry{"Class Code",                             INT8,        0,          3,    []byte{0x00, 0x80, 0x02}},
    entry{"PCI-SIG Vendor ID",                      INT8,        3,          2,    []byte{0xD8, 0x1D}},
    entry{"Serial Number",                          STRING,      5,          20,   []byte{0x20, 0x20, 0x20, 0x20, 0x20,
          0x20, 020, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Model Number",                           STRING,      25,         40,   []byte{0x50, 0x65, 0x6E, 0x73, 0x61,
          0x6E, 0x64, 0x6F, 0x20, 0x44, 0x53, 0x43, 0x2D, 0x31, 0x30, 0x30, 0x56, 0x20, 0x35, 0x30, 0x2F, 0x31, 0x30, 0x30, 
      0x47, 0x20, 0x32, 0x70, 0x20, 0x51, 0x53, 0x46, 0x50, 0x32, 0x38, 0x20, 0x43, 0x61, 0x72, 0x64}},
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
    entry{"Sensor 1 Address Offset",                INT8,        86,         1,    []byte{0x17}},
    entry{"Reserved",                               INT8,        87,         1,    []byte{0x16}},
    entry{"Warning Threshold",                      INT8,        88,         2,    []byte{0x00, 0x5F}},
    entry{"Critical Temp Threshold",                INT8,        90,         2,    []byte{0x00, 0x69}},
    entry{"PCIE Vendor ID - LSB",                   INT8,        92,         1,    []byte{0xD8}},
    entry{"PCIE Vendor ID - MSB",                   INT8,        93,         1,    []byte{0x1D}},
    entry{"PCIE Vendor ID - LSB",                   INT8,        94,         1,    []byte{0x00}},
    entry{"PCIE Vendor ID - MSB",                   INT8,        95,         1,    []byte{0x10}},
    entry{"PCIE Subsystem Vendor ID - LSB",         INT8,        96,         1,    []byte{0xD8}},
    entry{"PCIE Subsystem Vendor ID - MSB",         INT8,        97,         1,    []byte{0x1D}},
    entry{"PCIE Subsystem ID - LSB",                INT8,        98,         1,    []byte{0x09}},
    entry{"PCIE Subsystem ID - MSB",                INT8,        99,         1,    []byte{0x40}},
    entry{"PAD",                                    STRING,      100,        156,  []byte{0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }},
    entry{"Common Format Version",                  INT8,        256,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        257,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        258,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        259,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        260,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        261,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        262,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        263,        1,    []byte{0x00}},
    entry{"Board Info Format Version",              INT8,        264,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        265,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        266,        1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        267,        3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        270,        1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      271,        8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        279,        1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      280,        26,   []byte{0x44, 0x53, 0x43, 0x2D,
        0x31, 0x30, 0x30, 0x56, 0x20, 0x35, 0x30, 0x2F, 0x31, 0x30, 0x30, 0x47, 0x20, 0x32, 0x70, 0x20, 0x51, 0x53,
        0x46, 0x50, 0x32, 0x38}},
    entry{"PAD",                                    STRING,      306,        14,   []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        320,        1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      321,        11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        332,        1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      333,        16,   []byte{0x44, 0x53, 0x43, 0x31,
        0x2D, 0x32, 0x51, 0x31, 0x30, 0x30, 0x2D, 0x38, 0x56, 0x36, 0x34, 0x50}},
    entry{"PAD",                                    STRING,      349,        9,    []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,        358,        1,    []byte{0xC8}},
    entry{"06/03/20",                               STRING,      359,        8,    []byte{0x30, 0x36, 0x2F, 0x30,
        0x33, 0x2F, 0x32, 0x30}},
    entry{"Board ID Type/Length",                   INT8,        367,        1,    []byte{0x04}},
    entry{"Board ID",                               INT8,        368,        4,    []byte{0x06, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,        372,        1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        373,        2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,        375,        1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,        376,        2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,        378,        1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,        379,        6,    []byte{0x00, 0xAE, 0xCD, 0x00, 0x00, 
         0x00}},
    entry{"Assembly Number Type/Length",            INT8,        385,        1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,      386,        13,   []byte{0x36, 0x38, 0x2D, 0x30, 0x30, 
         0x31, 0x31, 0x2D, 0x30, 0x32, 0x20, 0x30, 0x31}},
    entry{"End of Field",                           INT8,        399,        1,    []byte{0xC1}},
    entry{"PAD",                                    STRING,      400,        7,    []byte{0x00, 0x00, 0x00, 0x00, 0x00,
         0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,        407,        1,    []byte{0x00}},
} 

var OrtanoTbl = []entry {
    entry{"Class Code",                             INT8,        0,          3,    []byte{0x00, 0x80, 0x02}},
    entry{"PCI-SIG Vendor ID",                      INT8,        3,          2,    []byte{0xD8, 0x1D}},
    entry{"Serial Number",                          STRING,      5,          20,   []byte{0x20, 0x20, 0x20, 0x20, 0x20,
          0x20, 020, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Model Number",                           STRING,      25,         40,   []byte{0x44, 0x53, 0x43, 0x32, 0x2d,
          0x32, 0x30, 0x30, 0x20, 0x32, 0x78, 0x32, 0x30, 0x30, 0x47, 0x62, 0x45, 0x20, 0x44, 0x75, 0x61, 0x6C, 0x20, 0x51, 
      0x53, 0x46, 0x50, 0x35, 0x36, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Port 0 Maximum Link Speed",              INT8,        65,         1,    []byte{0x04}},
    entry{"Port 0 Maximum Link Width",              INT8,        66,         1,    []byte{0x0F}},
    entry{"Port 1 Maximum Link Speed",              INT8,        67,         1,    []byte{0x04}},
    entry{"Port 1 Maximum Link Width",              INT8,        68,         1,    []byte{0x08}},
    entry{"12V Power Rail Initial Power",           INT8,        69,         1,    []byte{0x3C}},
    entry{"Reserved",                               INT8,        70,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        71,         1,    []byte{0x00}},
    entry{"12V Power Rail Maximum Power",           INT8,        72,         1,    []byte{0x3C}},
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
    entry{"Sensor Address",                         INT8,        85,         1,    []byte{0x94}},
    entry{"Sensor 1 Address Offset",                INT8,        86,         1,    []byte{0x18}},
    entry{"Reserved",                               INT8,        87,         1,    []byte{0x16}},
    entry{"Warning Threshold LSB",                  INT8,        88,         1,    []byte{0x55}},
    entry{"Warning Threshold MSB",                  INT8,        89,         1,    []byte{0x00}},
    entry{"Over Temp Threshold LSB",                INT8,        90,         1,    []byte{0x5F}},
    entry{"Over Temp Threshold MSB",                INT8,        91,         1,    []byte{0x00}},
    entry{"PCIE Vendor ID - LSB",                   INT8,        92,         1,    []byte{0xD8}},
    entry{"PCIE Vendor ID - MSB",                   INT8,        93,         1,    []byte{0x1D}},
    entry{"PCIE Vendor ID - LSB",                   INT8,        94,         1,    []byte{0x00}},
    entry{"PCIE Vendor ID - MSB",                   INT8,        95,         1,    []byte{0x10}},
    entry{"PCIE Subsystem Vendor ID - LSB",         INT8,        96,         1,    []byte{0xD8}},
    entry{"PCIE Subsystem Vendor ID - MSB",         INT8,        97,         1,    []byte{0x1D}},
    entry{"PCIE Subsystem ID - LSB",                INT8,        98,         1,    []byte{0x09}},
    entry{"PCIE Subsystem ID - MSB",                INT8,        99,         1,    []byte{0x40}},
    entry{"PAD",                                    STRING,      100,        156,  []byte{0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }},
    entry{"Common Format Version",                  INT8,        256,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        257,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        258,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        259,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        260,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        261,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        262,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        263,        1,    []byte{0x00}},
    entry{"Board Info Format Version",              INT8,        264,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        265,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        266,        1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        267,        3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        270,        1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      271,        8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        279,        1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      280,        29,   []byte{0x44, 0x53, 0x43, 0x32, 
        0x2d, 0x32, 0x30, 0x30, 0x20, 0x32, 0x78, 0x32, 0x30, 0x30, 0x47, 0x62, 0x45, 0x20, 0x44, 0x75, 0x61, 0x6C, 
        0x20, 0x51, 0x53, 0x46, 0x50, 0x35, 0x36}},
    entry{"PAD",                                    STRING,      309,        11,   []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        320,        1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      321,        11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        332,        1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      333,        22,   []byte{0x44, 0x53, 0x43, 0x32,
        0x2D, 0x32, 0x51, 0x32, 0x30, 0x30, 0x2D, 0x33, 0x32, 0x52, 0x33, 0x32, 0x46, 0x36, 0x34, 0x50, 0x2D, 0x52}},
    entry{"PAD",                                    STRING,      355,        3,    []byte{0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,        358,        1,    []byte{0xC8}},
    entry{"06/03/20",                               STRING,      359,        8,    []byte{0x30, 0x39, 0x2F, 0x32,
        0x39, 0x2F, 0x32, 0x30}},
    entry{"Board ID Type/Length",                   INT8,        367,        1,    []byte{0x04}},
    entry{"Board ID",                               INT8,        368,        4,    []byte{0x06, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,        372,        1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        373,        2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,        375,        1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,        376,        2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,        378,        1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,        379,        6,    []byte{0x00, 0xAE, 0xCD, 0x00, 0x00, 
         0x00}},
    entry{"Assembly Number Type/Length",            INT8,        385,        1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,      386,        13,   []byte{0x36, 0x38, 0x2D, 0x30, 0x30, 
         0x31, 0x35, 0x2D, 0x30, 0x31, 0x20, 0x30, 0x31}},
    entry{"End of Field",                           INT8,        399,        1,    []byte{0xC1}},
    entry{"PAD",                                    STRING,      400,        7,    []byte{0x00, 0x00, 0x00, 0x00, 0x00,
         0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,        407,        1,    []byte{0x00}},
} 


var OrtanoTbl_V2 = []entry {
    entry{"Class Code",                             INT8,        0,          3,    []byte{0x00, 0x80, 0x02}},
    entry{"PCI-SIG Vendor ID",                      INT8,        3,          2,    []byte{0xD8, 0x1D}},
    entry{"Serial Number",                          STRING,      5,          20,   []byte{0x20, 0x20, 0x20, 0x20,
          0x20, 0x20, 020, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Model Number",                           STRING,      25,         40,   []byte{0x44, 0x53, 0x43, 0x2d, 
          0x32, 0x30, 0x30, 0x56, 0x20, 0x32, 0x78, 0x32, 0x30, 0x30, 
          0x47, 0x62, 0x45, 0x20, 0x44, 0x75, 0x61, 0x6c, 0x20, 0x51, 
          0x53, 0x46, 0x50, 0x35, 0x36, 0x20, 0x20, 0x20, 0x20, 0x20, 
          0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Port 0 Maximum Link Speed",              INT8,        65,         1,    []byte{0x04}},
    entry{"Port 0 Maximum Link Width",              INT8,        66,         1,    []byte{0x0F}},
    entry{"Port 1 Maximum Link Speed",              INT8,        67,         1,    []byte{0x04}},
    entry{"Port 1 Maximum Link Width",              INT8,        68,         1,    []byte{0x08}},
    entry{"12V Power Rail Initial Power",           INT8,        69,         1,    []byte{0x3C}},
    entry{"Reserved",                               INT8,        70,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        71,         1,    []byte{0x00}},
    entry{"12V Power Rail Maximum Power",           INT8,        72,         1,    []byte{0x3C}},
    entry{"Reserved",                               INT8,        73,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        74,         1,    []byte{0x00}},
    entry{"Cap List Pointer",                       INT8,        75,         2,    []byte{0x50, 0x00}},
    entry{"",                                       INT8,        77,         1,    []byte{0x00}},
    entry{"",                                       INT8,        78,         1,    []byte{0x00}},
    entry{"",                                       INT8,        79,         1,    []byte{0x00}},
    entry{"VU Cap ID",                              INT8,        80,         1,    []byte{0xA5}},
    entry{"VU Cap ID",                              INT8,        81,         1,    []byte{0x00}},
    entry{"Next Cap address",                       INT8,        82,         1,    []byte{0x60}},
    entry{"Next Cap address",                       INT8,        83,         1,    []byte{0x00}},
    entry{"Vendor Specific Type",                   INT8,        84,         2,    []byte{0x01, 0x00}},
    entry{"PCI-SIG Vendor ID",                      INT8,        86,         2,    []byte{0x8E, 0x10}},
    entry{"PCIE Vendor ID",                         INT8,        88,         2,    []byte{0xD8, 0x1D}},
    entry{"PCIE Device ID ",                        INT8,        90,         2,    []byte{0x02, 00}},
    entry{"PCIE Subsystem Vendor ID LSB",           INT8,        92,         1,    []byte{0xD8}},
    entry{"PCIE Subsystem Vendor ID MSB",           INT8,        93,         1,    []byte{0x1D}},
    entry{"PCIE Subsystem ID - LSB",                INT8,        94,         1,    []byte{0x01}},
    entry{"PCIE Subsystem ID - MSB",                INT8,        95,         1,    []byte{0x50}},
    entry{"VU Cap ID",                              INT8,        96,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,        98,         2,    []byte{0x6C, 0x00}},
    entry{"Sensor Type",                            INT8,       100,         1,    []byte{0x50}},
    entry{"Sensor Address",                         INT8,       101,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       102,         1,    []byte{0x16}},
    entry{"Reserved",                               INT8,       103,         1,    []byte{0x00}},
    entry{"Warning ThreshB",                        INT8,       104,         2,    []byte{0x00, 0x55}},
    entry{"OverTemp Thresh",                        INT8,       106,         2,    []byte{0x00, 0x5F}},
    entry{"VU Cap ID",                              INT8,       108,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,       110,         2,    []byte{0x78, 0x00}},
    entry{"Sensor Type",                            INT8,       112,         1,    []byte{0x51}},
    entry{"Sensor Address",                         INT8,       113,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       114,         1,    []byte{0x19}},
    entry{"Reserved",                               INT8,       115,         1,    []byte{0x00}},
    entry{"Warning Thresh",                         INT8,       116,         2,    []byte{0x00, 0x35}},
    entry{"OverTemp Thresh",                        INT8,       118,         2,    []byte{0x00, 0x34}},
    entry{"VU Cap ID",                              INT8,       120,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,       122,         2,    []byte{0x00, 0x00}},
    entry{"Sensor Type",                            INT8,       124,         1,    []byte{0x51}},
    entry{"Sensor Address",                         INT8,       125,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       126,         1,    []byte{0x1A}},
    entry{"Reserved",                               INT8,       127,         1,    []byte{0x00}},
    entry{"Warning Thresh",                         INT8,       128,         2,    []byte{0x00, 0x37}},
    entry{"OverTemp Thresh",                        INT8,       130,         2,    []byte{0x00, 0x36}},
    entry{"PAD",                                    STRING,      132,        124,  []byte{0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  }},
    entry{"Common Format Version",                  INT8,        256,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        257,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        258,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        259,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        260,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        261,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        262,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        263,        1,    []byte{0x00}},
    entry{"Board Info Format Version",              INT8,        264,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        265,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        266,        1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        267,        3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        270,        1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      271,        8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        279,        1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      280,        29,   []byte{0x44, 0x53, 0x43, 0x32, 
        0x2d, 0x32, 0x30, 0x30, 0x20, 0x32, 0x78, 0x32, 0x30, 0x30, 0x47, 0x62, 0x45, 0x20, 0x44, 0x75, 0x61, 0x6C, 
        0x20, 0x51, 0x53, 0x46, 0x50, 0x35, 0x36}},
    entry{"PAD",                                    STRING,      309,        11,   []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        320,        1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      321,        11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        332,        1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      333,        22,   []byte{0x44, 0x53, 0x43, 0x32,
        0x2D, 0x32, 0x51, 0x32, 0x30, 0x30, 0x2D, 0x33, 0x32, 0x52, 0x33, 0x32, 0x46, 0x36, 0x34, 0x50, 0x2D, 0x52}},
    entry{"PAD",                                    STRING,      355,        3,    []byte{0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,        358,        1,    []byte{0xC8}},
    entry{"02/19/21",                               STRING,      359,        8,    []byte{0x30, 0x32, 0x2f, 0x31, 
        0x39, 0x2f, 0x32, 0x31}},
    entry{"Board ID Type/Length",                   INT8,        367,        1,    []byte{0x04}},
    entry{"Board ID",                               INT8,        368,        4,    []byte{0x06, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,        372,        1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        373,        2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,        375,        1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,        376,        2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,        378,        1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,        379,        6,    []byte{0x00, 0xAE, 0xCD, 0x00, 0x00, 
         0x00}},
    entry{"Assembly Number Type/Length",            INT8,        385,        1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,      386,        13,   []byte{0x36, 0x38, 0x2D, 0x30, 0x30, 
         0x31, 0x35, 0x2D, 0x30, 0x32, 0x20, 0x30, 0x31}},
    entry{"End of Field",                           INT8,        399,        1,    []byte{0xC1}},
    entry{"PAD",                                    STRING,      400,        7,    []byte{0x00, 0x00, 0x00, 0x00, 0x00,
         0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,        407,        1,    []byte{0x00}},

}

var OrtanoITbl_V2 = []entry {
    entry{"Class Code",                             INT8,        0,          3,    []byte{0x00, 0x80, 0x02}},
    entry{"PCI-SIG Vendor ID",                      INT8,        3,          2,    []byte{0xD8, 0x1D}},
    entry{"Serial Number",                          STRING,      5,          20,   []byte{0x20, 0x20, 0x20, 0x20,
          0x20, 0x20, 020, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Model Number",                           STRING,      25,         40,   []byte{0x44, 0x53, 0x43, 0x2d, 0x32, 0x30, 0x30, 0x56, 
                                                                                          0x20, 0x32, 0x78, 0x32, 0x30, 0x30, 0x47, 0x62, 
                                                                                          0x45, 0x20, 0x44, 0x75, 0x61, 0x6c, 0x20, 0x51, 
                                                                                          0x53, 0x46, 0x50, 0x35, 0x36, 0x20, 0x20, 0x20, 
                                                                                          0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Port 0 Maximum Link Speed",              INT8,        65,         1,    []byte{0x04}},
    entry{"Port 0 Maximum Link Width",              INT8,        66,         1,    []byte{0x0F}},
    entry{"Port 1 Maximum Link Speed",              INT8,        67,         1,    []byte{0x04}},
    entry{"Port 1 Maximum Link Width",              INT8,        68,         1,    []byte{0x08}},
    entry{"12V Power Rail Initial Power",           INT8,        69,         1,    []byte{0x3C}},
    entry{"Reserved",                               INT8,        70,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        71,         1,    []byte{0x00}},
    entry{"12V Power Rail Maximum Power",           INT8,        72,         1,    []byte{0x3C}},
    entry{"Reserved",                               INT8,        73,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        74,         1,    []byte{0x00}},
    entry{"Cap List Pointer",                       INT8,        75,         2,    []byte{0x50, 0x00}},
    entry{"",                                       INT8,        77,         1,    []byte{0x00}},
    entry{"",                                       INT8,        78,         1,    []byte{0x00}},
    entry{"",                                       INT8,        79,         1,    []byte{0x00}},
    entry{"VU Cap ID",                              INT8,        80,         1,    []byte{0xA5}},
    entry{"VU Cap ID",                              INT8,        81,         1,    []byte{0x00}},
    entry{"Next Cap address",                       INT8,        82,         1,    []byte{0x60}},
    entry{"Next Cap address",                       INT8,        83,         1,    []byte{0x00}},
    entry{"Vendor Specific Type",                   INT8,        84,         2,    []byte{0x01, 0x00}},
    entry{"PCI-SIG Vendor ID",                      INT8,        86,         2,    []byte{0x8E, 0x10}},
    entry{"PCIE Vendor ID",                         INT8,        88,         2,    []byte{0xD8, 0x1D}},
    entry{"PCIE Device ID ",                        INT8,        90,         2,    []byte{0x02, 00}},
    entry{"PCIE Subsystem Vendor ID LSB",           INT8,        92,         1,    []byte{0xD8}},
    entry{"PCIE Subsystem Vendor ID MSB",           INT8,        93,         1,    []byte{0x1D}},
    entry{"PCIE Subsystem ID - LSB",                INT8,        94,         1,    []byte{0x0C}},
    entry{"PCIE Subsystem ID - MSB",                INT8,        95,         1,    []byte{0x50}},
    entry{"VU Cap ID",                              INT8,        96,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,        98,         2,    []byte{0x6C, 0x00}},
    entry{"Sensor Type",                            INT8,       100,         1,    []byte{0x50}},
    entry{"Sensor Address",                         INT8,       101,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       102,         1,    []byte{0x16}},
    entry{"Reserved",                               INT8,       103,         1,    []byte{0x00}},
    entry{"Warning ThreshB",                        INT8,       104,         2,    []byte{0x00, 0x55}},
    entry{"OverTemp Thresh",                        INT8,       106,         2,    []byte{0x00, 0x5F}},
    entry{"VU Cap ID",                              INT8,       108,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,       110,         2,    []byte{0x78, 0x00}},
    entry{"Sensor Type",                            INT8,       112,         1,    []byte{0x51}},
    entry{"Sensor Address",                         INT8,       113,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       114,         1,    []byte{0x19}},
    entry{"Reserved",                               INT8,       115,         1,    []byte{0x00}},
    entry{"Warning Thresh",                         INT8,       116,         2,    []byte{0x00, 0x35}},
    entry{"OverTemp Thresh",                        INT8,       118,         2,    []byte{0x00, 0x34}},
    entry{"VU Cap ID",                              INT8,       120,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,       122,         2,    []byte{0x00, 0x00}},
    entry{"Sensor Type",                            INT8,       124,         1,    []byte{0x51}},
    entry{"Sensor Address",                         INT8,       125,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       126,         1,    []byte{0x1A}},
    entry{"Reserved",                               INT8,       127,         1,    []byte{0x00}},
    entry{"Warning Thresh",                         INT8,       128,         2,    []byte{0x00, 0x37}},
    entry{"OverTemp Thresh",                        INT8,       130,         2,    []byte{0x00, 0x36}},
    entry{"PAD",                                    STRING,      132,        124,  []byte{0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  }},
    entry{"Common Format Version",                  INT8,        256,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        257,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        258,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        259,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        260,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        261,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        262,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        263,        1,    []byte{0x00}},
    entry{"Board Info Format Version",              INT8,        264,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        265,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        266,        1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        267,        3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        270,        1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      271,        8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        279,        1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      280,        29,   []byte{0x44, 0x53, 0x43, 0x32, 0x2d, 0x32, 0x30, 0x30, 
                                                                                          0x20, 0x32, 0x78, 0x32, 0x30, 0x30, 0x47, 0x62, 
                                                                                          0x45, 0x20, 0x44, 0x75, 0x61, 0x6c, 0x20, 0x51, 
                                                                                          0x53, 0x46, 0x50, 0x35, 0x36}},
    entry{"PAD",                                    STRING,      309,        11,   []byte{0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                          0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        320,        1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      321,        11,   []byte{0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                                                                                          0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        332,        1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      333,        23,   []byte{0x44, 0x53, 0x43, 0x32, 0x2D, 0x32, 0x51, 0x32, 
                                                                                          0x30, 0x30, 0x2D, 0x33, 0x32, 0x52, 0x33, 0x32, 
                                                                                          0x46, 0x36, 0x34, 0x50, 0x2D, 0x52, 0x33}},
    entry{"PAD",                                    STRING,      356,        2,    []byte{0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,        358,        1,    []byte{0xC8}},
    entry{"05/02/22",                               STRING,      359,        8,    []byte{0x30, 0x35, 0x2f, 0x30, 
                                                                                          0x32, 0x2f, 0x32, 0x32}},
    entry{"Board ID Type/Length",                   INT8,        367,        1,    []byte{0x04}},
    entry{"Board ID",                               INT8,        368,        4,    []byte{0x06, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,        372,        1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        373,        2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,        375,        1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,        376,        2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,        378,        1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,        379,        6,    []byte{0x00, 0xAE, 0xCD, 0x00, 0x00, 
         0x00}},
    entry{"Assembly Number Type/Length",            INT8,        385,        1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,      386,        13,   []byte{0x36, 0x38, 0x2D, 0x30, 0x30, 0x32, 0x39, 0x2D, 
                                                                                          0x30, 0x32, 0x20, 0x30, 0x31}},
    entry{"End of Field",                           INT8,        399,        1,    []byte{0xC1}},
    entry{"PAD",                                    STRING,      400,        7,    []byte{0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,        407,        1,    []byte{0x00}},
}

var OrtanoATbl_V2 = []entry {
    entry{"Class Code",                             INT8,        0,          3,    []byte{0x00, 0x80, 0x02}},
    entry{"PCI-SIG Vendor ID",                      INT8,        3,          2,    []byte{0xD8, 0x1D}},
    entry{"Serial Number",                          STRING,      5,          20,   []byte{0x20, 0x20, 0x20, 0x20,
          0x20, 0x20, 020, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Model Number",                           STRING,      25,         40,   []byte{0x44, 0x53, 0x43, 0x2d, 0x32, 0x30, 0x30, 0x56, 
                                                                                          0x20, 0x41, 0x44, 0x49, 0x20, 0x32, 0x78, 0x32, 
                                                                                          0x30, 0x30, 0x47, 0x62, 0x45, 0x20, 0x44, 0x75, 
                                                                                          0x61, 0x6c, 0x20, 0x51, 0x53, 0x46, 0x50, 0x35, 
                                                                                          0x36, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Port 0 Maximum Link Speed",              INT8,        65,         1,    []byte{0x04}},
    entry{"Port 0 Maximum Link Width",              INT8,        66,         1,    []byte{0x0F}},
    entry{"Port 1 Maximum Link Speed",              INT8,        67,         1,    []byte{0x04}},
    entry{"Port 1 Maximum Link Width",              INT8,        68,         1,    []byte{0x08}},
    entry{"12V Power Rail Initial Power",           INT8,        69,         1,    []byte{0x3C}},
    entry{"Reserved",                               INT8,        70,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        71,         1,    []byte{0x00}},
    entry{"12V Power Rail Maximum Power",           INT8,        72,         1,    []byte{0x3C}},
    entry{"Reserved",                               INT8,        73,         1,    []byte{0x00}},
    entry{"Reserved",                               INT8,        74,         1,    []byte{0x00}},
    entry{"Cap List Pointer",                       INT8,        75,         2,    []byte{0x50, 0x00}},
    entry{"",                                       INT8,        77,         1,    []byte{0x00}},
    entry{"",                                       INT8,        78,         1,    []byte{0x00}},
    entry{"",                                       INT8,        79,         1,    []byte{0x00}},
    entry{"VU Cap ID",                              INT8,        80,         1,    []byte{0xA5}},
    entry{"VU Cap ID",                              INT8,        81,         1,    []byte{0x00}},
    entry{"Next Cap address",                       INT8,        82,         1,    []byte{0x60}},
    entry{"Next Cap address",                       INT8,        83,         1,    []byte{0x00}},
    entry{"Vendor Specific Type",                   INT8,        84,         2,    []byte{0x01, 0x00}},
    entry{"PCI-SIG Vendor ID",                      INT8,        86,         2,    []byte{0x8E, 0x10}},
    entry{"PCIE Vendor ID",                         INT8,        88,         2,    []byte{0xD8, 0x1D}},
    entry{"PCIE Device ID ",                        INT8,        90,         2,    []byte{0x02, 00}},
    entry{"PCIE Subsystem Vendor ID LSB",           INT8,        92,         1,    []byte{0xD8}},
    entry{"PCIE Subsystem Vendor ID MSB",           INT8,        93,         1,    []byte{0x1D}},
    entry{"PCIE Subsystem ID - LSB",                INT8,        94,         1,    []byte{0x0A}},
    entry{"PCIE Subsystem ID - MSB",                INT8,        95,         1,    []byte{0x50}},
    entry{"VU Cap ID",                              INT8,        96,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,        98,         2,    []byte{0x6C, 0x00}},
    entry{"Sensor Type",                            INT8,       100,         1,    []byte{0x50}},
    entry{"Sensor Address",                         INT8,       101,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       102,         1,    []byte{0x16}},
    entry{"Reserved",                               INT8,       103,         1,    []byte{0x00}},
    entry{"Warning ThreshB",                        INT8,       104,         2,    []byte{0x00, 0x55}},
    entry{"OverTemp Thresh",                        INT8,       106,         2,    []byte{0x00, 0x5F}},
    entry{"VU Cap ID",                              INT8,       108,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,       110,         2,    []byte{0x78, 0x00}},
    entry{"Sensor Type",                            INT8,       112,         1,    []byte{0x51}},
    entry{"Sensor Address",                         INT8,       113,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       114,         1,    []byte{0x19}},
    entry{"Reserved",                               INT8,       115,         1,    []byte{0x00}},
    entry{"Warning Thresh",                         INT8,       116,         2,    []byte{0x00, 0x35}},
    entry{"OverTemp Thresh",                        INT8,       118,         2,    []byte{0x00, 0x34}},
    entry{"VU Cap ID",                              INT8,       120,         2,    []byte{0xA2, 0x00}},
    entry{"Next Cap Address",                       INT8,       122,         2,    []byte{0x00, 0x00}},
    entry{"Sensor Type",                            INT8,       124,         1,    []byte{0x51}},
    entry{"Sensor Address",                         INT8,       125,         1,    []byte{0x94}},
    entry{"Sensor #1 Address Offset",               INT8,       126,         1,    []byte{0x1A}},
    entry{"Reserved",                               INT8,       127,         1,    []byte{0x00}},
    entry{"Warning Thresh",                         INT8,       128,         2,    []byte{0x00, 0x37}},
    entry{"OverTemp Thresh",                        INT8,       130,         2,    []byte{0x00, 0x36}},
    entry{"PAD",                                    STRING,      132,        124,  []byte{0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  }},
    entry{"Common Format Version",                  INT8,        256,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        257,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        258,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        259,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        260,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        261,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        262,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        263,        1,    []byte{0x00}},
    entry{"Board Info Format Version",              INT8,        264,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        265,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        266,        1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        267,        3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        270,        1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      271,        8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        279,        1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      280,        33,   []byte{0x44, 0x53, 0x43, 0x32, 0x2d, 0x32, 0x30, 0x30, 
                                                                                          0x20, 0x41, 0x44, 0x49, 0x20, 0x32, 0x78, 0x32, 
                                                                                          0x30, 0x30, 0x47, 0x62, 0x45, 0x20, 0x44, 0x75, 
                                                                                          0x61, 0x6c, 0x20, 0x51, 0x53, 0x46, 0x50, 0x35,
                                                                                          0x36}},
    entry{"PAD",                                    STRING,      313,        7,    []byte{0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        320,        1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      321,        11,   []byte{0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                                                                                          0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        332,        1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      333,        23,   []byte{0x44, 0x53, 0x43, 0x32, 0x2D, 0x32, 0x51, 0x32, 
                                                                                          0x30, 0x30, 0x2D, 0x33, 0x32, 0x52, 0x33, 0x32, 
                                                                                          0x46, 0x36, 0x34, 0x50, 0x2D, 0x52, 0x32}},
    entry{"PAD",                                    STRING,      356,        2,    []byte{0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,        358,        1,    []byte{0xC8}},
    entry{"02/19/21",                               STRING,      359,        8,    []byte{0x30, 0x32, 0x2f, 0x31, 
        0x39, 0x2f, 0x32, 0x31}},
    entry{"Board ID Type/Length",                   INT8,        367,        1,    []byte{0x04}},
    entry{"Board ID",                               INT8,        368,        4,    []byte{0x06, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,        372,        1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,        373,        2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,        375,        1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,        376,        2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,        378,        1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,        379,        6,    []byte{0x00, 0xAE, 0xCD, 0x00, 0x00, 
         0x00}},
    entry{"Assembly Number Type/Length",            INT8,        385,        1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,      386,        13,   []byte{0x36, 0x38, 0x2D, 0x30, 0x30, 0x32, 0x36, 0x2D, 
                                                                                          0x30, 0x31, 0x20, 0x30, 0x31}},
    entry{"End of Field",                           INT8,        399,        1,    []byte{0xC1}},
    entry{"PAD",                                    STRING,      400,        7,    []byte{0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,        407,        1,    []byte{0x00}},
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
    entry{"HPE Serial Number",                      STRING,     186,        10, []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"PCA Product Number Type/Length",         INT8,       196,        1,  []byte{0xCA}},
    entry{"HPE Product Number",                     STRING,     197,        10, []byte{0x50, 0x31, 0x38, 0x36,
        0x36, 0x39, 0x2D, 0x30, 0x30, 0x31}},
    entry{"FRU File ID Type/Length",                INT8,       207,        1,  []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     208,        8,  []byte{0x30, 0x36, 0x2F, 0x32,
        0x34, 0x2F, 0x31, 0x39}},
    entry{"OEM Revision Type/Length",               INT8,       216,        1,  []byte{0x3}},
    entry{"HP OEM Record ID",                       INT8,       217,        1,  []byte{0xD2}},
    entry{"Revision Code",                          STRING,     218,        2,  []byte{0x30, 0x42}},
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


var OrtanoPensandoTbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      24,      40,    []byte{0x44, 0x53, 0x43, 0x32, 
        0x2d, 0x32, 0x30, 0x30, 0x2c, 0x32, 0x78, 0x51, 0x53, 0x46, 
        0x50, 0x35, 0x36, 0x2c, 0x33, 0x32, 0x67, 0x52, 0x41, 0x4d, 
        0x2c, 0x36, 0x34, 0x47, 0x65, 0x4d, 0x4d, 0x43, 0x20, 0x20, 
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        64,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      65,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        76,       1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      77,       25,   []byte{0x44, 0x53, 0x43, 0x32, 
        0x2d, 0x32, 0x51, 0x32, 0x30, 0x30, 0x2d, 0x33, 0x32, 0x52, 
        0x33, 0x32, 0x46, 0x36, 0x34, 0x50, 0x20, 0x20, 0x20, 0x20, 
        0x20}},
    entry{"FRU File ID Type/Length",                INT8,       102,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     103,       8,    []byte{0x30, 0x34, 0x2f, 0x30, 
        0x36, 0x2f, 0x32, 0x31}},
    entry{"Board ID Type/Length",                   INT8,       111,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       112,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       116,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       117,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       119,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       120,       2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       122,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       123,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       129,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,     130,      13,    []byte{0x36, 0x38, 0x2d, 0x30, 
        0x30, 0x32, 0x31, 0x2d, 0x30, 0x32, 0x20, 0x30, 0x31}}, 
    entry{"End of Field",                           INT8,       143,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       144,       7,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       151,       1,    []byte{0x00}},
}

var OrtanoIBMTbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x65, 0x6E, 0x73, 0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      24,      40,    []byte{0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        64,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      65,       11,   []byte{0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20}},
    entry{"Part Number Type/Length",                INT8,        76,       1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      77,       25,   []byte{0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20}},
    entry{"FRU File ID Type/Length",                INT8,       102,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     103,       8,    []byte{0x30, 0x34, 0x2f, 0x30, 0x36, 0x2f, 0x32, 0x31}},
    entry{"Board ID Type/Length",                   INT8,       111,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       112,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       116,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       117,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       119,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       120,       2,    []byte{0x18, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       122,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       123,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       129,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,     130,      13,    []byte{0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                                                                                        0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"End of Field",                           INT8,       143,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       144,       7,    []byte{0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       151,       1,    []byte{0x00}},
}

var OrtanoTaorminaTbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      24,      40,    []byte{        
        0x44, 0x53, 0x53, 0x2d, 0x34, 0x38, 0x78, 0x32, 0x35, 0x47,                     //DSS-48x25G-6x100G
        0x2d, 0x36, 0x78, 0x31, 0x30, 0x30, 0x47, 0x20, 0x20, 0x20, 
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        64,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      65,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        76,       1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      77,       25,   []byte{
        0x44, 0x53, 0x53, 0x2d, 0x34, 0x38, 0x32, 0x35, 0x2d, 0x36,                      //DSS-4825-6100
        0x31, 0x30, 0x30, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,       102,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     103,       8,    []byte{0x30, 0x36, 0x2f, 0x30, 
        0x34, 0x2f, 0x32, 0x31}},
    entry{"Board ID Type/Length",                   INT8,       111,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       112,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       116,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       117,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       119,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       120,       2,    []byte{0x10, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       122,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       123,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       129,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,     130,      13,    []byte{0x36, 0x38, 0x2d, 0x30, 
        0x30, 0x31, 0x38, 0x2d, 0x30, 0x31, 0x20, 0x30, 0x31}}, 
    entry{"End of Field",                           INT8,       143,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       144,       7,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       151,       1,    []byte{0x00}},
}


//For Elba FRU on Cisco MtFuji switch
var MtFujiElba = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x43, 0x49, 0x53, 0x43, 0x4F, 0x20, 0x20, 0x20}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      24,      40,    []byte{
        0x4D, 0x54, 0x46, 0x55, 0x4A, 0x49, 0x20, 0x20, 0x20, 0x20,                        //MTFUJI
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        64,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      65,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        76,       1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      77,       25,   []byte{
        0x44, 0x53, 0x53, 0x2D, 0x4D, 0x54, 0x46, 0x55, 0x4A, 0x49,                       //DSS-MTFUJI
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,       102,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     103,       8,    []byte{0x31, 0x32, 0x2F, 0x30, 0x34, 0x2F, 0x32, 0x33}},
    entry{"Board ID Type/Length",                   INT8,       111,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       112,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       116,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       117,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       119,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       120,       2,    []byte{0x10, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       122,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       123,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       129,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,     130,      13,    []byte{0x37, 0x33, 0x2D, 0x32, 
        0x31, 0x34, 0x30, 0x33, 0x2D, 0x30, 0x31, 0x20, 0x20}}, 
    entry{"End of Field",                           INT8,       143,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       144,       7,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       151,       1,    []byte{0x00}},
}

var OrtanoLipariTbl = []entry {
    entry{"Common Format Version",                  INT8,        0,        1,    []byte{0x01}},
    entry{"Internal Use Area Offset",               INT8,        1,        1,    []byte{0x00}},
    entry{"Chassis Area Offset",                    INT8,        2,        1,    []byte{0x00}},
    entry{"Board Info Offset",                      INT8,        3,        1,    []byte{0x01}},
    entry{"Product Area Offset",                    INT8,        4,        1,    []byte{0x00}},
    entry{"Multi-Record Area Offset",               INT8,        5,        1,    []byte{0x00}},
    entry{"PAD",                                    INT8,        6,        1,    []byte{0x00}},
    entry{"Common Header Checksum",                 INT8,        7,        1,    []byte{0x00}},

    entry{"Board Info Format Version",              INT8,        8,        1,    []byte{0x01}},
    entry{"Board Area Length",                      INT8,        9,        1,    []byte{0x12}},
    entry{"Language Code",                          INT8,        10,       1,    []byte{0x19}},
    entry{"Manufacturing Date/Time",                INT8,        11,       3,    []byte{0x00, 0x00, 0x00}},
    entry{"Manufacturing Type/Length",              INT8,        14,       1,    []byte{0xC8}},
    entry{"Manufacturer",                           STRING,      15,       8,    []byte{0x50, 0x65, 0x6E, 0x73,
        0x61, 0x6E, 0x64, 0x6F}},
    entry{"Product Name Type/Length",               INT8,        23,       1,    []byte{0xE8}},
    entry{"Product Name",                           STRING,      24,      40,    []byte{
        0x44, 0x53, 0x53, 0x2D, 0x32, 0x38, 0x34, 0x30, 0x30, 0x20,                         //DSS-28400
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        64,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      65,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        76,       1,    []byte{0xD9}},
    entry{"Part Number",                            STRING,      77,       25,   []byte{
        0x44, 0x53, 0x53, 0x2D, 0x32, 0x38, 0x34, 0x30, 0x30, 0x20,                         //DSS-28400   
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20}},
    entry{"FRU File ID Type/Length",                INT8,       102,       1,    []byte{0xC8}},
    entry{"FRU ID",                                 STRING,     103,       8,    []byte{0x30, 0x36, 0x2f, 0x30, 
        0x34, 0x2f, 0x32, 0x31}},
    entry{"Board ID Type/Length",                   INT8,       111,       1,    []byte{0x04}},
    entry{"Board ID",                               INT8,       112,       4,    []byte{0x01, 0x00, 0x00, 0x00}},
    entry{"Engineering Change Level Type/Length",   INT8,       116,       1,    []byte{0xC2}},
    entry{"Engineering Change Level",               INT8,       117,       2,    []byte{0x00, 0x00}},
    entry{"Number of MAC Address Type/Length",      INT8,       119,       1,    []byte{0x02}},
    entry{"Number of MAC Address",                  INT8,       120,       2,    []byte{0x10, 0x00}},
    entry{"MAC Address Base Type/Length",           INT8,       122,       1,    []byte{0x06}},
    entry{"MAC Address Base",                       INT8,       123,       6,    []byte{0x00, 0xAE, 0xCD, 0x00, 
        0x00, 0x00}},
    entry{"Assembly Number Type/Length",            INT8,       129,       1,    []byte{0xCD}},
    entry{"Assembly Number",                        STRING,     130,      13,    []byte{0x36, 0x38, 0x2d, 0x30, 
        0x30, 0x33, 0x32, 0x2d, 0x30, 0x31, 0x20, 0x30, 0x31}}, 
    entry{"End of Field",                           INT8,       143,       1,    []byte{0xC1}},
    entry{"PAD",                                    INT8,       144,       7,    []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00}},
    entry{"Board Info Area Checksum",               INT8,       151,       1,    []byte{0x00}},
}


// Copy from Naples100Tbl, the same as Naples25 defined in:
// https://docs.google.com/spreadsheets/d/1lR_cD-IFT1vVWQT7m450V6-KdOdGaRXr/edit#gid=1562718635
var MtpOcpAdapTbl = []entry {
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
    entry{"Product Name",                           STRING,       37,       10,   []byte{0x4F, 0x43, 0x50, 0x41,
        0x64, 0x61, 0x70, 0x74, 0x65, 0x72}},
    entry{"Reserved",                               STRING,      47,       6,    []byte{0x20, 0x20, 0x20, 0x20,
        0x20, 0x20}},
    entry{"Serial Number Type/Length",              INT8,        53,       1,    []byte{0xCB}},
    entry{"Serial Number",                          STRING,      54,       11,   []byte{0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},
    entry{"Part Number Type/Length",                INT8,        65,       1,    []byte{0xCD}},
    entry{"Part Number",                            STRING,      66,       13,   []byte{0x37, 0x33, 0x2D, 0x30,
        0x30, 0x32, 0x34, 0x2D, 0x30, 0x33, 0x20, 0x30, 0x33}},
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


var MatchSearchBIA []byte
var MatchSearchEEread byte

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
var HpeLacona uint
var DellOcp uint
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
    DellOcp = 0
    I2cAddr16 = false

    MatchSearchBIA = make([]byte, 512)
    MatchSearchEEread = 0
}

func HasAssemblyEntry() (hasAssembly bool) {
    hasAssembly = false

    if CustType == "IBM"            ||
       CustType == "ORACLE"         ||
       CustType == "ORTANO"         ||
       CustType == "PENORTANO"      ||
       CustType == "DELLSWM"        ||
       CustType == "DELLNAPLES100"  ||
       CustType == "DELLOCP"        ||
       CustType == "PENSWM"         ||
       //CustType == "LACONA32DELL"   ||    //DELL 32G LACONA AND POMONTE HAVE AN ASSEMBLY FIELD, BUT IT IS NOT USED 
       //CustType == "POMONTEDELL"    ||    //DELL 32G LACONA AND POMONTE HAVE AN ASSEMBLY FIELD, BUT IT IS NOT USED 
       CustType == "LACONADELL" {

        hasAssembly = true

    }
    return
}

func writeField(devName string, offset int, numBytes int, data []byte) (err int) {
    var writeData byte

    if numBytes < len(data) {
        err = errType.INVALID_PARAM
        cli.Println("f", "Offset=", offset, "data length more than number of bytes! numBytes:", numBytes, "data length:", len(data))
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


    //Set Write Protect Bit from the Micro-controller to low on DPU's in Panarea MTP
    if os.Getenv("CARD_TYPE") == "MTP_PANAREA" && (bus > 2 && bus < 13) {
        cli.Printf("i", "Removing eeprom write protect");
        err = sucuart.Suc_exec_cmds(int(bus-2), "gpio conf pb 2 o0")
        if err != errType.SUCCESS {
           cli.Printf("e", "ERROR: Failed to disable the eeprom write protect bit on the SuC")
            return
        }
    }
    //Set Write Protect Bit from the Micro-controller to low on Vulsei boards in Ponza MTP
    if os.Getenv("CARD_TYPE") == "MTP_PONZA" && (bus > 2 && bus < 9) {
        cli.Printf("i", "Removing eeprom write protect");
        err = sucuart.Suc_exec_cmds(int(bus-2), "gpio conf pe 3 o0")
        if err != errType.SUCCESS {
           cli.Printf("e", "ERROR: Failed to disable the eeprom write protect bit on the SuC")
            return
        }
    }
    //For Vulcano Asic based platfrom to blank out the Microcontroller fru stored in it's flash
    if devName == "SUCFRU" {
        var Length int = 378
        fmt.Printf("WRITE TO SUC Microcontroller  Bus=%d  Len=%d\n", bus, len(Data));
        i2cinfo.SwitchI2cTbl("UUT_NONE")
        fmt.Printf("TBL LEN=%d\n", Length);
        for i:=0; i<Length; i++ {
            command := fmt.Sprintf("fru write %d hex %x", i, 0xFF)
            fmt.Printf("%s\n", command);
            sucuart.Suc_exec_cmds(int(bus-2), command)
        }
        sucuart.Suc_exec_cmds(int(bus-2), "fru save")
        return
    } 

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
    var multiRecordNumber uint32 = 0;
    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()
    is8g := 0
    for _, entry := range(EepromTbl) {
        if entry.Name == "Product Area Offset" {
            if HpeNaples == 1 {
                copy(entry.Value, []byte{0x10})
            }
        }
        if entry.Name == "Product Name" {
            
            if CardType == "NAPLES25" {
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
             (HpeOcp == 1) ) {
            if entry.Value[6] == byte(0x38) {
                 is8g = 1
            }
        }
        if entry.Name == "Board ID" {
            if (CardType == "NAPLES25")    ||
               (HpeOcp == 1) ||
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

        //For Pomonta and Lacona for Dell, need to copy the mac address into the mrec in little endian order
        if (CardType == "LACONA32DELL" || (CardType == "POMONTEDELL")) { 
            if entry.Name == "LE MAC Address Base" {
                for _, tblEntry := range(EepromTbl) {
                    if tblEntry.Name == "MAC Address Base" {
                        for j:=0;j<6;j++ {
                            entry.Value[5-j] = tblEntry.Value[j]
                        }
                        break
                    }
                }
            }
        }
    }

    for _, entry := range(EepromTbl) {
        if entry.Name == "Board Info Area Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - brdInfoChk % 0x100)
        } else if entry.Name == "Common Header Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - cmnHeadChk % 0x100)
        } else if entry.Name == "Product info Area Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - productInfoChk % 0x100)
        } else if entry.Name == "Record Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - mraChk[multiRecordNumber] % 0x100)
            //fmt.Printf("RECORD [%d] = %x\n", multiRecordNumber, mraChk[multiRecordNumber]) 
            updateIntChk() //Have it go re-calculate the header checksum now that the record checksum is in place
        } else if entry.Name == "Header Checksum" {
            updateIntChk()
            entry.Value[0] = byte(0x100 - mraHdrChk[multiRecordNumber] % 0x100)
            //fmt.Printf("HEADER [%d] = %x\n", multiRecordNumber, mraHdrChk[multiRecordNumber]) 
            multiRecordNumber++
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
    if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 || HpeLacona == 1 {
        for _, entry := range(EepromExtTbl) {
            if entry.Name == "Product info Area Checksum" || entry.Name == "HPE Multi-Record Area Checksum" {
                updateIntChk()
                entry.Value[0] = byte(0x100 - productInfoChk % 0x100)
            } else if entry.Name == "Record Checksum" {
                updateIntChk()
                entry.Value[0] = byte(0x100 - mraChk[multiRecordNumber] % 0x100)
                //fmt.Printf("RECORD [%d] = %x\n", multiRecordNumber, mraChk[multiRecordNumber]) 
                updateIntChk() //Have it go re-calculate the header checksum now that the record checksum is in place
            } else if entry.Name == "Header Checksum" {
                updateIntChk()
                entry.Value[0] = byte(0x100 - mraHdrChk[multiRecordNumber] % 0x100)
                //fmt.Printf("HEADER [%d] = %x\n", multiRecordNumber, mraHdrChk[multiRecordNumber]) 
                multiRecordNumber++
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
        hasAssembly := HasAssemblyEntry()
        for _, entry := range(EepromTbl) {
            if hasAssembly == false {
                if entry.Name == "Part Number" {
                    pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, pn)
                    continue
                }
            }
            if hasAssembly == true {
                if entry.Name == "Assembly Number" {
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
            } 
        }

        if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 || HpeLacona == 1 {
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
                } else if entry.Name == "HPE Product Number" && HpeNaples == 1 {
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
    if HpeNaples == 1 {
        for _, entry := range(EepromExtTbl) {
            if (entry.Offset > 127) && (entry.Offset < 247) {
                productInfoChk += calcSum(entry)
            }
        }
    }
    if ((HpeSwm == 1) || (HpeOcp == 1) || (CustType == "PENSWM") || (HpeLacona == 1)) {
        brdInfoChk = 0
        productInfoChk = 0;
        cmnHeadChk = 0
        var biaOff, piaOff, cHdrLen, biaLen, piaLen int = 0, 0, 8, 0, 0

        for _, entry := range(EepromTbl) {
            if entry.Name == "Board Info Offset" {
                biaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Product Area Offset" {
                piaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Board Area Length" {
                biaLen = int(entry.Value[0]) * 8
            }
        }
        for _, entry := range(EepromExtTbl) {
            if entry.Name == "Product Area Length" {
                piaLen = int(entry.Value[0]) * 8
            }
        }
        for _, entry := range(EepromTbl) {
            if (entry.Offset >= 0) && (entry.Offset < (cHdrLen - 1)) {      //common header
                cmnHeadChk += calcSum(entry)
            } else if (entry.Offset > (biaOff - 1)) && (entry.Offset < (biaLen + cHdrLen - 1)) {  //board info area
                brdInfoChk += calcSum(entry)
            }
        }
        for _, entry := range(EepromExtTbl) {
            if (entry.Offset > (piaOff - 1)) && (entry.Offset < (piaOff + piaLen - 1)) {  //product info area
                productInfoChk += calcSum(entry)
            }
        }
    }

    //calc multi-record checksum.  BIA + PIA checksum is calculated above
    if HpeLacona == 1 {
        //Calculate multi-record checksum
        for _, entry := range(EepromExtTbl) {
            if (entry.Offset > 228) && (entry.Offset < 265) {
                mraChk[0] += calcSum(entry)
                //fmt.Printf(" mraChk Name -> %s [0x%.02x]   HDRCHKSUM=%x\n", entry.Name, entry.Offset, mraChk[0])
            }
        }
        


        //Calculate multi-record header checksum
        for _, entry := range(EepromExtTbl) {
            if (entry.Offset > 223) && (entry.Offset < 228) {
                mraHdrChk[0] += calcSum(entry)
                //fmt.Printf(" mraHdrChk Name -> %s [0x%.02x]   HDRCHKSUM=%x\n", entry.Name, entry.Offset, mraHdrChk[0])
            }
        }
    }

    if DellOcp == 1 {
        brdInfoChk = 0
        productInfoChk = 0
        cmnHeadChk = 0
        var biaOff, piaOff, cHdrLen, biaLen, piaLen int = 0, 0, 8, 0, 0

        for i:=0; i<len(mraHdrChk); i++ {
            mraChk[i] = 0
            mraHdrChk[i] = 0
        }

        for _, entry := range(EepromTbl) {
            if entry.Name == "Board Info Offset" {
                biaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Product Area Offset" {
                piaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Board Area Length" {
                biaLen = int(entry.Value[0]) * 8
            }
            if entry.Name == "Product Area Length" {
                piaLen = int(entry.Value[0]) * 8
            }
        }
        for _, entry := range(EepromTbl) {
            if (entry.Offset >= 0) && (entry.Offset < (cHdrLen - 1)) {      //common header
                cmnHeadChk += calcSum(entry)
            } else if (entry.Offset > (biaOff - 1)) && (entry.Offset < (biaLen + cHdrLen - 1)) {  //board info area
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset > (piaOff - 1)) && (entry.Offset < (piaOff + piaLen - 1)) {  //product info area
                productInfoChk += calcSum(entry)
            }
        }
        //Calculate multi-record checksum
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 316) && (entry.Offset < 365) {
                mraChk[0] += calcSum(entry)
            }
            if (entry.Offset > 369) && (entry.Offset < 395) {
                mraChk[1] += calcSum(entry)
            }
            if (entry.Offset > 399) && (entry.Offset < 415) {
                mraChk[2] += calcSum(entry)
            }
            if (entry.Offset > 419) && (entry.Offset < 430) {
                mraChk[3] += calcSum(entry)
            }
        }


        //Calculate multi-record header checksum
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 311) && (entry.Offset < 316) {
                mraHdrChk[0] += calcSum(entry)
                //fmt.Printf(" MRH CSUM Name -> %s [0x%.02x]   HDRCHKSUM=%x\n", entry.Name, entry.Offset, mraHdrChk[0])
            }
            if (entry.Offset > 364) && (entry.Offset < 369) {
                mraHdrChk[1] += calcSum(entry)
                //fmt.Printf(" MRH CSUM Name -> %s [0x%.02x]   HDRCHKSUM=%x\n", entry.Name, entry.Offset, mraHdrChk[1])
            }
            if (entry.Offset > 394) && (entry.Offset < 399) {
                mraHdrChk[2] += calcSum(entry)
                //fmt.Printf(" MRH CSUM Name -> %s [0x%.02x]   HDRCHKSUM=%x\n", entry.Name, entry.Offset, mraHdrChk[2])
            }
            if (entry.Offset > 414) && (entry.Offset < 419) {
                mraHdrChk[3] += calcSum(entry)
                //fmt.Printf(" MRH CSUM Name -> %s [0x%.02x]   HDRCHKSUM=%x\n", entry.Name, entry.Offset, mraHdrChk[2])
            }
        }
    }

    if CustType == "LACONADELL" {
        brdInfoChk = 0
        productInfoChk = 0
        cmnHeadChk = 0
        var biaOff, piaOff, cHdrLen, biaLen, piaLen int = 0, 0, 8, 0, 0

        for i:=0; i<len(mraHdrChk); i++ {
            mraChk[i] = 0
            mraHdrChk[i] = 0
        }

        for _, entry := range(EepromTbl) {
            if entry.Name == "Board Info Offset" {
                biaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Product Area Offset" {
                piaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Board Area Length" {
                biaLen = int(entry.Value[0]) * 8
            }
            if entry.Name == "Product Area Length" {
                piaLen = int(entry.Value[0]) * 8
            }
        }
        for _, entry := range(EepromTbl) {
            if (entry.Offset >= 0) && (entry.Offset < (cHdrLen - 1)) {      //common header
                cmnHeadChk += calcSum(entry)
            } else if (entry.Offset > (biaOff - 1)) && (entry.Offset < (biaLen + cHdrLen - 1)) {  //board info area
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset > (piaOff - 1)) && (entry.Offset < (piaOff + piaLen - 1)) {  //product info area
                productInfoChk += calcSum(entry)
            }
        }

        //Calculate multi-record checksum
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 316) && (entry.Offset < 342) {
                mraChk[0] += calcSum(entry)
            }
            if (entry.Offset > 346) && (entry.Offset < 362) {
                mraChk[1] += calcSum(entry)
            }
            if (entry.Offset > 366) && (entry.Offset < 377) {
                mraChk[2] += calcSum(entry)
            }
            if (entry.Offset > 381) && (entry.Offset < 391) {
                mraChk[3] += calcSum(entry)
            }
        }

        //Calculate multi-record header checksum
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 311) && (entry.Offset < 316) {
                mraHdrChk[0] += calcSum(entry)
            }
            if (entry.Offset > 341) && (entry.Offset < 346) {
                mraHdrChk[1] += calcSum(entry)
            }
            if (entry.Offset > 361) && (entry.Offset < 366) {
                mraHdrChk[2] += calcSum(entry)
            }
            if (entry.Offset > 376) && (entry.Offset < 381) {
                mraHdrChk[3] += calcSum(entry)
            }
        }
    }

    if CustType == "LACONA32DELL" || CustType == "POMONTEDELL" {
        brdInfoChk = 0
        productInfoChk = 0
        cmnHeadChk = 0
        var biaOff, piaOff, cHdrLen, biaLen, piaLen int = 0, 0, 8, 0, 0

        for i:=0; i<len(mraHdrChk); i++ {
            mraChk[i] = 0
            mraHdrChk[i] = 0
        }

        for _, entry := range(EepromTbl) {
            if entry.Name == "Board Info Offset" {
                biaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Product Area Offset" {
                piaOff = int(entry.Value[0]) * 8
            }
            if entry.Name == "Board Area Length" {
                biaLen = int(entry.Value[0]) * 8
            }
            if entry.Name == "Product Area Length" {
                piaLen = int(entry.Value[0]) * 8
            }
        }
        for _, entry := range(EepromTbl) {
            if (entry.Offset >= 0) && (entry.Offset < (cHdrLen - 1)) {      //common header
                cmnHeadChk += calcSum(entry)
            } else if (entry.Offset > (biaOff - 1)) && (entry.Offset < (biaLen + cHdrLen - 1)) {  //board info area
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset > (piaOff - 1)) && (entry.Offset < (piaOff + piaLen - 1)) {  //product info area
                productInfoChk += calcSum(entry)
            }
        }
        //Calculate multi-record checksum
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 292) && (entry.Offset < 318) {
                mraChk[0] += calcSum(entry)
            }
            if (entry.Offset > 322) && (entry.Offset < 338) {
                mraChk[1] += calcSum(entry)
            }
            if (entry.Offset > 342) && (entry.Offset < 353) {
                mraChk[2] += calcSum(entry)
            }
            if (entry.Offset > 357) && (entry.Offset < 373) {
                mraChk[3] += calcSum(entry)
            }
        }

        //Calculate multi-record header checksum
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 287) && (entry.Offset < 292) {
                mraHdrChk[0] += calcSum(entry)
            }
            if (entry.Offset > 317) && (entry.Offset < 322) {
                mraHdrChk[1] += calcSum(entry)
            }
            if (entry.Offset > 337) && (entry.Offset < 342) {
                mraHdrChk[2] += calcSum(entry)
            }
            if (entry.Offset > 352) && (entry.Offset < 357) {
                mraHdrChk[3] += calcSum(entry)
            }
        }
    }

    if CustType == "IBM" || CustType == "DELLSWM" || CustType == "DELLNAPLES100" || CustType == "PENORTANO" {
        brdInfoChk = 0
        productInfoChk = 0
        cmnHeadChk = 0
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 7) && (entry.Offset < 151) {
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset >= 0) && (entry.Offset < 7) {
                cmnHeadChk += calcSum(entry)
            }
        }
    }

    if CustType == "ORACLE" || CustType == "ORTANO" {
        brdInfoChk = 0
        productInfoChk = 0
        cmnHeadChk = 0
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 263) && (entry.Offset < 406) {
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset >= 256) && (entry.Offset < 263) {
                cmnHeadChk += calcSum(entry)
            }
        }
    }

    if CustType == "HPE" {
        brdInfoChk = 0
        productInfoChk = 0
        cmnHeadChk = 0
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 7) && (entry.Offset < 127) {
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset > 127) && (entry.Offset < 215) {
                productInfoChk += calcSum(entry)
            } else if (entry.Offset >= 0) && (entry.Offset < 7) {
                cmnHeadChk += calcSum(entry)
            }
        }
    }

    if CustType == "HPE100CLOUD" {
        brdInfoChk = 0
        productInfoChk = 0
        cmnHeadChk = 0
        for _, entry := range(EepromTbl) {
            if (entry.Offset > 7) && (entry.Offset < 127) {
                brdInfoChk += calcSum(entry)
            } else if (entry.Offset > 127) && (entry.Offset < 223) {
                productInfoChk += calcSum(entry)
            } else if (entry.Offset >= 0) && (entry.Offset < 7) {
                cmnHeadChk += calcSum(entry)
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
        hasAssembly := HasAssemblyEntry()
        for _, entry := range(EepromTbl) {
            if hasAssembly == false {
                if entry.Name == "Part Number" {
                    pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, pn)
                    continue
                }
            } else {
                if entry.Name == "Assembly Number" {
                    pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                    copy(entry.Value, pn)
                    continue
                }
            }

            if entry.Name == "Serial Number" {
                // Not a good solution to set SN padding
                var snInitVal byte
                if CustType == "ORACLE" || CustType == "ORTANO" || CustType == "PENORTANO"  {
                    snInitVal = 0x20
                } else {
                    snInitVal = 0x0
                }
                for i := range entry.Value {
                    entry.Value[i] = snInitVal
                }

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

        if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 || HpeLacona == 1 {
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
                } else if entry.Name == "HPE Product Number" && HpeNaples == 1 {
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
    var an_ptr []byte
    var pn_ptr []byte

    if len(pn) > 13 {
        cli.Println("f", "PN too long: ", pn)
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
            if entry.Name == "Part Number" {
                pn_ptr = entry.Value
                //copy(entry.Value, pn)
                continue
            } else if entry.Name == "Serial Number" {
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
            } else if entry.Name == "Assembly Number" {
                an_ptr = entry.Value
                continue
            }
        }

        hasAssembly := HasAssemblyEntry()
        if hasAssembly == true {
            copy(an_ptr, pn)
        } else {
            copy(pn_ptr, pn)
        }

        if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 || HpeLacona == 1 {
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
                } else if entry.Name == "HPE Product Number" && HpeNaples == 1 {
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
    hasAssembly := HasAssemblyEntry()
    for _, entry := range(EepromTbl) {

        if hasAssembly == false {
            if entry.Name == "Part Number" {
                pn, _ := readField(devName, entry.Offset, entry.NumBytes)
                copy(entry.Value, pn)
                continue
            }
        }else {
            if entry.Name == "Assembly Number" {
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
        } 
    }

    if HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 || HpeLacona == 1 {
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
            } else if entry.Name == "HPE Product Number" && HpeNaples == 1 {
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
        if ((HpeNaples == 1) && (field != "ALL")) {
            continue
        }

        if(field == "SN") {
            if entry.Name != "Serial Number" {
                continue
            }
        } else if(field == "MAC") {
            if entry.Name != "MAC Address Base" {
                continue
            }
        } else if(field == "PN") {
            hasAssembly := HasAssemblyEntry()
            if hasAssembly == true {
                if entry.Name != "Assembly Number" {
                    continue
                }
            } else if ( entry.Name != "Part Number" ) {
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
            } else if entry.Name == "LE MAC Address Base" {
                outStr = fmt.Sprintf(fmtMac, entry.Name, data[0], data[1], data[2], data[3], data[4], data[5])
            } else if entry.Name == "Class Code" {
                outStr = fmt.Sprintf("%-45s0x%02X%02X%02X", entry.Name, data[2], data[1], data[0]) 
            } else if entry.Name == "PCI-SIG Vendor ID" {
                outStr = fmt.Sprintf("%-45s0x%02X%02X", entry.Name, data[1], data[0]) 
            } else if entry.Name == "Cap List Pointer" {
                outStr = fmt.Sprintf("%-45s0x%02X%02X", entry.Name, data[1], data[0]) 
            } else {
                outStr = fmt.Sprintf(fmtHex, entry.Name, data)
            }
        }
        cli.Println("i", outStr)
    }

    if (HpeNaples == 1 || HpeOcp == 1 || HpeSwm == 1 || HpeLacona == 1) {
        fmt.Println()
        for _, entry := range(EepromExtTbl) {
            if ((HpeNaples != 1) && (field != "ALL")) {
                continue;
            }

            //For Naples25 HPE.  ICT programs these fields which need to be read out to program entire FRU
            if ((HpeNaples == 1) && (field != "ALL")) {
                if(field == "SN") {
                    if entry.Name != "HPE Serial Number" {
                        continue
                    }
                } else if(field == "MAC") {
                    if entry.Name != "MAC Address Base" {
                        continue
                    }
                } else if(field == "PN") {
                    if ( entry.Name != "HPE Product Number" ) {
                        continue
                    }
                }
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
                if entry.Name == "Manufacture Date/Time" {
                    start := time.Date(1996, 1, 1, 0, 0, 0, 0, time.UTC)
                    minutes := int((int(data[2]) * 0x10000) + (int(data[1]) * 0x100) + int(data[0]))
                    now := start.Add(time.Minute * time.Duration(minutes))
                    year, month, day := now.Date()
                    date := fmt.Sprintf("%02d/%02d/%02d", int(month), int(day), (int(year) % 100))
                    outStr = fmt.Sprintf(fmtDate, entry.Name, data[2], data[1], data[0], date)
                } else if entry.Name == "MAC Address Base" {
                    outStr = fmt.Sprintf(fmtMac, entry.Name, data[0], data[1], data[2], data[3], data[4], data[5])
                } else if entry.Name == "LE MAC Address Base" {
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

func DumpEeprom(devName string, bus uint32, devAddr byte, numBytes int, fname string, toFile bool) (output []byte, err int) {
    var f *os.File
    var err_ error
    var data []byte
    rdData := []byte{}

    if devName == "CPLD_FRU" {
        var errGo error
        i2cinfo.SwitchI2cTbl("UUT_NONE")
        rdData, errGo = materafpga.Spi_cpldX03_read_flash(uint32(bus-3), "ufm2", 0x00, uint32(MAX_BYTES))
        if errGo != nil {
            err = errType.FAIL 
            return 
        }
    } else {
        err = smbusNew.Open(devName, bus, devAddr)
        if err != errType.SUCCESS {
            return
        }
        for i := 0; i < numBytes; i++ {
            data, err = readField(devName, i, 1)
            if err != errType.SUCCESS {
                cli.Println("f", "Failed to read field at offset", i)
                smbusNew.Close()
                return
            }
            rdData = append(rdData, data...)
        }
        smbusNew.Close()
    }

    if toFile == true {
        f, err_ = os.OpenFile(fname, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0600)
        if err_ != nil {
            cli.Println("e", "file create failed. Filename:", fname)
            return nil, -1
        }
        cli.Println("i", "dump FRU to file", fname)
        f.WriteString(string(rdData[:]))
        f.Close()
        cli.Println("i", "EEPROM: dumped", numBytes, "bytes to file", fname)
    }

    return

}


func MatchSearchFruPartnumber(devName string, bus uint32, devAddr byte, pn string) (err int) {
    var rdLength int = 256

    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()

    if (CardType == "ORTANO2" || CardType == "ORTANO2A" || CardType == "ORTANO2I") {
        cli.Println("i", "Adjust read lenghth for Ortano2/2A/2I")
        rdLength = 512
    }

    //Read out 256 bytes.. should be enough to get the part number
    //128 would be enough but Oracle starts their BIA at offset 128
    if(MatchSearchEEread==0) {
        for i := 0; i < rdLength; i++ {
            if I2cAddr16 == true {
                MatchSearchBIA[i], err = smbusNew.I2C16ReadByte(devName, uint16(i))
            } else {
                MatchSearchBIA[i], err = smbusNew.ReadByte(devName, uint64(i))
            }
            if err != errType.SUCCESS {
                return -1
            }
        }
    }
    MatchSearchEEread=1

    res := strings.Index(string(MatchSearchBIA), pn)
    if res > 0 {
        return errType.SUCCESS
    }
    return errType.FAIL
}

func GetFruPartnumber(devName string, bus uint32, devAddr byte, pn []uint8) (err int) {
    BIA := make([]byte, 128)
    var offset uint16 = 0
    var BoardInfoAreaOff byte = 0
    var i int = 0

    err = smbusNew.Open(devName, bus, devAddr)
    if err != errType.SUCCESS {
        return
    }
    defer smbusNew.Close()
    
    //Get board info area offset
    if I2cAddr16 == true {
        BoardInfoAreaOff, err = smbusNew.I2C16ReadByte(devName, uint16(0x03))
    } else {
        BoardInfoAreaOff, err = smbusNew.ReadByte(devName, uint64(0x03))
    }
    if err != errType.SUCCESS {
        return 
    }

    //Read out 128 bytes.. should be enough to get the part number
    offset = uint16(BoardInfoAreaOff) * 8
    for i := 0; i < 128; i++ {
        if I2cAddr16 == true {
            BIA[i], err = smbusNew.I2C16ReadByte(devName, uint16(int(offset)+i))
        } else {
            BIA[i], err = smbusNew.ReadByte(devName, uint64(int(offset)+i))
        }
        if err != errType.SUCCESS {
            return errType.FAIL
        }
    }
    offset=6
    //Mfg Type/Length
    offset = offset + uint16(BIA[offset] - 0xC0) + 1
    //Product Name Type/Length
    offset = offset + uint16(BIA[offset] - 0xC0) + 1
    //Serial Name Type/Length
    offset = offset + uint16(BIA[offset] - 0xC0) + 1
    //Part Number
    for i = 0; i < int(BIA[offset] - byte(0xC0)); i++ {
        pn[i] = BIA[offset + uint16(i) + 1]
    }
    pn[i] = '\000'

    return errType.SUCCESS
}


//Take care of 8 bit vs 16 bit eeprom reads
func eeRead(devName string, bus uint32, devAddr byte, offset uint16) (data byte, err int) {
    if devName == "CPLD_FRU" {
        i2cinfo.SwitchI2cTbl("UUT_NONE")
        rdData, errGo := materafpga.Spi_cpldX03_read_flash(uint32(bus-3), "ufm2", uint32(offset), 1)
        if errGo != nil {
            err = errType.FAIL 
            return 
        }
        data = rdData[0]
    } else {
        err = smbusNew.Open(devName, bus, devAddr)
        if err != errType.SUCCESS {
            return
        }

        if I2cAddr16 == true {
            data, err = smbusNew.I2C16ReadByte(devName, uint16(offset))
        } else {
            data, err = smbusNew.ReadByte(devName, uint64(offset))
        }

        smbusNew.Close()
    }
    return
}

func fruGenerateChecksum(data []byte, length uint16) (checksum uint8) {

    for i:=0; i<int(length); i++ {
        checksum += data[i]
    }
    checksum = uint8(0x100 - uint16(checksum))
    return
}


func fruDumpData(data []byte) {
    var s2 string
    for i:=0; i<len(data); i++ {
        if (i % 0x10) == 0 {
            s2 = s2 + fmt.Sprintf("\n%.04x: ", i)
        }
        s2 = s2 + fmt.Sprintf("%.02x ", data[i])
    }
    fmt.Printf("%s\n", s2);
    
    return
}

func VerifyFruCSUM(devName string, bus uint32, devAddr byte, OutputEnabled bool) (err int) {

    const CMN_HDR_IU_OFFSET  uint8 = 1
    const CMN_HDR_CHS_OFFSET uint8 = 2
    const CMN_HDR_BIA_OFFSET uint8 = 3
    const CMN_HDR_PIA_OFFSET uint8 = 4    
    const CMN_HDR_MR_OFFSET  uint8 = 5
    const CMN_HDR_LENGTH     uint8 = 8
    const MR_HDR_FORMAT_OFFSET   uint8 = 1
    const MR_HDR_LENGTH_OFFSET   uint8 = 2
    const MR_HDR_CSUM_OFFSET     uint8 = 3
    const MR_HDR_HDR_CSUM_OFFSET uint8 = 4
    const MR_HDR_LENGTH          uint8 = 5
    const BIAsize                uint16 = 256
    rawFru := []byte{}//make([]byte, 0)

    found, _ := CardInListTlv(devName)
    if found == true {
        err = VerifyFruTlvs(devName)
        return
    }

    header := make([]byte, 0)
    board_info_area := make([]byte, 0)
    product_info_area := make([]byte, 0)
    var bia_length uint16 = 0
    var pia_length uint16 = 0
    var mr_length uint16 = 0
    var i uint16 = 0
    var data8, hdr_csum, bia_csum, pia_csum, mr_csum, mr_header_csum  uint8  = 0, 0, 0, 0, 0, 0
    var offset, offset_add uint16 = 0, 0


    defer func() {
        if err != errType.SUCCESS {
            fruDumpData(rawFru)
        }
    } ()

    //Oracle cards start their Fru information at offset 256
    if CardType == "VOMERO2"  || CustType == "ORTANO" {
        offset_add = 256
    }
    if HpeAlom == true {
        return
    }

    for offset = 0; offset < uint16(CMN_HDR_LENGTH); offset++ {
        data8, err = eeRead(devName, bus, devAddr, offset + offset_add)
        header = append(header, data8)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to read device", devName, "field at offset", offset + offset_add) 
            return errType.FAIL
        }
    }
    rawFru = append(rawFru, header...)

    
    hdr_csum = fruGenerateChecksum(header, uint16(CMN_HDR_LENGTH) - 1)
    if hdr_csum == header[CMN_HDR_LENGTH-1] {
        if OutputEnabled == true { cli.Printf("i","%s Common Header Checksum Passed  Calculated 0x%.02x    Read 0x%.02x\n", devName, hdr_csum, header[CMN_HDR_LENGTH-1]) }
    } else {
        cli.Printf("e","%s Common Header Checksum Failed  Calculated 0x%.02x    Read 0x%.02x\n", devName, hdr_csum, header[CMN_HDR_LENGTH-1])
        return errType.FAIL
    }

    //board information area
    if header[CMN_HDR_BIA_OFFSET] > 0 {
        //read the length
        offset = uint16(header[CMN_HDR_BIA_OFFSET] * 8) + 1 + offset_add

        data8, err = eeRead(devName, bus, devAddr, offset)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to read device", devName, "field at offset", offset)
            return errType.FAIL
        }
        bia_length = uint16(data8 * 8)
        if bia_length > BIAsize {
            cli.Println("e", " Board Information Area Length > ", BIAsize,"for device", devName, " BIA Length = ", bia_length)
            return errType.FAIL
        }
        for i, offset = 0, uint16(header[CMN_HDR_BIA_OFFSET] * 8) + offset_add; i < bia_length; offset, i = offset+1, i+1 {
            data8, err = eeRead(devName, bus, devAddr, offset)
            board_info_area = append(board_info_area, data8)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device ", devName, " field at offset", offset)
                return errType.FAIL
            }
        }
        rawFru = append(rawFru, board_info_area...)

        bia_csum = fruGenerateChecksum(board_info_area, bia_length - 1)
        if bia_csum == board_info_area[bia_length-1] {
            if OutputEnabled == true { cli.Printf("i","%s Board Information Area Checksum Passed  Calculated 0x%.02x    Read 0x%.02x\n", devName, bia_csum, board_info_area[bia_length-1]) }
        } else {
            cli.Printf("e", "%s Board Information Area Checksum Failed  Calculated 0x%.02x    Read 0x%.02x\n", devName, bia_csum, board_info_area[bia_length-1])
            return errType.FAIL
        }
    }

    //product information area
    if header[CMN_HDR_PIA_OFFSET] > 0 {
        //read the length
        offset = uint16(header[CMN_HDR_PIA_OFFSET] * 8) + 1
        data8, err = eeRead(devName, bus, devAddr, offset)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to read device", devName, "field at offset", offset)
            return errType.FAIL
        }
        pia_length = uint16(data8 * 8)
        if pia_length > BIAsize {
            cli.Println("e", " ERROR: Product Information Area Length >",BIAsize,"for device", devName, "PIA Length = ", pia_length)
            return errType.FAIL
        }
        for i, offset = 0, uint16(header[CMN_HDR_PIA_OFFSET] * 8) + offset_add; i < pia_length; offset, i = offset+1, i+1 {
            data8, err = eeRead(devName, bus, devAddr, offset)
            product_info_area = append(product_info_area, data8)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device", devName, "field at offset", offset)
                return errType.FAIL
            }
        }
        rawFru = append(rawFru, product_info_area...)

        pia_csum = fruGenerateChecksum(product_info_area, pia_length - 1)
        if pia_csum == product_info_area[pia_length-1] {
            if OutputEnabled == true { cli.Printf("i", "%s Product Information Area Checksum Passed  Calculated 0x%.02x    Read 0x%.02x\n", devName, pia_csum, product_info_area[pia_length-1]) }
        } else {
            cli.Printf("e", "%s Product Information Area Checksum Failed  Calculated 0x%.02x    Read 0x%.02x\n", devName, pia_csum, product_info_area[pia_length-1])
            return errType.FAIL
        }
    }

    //multi-record offset
    if header[CMN_HDR_MR_OFFSET] > 0 {
        var mr_offset uint16 = 0
        mrRecords := 0
        
        mr_offset = uint16(header[CMN_HDR_MR_OFFSET])
        mr_offset = (mr_offset * 8)         
        for mrRecords = 0; mrRecords < 10; mrRecords++ {
            multi_record_area := make([]byte, 0)

            //read the length
            data8, err = eeRead(devName, bus, devAddr, mr_offset + uint16(MR_HDR_LENGTH_OFFSET) + offset_add)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read device", devName, "field at offset", offset)
                return errType.FAIL
            }
            mr_length = uint16(data8) + uint16(MR_HDR_LENGTH)
            if mr_length > BIAsize {
                cli.Println("e", " ERROR: Multi-record Length >",BIAsize,"for device", devName, "Multi-Record Length = ", mr_length)
                return errType.FAIL
            }
            for i, offset = 0, mr_offset + offset_add; i < mr_length; offset, i = offset+1, i+1 {
                data8, err = eeRead(devName, bus, devAddr, offset)
                multi_record_area = append(multi_record_area, data8)
                if err != errType.SUCCESS {
                    cli.Println("e", "Failed to read device", devName, "field at offset", offset)
                    return errType.FAIL
                }
            }
            rawFru = append(rawFru, multi_record_area...)

            mr_csum = fruGenerateChecksum(multi_record_area[5:], mr_length - uint16(MR_HDR_LENGTH))
            if mr_csum == multi_record_area[MR_HDR_CSUM_OFFSET] {
                if OutputEnabled == true { cli.Printf("i", "%s Multi-record Entry-%d Checksum Passed  Calculated 0x%.02x    Read 0x%.02x\n", devName, mrRecords, mr_csum, multi_record_area[MR_HDR_CSUM_OFFSET]) }
            } else {
                cli.Printf("e", "%s Multi-record Entry-%d Checksum Failed  Calculated 0x%.02x    Read 0x%.02x\n", devName, mrRecords, mr_csum, multi_record_area[MR_HDR_CSUM_OFFSET])
                return errType.FAIL
            }
            mr_header_csum = fruGenerateChecksum(multi_record_area[0:5], uint16(MR_HDR_LENGTH) - 1)
            if mr_header_csum == multi_record_area[MR_HDR_HDR_CSUM_OFFSET] {
                if OutputEnabled == true { cli.Printf("i", "%s Multi-record Entry-%d Header Checksum Passed  Calculated 0x%.02x    Read 0x%.02x\n", devName, mrRecords, mr_header_csum, multi_record_area[MR_HDR_HDR_CSUM_OFFSET]) }
            } else {
                cli.Printf("e", "%s Multi-record Entry-%d Header Checksum Failed  Calculated 0x%.02x    Read 0x%.02x\n", devName, mrRecords, mr_header_csum, multi_record_area[MR_HDR_HDR_CSUM_OFFSET])
                return errType.FAIL
            }

            if (multi_record_area[MR_HDR_FORMAT_OFFSET] & 0x80) == 0x80 {
                break;
            }
            mr_offset = mr_offset + mr_length
        }

        if mrRecords > 9 {
            cli.Println("e", "Finding to many multi-record entries.  Something is wrong!!")
            return errType.FAIL
        }
    }

    if header[CMN_HDR_BIA_OFFSET] > 0 {
        var length uint16 = 6
        var found_C1 bool = false
        var tmp, i, j uint8 = 0, 0, 0
        if OutputEnabled == true { cli.Printf("i", "Checking Board Info Area Type/Lengths\n") }
        for length, i = 6, 0; length < bia_length; i++ {
            tmp = board_info_area[length]
            if tmp == 0xC1 {                //0xC1 = END OF FIELD
                found_C1 = true
                length++
                for j=uint8(length); j<uint8(bia_length)-1; j++ {
                    if(board_info_area[j]!=0){
                        cli.Printf("e", " BIA Padding not equal to zero\n")
                        return errType.FAIL
                    }
                }
                break
            } else if tmp & 0xC0 == 0xC0 {  //TYPE/LENGTH
                length++
                if OutputEnabled == true { cli.Printf("i","[%.02x] %s\n", tmp, board_info_area[length:length+uint16(tmp & 0x3F)]) }
            } else if tmp & 0x80 == 0x80 {  //TYPE/LENGTH 6-BIT ASCII
                length++
                if OutputEnabled == true { cli.Printf("i","[%.02x] \n", tmp) }
                //if OutputEnabled == true { cli.Printf("i","[%.02x] %s\n", tmp, board_info_area[length:length+uint16(tmp & 0x3F)]) }
            } else {
                length++
                if OutputEnabled == true {  cli.Printf("i","[%.02x] %x\n", tmp, board_info_area[length:length+uint16(tmp & 0x3F)]) }
            }
            length+= (uint16(tmp & 0x3F))
        }
        if(found_C1 == false){
            cli.Println("e", " Failed to find BIA end marker (0xC1)\n")
            return errType.FAIL
        }
    }

    if header[CMN_HDR_PIA_OFFSET] > 0 {
        var length uint16 = 3
        var found_C1 bool = false
        var tmp, i, j uint8 = 0, 0, 0

        if OutputEnabled == true { cli.Printf("i", "Checking Product Info Area Type/Lengths\n") }
        for length, i = 3, 0; length < pia_length; i++ {
            tmp = product_info_area[length]
            if tmp == 0xC1 {
                found_C1 = true
                length++
                for j=uint8(length); j<uint8(pia_length)-1; j++ {
                    if(product_info_area[j]!=0){
                        cli.Printf("e", " PIA Padding not equal to zero\n")
                        return errType.FAIL
                    }
                }
                break
            } else if tmp & 0xC0 == 0xC0 {
                length++
                if OutputEnabled == true { cli.Printf("i","[%.02x] %s\n", tmp, product_info_area[length:length+uint16(tmp & 0x3F)]) }
            } else if tmp & 0x80 == 0x80 {  //TYPE/LENGTH 6-BIT ASCII
                length++
                //if OutputEnabled == true { cli.Printf("i","[%.02x] %s\n", tmp, board_info_area[length:length+uint16(tmp & 0x3F)]) }
                if OutputEnabled == true { cli.Printf("i","[%.02x] \n", tmp) }
            } else {
                length++
                if OutputEnabled == true { cli.Printf("i","[%.02x] %x\n", tmp, product_info_area[length:length+uint16(tmp & 0x3F)]) }
            }
            length+= (uint16(tmp & 0x3F))
        }
        if(found_C1 == false){
            cli.Println("e", " Failed to find PIA end marker (0xC1)\n")
            return errType.FAIL
        }
    }
    cli.Println("i", "FRU Checkum and Type/Length Checks Passed\n")

    return errType.SUCCESS
}
