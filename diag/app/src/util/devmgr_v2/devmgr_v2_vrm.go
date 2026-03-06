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
        devName, _ := cmd.Flags().GetString("dev")
        marginPercent, _ := cmd.Flags().GetInt("pct")
        if os.Getenv("CARD_TYPE") == "MTP_PONZA" {
            // For MTP_PONZA, slot represents vul_index (1-36)
            if slot >= 1 && slot <= 36 {
                sucuart.Suc_dev_margin_ponza(slot, strings.ToUpper(devName), marginPercent)
                return
            } else {
                fmt.Printf("ERROR: For MTP_PONZA, vul_index must be in range 1 to 36\n")
            }
        } else {
            if slot >= 1 && slot <= 10 {
                if os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
                    sucuart.Suc_dev_margin(slot, strings.ToUpper(devName), marginPercent)
                    return
                }
                uut = "UUT_" + strconv.Itoa(slot)
            }

            if marginPercent > 10 || marginPercent < -10 {
                fmt.Printf("ERROR: Margin percent must be between -10 and 10.  You entered %d\n", marginPercent)
                os.Exit(-1)
            }
            hwdev.Margin(strings.ToUpper(devName), marginPercent, uut)
        }
    },
}

func init() {
    marginCmd.Flags().IntP("slot", "s", 0, "UUT Slot (or vul_index for MTP_PONZA)")
    marginCmd.Flags().StringP("dev", "d", "ALL", "Device name")
    marginCmd.Flags().IntP("pct", "p", 0, "Voltage margin percent between -10 and 10")
    marginCmd.MarkFlagRequired("pct")
    if os.Getenv("CARD_TYPE") == "MTP_PANAREA" || os.Getenv("CARD_TYPE") == "MTP_PONZA" {
        marginCmd.AddCommand(createMarginInfoCommand())
        marginCmd.AddCommand(createSetCommand())
    }
}

func createMarginInfoCommand() *cobra.Command {
    var marginInfoCmd = &cobra.Command{
        Use:   "info",
        Short: "Show voltage margin info from DS4424",
        Run: func(cmd *cobra.Command, args []string) {
            slot, _ := cmd.Flags().GetInt("slot")
            if os.Getenv("CARD_TYPE") == "MTP_PONZA" {
                // For MTP_PONZA, slot represents vul_index (1-36)
                if slot >= 1 && slot <= 36 {
                    sucuart.Suc_dev_margin_info_ponza(slot)
                    return
                } else {
                    fmt.Printf("ERROR: For MTP_PONZA, vul_index must be in range 1 to 36\n")
                }
            } else {
                if slot >= 1 && slot <= 10 {
                    sucuart.Suc_dev_margin_info(slot)
                }
            }
        },
    }
    marginInfoCmd.Flags().IntP("slot", "s", 0, "UUT Slot")
    return marginInfoCmd
}

func createSetCommand() *cobra.Command {
    var setCmd = &cobra.Command{
        Use:   "set",
        Short: "Set vboot/vout/vmin/vmax",
        Run: func(cmd *cobra.Command, args []string) {
            slot, _ := cmd.Flags().GetInt("slot")
            devName, _ := cmd.Flags().GetString("dev")
            vboot, _ := cmd.Flags().GetInt("vboot")
            vout, _ := cmd.Flags().GetInt("vout")
            vmin, _ := cmd.Flags().GetInt("vmin")
            vmax, _ := cmd.Flags().GetInt("vmax")
            if os.Getenv("CARD_TYPE") == "MTP_PONZA" {
                // For MTP_PONZA, slot represents vul_index (1-36)
                if slot >= 1 && slot <= 36 {
                    sucuart.Suc_dev_vset_ponza(slot, strings.ToUpper(devName), vboot, vout, vmin, vmax)
                    return
                } else {
                    fmt.Printf("ERROR: For MTP_PONZA, vul_index must be in range 1 to 36\n")
                }
            } else {
                if slot >= 1 && slot <= 10 {
                    sucuart.Suc_dev_vset(slot, strings.ToUpper(devName), vboot, vout, vmin, vmax)
                }
            }
        },
    }
    setCmd.Flags().IntP("slot", "s", 0, "UUT Slot (or vul_index for MTP_PONZA)")
    setCmd.Flags().StringP("dev", "d", "ALL", "Device name")
    setCmd.Flags().IntP("vboot", "b", -1, "vboot(mv)")
    setCmd.Flags().IntP("vout", "o", -1, "vout(mv)")
    setCmd.Flags().IntP("vmin", "m", -1, "vmin(mv)")
    setCmd.Flags().IntP("vmax", "n", -1, "vmax(mv)")
    return setCmd
}