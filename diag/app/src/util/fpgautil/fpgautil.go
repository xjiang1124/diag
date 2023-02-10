package main

import (
    "os"
)

                               

func main() {

    cardType := os.Getenv("CARD_TYPE")
    if cardType == "LIPARI" {
        lipari_fpga_cli()
    } else {
        taormina_fpga_cli()
    }
    return
}

 
