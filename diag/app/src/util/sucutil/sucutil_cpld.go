package main

import (
    "github.com/spf13/cobra"
    "device/sucuart"
)

// Read Command
var offset uint
var slot int
var value uint

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
            if slot >= 1 && slot <= 10 {
                sucuart.Suc_cpld_read(slot, byte(offset))
            }
        },
    }

    readCmd.Flags().IntVarP(&slot, "slot", "s", 0, "UUT Slot")
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
            if slot >= 1 && slot <= 10 {
                sucuart.Suc_cpld_write(slot, byte(offset), byte(value))
            }
        },
    }

    writeCmd.Flags().IntVarP(&slot, "slot", "s", 0, "UUT Slot")
    writeCmd.Flags().UintVarP(&offset, "addr", "a", 0, "Hex address to write to (8-bit)")
    writeCmd.Flags().UintVarP(&value, "data", "d", 0, "Hex value to write (8-bit)")
    writeCmd.MarkFlagRequired("slot")
    writeCmd.MarkFlagRequired("addr")
    writeCmd.MarkFlagRequired("data")
    return writeCmd
}

