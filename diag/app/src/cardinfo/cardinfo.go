package cardinfo

var Cardinfo = map[string]map[string]string{
    "ORTANO": map[string]string{
        "ASIC": "ELBA"},
    "ORTANO2": map[string]string{
        "ASIC": "ELBA"},
    "LACONA": map[string]string{
        "ASIC": "ELBA"},
    "LACONA_DELL": map[string]string{
        "ASIC": "ELBA"},
}

func GetAsicType(cardType string) (err int, asicType string) {
    asicType, ok:= Cardinfo[cardType]["ASIC"]
    if !ok {
        asicType = "CAPRI"
    }
    return
}

