package main

import (
    "fmt"
    "os"
    "strconv"
    "common/errType"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    "github.com/spf13/cobra"
    "device/sucuart"
)

var listCmd = &cobra.Command{
    Use:   "list",
    Short: "List all i2c devices",
    Run: func(cmd *cobra.Command, args []string) {
        uut := "UUT_NONE"
        slot, _ := cmd.Flags().GetInt("slot")
        if os.Getenv("CARD_TYPE") == "MTP_PONZA" {
            // For MTP_PONZA, slot represents vul_index (1-36)
            if slot >= 1 && slot <= 6 {
                sucuart.Suc_dev_list(slot)
                return
            } else {
                fmt.Printf("ERROR: For MTP_PONZA, slot must be in range 1 to 6\n")
            }
        } else {
            if slot >= 1 && slot <= 10 {
                if os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                    sucuart.Suc_dev_list(slot)
                    return
                }
                uut = "UUT_" + strconv.Itoa(slot)
                lockName, err := hwinfo.PreUutSetup(uut)
                if err != errType.SUCCESS {
                    return
                }
                defer hwinfo.PostUutClean(lockName)
            }
            i2cinfo.DispI2cInfoAll()
        }
    },
}

func init() {
    listCmd.Flags().IntP("slot", "s", 0, "UUT Slot")
}
