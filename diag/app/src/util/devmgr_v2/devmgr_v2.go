package main

import (
    //"fmt"
    //"flag"
    //"os"
    "strings"

    //"common/cli"
    //"common/errType"
    //"config"
    "hardware/i2cinfo"
    "hardware/hwdev"
    //"device/tempsensor/tmp451"
	"github.com/spf13/cobra"
)

// User guild for Cobra can be found at
// https://github.com/spf13/cobra/blob/main/site/content/user_guide.md

var slot string
var devName string

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "devmgr_v2",
	Short: "devmgr_v2 command",
	Long:  `devmgr_v2 command`,
	// Uncomment the following line if your bare application
	// has an action associated with it:
	// Run: func(cmd *cobra.Command, args []string) { },
}

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List all i2c devices",
	Long:  `List all i2c devices`,
	Run: func(cmd *cobra.Command, args []string) {
        i2cinfo.SwitchI2cTbl(strings.ToUpper(slot))
        i2cinfo.DispI2cInfoAll()
	},
}

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Device status",
	Long:  `Device status`,
	Run: func(cmd *cobra.Command, args []string) {
        hwdev.DispStatus(strings.ToUpper(devName), strings.ToUpper(slot))
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	rootCmd.Execute()
}

func init() {
	listCmd.Flags().StringVarP(&slot, "slot", "s", "UUT_NONE", "UUT name, e.g. UUT_1")

	statusCmd.Flags().StringVarP(&slot, "slot", "s", "UUT_NONE", "UUT name, e.g. UUT_1")
	statusCmd.Flags().StringVarP(&devName, "dev", "d", "ALL", "Device name")

	rootCmd.AddCommand(listCmd)
	rootCmd.AddCommand(statusCmd)
    rootCmd.CompletionOptions.DisableDefaultCmd = true
}

func main() {
    Execute()
}
