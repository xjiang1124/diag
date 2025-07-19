package main

import (
    "os"
    "common/cli"
)

var cardType string

func init() {
    cardType = os.Getenv("CARD_TYPE")

    if cardType != "LIPARI" && 
       cardType != "MTP_MATERA" &&
       cardType != "MTP_PANAREA" &&
       cardType != "TAORMINA" {
        //See if we are SONIC OS.. if yes we are lipari
        exists, _ := Path_exists("/etc/sonic")
        if exists == true {
            cardType = "LIPARI"
            os.Setenv("CARD_TYPE",cardType)
            cli.Println("d", "Found card:", cardType)
        } else {
            cardType = "TAORMINA"
            os.Setenv("CARD_TYPE",cardType)
            cli.Println("d", "Found card:", cardType)
        }
    }
}

func main() {
    if cardType == "LIPARI" {
        lipari_fpga_cli()
    } else if cardType == "TAORMINA" {
        taormina_fpga_cli()
    } else if cardType == "MTP_MATERA" {
        matera_fpga_cli()
    } else if cardType == "MTP_PANAREA" {
        panarea_fpga_cli()
    } else {
        cli.Println("e", "Wrong card type:", cardType)
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
