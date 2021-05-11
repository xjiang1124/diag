package main

import (
    "fmt"
    "gopkg.in/yaml.v2"
    "io/ioutil"
    "log"
    "reflect"
)

type conf struct {
    Hits int64 `yaml:"hits"`
    //Time int64 `yaml:"time"`
}

func (c *conf) getConf() *conf {

    //yamlFile, err := ioutil.ReadFile("conf.yaml")
    yamlFile, err := ioutil.ReadFile("card_info.yaml")
    if err != nil {
        log.Printf("yamlFile.Get err   #%v ", err)
    }
    err = yaml.Unmarshal(yamlFile, c)
    if err != nil {
        log.Fatalf("Unmarshal: %v", err)
    }

    return c
}

type cInfo struct {
    Cardinfo map[string]map[string]string
}

//type cInfo struct {
//  //Description string
//  Fruits map[string]string
//}

func (c *cInfo) getConf() *cInfo {

    //yamlFile, err := ioutil.ReadFile("conf.yaml")
    yamlFile, err := ioutil.ReadFile("card_info.yaml")
    if err != nil {
        log.Printf("yamlFile.Get err   #%v ", err)
    }
    err = yaml.Unmarshal(yamlFile, c)
    if err != nil {
        log.Fatalf("Unmarshal: %v", err)
    }

    return c
}

type Config struct {
  //Description string
  Fruits map[string]string
}

func (c *Config) getConf() *Config {

    //yamlFile, err := ioutil.ReadFile("conf.yaml")
    yamlFile, err := ioutil.ReadFile("fruit.yaml")
    if err != nil {
        log.Printf("yamlFile.Get err   #%v ", err)
    }
    err = yaml.Unmarshal(yamlFile, c)
    if err != nil {
        log.Fatalf("Unmarshal: %v", err)
    }

    return c
}

func main() {
    //var c conf
    var c cInfo
    //var c Config

    c.getConf()

    fmt.Println(c)
    fmt.Println(reflect.TypeOf(c))
    //fmt.Println(c.Hits)
    //fmt.Println(c.cardInfo)
    fmt.Printf("%#v\n", c)
}
