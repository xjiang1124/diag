package main

import (
    "github.com/spf13/cobra"
    "device/sucuart"
)

// CreateExecCmd creates the parent exec command
func CreateExecCmd() *cobra.Command {
    var execCmd = &cobra.Command{
        Use:   "exec",
        Short: "execute a list of raw uart commands",
        Run: func(cmd *cobra.Command, args []string) {
            if slot >= 1 && slot <= 10 {
                sucuart.Suc_exec_cmds(slot, commands)
            }
        },
    }
    execCmd.Flags().IntVarP(&slot, "slot", "s", 0, "UUT Slot")
    execCmd.Flags().StringVarP(&commands, "commands", "c", "", "Semicolon-separated list of commands")
    execCmd.MarkFlagRequired("slot")
    execCmd.MarkFlagRequired("commands")
    return execCmd
}
