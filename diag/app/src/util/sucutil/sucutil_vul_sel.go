package main

import (
    "fmt"
    "github.com/spf13/cobra"
    "device/sucuart"
)

// CreateVulSelCmd creates the vul_sel command
func CreateVulSelCmd() *cobra.Command {
    var vul_sel_index int

    var vulSelCmd = &cobra.Command{
        Use:   "vul_sel",
        Short: "Select a Vulcano ASIC (without power on)",
        Long: `Select a Vulcano ASIC by index (1-36).
The system has 6 slots, each with 3 FPGAs, and each FPGA connects to 2 Vulcano ASICs.
This command selects the appropriate slot, FPGA, and Vulcano without powering it on.`,
        Run: func(cmd *cobra.Command, args []string) {
            if vul_sel_index < 1 || vul_sel_index > 36 {
                fmt.Printf("ERROR: vul_index must be in range 1 to 36\n")
                return
            }
            err := sucuart.Suc_vul_sel_and_power_on(vul_sel_index, false)
            if err != 0 {
                fmt.Printf("ERROR: Failed to select Vulcano %d\n", vul_sel_index)
            }
        },
    }

    vulSelCmd.Flags().IntVarP(&vul_sel_index, "vul_index", "i", 0, "Vulcano index (1-36)")
    vulSelCmd.MarkFlagRequired("vul_index")
    return vulSelCmd
}

// CreateVulPowerOnCmd creates the vul_power_on command
func CreateVulPowerOnCmd() *cobra.Command {
    var vul_power_on_index int

    var vulPowerOnCmd = &cobra.Command{
        Use:   "vul_power_on",
        Short: "Power on a Vulcano ASIC",
        Long: `Power on a Vulcano ASIC by index (1-36).
The system has 6 slots, each with 3 FPGAs, and each FPGA connects to 2 Vulcano ASICs.
This command selects the appropriate slot, FPGA, and Vulcano, then powers it on.`,
        Run: func(cmd *cobra.Command, args []string) {
            if vul_power_on_index < 1 || vul_power_on_index > 36 {
                fmt.Printf("ERROR: vul_index must be in range 1 to 36\n")
                return
            }
            err := sucuart.Suc_vul_sel_and_power_on(vul_power_on_index, true)
            if err != 0 {
                fmt.Printf("ERROR: Failed to power on Vulcano %d\n", vul_power_on_index)
            }
        },
    }

    vulPowerOnCmd.Flags().IntVarP(&vul_power_on_index, "vul_index", "i", 0, "Vulcano index (1-36)")
    vulPowerOnCmd.MarkFlagRequired("vul_index")
    return vulPowerOnCmd
}
