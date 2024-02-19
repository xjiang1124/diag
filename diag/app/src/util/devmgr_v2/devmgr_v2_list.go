package main
import (
    "strings"

    "hardware/i2cinfo"
    "github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
    Use:   "list",
    Short: "List all i2c devices",
    Run: func(cmd *cobra.Command, args []string) {
        slot, _ := cmd.Flags().GetString("slot")
        i2cinfo.SwitchI2cTbl(strings.ToUpper(slot))
        i2cinfo.DispI2cInfoAll()
    },
}

func init() {
    listCmd.Flags().StringP("slot", "s", "UUT_NONE", "UUT Slot, e.g. UUT_1")
}
