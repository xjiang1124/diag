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
)

var regTblA0 = []sfpPage_t {
    sfpPage_t {"ID",       0,   1,},
}

