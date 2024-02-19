package main

import (
    "strconv"
    "hardware/i2cinfo"
    "github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
    Use:   "list",
    Short: "List all i2c devices",
    Run: func(cmd *cobra.Command, args []string) {
        uut := "UUT_NONE"
        slot, _ := cmd.Flags().GetInt("slot")
        if slot >= 1 && slot <= 10 {
            uut = "UUT_" + strconv.Itoa(slot)
        }
        i2cinfo.SwitchI2cTbl(uut)
        i2cinfo.DispI2cInfoAll()
    },
}

func init() {
    listCmd.Flags().IntP("slot", "s", 0, "UUT Slot")
}
