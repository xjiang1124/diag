package main

import (
    "strconv"
    "strings"
    "hardware/hwdev"
    "github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
    Use:   "status",
    Short: "Device status",
    Run: func(cmd *cobra.Command, args []string) {
        uut := "UUT_NONE"
        slot, _ := cmd.Flags().GetInt("slot")
        if slot >= 1 && slot <= 10 {
            uut = "UUT_" + strconv.Itoa(slot)
        }
        devName, _ := cmd.Flags().GetString("dev")
        hwdev.DispStatus(strings.ToUpper(devName), uut)
    },
}

func init() {
    statusCmd.Flags().IntP("slot", "s", 0, "UUT Slot")
    statusCmd.Flags().StringP("dev", "d", "ALL", "Device name")
}
