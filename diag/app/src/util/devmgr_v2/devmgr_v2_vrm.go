package main

import (
    "fmt"
    "os"
    "strconv"
    "strings"
    "hardware/hwdev"
    "github.com/spf13/cobra"
    "device/sucuart"
)

var marginCmd = &cobra.Command{
    Use:   "margin",
    Short: "Margin a VRM device by percent of nominal",
    Run: func(cmd *cobra.Command, args []string) {
        uut := "MTP_MATERA"
        slot, _ := cmd.Flags().GetInt("slot")
        if slot >= 1 && slot <= 10 {
            if os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                sucuart.Suc_dev_margin(slot)
                return
            }
            uut = "UUT_" + strconv.Itoa(slot)
        }
        marginPercent, _ := cmd.Flags().GetInt("pct")
        if marginPercent > 10 || marginPercent < -10 {
            fmt.Printf("ERROR: Margin percent must be between -10 and 10.  You entered %d\n", marginPercent)
            os.Exit(-1)
        }
        devName, _ := cmd.Flags().GetString("dev")
        hwdev.Margin(strings.ToUpper(devName), marginPercent, uut)
    },
}

func init() {
    marginCmd.Flags().IntP("slot", "s", 0, "UUT Slot")
    marginCmd.Flags().StringP("dev", "d", "ALL", "Device name")
    marginCmd.Flags().IntP("pct", "p", 0, "Voltage margin percent between -10 and 10")
    marginCmd.MarkFlagRequired("pct")
}
