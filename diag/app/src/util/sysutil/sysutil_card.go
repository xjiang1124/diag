package main

import (
	"fmt"
	"os"
	"github.com/spf13/cobra"
	"device/fpga/panareafpga"
)

// CreateCardPresentCmd creates the card_present command
func CreateCardPresentCmd() *cobra.Command {
	var slot_num int

	var cardPresentCmd = &cobra.Command{
		Use:   "card_present",
		Short: "Check if a card is present in the specified slot",
		Long: `Check if a card is present in the specified slot (1-6).
Reads the FPGA register and checks bit 9 (0x200).
If bit 9 is 0, the card is present.`,
		Run: func(cmd *cobra.Command, args []string) {
			if slot_num < 1 || slot_num > 6 {
				fmt.Printf("ERROR: slot_num must be in range 1 to 6\n")
				os.Exit(-1)
			}

			// Calculate register address: 0x180 + (slot_zero_based * 4)
			slot_zero_based := slot_num - 1
			reg_addr := uint64(0x180 + (slot_zero_based * 4))

			// Read the register
			rValue, err := panareafpga.ReadU32(reg_addr)
			if err != nil {
				fmt.Printf("ERROR: Failed to read FPGA register 0x%.04x\n", reg_addr)
				os.Exit(-1)
			}

			// Check bit 9 (0x200): if 0, card is present
			nic_present := rValue & 0x200
			if nic_present == 0 {
				fmt.Printf("Card in slot %d is PRESENT\n", slot_num)
				os.Exit(0)
			} else {
				fmt.Printf("Card in slot %d is NOT PRESENT\n", slot_num)
				os.Exit(1)
			}
		},
	}

	cardPresentCmd.Flags().IntVarP(&slot_num, "slot_num", "s", 0, "Slot number (1-6)")
	cardPresentCmd.MarkFlagRequired("slot_num")
	return cardPresentCmd
}

// CreateCardPoweredOnCmd creates the card_powered_on command
func CreateCardPoweredOnCmd() *cobra.Command {
	var slot_num int

	var cardPoweredOnCmd = &cobra.Command{
		Use:   "card_powered_on",
		Short: "Check if a card is powered on in the specified slot",
		Long: `Check if a card is powered on in the specified slot (1-6).
Reads the FPGA register and checks power bits 1 and 3.
Bit 1: 12V power rail
Bit 3: 54V power rail`,
		Run: func(cmd *cobra.Command, args []string) {
			if slot_num < 1 || slot_num > 6 {
				fmt.Printf("ERROR: slot_num must be in range 1 to 6\n")
				os.Exit(-1)
			}

			// Calculate register address: 0x180 + (slot_zero_based * 4)
			slot_zero_based := slot_num - 1
			reg_addr := uint64(0x180 + (slot_zero_based * 4))

			// Read the register
			rValue, err := panareafpga.ReadU32(reg_addr)
			if err != nil {
				fmt.Printf("ERROR: Failed to read FPGA register 0x%.04x\n", reg_addr)
				os.Exit(-1)
			}

			// Check power bits (bits 1 and 3)
			// Bit 1: 12V power rail (0x2)
			// Bit 3: 54V power rail (0x8)
			power_12v := rValue & 0x2
			power_54v := rValue & 0x8

			fmt.Printf("Card in slot %d power status:\n", slot_num)
			fmt.Printf("  12V: %s\n", getPowerStatus(power_12v))
			fmt.Printf("  54V: %s\n", getPowerStatus(power_54v))

			// Card is considered powered on if both power bits are set
			if power_12v != 0 && power_54v != 0 {
				fmt.Printf("Card in slot %d is POWERED ON\n", slot_num)
				os.Exit(0)
			} else {
				fmt.Printf("Card in slot %d is NOT POWERED ON\n", slot_num)
				os.Exit(1)
			}
		},
	}

	cardPoweredOnCmd.Flags().IntVarP(&slot_num, "slot_num", "s", 0, "Slot number (1-6)")
	cardPoweredOnCmd.MarkFlagRequired("slot_num")
	return cardPoweredOnCmd
}

func getPowerStatus(bit uint32) string {
	if bit != 0 {
		return "ON"
	}
	return "OFF"
}
