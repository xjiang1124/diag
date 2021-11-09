package cardinfo

var Cardinfo = map[string]map[string]string{
    "ORTANO2": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "CPLD"},
    "LACONA32": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "FPGA"},
    "LACONA32DELL": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "FPGA"},
    "POMONTE": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "FPGA"},
    "POMONTEDELL": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "FPGA"},
}

func GetAsicType(cardType string) (err int, asicType string) {
    asicType, ok:= Cardinfo[cardType]["ASIC"]
    if !ok {
        asicType = "CAPRI"
    }
    return
}

func GetCtrlType(cardType string) (err int, asicType string) {
    asicType, ok:= Cardinfo[cardType]["CTRL"]
    if !ok {
        asicType = "CPLD"
    }
    return
}

