package main

import (
    "fmt"
    "os"
    "github.com/spf13/cobra"
    "hardware/hwdev"
)

var faninitCmd = &cobra.Command{
    Use:   "faninit",
    Short: "Initialize the fans to a default state",
    Run: func(cmd *cobra.Command, args []string) {
        //This will need an arg for fan controller number if this ever supports 
        //a platform with more than one fan controller
        devName, _ := hwdev.FanGetDeviceName(0)
        hwdev.FanSetup(devName)
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
        devName, _ := hwdev.FanGetDeviceName(0)
        hwdev.FanSpeedSet(devName, int(pwmPercent), 0xFF)
        fmt.Printf("Fan PWM set to %d percent\n", pwmPercent)
    },
}


func init() {
    fanctrlCmd.Flags().Uint32("pct", 100, "PWM percent 0 - 100")
    fanctrlCmd.MarkFlagRequired("pct")
}
