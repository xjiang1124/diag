package main

import (
    "os"
)

 

                               

func main() {

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "LIPARI" {
        lipari_switch_cli()
    } else {
        taormina_switch_cli()
    }
    return
}






 
