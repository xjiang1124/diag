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

var statusCmd = &cobra.Command{
    Use:   "status",
    Short: "Device status",
    Run: func(cmd *cobra.Command, args []string) {
        uut := "UUT_NONE"
        slot, _ := cmd.Flags().GetInt("slot")
        if os.Getenv("CARD_TYPE") == "MTP_PONZA" {
            // For MTP_PONZA, slot represents vul_index (1-36)
            if slot >= 1 && slot <= 36 {
                sucuart.Suc_dev_status_ponza(slot)
                return
            } else {
                fmt.Printf("ERROR: For MTP_PONZA, vul_index must be in range 1 to 36\n")
            }
        } else {
            if slot >= 1 && slot <= 10 {
                if os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                    sucuart.Suc_dev_status(slot)
                    return
                }
                uut = "UUT_" + strconv.Itoa(slot)
            }
            devName, _ := cmd.Flags().GetString("dev")
            hwdev.DispStatus(strings.ToUpper(devName), uut)
        }
    },
}

func init() {
    statusCmd.Flags().IntP("slot", "s", 0, "UUT Slot (or vul_index for MTP_PONZA)")
    statusCmd.Flags().StringP("dev", "d", "ALL", "Device name")
}
