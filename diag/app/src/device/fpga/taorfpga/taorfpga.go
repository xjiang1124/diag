/* Notes
 
SPI BUS HOOKUP 
SPI0 = CPU CPLD 
SPI1 = ELBA0 CPLD
SPI2 = ELBA1 CPLD
SPI3 = GPIO CPLD0
SPI4 = GPIO CPLD1
SPI5 = GPIO CPLD2
SPI6 = ELBA0 SERIAL FLASH
SPI7 = ELBA1 SERIAL FLASH 
 
 
*/ 
 
package taorfpga

import (
    "bufio"
    "errors"
    "fmt"
    "os"
    "os/exec"
    "strconv"
    "time"
    "strings"
    "syscall"
    "unsafe"

    "common/cli"
    //"common/errType"
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
    FAN5 = 5
    MAXFAN = 6
    AIRFLOW_FRONT_TO_BACK = 0
    AIRFLOW_BACK_TO_FRONT = 1
    AIRFLOW_MIXED_ERROR = 2
    MAXSFP = 48
    MAXQSFP = 6
)

const (
    ELBA0 = 0
    ELBA1 = 1
    TD3   = 2
    ALL   = 3
    NUMBER_ELBAS = 2

    ELBA0_PCIBUS = "0b:00.0"
    ELBA1_PCIBUS = "05:00.0"
    ELBA0_ETH_PCIBUS = "0d:00.0"
    ELBA1_ETH_PCIBUS = "07:00.0"
    
)

const (
    POWER_STATE_CYCLE = 1
    POWER_STATE_OFF   = 2
    POWER_STATE_ON    = 3
)


const MEM_ACCESS_32  uint32 = 1
const MEM_ACCESS_64  uint32 = 2

/* ELBA PCI DEVICES
05:00.0 0604: 1dd8:0002
06:00.0 0604: 1dd8:1001
07:00.0 0200: 1dd8:1004
 
0b:00.0 0604: 1dd8:0002
0c:00.0 0604: 1dd8:1001
0d:00.0 0200: 1dd8:1004 
*/ 

/* FPGA PCI DEVICES
12:00.0 0000: 1dd8:0003
12:00.1 0000: 1dd8:0004
12:00.2 0000: 1dd8:0005
12:00.3 0000: 1dd8:0006
*/ 
const TAORMINA_PCI_VENDOR_ID  uint32 = 0x1dd8
const TAORMINA_MAX_PCI_DEV    uint32 = 0x0004
const TAORMINA_PCI_DEV_ID0    uint32 = 0x0003
const TAORMINA_PCI_DEV_ID1    uint32 = 0x0004
const TAORMINA_PCI_DEV_ID2    uint32 = 0x0005
const TAORMINA_PCI_DEV_ID3    uint32 = 0x0006


var Glob_fd0 *os.File = nil
var Glob_fd1 *os.File = nil
var Glob_fd2 *os.File = nil
var Glob_fd3 *os.File = nil
var Glob_mmap0 []byte
var Glob_mmap1 []byte
var Glob_mmap2 []byte
var Glob_mmap3 []byte
 
const FPGAstrappingOverrideFile = "/tmp/fpga_rev_override.txt" 


func init () {
    var cardType string
    
    //quick hack to see if we are a Taormina since diag env is not setup yet
    exists, _ := Path_exists("/etc/openswitch/platform/HPE/10000")
    if exists == true {
        os.Setenv("CARD_TYPE","TAORMINA")
        cardType = "TAORMINA"
    } else {
        cardType = os.Getenv("CARD_TYPE")
        if cardType == "TAORMINA" {
            os.Setenv("CARD_TYPE","TAORMINA")
            cardType = "TAORMINA"
        } else if cardType != "TAORMINA" { 
            out, errGo := exec.Command("uname", "-a").Output()
            if errGo != nil {
                cli.Println("e", errGo)
            }
            if strings.Contains(string(out), "Taormina")==true {
                os.Setenv("CARD_TYPE","TAORMINA")
                cardType = "TAORMINA"
            }
            if strings.Contains(string(out), "ServiceOS")==true {
                os.Setenv("CARD_TYPE","TAORMINA")
                cardType = "TAORMINA"
            }
        }
    }
    if cardType == "TAORMINA" {
        bar := []uint64 { 0,0,0,0 }
        exists, _ := Path_exists("/tmp/fpgabars")
        //TRY TO STORE THE BAR VALUES IN A FILE.  WE DONT WANT TO SCAN THE PCI AND GET THE BARS EVERYTIME WE USE ONE OF THE DIAG UTILITIES THAT CALLS THIS INIT
        if exists == true {
            var i int
            file, errGo := os.Open("/tmp/fpgabars")
            if errGo != nil {
                cli.Println("e", "ERROR: Failed to get FPGA BAR VALUE.   GO ERROR=%v", errGo)
                return
            }
            scanner := bufio.NewScanner(file)
            for scanner.Scan() {
                bar[i], _ = strconv.ParseUint(strings.TrimSuffix(scanner.Text(), "\n"), 0, 64)
                i++
            }
            file.Close()
        } else {
            shcmds := []string{ "lspci -s 12:00.0 -v | grep Memory | awk '{print $3}'", 
                                "lspci -s 12:00.1 -v | grep Memory | awk '{print $3}'", 
                                "lspci -s 12:00.2 -v | grep Memory | awk '{print $3}'", 
                                "lspci -s 12:00.3 -v | grep Memory | awk '{print $3}'" }
            for i:=0;i<len(shcmds);i++ {
                execOutput, errGo := exec.Command("sh", "-c", shcmds[i] ).Output()
                if errGo != nil {
                    cli.Println("e", "ERROR: Failed to get FPGA BAR VALUE.   GO ERROR=%v", errGo)
                    return
                }
                tmp := "0x" + strings.TrimSuffix(string(execOutput), "\n")
                if i==0        { bar[0], _ = strconv.ParseUint(tmp, 0, 64) 
                } else if i==1 { bar[1], _ = strconv.ParseUint(tmp, 0, 64) 
                } else if i==2 { bar[2], _ = strconv.ParseUint(tmp, 0, 64) 
                } else if i==3 { bar[3], _ = strconv.ParseUint(tmp, 0, 64) }
            }

            file, errGo := os.OpenFile("/tmp/fpgabars", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
            if errGo != nil {
                cli.Println("e", "ERROR: Failed to get open file /tmp/fpgabars.   GO ERROR=%v", errGo)
                return
            }
            datawriter := bufio.NewWriter(file)
            for i:=0;i<len(bar);i++ {
                    _, _ = datawriter.WriteString(fmt.Sprintf("0x%x\n", bar[i]))
            }
     
            datawriter.Flush()
            file.Close()
        }
        Glob_mmap0, Glob_fd0, _ = MMAP_Device(int64(bar[0]), MAP_SIZE)
        Glob_mmap1, Glob_fd1, _ = MMAP_Device(int64(bar[1]), MAP_SIZE)
        Glob_mmap2, Glob_fd2, _ = MMAP_Device(int64(bar[2]), MAP_SIZE)
        Glob_mmap3, Glob_fd3, _ = MMAP_Device(int64(bar[3]), MAP_SIZE)
        //How do we gracefully unmap?   OS should do it, but would be nice to do it in code 
        
        //defer func() {
        //    MunMAP_Device(Glob_fd0, Glob_mmap0)
        //    MunMAP_Device(Glob_fd1, Glob_mmap1)
        //    MunMAP_Device(Glob_fd2, Glob_mmap2)
        //    MunMAP_Device(Glob_fd3, Glob_mmap3)
        //    fmt.Printf(" ADD DEBUG: Munmap\n")
        //} () 
    }
} 
 

// exists returns whether the given file or directory exists
func Path_exists(path string) (bool, error) {
    _, err := os.Stat(path)
    if err == nil { return true, nil }
    if os.IsNotExist(err) { return false, nil }
    return false, err
}


func FpgaDumpRegionRegisters(devRegion uint32) (err error) {

    var data32 uint32 = 0
    var taor_reg_ptr []TAOR_FPGA_REGISTERS
    

    if uint32(devRegion) >= TAORMINA_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINA_MAX_PCI_DEV -1), devRegion); 
        err = errors.New(" ERROR") 
        return
    }

    if devRegion == 0 {
        taor_reg_ptr = TAOR_DEV0_REGISTERS
    } else if devRegion == 1 {
        taor_reg_ptr = TAOR_DEV1_REGISTERS
    } else if devRegion == 2 {
        taor_reg_ptr = TAOR_DEV2_REGISTERS
    } else {
        taor_reg_ptr = TAOR_DEV3_REGISTERS
    }
    

    fmt.Printf("FPGA DEVICE REGION-%d REGISTER DUMP---\n", devRegion)
    for _, entry := range(taor_reg_ptr) {

        data32, err = TaorReadU32(devRegion, uint64(entry.Address))
        if err != nil {
            return
        }
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }
    fmt.Printf("\n");

    return
}



func TaorReadU8(devID uint32, addr uint64) (value uint8, err error) {
    //var bar uint64
    //var pcidevid uint32

    if uint32(devID) >= TAORMINA_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINA_MAX_PCI_DEV -1), devID); 
        err = errors.New(" ERROR") 
        return
    }

    switch(devID){
        case 0: value = *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr])); break
        case 1: value = *(*uint8)(unsafe.Pointer(&Glob_mmap1[addr])); break
        case 2: value = *(*uint8)(unsafe.Pointer(&Glob_mmap2[addr])); break
        case 3: { 
            value = *(*uint8)(unsafe.Pointer(&Glob_mmap3[addr]));
            break
        }
    }
    return
}

func TaorReadU32(devID uint32, addr uint64) (value uint32, err error) {
    var bar uint64
    //var pcidevid uint32

    if uint32(devID) >= TAORMINA_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINA_MAX_PCI_DEV -1), devID); 
        err = errors.New(" ERROR") 
        return
    }

    switch(devID){
        case 0: value = *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr])); break
        case 1: value = *(*uint32)(unsafe.Pointer(&Glob_mmap1[addr])); break
        case 2: value = *(*uint32)(unsafe.Pointer(&Glob_mmap2[addr])); break
        case 3: { 
            value = *(*uint32)(unsafe.Pointer(&Glob_mmap3[addr]));
            break
        }
    }
    return

    /*
    pcidevid = (TAORMINA_PCI_VENDOR_ID<<16 |  (TAORMINA_PCI_DEV_ID0 + uint32(devID)))
    err = PCI_get_bar(pcidevid, &bar)
    if err != nil {
        cli.Printf("e", "Failed to find FPGA DevID 0x%x memory bar", pcidevid)
        return
    }
    fmt.Printf(" Bar=%x\n", bar) 
    */ 
    
    switch(devID){
        case 0: bar = uint64(DEV0_BAR)
        case 1: bar = uint64(DEV1_BAR)
        case 2: bar = uint64(DEV2_BAR)
        case 3: bar = uint64(DEV3_BAR)
    } 
     

    value, err = ReadU32(uint64(bar) + addr)
    return
}

func ReadU32(addr uint64) (value uint32, err error) {
    pageSize := syscall.Getpagesize()
    pageSize64 := uint64(pageSize)
    pageAddr := addr / pageSize64 * pageSize64
    pageOffset := addr - pageAddr

    file, err := os.Open("/dev/mem")
    if err != nil {
        cli.Printf("e", "os.Open /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err)
        return
    }

    defer file.Close()
    mmap, err := syscall.Mmap(int(file.Fd()), int64(pageAddr), pageSize, syscall.PROT_READ, syscall.MAP_SHARED)
    if err != nil {
        cli.Printf("e", "syscall.Mmap /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err)
        return
    }
    value = *(*uint32)(unsafe.Pointer(&mmap[pageOffset]))
    err = syscall.Munmap(mmap) 
    if err != nil {
        cli.Printf("e", " syscall.Munmap failed.  Err !=nil:   ERR = '%s'\n", err)  
        return 
    }
    return
}

func TaorWriteU8(devID uint32, addr uint64, data uint8) (err error) {
    if uint32(devID) >= TAORMINA_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINA_MAX_PCI_DEV -1), devID); 
        err = errors.New(" ERROR") 
        return
    }

    switch(devID){
        case 0: *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr])) = data; break
        case 1: *(*uint8)(unsafe.Pointer(&Glob_mmap1[addr])) = data; break
        case 2: *(*uint8)(unsafe.Pointer(&Glob_mmap2[addr])) = data; break
        case 3: *(*uint8)(unsafe.Pointer(&Glob_mmap3[addr])) = data; break
    }
    return
}

func TaorWriteU16(devID uint32, addr uint64, data uint16) (err error) {

    if uint32(devID) >= TAORMINA_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINA_MAX_PCI_DEV -1), devID); 
        err = errors.New(" ERROR") 
        return
    }

    switch(devID){
        case 0: *(*uint16)(unsafe.Pointer(&Glob_mmap0[addr])) = data; break
        case 1: *(*uint16)(unsafe.Pointer(&Glob_mmap1[addr])) = data; break
        case 2: *(*uint16)(unsafe.Pointer(&Glob_mmap2[addr])) = data; break
        case 3: *(*uint16)(unsafe.Pointer(&Glob_mmap3[addr])) = data; break
    }
    return
}

func TaorWriteU32(devID uint32, addr uint64, data uint32) (err error) {
    var bar uint64
    //var pcidevid uint32

    if uint32(devID) >= TAORMINA_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINA_MAX_PCI_DEV -1), devID); 
        err = errors.New(" ERROR") 
        return
    }

    switch(devID){
        case 0: *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr])) = data; break
        case 1: *(*uint32)(unsafe.Pointer(&Glob_mmap1[addr])) = data; break
        case 2: *(*uint32)(unsafe.Pointer(&Glob_mmap2[addr])) = data; break
        case 3: *(*uint32)(unsafe.Pointer(&Glob_mmap3[addr])) = data; break
    }
    return

    /*
    pcidevid = (TAORMINA_PCI_VENDOR_ID<<16 |  (TAORMINA_PCI_DEV_ID0 + uint32(devID)))
    err = PCI_get_bar(pcidevid, &bar)
    if err != nil {
        cli.Printf("e", "Failed to find FPGA DevID 0x%x memory bar", pcidevid)
        return
    }
    */
    switch(devID){
        case 0: bar = uint64(DEV0_BAR)
        case 1: bar = uint64(DEV1_BAR)
        case 2: bar = uint64(DEV2_BAR)
        case 3: bar = uint64(DEV3_BAR)
    }

    err = WriteU32(uint64(bar) + addr, data)
    return
}


func WriteU32(addr uint64, data uint32) (err error) {
    pageSize := syscall.Getpagesize()
    pageSize64 := uint64(pageSize)
    pageAddr := addr / pageSize64 * pageSize64
    pageOffset := addr - pageAddr

    file, err := os.OpenFile("/dev/mem", os.O_RDWR, 0333)
    if err != nil {
        cli.Printf("e", "os.Open /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err)
        return
    }

    defer file.Close()
    mmap, err := syscall.Mmap(int(file.Fd()), int64(pageAddr), pageSize, syscall.PROT_WRITE, syscall.MAP_SHARED)
    if err != nil {
        cli.Printf("e", "syscall.Mmap /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err)
        return
    }

    *(*uint32)(unsafe.Pointer(&mmap[pageOffset])) = data

    err = syscall.Munmap(mmap)
    if err != nil {
        cli.Printf("e", "syscall.Munmap /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err)
    }
    return
}

func PCI_get_bar(pciDevID uint32, bar *uint64) (err error) {
    var s_devfn, vend_dev_Id, irq uint32 = 0,0,0
    var mbar uint64 = 0
    var s1 string

    f, err := os.Open("/proc/bus/pci/devices")
    if err != nil {
        cli.Printf("e", "os.Open failed.  Err !=nil:   ERR = '%s'\n", err)  
        return
    }

    defer func() {
        if err = f.Close(); err != nil {
            cli.Printf("e", " f.Close() failed.  Err !=nil:   ERR = '%s'\n", err)  
        }
    }()

    s := bufio.NewScanner(f)
    err = s.Err()
    if err != nil {
        cli.Printf("e", "bufio.NewScanner() failed.  Err !=nil:   ERR = '%s'\n", err)  
        return
    }

    //fmt.Printf("[DEBUG] pciDevID-%.08x\n", pciDevID)

    for s.Scan() {
        fmt.Sscanf(s.Text(), "%x %x %x %s ", &s_devfn, &vend_dev_Id, &irq, &s1)
        if pciDevID == vend_dev_Id {
            mbar, err = strconv.ParseUint(s1, 16, 64)
            if err != nil {
                cli.Printf("e", "strconv.ParseUint failed.  Err !=nil:   ERR = '%s'\n", err)  
                return
            }
            *bar = mbar & (0xFFFFFFFFFFFFF000)  //mask to page boundy
            break;
        }
    }

    return
}


func MMAP_Device(addr int64, size int) (mmap []byte, fd *os.File, err error) {
    fd, err = os.OpenFile("/dev/mem", os.O_RDWR, 0333)
    if err != nil {
        cli.Printf("e", "os.Open /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err) 
        return 
    }

    mmap, err = syscall.Mmap(int(fd.Fd()), addr, size, syscall.PROT_READ | syscall.PROT_WRITE, syscall.MAP_SHARED)
    if err != nil {
        cli.Printf("e", "syscall.Mmap failed.  Err !=nil:   ERR = '%s'\n", err)  
        fd.Close()
        return 
    }
   
    return 
}

func MMAP_Device_Read(addr int64, size int) (mmap []byte, fd *os.File, err error) {
    //fd, err = os.Open("/dev/mem")
    fd, err = os.OpenFile("/dev/mem", os.O_RDWR, 0333)
    if err != nil {
        cli.Printf("e", "os.Open /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err) 
        return 
    }

    mmap, err = syscall.Mmap(int(fd.Fd()), addr, size, syscall.PROT_READ, syscall.MAP_SHARED)
    if err != nil {
        cli.Printf("e", "syscall.Mmap failed.  Err !=nil:   ERR = '%s'\n", err)  
        fd.Close()
        return 
    }
   
    return 
}

func MMAP_Device_Write(addr int64, size int) (mmap []byte, fd *os.File, err error) {
    fd, err = os.OpenFile("/dev/mem", os.O_RDWR, 0333)
    if err != nil {
        cli.Printf("e", "os.Open /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err) 
        return 
    }

    mmap, err = syscall.Mmap(int(fd.Fd()), addr, size, syscall.PROT_READ | syscall.PROT_WRITE, syscall.MAP_SHARED)
    if err != nil {
        cli.Printf("e", "syscall.Mmap failed.  Err !=nil:   ERR = '%s'\n", err)  
        fd.Close()
        return 
    }
   
    return 
}


func MunMAP_Device(fd *os.File, mmap []byte) (err error) {
    err = syscall.Munmap( mmap )
    if err != nil {
        cli.Printf("e", " syscall.Munmap failed.  Err !=nil:   ERR = '%s'\n", err)  
        return 
    }
    err = fd.Close()
    if  err != nil {
        cli.Printf("e", "fd.Close() failed.  Err !=nil:   ERR = '%s'\n", err)  
        return 
    }
    return 
}


func SetI2Cmux(channel uint32, mux uint32) (err error) {

    TaorWriteU32(DEVREGION3, D3_I2C_CH0_MUX_SEL_REG + uint64( channel * I2C_MAILBOX_STRIDE ) , mux) 
    return
}

/*************************************************************** 
* Strapping options for the spin 
*  
* 0x4: GB refclk spin 
* 0x5: GB refclk  spin + TPM2.0 
* 
****************************************************************/ 
func GetResistorStrapping() (value uint32, err error) {
    //Check if the strapping override file is there.  If it is take the strapping from the file
    //This is used for test purposes only
    //If no file read it directly from the fpga
    exists, _ := Path_exists(FPGAstrappingOverrideFile)
    if exists == true {
        file, errGo := os.Open(FPGAstrappingOverrideFile)
        if errGo != nil {
            cli.Println("e", "ERROR: Failed to Open", FPGAstrappingOverrideFile, " GO ERROR=%v", errGo)
            return
        }
        scanner := bufio.NewScanner(file)
        for scanner.Scan() {
            data64, _ := strconv.ParseUint(strings.TrimSuffix(scanner.Text(), "\n"), 0, 64)
            value = uint32(data64)
        }
        file.Close()
    } else {
        value, err = TaorReadU32(DEVREGION0, D0_BOARD_REV_ID_REG)
    } 
    return
}


/*************************************************************** 
*  
*  Set the resistor strapping in a tmp file
*  This is used for testing to mimic different resistor
*  strapping settings
*  
****************************************************************/ 
func SetResistorStrapping() (value uint32, err error) {
    file, errGo := os.OpenFile(FPGAstrappingOverrideFile, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if errGo != nil {
        cli.Println("e", "ERROR: Failed to Open ", FPGAstrappingOverrideFile, " GO ERROR=%v", errGo)
        return
    }
    datawriter := bufio.NewWriter(file)
    _, _ = datawriter.WriteString(fmt.Sprintf("0x%x\n", value))
    datawriter.Flush()
    file.Close()
    fmt.Printf("Wrote 0x%x to file %s\n", FPGAstrappingOverrideFile);
    return
}

func Asic_PowerCycle(device uint32, state uint32, nopciscan uint32) (err error) {
    var args string
    var data32 uint32
    var ctrl_pwr_reg, stat_reg, ctrl_reg uint64 = D1_ELBA0_PWR_CTRL_REG, D1_ELBA0_PWR_STAT_REG, D1_ELBA0_CTRL_REG
    var dev, dev_start, dev_end int

    if device > ALL {
            err = fmt.Errorf(" Error: Asic_PowerCycle.  Device number passed (%d) is not valid", device)
            cli.Printf("e", "%s", err)
            return
    }
    if state != POWER_STATE_CYCLE && state != POWER_STATE_OFF && state != POWER_STATE_ON {
            err = fmt.Errorf(" Error: Asic_PowerCycle.  Power Stated passed (%d) is not valid", state)
            cli.Printf("e", "%s", err)
            return
    }

    if device == ALL {
        dev_start = 0; dev_end = ALL;
    } else {
        dev_start = int(device); dev_end = int(device) + 1
    }

    //remove device from linux & power off
    if state == POWER_STATE_OFF || state == POWER_STATE_CYCLE {
        for dev=dev_start;dev<dev_end;dev++ {
            switch(dev){
                case ELBA0: ctrl_pwr_reg = D1_ELBA0_PWR_CTRL_REG
                            stat_reg = D1_ELBA0_PWR_STAT_REG
                            ctrl_reg = D1_ELBA0_CTRL_REG
                            fmt.Printf(" Removing Elba0 from Linux PCI Enumeration and Powering Off\n")
                case ELBA1: ctrl_pwr_reg = D1_ELBA1_PWR_CTRL_REG 
                            stat_reg = D1_ELBA1_PWR_STAT_REG
                            ctrl_reg = D1_ELBA1_CTRL_REG
                            fmt.Printf(" Removing Elba1 from Linux PCI Enumeration and Powering Off\n")
                case TD3:   ctrl_pwr_reg = D1_TD3_PWR_CTRL_REG 
                            stat_reg = D1_TD3_PWR_STAT_REG
                            fmt.Printf(" Removing TD3 from Linux PCI Enumeration and Powering Off\n")
            }
            switch(dev){
                case ELBA0: args = "echo 1 > /sys/bus/pci/devices/0000:0b:00.0/remove"
                case ELBA1: args = "echo 1 > /sys/bus/pci/devices/0000:05:00.0/remove"
                case TD3:   args = "echo 1 > /sys/bus/pci/devices/0000:01:00.0/remove" 
            }
            exec.Command("bash", "-c", args).Output()
            time.Sleep(time.Duration(1) * time.Second) 

            if dev == ELBA0 || dev == ELBA1 {
                TaorWriteU32(DEVREGION1, ctrl_pwr_reg, 0x53) 
                TaorWriteU32(DEVREGION1, ctrl_reg, 0x3) 
                if dev == ELBA0 {
                    TaorWriteU32(DEVREGION2, D2_SPI4_MUXSEL_REG, 0x0) 
                    TaorWriteU32(DEVREGION2, D2_SPI1_MUXSEL_REG, 0x0) 
                    TaorWriteU32(DEVREGION2, D2_SPI6_MUXSEL_REG, 0x0)
                } else {
                    TaorWriteU32(DEVREGION2, D2_SPI5_MUXSEL_REG, 0x0) 
                    TaorWriteU32(DEVREGION2, D2_SPI2_MUXSEL_REG, 0x0) 
                    TaorWriteU32(DEVREGION2, D2_SPI7_MUXSEL_REG, 0x0)
                }
            }
            if dev == TD3 {
                TaorWriteU32(DEVREGION1, D1_TD_CTRL_REG, 0x1ff) 
                TaorWriteU32(DEVREGION1, D1_TD3_PWR_CTRL_REG, 0x53) 
            }
        }
        time.Sleep(time.Duration(500) * time.Millisecond)
    }

    //power up if needed
    if state == POWER_STATE_ON || state == POWER_STATE_CYCLE {
        for dev=dev_start;dev<dev_end;dev++ {
            switch(dev){
                case ELBA0: ctrl_pwr_reg = D1_ELBA0_PWR_CTRL_REG
                            stat_reg = D1_ELBA0_PWR_STAT_REG
                            ctrl_reg = D1_ELBA0_CTRL_REG
                            TaorWriteU32(DEVREGION2, D2_SPI4_MUXSEL_REG, 0x1) 
                            TaorWriteU32(DEVREGION2, D2_SPI1_MUXSEL_REG, 0x1) 
                            TaorWriteU32(DEVREGION2, D2_SPI6_MUXSEL_REG, 0x1)
                case ELBA1: ctrl_pwr_reg = D1_ELBA1_PWR_CTRL_REG
                            stat_reg = D1_ELBA1_PWR_STAT_REG
                            ctrl_reg = D1_ELBA1_CTRL_REG
                            TaorWriteU32(DEVREGION2, D2_SPI5_MUXSEL_REG, 0x1) 
                            TaorWriteU32(DEVREGION2, D2_SPI2_MUXSEL_REG, 0x1) 
                            TaorWriteU32(DEVREGION2, D2_SPI7_MUXSEL_REG, 0x1)
                case TD3:   ctrl_pwr_reg = D1_TD3_PWR_CTRL_REG
                            stat_reg = D1_TD3_PWR_STAT_REG
            }
            if dev == ELBA0 || dev == ELBA1 {
                if nopciscan == 1 {
                    fmt.Printf(" Powering up Elba-%d\n", dev)
                } else {
                    fmt.Printf(" Powering up Elba and Waiting 15 seconds for Elba to boot and enumerate\n")
                }
                TaorWriteU32(DEVREGION1, ctrl_reg, 0x1) 
                TaorWriteU32(DEVREGION1, ctrl_pwr_reg, 0xD1) 
                time.Sleep(time.Duration(300) * time.Millisecond)
                TaorWriteU32(DEVREGION1, ctrl_reg, 0x0)
                time.Sleep(time.Duration(1000) * time.Millisecond) 
            }
            if dev == TD3 {
                if nopciscan == 1 {
                    fmt.Printf(" Powering up TD3\n")
                } else {
                    fmt.Printf(" Powering up TD3 and Waiting 5 seconds for TD3 to come up and enumerate\n")
                }
                TaorWriteU32(DEVREGION1, D1_TD3_PWR_CTRL_REG, 0xd1) 
                time.Sleep(time.Duration(100) * time.Millisecond)
                TaorWriteU32(DEVREGION1, D1_TD_CTRL_REG, 0x1fd) 
                time.Sleep(time.Duration(100) * time.Millisecond)
                TaorWriteU32(DEVREGION1, D1_TD_CTRL_REG, 0x0) 
                
                data32, err = TaorReadU32(DEVREGION1, stat_reg)
                if (data32 & 0x2) != 0x2 {
                    err = fmt.Errorf(" Error: Asic_PowerCycle.  FPGA status indicates Device did not power up ok")
                    cli.Printf("e", "%s", err)
                    return
                }
            }
        }

        // Sleep .. duration depends on what is getting reset
        if nopciscan == 0 {
            switch(device){
                case ALL: time.Sleep(time.Duration(15) * time.Second); break
                case ELBA0: time.Sleep(time.Duration(15) * time.Second); break
                case ELBA1: time.Sleep(time.Duration(15) * time.Second); break
                case TD3:   time.Sleep(time.Duration(5) * time.Second); break
            }
        } else {
            time.Sleep(time.Duration(1) * time.Second)
        }


        for dev=dev_start;dev<dev_end;dev++ {
            switch(dev){
                case ELBA0: stat_reg = D1_ELBA0_PWR_STAT_REG
                case ELBA1: stat_reg = D1_ELBA1_PWR_STAT_REG
                case TD3:   stat_reg = D1_TD3_PWR_STAT_REG
            }

            data32, err = TaorReadU32(DEVREGION1, stat_reg)
            if (data32 & 0x2) != 0x2 {
                err = fmt.Errorf(" Error: Asic_PowerCycle.  FPGA status indicates Device did not power up ok")
                cli.Printf("e", "%s", err)
                return
            }
        }
        //Have Linux rescan the PCI bus to enumerate the devices
        if nopciscan == 0 {
            err = LinuxPCIscan()
        }
    }

    return
}



/***********************************************************************************
*
*   Scan the PCI Bus for elba or td3 power cycle
*
***********************************************************************************/
func LinuxPCIscan() (err error) {
    args := "echo 1 > /sys/bus/pci/rescan"
    _, err = exec.Command("bash", "-c", args).Output()
    if err != nil {
        cli.Println("e", "Linux PCI Scan Failed.. Err = -->",  err)
    }
    return
}

/***********************************************************************************
*
*   Hard power cycle the system by disabling the PSU's
*
***********************************************************************************/
func SystemPowerCycle() {

    TaorWriteU32(DEVREGION1, D1_PSU_CTRL_REG, 0xD1) 
    return
}


func FAN_AirFlow_Direction() (fan_air_direction int, err error) {
    var data32 uint32

    data32, err = TaorReadU32(DEVREGION1, D1_FAN_STAT_REG)
    if err != nil {
        return
    }
    //fan present is 0 for present, 1 for not present
    if (data32 &  D1_FAN_STAT_PORT_SIDE_INTAKE_MASK) == D1_FAN_STAT_PORT_SIDE_INTAKE_MASK {
        fan_air_direction = AIRFLOW_FRONT_TO_BACK
    } else if (data32 &  D1_FAN_STAT_PORT_SIDE_INTAKE_MASK) == 0x00 {
        fan_air_direction = AIRFLOW_BACK_TO_FRONT
    } else {
        fan_air_direction = AIRFLOW_MIXED_ERROR
    }
    return
}

func FAN_Module_present(FANnumber uint32) (present bool, err error) {
    var data32 uint32
    present = false

    if FANnumber > FAN5 {
        err = fmt.Errorf(" Error: FAN_Module_present.  FAN NUMBER PASSED (%d) IS NOT VALID!", FANnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = TaorReadU32(DEVREGION1, D1_FAN_STAT_REG)
    if err != nil {
        return
    }
    //fan present is 0 for present, 1 for not present
    if (data32 &  (D1_FAN_STAT_REG_NOT_PRESENT0_BIT << (D1_FAN_STAT_REG_NOT_PRESENT0_SHIFT + FANnumber))) == 0x00 {
        present = true
    }
    return
}

func PSU_present(PSUnumber uint32) (present bool, err error) {
    var data32 uint32
    present = false

    if PSUnumber > PSU1 {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = TaorReadU32(DEVREGION1, D1_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  D1_PSU_STAT_REG_PRESENT0) == D1_PSU_STAT_REG_PRESENT0) {
        present = true
    }
    if PSUnumber == PSU1 && ( (data32 &  D1_PSU_STAT_REG_PRESENT1) == D1_PSU_STAT_REG_PRESENT1) {
        present = true
    }
    return
}

func PSU_pwrok(PSUnumber uint32) (pwrok bool, err error) {
    var data32 uint32
    pwrok = false

    if PSUnumber > PSU1 {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = TaorReadU32(DEVREGION1, D1_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  D1_PSU_STAT_PWROK0) == D1_PSU_STAT_PWROK0) {
        pwrok = true
    }
    if PSUnumber == PSU1 && ( (data32 &  D1_PSU_STAT_PWROK1) == D1_PSU_STAT_PWROK1) {
        pwrok = true
    }
    return
}



func SFP_present(SFPnumber uint32) (present bool, err error) {
    var data32 uint32
    var addr uint64 = D0_FP_SFP_STAT_3_0_REG;
    var bitcompare uint32 = 0
    present = false

    if SFPnumber > (MAXSFP - 1) {
        err = fmt.Errorf(" Error: SFP_present.  SFP NUMBER PASSED (%d) IS NOT VALID!", SFPnumber)
        cli.Printf("e", "%s", err)
        return
    }

    addr = addr + ((uint64(SFPnumber)/4) * 4)
    bitcompare = (1 << ((SFPnumber%4)*8))
    data32, err = TaorReadU32(DEVREGION0, addr)
    if err != nil {
        return
    }

    //1 = NOT PRESENT
    if (data32 & bitcompare) == bitcompare {
        present = false
    } else {
        present = true
    }
    return
}

func QSFP_present(QSFPnumber uint32) (present bool, err error) {
    var data32 uint32
    var addr uint64 = D0_FP_QSFP_STAT_51_48_REG;
    var bitcompare uint32 = 0
    present = false

    if QSFPnumber > (MAXSFP - 1) {
        err = fmt.Errorf(" Error: SFP_present.  SFP NUMBER PASSED (%d) IS NOT VALID!", QSFPnumber)
        cli.Printf("e", "%s", err)
        return
    }

    addr = addr + ((uint64(QSFPnumber)/4) * 4)
    bitcompare = (1 << ((QSFPnumber%4)*8))
    data32, err = TaorReadU32(DEVREGION0, addr)
    if err != nil {
        return
    }

    //1 = NOT PRESENT
    if (data32 & bitcompare) == bitcompare {
        present = false
    } else {
        present = true
    }
    return
}

func AsicCoreTemp(devName string) (err int) {
    var data32 uint32
    var addr uint64 = D1_ELBA0_STAT_REG

    if strings.Contains(devName, "1") == true {
        addr = D1_ELBA1_STAT_REG
    }
    data32, _ = TaorReadU32(DEVREGION1, addr)

    cli.Printf("i", "%s(%cC)  %d\n", devName, 0xB0, data32 & 0xFF)
    return
}

/****************************************************************
*
* GET ELBA TEMPERATURE
* 
****************************************************************/
func GetTemperature(devName string) (temperatures []float64, err int) {
    var data32 uint32
    var addr uint64 = D1_ELBA0_STAT_REG

    if strings.Contains(devName, "1") == true {
        addr = D1_ELBA1_STAT_REG
    }
    data32, _ = TaorReadU32(DEVREGION1, addr)
    data32 = data32 & 0xFF

    temperatures = append(temperatures, float64(data32))
    return
}


