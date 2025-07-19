package panareafpga
import (
    "device/fpga/materafpga"
)


/*
 * Registers offset
 */





//Convert registger and address from excel spreadsheet.  Save 2 columns to reg1.txt and run commands below
//awk '{print "FPGA_" $0}' reg1.txt > reg1_.txt
//awk '{ printf "const %-28s uint64 = 0x%s\n", $1, $2 }' ./reg1_.txt > reg2_.txt
//awk '{ printf "    FPGA_REGISTERS{\"FGPA_%-26s\",             FPGA_%s},\n", $1, $1 }' ./reg1.txt > reg3_.txt

const FPGA_S0_CONTROL_REG       uint64 = 0x180
const FPGA_S1_CONTROL_REG       uint64 = 0x184
const FPGA_S2_CONTROL_REG       uint64 = 0x188
const FPGA_S3_CONTROL_REG       uint64 = 0x18C
const FPGA_S4_CONTROL_REG       uint64 = 0x190
const FPGA_S5_CONTROL_REG       uint64 = 0x194
const FPGA_S6_CONTROL_REG       uint64 = 0x198
const FPGA_S7_CONTROL_REG       uint64 = 0x19C
const FPGA_S8_CONTROL_REG       uint64 = 0x1A0
const FPGA_S9_CONTROL_REG       uint64 = 0x1A4



var PANAREA_FPGA_REGISTERS = append(
    materafpga.MATERA_FPGA_REGISTERS,
    materafpga.FPGA_REGISTERS{"FPGA_S0_CONTROL_REG           ",             FPGA_S0_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S1_CONTROL_REG           ",             FPGA_S1_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S2_CONTROL_REG           ",             FPGA_S2_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S3_CONTROL_REG           ",             FPGA_S3_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S4_CONTROL_REG           ",             FPGA_S4_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S5_CONTROL_REG           ",             FPGA_S5_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S6_CONTROL_REG           ",             FPGA_S6_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S7_CONTROL_REG           ",             FPGA_S7_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S8_CONTROL_REG           ",             FPGA_S8_CONTROL_REG},
    materafpga.FPGA_REGISTERS{"FPGA_S9_CONTROL_REG           ",             FPGA_S9_CONTROL_REG},
)
