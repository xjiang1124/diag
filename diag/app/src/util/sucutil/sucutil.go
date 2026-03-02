package main

import (
    "github.com/spf13/cobra"
)

// User guild for Cobra can be found at
// https://github.com/spf13/cobra/blob/main/site/content/user_guide.md

var slot int
var commands string
var offset uint
var value uint

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
    Use:   "sucutil",
    Short: "sucutil command",
    // Uncomment the following line if your bare application
    // has an action associated with it:
    // Run: func(cmd *cobra.Command, args []string) { },
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
    rootCmd.Execute()
}

func init() {
    rootCmd.AddCommand(CreateCpldCmd())
    rootCmd.AddCommand(CreateExecCmd())
    rootCmd.AddCommand(CreateVulSelCmd())
    rootCmd.AddCommand(CreateVulPowerOnCmd())
    //add more sucutil commands here
    rootCmd.CompletionOptions.DisableDefaultCmd = true
}

func main() {
    Execute()
}
