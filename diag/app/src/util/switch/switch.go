package main

import (
    "os"
)

 

                               

func main() {

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "LIPARI" {
        lipari_cli()
    } else {
        taormina_cli()
    }
    return
}






 
