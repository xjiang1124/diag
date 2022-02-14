package nicCpldCommon

type  MctpCmd struct {
    Cmd        uint64
    Value      []byte
    Len        uint64
    ResLen     uint64
    Pec        bool
    DevAddr    bool
}

var nilData []byte = []byte{}
var udid []byte = []byte{0x15, 0x14, 0x13, 0x12, 0x11, 0x10, 0x09, 0x08,
                         0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00, 0xC2}

var GetUDIDgen = MctpCmd{0x03, nilData, 0, 17, false, false}
var GetUDIDdirect = MctpCmd{0xC2, nilData, 0, 17, false, true}
var ClearAp = MctpCmd{0x01, nilData, 0, 0, true, false}
var Reset = MctpCmd{0x02, nilData, 0, 0, true, false}
var SetAddr = MctpCmd{0x04, udid, 17, 0, true, false}

