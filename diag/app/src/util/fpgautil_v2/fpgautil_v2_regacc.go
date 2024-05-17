package main

import (
    "fmt"
    "os"
    "github.com/spf13/cobra"
    "device/fpga/materafpga"
)

var regrdCmd = &cobra.Command{
    Use:   "regrd",
    Short: "FPGA register read",
    Run: func(cmd *cobra.Command, args []string) {
        var err error
        var addr, data32 uint32
        addr, err = cmd.Flags().GetUint32("addr")
        if err != nil {
            fmt.Printf(" Error reading addr arg\n")
            os.Exit(-1)
        }
        data32, err = materafpga.MateraReadU32(uint64(addr))
        if err != nil {
            fmt.Printf("ERROR: MateraReadU32 Failed")
            os.Exit(-1)
        }
        fmt.Printf("RD [0x%.04x] = 0x%.08x\n", addr, data32)

        os.Exit(0)
    },
}


var regwrCmd = &cobra.Command{
    Use:   "regwr",
    Short: "FPGA register write",
    Run: func(cmd *cobra.Command, args []string) {
        var err error
        var addr, data32 uint32
        addr, err = cmd.Flags().GetUint32("addr")
        if err != nil {
            fmt.Printf(" Error reading addr arg\n")
            os.Exit(-1)
        }
        data32, err = cmd.Flags().GetUint32("data")
        if err != nil {
            fmt.Printf(" Error reading data arg\n")
            os.Exit(-1)
        }
        err = materafpga.MateraWriteU32(uint64(addr), data32)
        fmt.Printf("WR [0x%.04x] = 0x%.08x\n", addr, data32)
        os.Exit(0) 
    },
}


func init() {

    //regrd command
    regrdCmd.Flags().Uint32("addr", 100, "Register Address to read")
    regrdCmd.MarkFlagRequired("addr")

    //regwr command
    regwrCmd.Flags().Uint32("addr", 100, "Register Address to write")
    regwrCmd.MarkFlagRequired("addr")
    regwrCmd.Flags().Uint32("data", 100, "Data to write")
    regwrCmd.MarkFlagRequired("data")
}

