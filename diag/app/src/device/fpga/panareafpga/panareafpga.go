package panareafpga
import (
    "bufio"
    "fmt"
    "os"
    "os/exec"
    "strconv"
    "strings"
    "syscall"
    "unsafe"
    "common/cli"
)

const (
    PSU0 = 0
    PSU1 = 1
    MAXPSU = 2
    FAN0 = 0
    FAN1 = 1
    FAN2 = 2
    FAN3 = 3
    FAN4 = 4
    MAXFAN = 5
    DUALFAN = 1
    MAXSLOTS = 10       //10 NORMAL SLOTS
    DEBUGSLOTS = 1      //AND A DEBUG SLOT FOR 10+1 SLOTS
)

var Glob_fd0 *os.File = nil
var Glob_mmap0 []byte

const MAP_SIZE int = 1048576


func init () {
    var cardType string
    cardType = os.Getenv("CARD_TYPE")
    if cardType == "MTP_PANAREA" {
    var bar uint64 =0
    exists, _ := Path_exists("/tmp/fpgabars")

    //TRY TO STORE THE BAR VALUES IN A FILE.  WE DONT WANT TO SCAN THE PCI AND GET THE BARS EVERYTIME WE USE ONE OF THE DIAG UTILITIES THAT CALLS THIS INIT
    if exists == true {
        file, errGo := os.Open("/tmp/fpgabars")
        if errGo != nil {
            cli.Println("e", "ERROR: Failed to get FPGA BAR VALUE.   GO ERROR=%v", errGo)
            return
        }
        scanner := bufio.NewScanner(file)
        for scanner.Scan() {
            line := scanner.Text()
            bar, _ = strconv.ParseUint(strings.TrimSuffix(line, "\n"), 0, 64)
        }
        file.Close()
    } else {
        shcmds := []string{ "lspci -v -d 1dd8:000B | grep 'Memory at' | awk '{print $3}'"}
        execOutput, errGo := exec.Command("sh", "-c", shcmds[0] ).Output()
        if errGo != nil {
            cli.Println("e", "ERROR: Failed to get FPGA BAR VALUE.   GO ERROR=%v", errGo)
            return
        }
        tmp := "0x" + strings.TrimSuffix(string(execOutput), "\n")
        bar, _ = strconv.ParseUint(tmp, 0, 64) 

        file, errGo := os.OpenFile("/tmp/fpgabars", os.O_RDWR | os.O_CREATE | os.O_TRUNC, 0644)
        if errGo != nil {
            cli.Println("e", "ERROR: Failed to get open file /tmp/fpgabars.   GO ERROR=%v", errGo)
            return
        }
        datawriter := bufio.NewWriter(file)
        _, _ = datawriter.WriteString(fmt.Sprintf("0x%x\n", bar))
 
        datawriter.Flush()
        file.Close() 
         
    }
    Glob_mmap0, Glob_fd0, _ = MMAP_Device(int64(bar), MAP_SIZE)
    }
}
 
 
// exists returns whether the given file or directory exists
func Path_exists(path string) (bool, error) {
    _, err := os.Stat(path)
    if err == nil { return true, nil }
    if os.IsNotExist(err) { return false, nil }
    return false, err
}


func MMAP_Device(addr int64, size int) (mmap []byte, fd *os.File, err error) {
    fd, err = os.OpenFile("/dev/mem", os.O_RDWR, 0333)
    if err != nil {
        cli.Printf("e", "os.Open /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err) 
        return 
    }

    mmap, err = syscall.Mmap(int(fd.Fd()), addr, size, syscall.PROT_READ | syscall.PROT_WRITE, syscall.MAP_SHARED)
    fd.Close()
    if err != nil {
        cli.Printf("e", "syscall.Mmap failed.  Err !=nil:   ERR = '%s'\n", err)  
        fd.Close()
        return 
    }
   
    return 
} 
 

func ReadU8(addr uint64) (value uint8, err error) {
    value = *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr]))
    return
}


func ReadU16(addr uint64) (value uint16, err error) {
    value = *(*uint16)(unsafe.Pointer(&Glob_mmap0[addr]))
    return
}


func ReadU32(addr uint64) (value uint32, err error) {
    value = *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr]))
    return
}


func WriteU8(addr uint64, data uint8) (err error) {
    *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr])) = data
    return
}


func WriteU16(addr uint64, data uint16) (err error) {
    *(*uint16)(unsafe.Pointer(&Glob_mmap0[addr])) = data
    return
}


func WriteU32(addr uint64, data uint32) (err error) {
    *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr])) = data
    return
}


func FpgaDumpRegionRegisters() (err error) {

    var data32 uint32 = 0

    fmt.Printf("PANAREA FPGA REGISTER DUMP---\n")
    for _, entry := range(PANAREA_FPGA_REGISTERS) {

        data32, err = ReadU32(uint64(entry.Address))
        if err != nil {
            return
        }
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }
    fmt.Printf("\n");

    return
}


func PSU_present(PSUnumber uint32) (present bool, err error) {
    var data32 uint32
    present = false

    if PSUnumber > (MAXPSU - 1) {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = ReadU32(FPGA_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  FPGA_PSU_STAT_PRSNT0) == FPGA_PSU_STAT_PRSNT0) {
        present = true
    }
    if PSUnumber == PSU1 && ( (data32 &  FPGA_PSU_STAT_PRSNT1) == FPGA_PSU_STAT_PRSNT1) {
        present = true
    }
    return
}


/*************************************************************
* Check NIC slot present
**************************************************************/
func SLOTpresent(slotNumber uint32) (present bool, err error) {
    var data32 uint32
    present = false

    if slotNumber > ((MAXSLOTS + DEBUGSLOTS) - 1) {
        err = fmt.Errorf(" Error: SLOT_present.  SLOT NUMBER PASSED (%d) IS NOT VALID!", slotNumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = ReadU32(FPGA_MISC_STAT_REG)
    if err != nil {
        return
    }
    data32 = (data32 & FPGA_MISC_STAT_SLOT_MASK) >> FPGA_MISC_STAT_SLOT_SHIFT;

    //Present is Zero based, not 1 based for this one
    if ( (data32 & (1<<slotNumber)) == 0 ) {
        present = true
    }

    return
}


/*************************************************************
* Check NIC slot present based on UUT_SLOT# format. 
* Example:   UUT_10 
**************************************************************/
func SLOTpresentUUT(uutName string) (present bool, err error) {
    strLength := len(uutName)
    if strLength < 5 {
        err = fmt.Errorf(" Error: SLOTpresentUUT.  String passed is less than 5 characters.  Expectings something like UUT_5")
        cli.Printf("e", "%s", err)
        return
    }
    slotNumber, err := strconv.ParseUint(uutName[4:strLength], 0, 32)
    //Zero based
    slotNumber = slotNumber - 1 
    if err != nil {
        fmt.Printf("ERROR: Pasring Slot number failed. Go Erro ->  %v", err)
        return
    }

    present, err = SLOTpresent(uint32(slotNumber))
    return
}
