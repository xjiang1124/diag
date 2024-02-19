package main

import (
    "strings"
    "hardware/hwdev"
    "github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
    Use:   "status",
    Short: "Device status",
    Run: func(cmd *cobra.Command, args []string) {
        slot, _ := cmd.Flags().GetString("slot")
        devName, _ := cmd.Flags().GetString("dev")
        hwdev.DispStatus(strings.ToUpper(devName), strings.ToUpper(slot))
    },
}

func init() {
    statusCmd.Flags().StringP("slot", "s", "UUT_NONE", "UUT slot, e.g. UUT_1")
    statusCmd.Flags().StringP("dev", "d", "ALL", "Device name")
}
