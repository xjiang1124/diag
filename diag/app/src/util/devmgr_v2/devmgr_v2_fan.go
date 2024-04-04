package main

import (
    "fmt"
    "os"
    "github.com/spf13/cobra"
    "device/fpga/materafpga"
)

var faninitCmd = &cobra.Command{
    Use:   "faninit",
    Short: "Initialize the fans to a default state",
    Run: func(cmd *cobra.Command, args []string) {
        materafpga.Fan_Init()
    },
}


var fanctrlCmd = &cobra.Command{
    Use:   "fanctrl",
    Short: "Set the fan speed",
    Run: func(cmd *cobra.Command, args []string) {
        pwmPercent, _ := cmd.Flags().GetUint32("pct")
        if pwmPercent > 100 {
            fmt.Printf("ERROR: Pwm percent must be 0 - 100.  You entered %d\n", pwmPercent)
            os.Exit(-1)
        }
        for i:=0; i<materafpga.MAXFAN; i++ {
            materafpga.FAN_Set_PWM(uint32(i), pwmPercent) 
        }
    },
}


func init() {
    fanctrlCmd.Flags().Uint32("pct", 100, "PWM percent 0 - 100")
    fanctrlCmd.MarkFlagRequired("pct")
}
