package main

import (
    "github.com/spf13/cobra"
    "fmt"
    "os"
)

// User guild for Cobra can be found at
// https://github.com/spf13/cobra/blob/main/site/content/user_guide.md

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
    Use:   "fpgautil_v2",
    Short: "fpgautil_v2 command",
    // Uncomment the following line if your bare application
    // has an action associated with it:
    // Run: func(cmd *cobra.Command, args []string) { },
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Println(err)
        os.Exit(-1)
    }
}

func init() {
    rootCmd.AddCommand(programCmd)
    rootCmd.AddCommand(validateCmd)
    rootCmd.AddCommand(flashDumpCmd)
    rootCmd.CompletionOptions.DisableDefaultCmd = true
}

func main() {
    Execute()
}
