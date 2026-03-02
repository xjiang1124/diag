package main

import (
    "fmt"
    "os"
    "github.com/spf13/cobra"
    "device/sucuart"
)

// CreateCpldCmd creates the parent cpld command
func CreateCpldCmd() *cobra.Command {
    var cpldCmd = &cobra.Command{
        Use:   "cpld",
        Short: "Interact with CPLD devices",
    }
    // Add subcommands to the cpld command
    cpldCmd.AddCommand(createReadCommand())
    cpldCmd.AddCommand(createWriteCommand())

    return cpldCmd
}

func createReadCommand() *cobra.Command {
    var readCmd = &cobra.Command{
        Use:   "read",
        Short: "Read from a CPLD register address",
        Run: func(cmd *cobra.Command, args []string) {
            cardType := os.Getenv("CARD_TYPE")

            if cardType == "MTP_PONZA" {
                // For MTP_PONZA, slot represents vul_index (1-36)
                if slot >= 1 && slot <= 36 {
                    data8, err := sucuart.Suc_cpld_read_ponza(slot, byte(offset))
                    if err != 0 {
                        fmt.Printf("ERROR: Failed to read cpld reg %.02x for vul_index %d\n", byte(offset), slot)
                    } else {
                        fmt.Printf("cpld read %.02x, value %.02x\n", byte(offset), data8)
                    }
                } else {
                    fmt.Printf("ERROR: For MTP_PONZA, vul_index must be in range 1 to 36\n")
                }
            } else {
                // For other MTP types, slot represents physical slot (1-10)
                if slot >= 1 && slot <= 10 {
                    data8, err := sucuart.Suc_cpld_read(slot, byte(offset))
                    if err != 0 {
                        fmt.Printf("ERROR: Failed to read cpld reg %.02x\n", byte(offset))
                    } else {
                        fmt.Printf("cpld read %.02x, value %.02x\n", byte(offset), data8)
                    }
                } else {
                    fmt.Printf("ERROR: slot must be in range 1 to 10\n")
                }
            }
        },
    }

    readCmd.Flags().IntVarP(&slot, "slot", "s", 0, "UUT Slot (or vul_index for MTP_PONZA)")
    readCmd.Flags().UintVarP(&offset, "addr", "a", 0, "Hex address to read from (8-bit)")
    readCmd.MarkFlagRequired("slot")
    readCmd.MarkFlagRequired("addr")
    return readCmd
}

func createWriteCommand() *cobra.Command {
    var writeCmd = &cobra.Command{
        Use:   "write",
        Short: "Write to a CPLD register address",
        Run: func(cmd *cobra.Command, args []string) {
            cardType := os.Getenv("CARD_TYPE")

            if cardType == "MTP_PONZA" {
                // For MTP_PONZA, slot represents vul_index (1-36)
                if slot >= 1 && slot <= 36 {
                    err := sucuart.Suc_cpld_write_ponza(slot, byte(offset), byte(value))
                    if err != 0 {
                        fmt.Printf("ERROR: Failed to write cpld reg %.02x for vul_index %d\n", byte(offset), slot)
                    } else {
                        fmt.Printf("cpld write %.02x, value %.02x\n", byte(offset), byte(value))
                    }
                } else {
                    fmt.Printf("ERROR: For MTP_PONZA, vul_index must be in range 1 to 36\n")
                }
            } else {
                // For other MTP types, slot represents physical slot (1-10)
                if slot >= 1 && slot <= 10 {
                    err := sucuart.Suc_cpld_write(slot, byte(offset), byte(value))
                    if err != 0 {
                        fmt.Printf("ERROR: Failed to write cpld reg %.02x\n", byte(offset))
                    } else {
                        fmt.Printf("cpld write %.02x, value %.02x\n", byte(offset), byte(value))
                    }
                } else {
                    fmt.Printf("ERROR: slot must be in range 1 to 10\n")
                }
            }
        },
    }

    writeCmd.Flags().IntVarP(&slot, "slot", "s", 0, "UUT Slot (or vul_index for MTP_PONZA)")
    writeCmd.Flags().UintVarP(&offset, "addr", "a", 0, "Hex address to write to (8-bit)")
    writeCmd.Flags().UintVarP(&value, "data", "d", 0, "Hex value to write (8-bit)")
    writeCmd.MarkFlagRequired("slot")
    writeCmd.MarkFlagRequired("addr")
    writeCmd.MarkFlagRequired("data")
    return writeCmd
}

