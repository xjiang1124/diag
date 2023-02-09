package main


import (
    "os"
    "fmt"
    "strconv"
    "device/fpga/liparifpga"
)


        
const errhelpLipari = "\nfpgautil:\n" +
        "fpgautil regdump <fgpa0/fpga1>\n" 
        

                               

func lipari_fpga_cli() {
    argc := len(os.Args[0:])

    if argc < 3 {
        fmt.Printf(" %s \n", errhelpLipari)
        return
    }

    if os.Args[1] == "regdump" {
        fpga_number, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        //taorfpga.FpgaDumpRegionRegisters(uint32(fpga_region))
        fmt.Printf(" FPGA0_FPGA_REV_ID_REG=%x\n  fpga_number=%d", liparifpga.FPGA0_FPGA_REV_ID_REG, fpga_number)
        os.Exit(0)
    }
    return
}
 
