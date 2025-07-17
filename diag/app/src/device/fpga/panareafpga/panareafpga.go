package panareafpga
import (
    //"errors"
    "fmt"
    //"common/errType"
    "device/fpga/materafpga"
)

func FpgaDumpRegionRegisters() (err error) {

    var data32 uint32 = 0

    fmt.Printf("PANAREA FPGA REGISTER DUMP---\n")
    for _, entry := range(PANAREA_FPGA_REGISTERS) {

        data32, err = materafpga.MateraReadU32(uint64(entry.Address))
        if err != nil {
            return
        }
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }
    fmt.Printf("\n");

    return
}
