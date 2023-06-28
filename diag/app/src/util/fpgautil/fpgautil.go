package main

import (
    "os"
)

var cardType string

func init() {
    cardType = os.Getenv("CARD_TYPE")
    
    if cardType != "LIPARI" && cardType != "TAORMINA" {
        //See if we are SONIC OS.. if yes we are lipari
        exists, _ := Path_exists("/etc/sonic")
        if exists == true {
            cardType = "LIPARI"
            os.Setenv("CARD_TYPE",cardType)
        } else {
            cardType = "TAORMINA"
            os.Setenv("CARD_TYPE",cardType)
            
        }
    }
}
                               

func main() {
    if cardType == "LIPARI" {
        lipari_fpga_cli()
    } else {
        taormina_fpga_cli()
    }
    return
}

// exists returns whether the given file or directory exists
func Path_exists(path string) (bool, error) {
    _, err := os.Stat(path)
    if err == nil { return true, nil }
    if os.IsNotExist(err) { return false, nil }
    return false, err
}

 
