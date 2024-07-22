package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"common/misc"
	"common/errType"
)


func main() {
	if len(os.Args) != 3 {
		fmt.Printf("Usage: %s <str2asc|asc2str> <input_string|input_hex>\n", os.Args[0])
		return
	}

	action := os.Args[1]
	input := os.Args[2]

	switch action {
	case "str2asc":

		packedOutput, err := misc.StrToAsc6(input)
		if err != errType.SUCCESS {
			return
		}

		fmt.Printf("Original string: \"%s\"\n", input)
		fmt.Printf("Packed 6-bit ASCII representation:\n")

		fmt.Print("Binary: ")
		for i := 0; i < misc.STR_MAX_SIZE; i++ {
			for j := 7; j >= 0; j-- {
				fmt.Printf("%d", (packedOutput[i]>>uint32(j))&1)
			}
			fmt.Print(" ")
		}
		fmt.Println()

		fmt.Print("Hex:    ")
		for i := 0; i < misc.STR_MAX_SIZE; i++ {
			fmt.Printf("%02X ", packedOutput[i])
		}
		fmt.Println()

	case "asc2str":
		packedInput, err := hex.DecodeString(input)
		if err != nil {
			fmt.Println("Error: Invalid hex input.")
			return
		}
		
		unpackedString, err2 := misc.Asc6ToStr(packedInput)
		if err2 != errType.SUCCESS {
			return
		}

		fmt.Printf("Original hex input: %s\n", input)
		fmt.Printf("Unpacked string: \"%s\"\n", unpackedString)

	default:
		fmt.Println("Error: Invalid action. Use 'str2asc' or 'asc2str'.")
	}
}