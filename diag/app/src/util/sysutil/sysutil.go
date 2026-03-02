package main

import (
	"github.com/spf13/cobra"
)

var slot_num int

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "sysutil",
	Short: "sysutil command",
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	rootCmd.Execute()
}

func init() {
	rootCmd.AddCommand(CreateCardPresentCmd())
	rootCmd.AddCommand(CreateCardPoweredOnCmd())
	rootCmd.CompletionOptions.DisableDefaultCmd = true
}

func main() {
	Execute()
}
