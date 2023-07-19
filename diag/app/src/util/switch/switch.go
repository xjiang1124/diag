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
            cardType = os.Getenv("CARD_TYPE")
        }
    }
}

// exists returns whether the given file or directory exists
func Path_exists(path string) (bool, error) {
    _, err := os.Stat(path)
    if err == nil { return true, nil }
    if os.IsNotExist(err) { return false, nil }
    return false, err
}

                               

func main() {

    cardType = os.Getenv("CARD_TYPE")
    if cardType == "LIPARI" {
        lipari_switch_cli()
    } else {
        taormina_switch_cli()
    }
    return
}






 
