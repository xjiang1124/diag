package cardinfo

import (
    "gopkg.in/yaml.v2"
    "io/ioutil"

    "common/dcli"
    "common/errType"
)

type cardInfo struct {
    Cardinfo map[string]map[string]string
}

func (c *cardInfo) getConf() *cardInfo {

    //yamlFile, err := ioutil.ReadFile("conf.yaml")
    yamlFile, err := ioutil.ReadFile("card_info.yaml")
    if err != nil {
        dcli.Printf("e", "yamlFile.Get err   #%v ", err)
    }
    err = yaml.Unmarshal(yamlFile, c)
    if err != nil {
        dcli.Printf("e", "Unmarshal: %v", err)
    }

    return c
}

var cdInfo cardInfo

func init() {
    cdInfo.getConf()
}

func GetAsicType(cardType string) (err int, asicType string) {
    asicType, ok:= cdInfo.Cardinfo[cardType]["ASIC"]
    if !ok {
        dcli.Println("e", "Failed to retrievd ASIC type:", cardType)
        err = errType.FAIL
    }
    return
}

