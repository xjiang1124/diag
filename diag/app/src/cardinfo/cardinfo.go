package cardinfo

var Cardinfo = map[string]map[string]string{
    "ORTANO2": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "CPLD"},
    "ORTANO2A": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "CPLD"},
    "ORTANO2I": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "CPLD"},
    "ORTANO2S": map[string]string{
        "ASIC": "ELBA",
        "CTRL": "CPLD"},
    "ORTANO2AC": map[string]string{
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
    "GINESTRA_D5": map[string]string{
        "ASIC": "GIGLIO",
        "CTRL": "CPLD"},
    "GINESTRA_D4": map[string]string{
        "ASIC": "GIGLIO",
        "CTRL": "CPLD"},
    "MALFA": map[string]string{
        "ASIC": "SALINA",
        "CTRL": "CPLD"},
    "POLLARA": map[string]string{
        "ASIC": "SALINA",
        "CTRL": "CPLD"},
    "LENI": map[string]string{
        "ASIC": "SALINA",
        "CTRL": "CPLD"},
    "LENI48G": map[string]string{
        "ASIC": "SALINA",
        "CTRL": "CPLD"},
    "LINGUA": map[string]string{
        "ASIC": "SALINA",
        "CTRL": "CPLD"},
    "GELSOP": map[string]string{
        "ASIC": "VULCANO",
        "CTRL": "CPLD"},
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

