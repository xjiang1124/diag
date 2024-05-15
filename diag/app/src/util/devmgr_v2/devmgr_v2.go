package main

import (
	"github.com/spf13/cobra"
)

// User guild for Cobra can be found at
// https://github.com/spf13/cobra/blob/main/site/content/user_guide.md

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
    Use:   "devmgr_v2",
    Short: "devmgr_v2 command",
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
    rootCmd.AddCommand(listCmd)
    rootCmd.AddCommand(statusCmd)
    rootCmd.AddCommand(faninitCmd)
    rootCmd.AddCommand(fanctrlCmd)
    rootCmd.AddCommand(marginCmd)
    rootCmd.CompletionOptions.DisableDefaultCmd = true
}

func main() {
    Execute()
}
