package main

import (
    "fmt"
    "os"
    "time"
    "github.com/spf13/cobra"
    "device/fpga/materafpga"
)

var programCmd = &cobra.Command{
    Use:   "program",
    Short: "Program FPGA Flash",
    Run: func(cmd *cobra.Command, args []string) {
        var err error = nil
        flashPartition, _ := cmd.Flags().GetString("partition")
        filename, _ := cmd.Flags().GetString("filename")
        
        t1 := time.Now()
        err = materafpga.Spi_flash_WriteImage(materafpga.SPI_FPGA, flashPartition, filename)
        if err != nil {
            os.Exit(-1)
        }
        t2 := time.Now()
        fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
        err = materafpga.Spi_flash_VerifyImage(materafpga.SPI_FPGA, flashPartition, filename)
        if err != nil {
            os.Exit(-1)
        }
        t3 := time.Now()
        fmt.Println(" Verifying the image took ", t3.Sub(t2), " time")
        os.Exit(0)

    },
}


var validateCmd = &cobra.Command{
    Use:   "validate",
    Short: "Validate FPGA Flash",

    Run: func(cmd *cobra.Command, args []string) {
        flashPartition, _ := cmd.Flags().GetString("partition")
        fmt.Printf(" partition ='%s'\n", flashPartition)
        filename, _ := cmd.Flags().GetString("filename")
        fmt.Printf(" filename ='%s'\n", filename)
        var err error = nil
        t1 := time.Now()
        err = materafpga.Spi_flash_VerifyImage(materafpga.SPI_FPGA, flashPartition, filename)
        if err != nil {
            os.Exit(-1)
        }
        t2 := time.Now()
        fmt.Println(" Verifying the image took ", t2.Sub(t1), " time")
        os.Exit(0)

    },
}


var flashDumpCmd = &cobra.Command{
    Use:   "dump",
    Short: "Dump FPGA Flash to a file",
    Run: func(cmd *cobra.Command, args []string) {
        var err error = nil
        var flashPartition, filename string
        flashPartition, err = cmd.Flags().GetString("partition")
        if err != nil {
            fmt.Printf(" Error reading partition arg. error=%v\n", err)
            os.Exit(-1)
        }
        fmt.Printf(" partition ='%s'\n", flashPartition)
        filename, err = cmd.Flags().GetString("filename")
        if err != nil {
            fmt.Printf(" Error reading partition arg,  error=%v\n", err)
            os.Exit(-1)
        }
        fmt.Printf(" filename ='%s'\n", filename)
        
        t1 := time.Now()
        err = materafpga.Spi_flash_GenerateImageFromFlash(materafpga.SPI_FPGA, flashPartition, filename)
        if err != nil {
            os.Exit(-1)
        }
        t2 := time.Now()
        fmt.Println(" Generating the image took ", t2.Sub(t1), " time")
        os.Exit(0)

    },
}


func init() {
    programCmd.Flags().StringP("partition", "p", "", "primary/secondary/allflash")
    programCmd.MarkFlagRequired("partition")
    programCmd.Flags().StringP("filename", "f", "", "file to flash")
    programCmd.MarkFlagRequired("filename")

    validateCmd.Flags().StringP("partition", "p", "", "primary/secondary/allflash")
    validateCmd.MarkFlagRequired("partition")
    validateCmd.Flags().StringP("filename", "f", "", "file to verify against the flash partition")
    validateCmd.MarkFlagRequired("filename")

    flashDumpCmd.Flags().StringP("partition", "p", "", "primary/secondary/allflash")
    flashDumpCmd.MarkFlagRequired("partition")
    flashDumpCmd.Flags().StringP("filename", "f", "", "file to verify against the flash partition")
    flashDumpCmd.MarkFlagRequired("filename")
}
