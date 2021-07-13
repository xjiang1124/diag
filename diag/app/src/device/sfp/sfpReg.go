package sfp

type sfpPage_t struct {
    name     string
    offset   uint64
    numBytes uint64
}


// SFP Identifier
// SFF-8472
const (
    ID_SFPP byte = 0x3

    SFP_BITRATE_NOM       byte = 0xC

    SFP_VENDOR_NAME_START byte = 0x14
    SFP_VENDOR_NAME_SIZE  byte = 16
    
    SFP_PART_NUM_START    byte = 0x28
    SFP_PART_NUM_SIZE     byte = 16

    SFP_CC_BASE           byte = 0x3F

    SFP_BITRATE_MAX       byte = 0x42

    SFP_SREIAL_NUM_START  byte = 0x44
    SFP_SREIAL_NUM_SIZE   byte = 16

    SFP_DATE_CODE_START   byte = 0x54
    SFP_DATE_CODE_SIZE    byte = 8

    SFP_CC_EXT_BASE       byte = 0x5F

    
)

var regTblA0 = []sfpPage_t {
    sfpPage_t {"ID",       0,   1,},
    sfpPage_t {"VENDORNAME",   uint64(SFP_VENDOR_NAME_START), uint64(SFP_VENDOR_NAME_SIZE)},
    sfpPage_t {"PN",           uint64(SFP_PART_NUM_START),    uint64(SFP_PART_NUM_SIZE)},
    sfpPage_t {"SERIALNUMBER", uint64(SFP_SREIAL_NUM_START),  uint64(SFP_SREIAL_NUM_SIZE)},
    sfpPage_t {"DATE",         uint64(SFP_DATE_CODE_START),   uint64(SFP_DATE_CODE_SIZE)},
}


type sfpEeprom_t struct {
    ID  uint8    // Transceiver type - raw value
    extID  uint8   // Transceiver type extended id
    connectType uint8 /* Connector type */
    sfpCode     [8]uint8 // Transceiver Compliance code 
    encoding  uint8       // code for encoding
    baudRate  uint8     
    rateID  uint8      
    lengthFiber  [4]uint8
    lengthCopper  uint8
    lengthCopper2  uint8
    vendorName  [16]uint8 // ASCII Vendor Name
    extTransceiverCode  uint8
    vendorOUI  [3]uint8 
    vendorPN  [16]uint8 // Vendor Part Number
    eepromRev  [4]uint8 // Vendor revision level
    cableCompliance  [2]uint8
    reserved uint8
    ccBase  uint8  //checksum of first 63 bytes

    // Extended id fields
    options  [2]uint8
    brMax  uint8
    brMin  uint8
    vendorSN  [16]uint8 // Vendor Serial Number
    dateCode  [8]uint8 // Date Code
    diagMonType  uint8 // DOM?
    enhancedOptions  uint8 
    SFF8472Compliance  uint8  
    ccex  uint8 // checksum for 65-94
}
