/* Notes
 
SPI BUS HOOKUP 
SPI0 = CPU CPLD 
SPI1 = ELBA0 CPLD
SPI2 = ELBA1 CPLD 
SPI3 = ELBA2 CPLD 
SPI4 = ELBA3 CPLD 
SPI5 = ELBA4 CPLD 
SPI6 = ELBA5 CPLD 
SPI7 = ELBA6 CPLD 
SPI8 = ELBA7 CPLD 
SPI9 = ELBA0 SERIAL FLASH
SPI10 = ELBA1 SERIAL FLASH 
SPI11 = ELBA2 SERIAL FLASH 
SPI12 = ELBA3 SERIAL FLASH 
SPI13 = ELBA4 SERIAL FLASH 
SPI14 = ELBA5 SERIAL FLASH 
SPI15 = ELBA6 SERIAL FLASH 
SPI16 = ELBA7 SERIAL FLASH  
 
 
*/ 
 
package liparifpga

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
    MAXFAN = 4
    DUALFAN = 1
    AIRFLOW_FRONT_TO_BACK = 0
    AIRFLOW_BACK_TO_FRONT = 1
    AIRFLOW_MIXED_ERROR = 2
    MAXQSFPDD = 28
    //MAXSFP = 48
    //MAXQSFP = 6
)

const (
    ELBA0 = 0
    ELBA1 = 1
    ELBA2 = 2
    ELBA3 = 3
    ELBA4 = 4
    ELBA5 = 5
    ELBA6 = 6
    ELBA7 = 7
    TH4   = 8
    ALL   = 9
    NUMBER_ELBAS = 8

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

//Base Address is static, so just skip getting it from linux to save time and use static base address for each FPGA region
const FPGA0_BAR int64 = 0x10020300000
const FPGA1_BAR int64 = 0x10020200000

const DEV0_BAR int64 =  0x10020300000
const DEV1_BAR int64 =  0x10020200000
const MAP_SIZE int = 1048576



const L_FPGA_PCI_VENDOR_ID    uint32 = 0x1dd8
const LIPARI_FPGA0            uint32 = 0x0000
const LIPARI_FPGA1            uint32 = 0x0001
const LIPARI_NUMBER_FPGA      uint32 = 0x0002
const LIPARI_FPGA0_PCI_DEV_ID uint32 = 0x0009
const LIPARI_FPGA1_PCI_DEV_ID uint32 = 0x000A


var Glob_fd0 *os.File = nil
var Glob_fd1 *os.File = nil
var Glob_mmap0 []byte
var Glob_mmap1 []byte


func init () {
    var cardType string
    cardType = os.Getenv("CARD_TYPE")
    
    //quick hack to see if we are a Taormina since diag env is not setup yet
    exists, _ := Path_exists("/etc/openswitch/platform/HPE/10000")
    if exists == true {
        os.Setenv("CARD_TYPE","TAORMINA")
        cardType = "TAORMINA"
    } 
    if cardType == "LIPARI" {
        bar := []uint64 { 0,0 }
        exists, _ := Path_exists("/tmp/fpgabars")

        os.Setenv("CARD_TYPE",cardType)

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
            shcmds := []string{ "lspci -v -d 1dd8:0009 | grep 'Memory at' | awk '{print $3}'", 
                                "lspci -v -d 1dd8:000A | grep 'Memory at' | awk '{print $3}'"  }
            for i:=0;i<len(shcmds);i++ {
                execOutput, errGo := exec.Command("sh", "-c", shcmds[i] ).Output()
                if errGo != nil {
                    cli.Println("e", "ERROR: Failed to get FPGA BAR VALUE.   GO ERROR=%v", errGo)
                    return
                }
                tmp := "0x" + strings.TrimSuffix(string(execOutput), "\n")
                fmt.Printf("%s\n", execOutput);
                fmt.Printf("%s\n", tmp);
                if i==0        { bar[0], _ = strconv.ParseUint(tmp, 0, 64) 
                } else if i==1 { bar[1], _ = strconv.ParseUint(tmp, 0, 64) }
            }

            file, errGo := os.OpenFile("/tmp/fpgabars", os.O_RDWR | os.O_CREATE | os.O_TRUNC, 0644)
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
        //fmt.Printf("bar[0]=0x%x\n", bar[0]);
        //fmt.Printf("bar[1]=0x%x\n", bar[1]);
        Glob_mmap0, Glob_fd0, _ = MMAP_Device(int64(bar[0]), MAP_SIZE)
        Glob_mmap1, Glob_fd1, _ = MMAP_Device(int64(bar[1]), MAP_SIZE)
        //How do we gracefully unmap?   OS should do it, but would be nice to do it in code 
        //
        //defer func() {
        //    MunMAP_Device(Glob_fd0, Glob_mmap0)
        //    MunMAP_Device(Glob_fd1, Glob_mmap1)
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


func FpgaDumpRegionRegisters(fpgaNumber uint32) (err error) {

    var data32 uint32 = 0
    var lipari_reg_ptr []LIPARI_FPGA_REGISTERS
    

    if uint32(fpgaNumber) >= LIPARI_NUMBER_FPGA {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (LIPARI_NUMBER_FPGA -1), fpgaNumber); 
        err = errors.New(" ERROR") 
        return
    }

    if fpgaNumber == 0 {
        lipari_reg_ptr = LIPARI_FPGA0_REGISTERS
    } else if fpgaNumber == 1 {
        lipari_reg_ptr = LIPARI_FPGA1_REGISTERS
    } 

    fmt.Printf("FPGA-%d REGISTER DUMP---\n", fpgaNumber)
    for _, entry := range(lipari_reg_ptr) {

        data32, err = LipariReadU32(fpgaNumber, uint64(entry.Address))
        if err != nil {
            return
        }
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }
    fmt.Printf("\n");

    return
}



func LipariReadU8(fpgaNumber uint32, addr uint64) (value uint8, err error) {
    //var bar uint64
    //var pcidevid uint32

    if uint32(fpgaNumber) >= LIPARI_NUMBER_FPGA {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (LIPARI_NUMBER_FPGA -1), fpgaNumber); 
        err = errors.New(" ERROR") 
        return
    }

    switch(fpgaNumber){
        case 0: value = *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr])); break
        case 1: value = *(*uint8)(unsafe.Pointer(&Glob_mmap1[addr])); break
    }
    return
}

func LipariReadU32(fpgaNumber uint32, addr uint64) (value uint32, err error) {
    var bar uint64
    //var pcidevid uint32

    if uint32(fpgaNumber) >= LIPARI_NUMBER_FPGA {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (LIPARI_NUMBER_FPGA -1), fpgaNumber); 
        err = errors.New(" ERROR") 
        return
    }

    switch(fpgaNumber){
        case 0: value = *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr])); break
        case 1: value = *(*uint32)(unsafe.Pointer(&Glob_mmap1[addr])); break
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
    
    switch(fpgaNumber){
        case 0: bar = uint64(DEV0_BAR)
        case 1: bar = uint64(DEV1_BAR)
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


func LipariWriteU8(fpgaNumber uint32, addr uint64, data uint8) (err error) {
    if uint32(fpgaNumber) >= LIPARI_NUMBER_FPGA {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (LIPARI_NUMBER_FPGA -1), fpgaNumber); 
        err = errors.New(" ERROR") 
        return
    }

    switch(fpgaNumber){
        case 0: *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr])) = data; break
        case 1: *(*uint8)(unsafe.Pointer(&Glob_mmap1[addr])) = data; break
    }
    return
}

func LipariWriteU16(fpgaNumber uint32, addr uint64, data uint16) (err error) {

    if uint32(fpgaNumber) >= LIPARI_NUMBER_FPGA {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (LIPARI_NUMBER_FPGA -1), fpgaNumber); 
        err = errors.New(" ERROR") 
        return
    }

    switch(fpgaNumber){
        case 0: *(*uint16)(unsafe.Pointer(&Glob_mmap0[addr])) = data; break
        case 1: *(*uint16)(unsafe.Pointer(&Glob_mmap1[addr])) = data; break
    }
    return
}

func LipariWriteU32(fpgaNumber uint32, addr uint64, data uint32) (err error) {
    var bar uint64
    //var pcidevid uint32

    if uint32(fpgaNumber) >= LIPARI_NUMBER_FPGA {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (LIPARI_NUMBER_FPGA -1), fpgaNumber); 
        err = errors.New(" ERROR") 
        return
    }

    switch(fpgaNumber){
        case 0: *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr])) = data; break
        case 1: *(*uint32)(unsafe.Pointer(&Glob_mmap1[addr])) = data; break
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
    switch(fpgaNumber){
        case 0: bar = uint64(DEV0_BAR)
        case 1: bar = uint64(DEV1_BAR)
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

    LipariWriteU32(LIPARI_FPGA0, FPGA0_I2C_CH0_MUX_SEL_REG + uint64( channel * L_I2C_MAILBOX_STRIDE ) , mux) 
    return
}


func GetResistorStrapping() (value uint32, err error) {

    value, err = LipariReadU32(LIPARI_FPGA0, FPGA0_BOARD_REV_ID_REG)
    return
}


func Asic_PowerCycle(device uint32, state uint32, nopciscan uint32, bootGoldFW uint32) (err error) {
    //var args string
    var data32 uint32
    var ctrl_pwr_reg, stat_reg, ctrl_reg uint64 = FPGA0_ELBA0_PWR_CTRL_REG, FPGA0_ELBA0_PWR_STAT_REG, FPGA1_ELBA0_CTRL_REG
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
                case ELBA0: ctrl_pwr_reg = FPGA0_ELBA0_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA0_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA0_CTRL_REG
                            fmt.Printf(" Removing Elba0 from Linux PCI Enumeration and Powering Off\n")
                case ELBA1: ctrl_pwr_reg = FPGA0_ELBA1_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA1_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA1_CTRL_REG
                            fmt.Printf(" Removing Elba1 from Linux PCI Enumeration and Powering Off\n")
                case ELBA2: ctrl_pwr_reg = FPGA0_ELBA2_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA2_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA2_CTRL_REG
                            fmt.Printf(" Removing Elba2 from Linux PCI Enumeration and Powering Off\n")
                case ELBA3: ctrl_pwr_reg = FPGA0_ELBA3_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA3_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA3_CTRL_REG
                            fmt.Printf(" Removing Elba3 from Linux PCI Enumeration and Powering Off\n")
                case ELBA4: ctrl_pwr_reg = FPGA0_ELBA4_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA4_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA4_CTRL_REG
                            fmt.Printf(" Removing Elba4 from Linux PCI Enumeration and Powering Off\n")
                case ELBA5: ctrl_pwr_reg = FPGA0_ELBA5_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA5_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA5_CTRL_REG
                            fmt.Printf(" Removing Elba5 from Linux PCI Enumeration and Powering Off\n")
                case ELBA6: ctrl_pwr_reg = FPGA0_ELBA6_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA6_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA6_CTRL_REG
                            fmt.Printf(" Removing Elba6 from Linux PCI Enumeration and Powering Off\n")
                case ELBA7: ctrl_pwr_reg = FPGA0_ELBA7_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA7_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA7_CTRL_REG
                            fmt.Printf(" Removing Elba7 from Linux PCI Enumeration and Powering Off\n")
                case TH4:   ctrl_pwr_reg = FPGA0_TH4_PWR_CTRL_REG 
                            stat_reg = FPGA0_TH4_PWR_STAT_REG
                            fmt.Printf(" Removing TH4 from Linux PCI Enumeration and Powering Off\n")
            }
            /*
            switch(dev){
                case ELBA0: args = "echo 1 > /sys/bus/pci/devices/0000:0A:00.0/remove"
                case ELBA1: args = "echo 1 > /sys/bus/pci/devices/0000:12:00.0/remove"
                case ELBA2: args = "echo 1 > /sys/bus/pci/devices/0000:1A:00.0/remove"
                case ELBA3: args = "echo 1 > /sys/bus/pci/devices/0000:23:00.0/remove"
                case ELBA4: args = "echo 1 > /sys/bus/pci/devices/0000:1F:00.0/remove"
                case ELBA5: args = "echo 1 > /sys/bus/pci/devices/0000:17:00.0/remove"
                case ELBA6: args = "echo 1 > /sys/bus/pci/devices/0000:0E:00.0/remove"
                case ELBA7: args = "echo 1 > /sys/bus/pci/devices/0000:06:00.0/remove"
                case TH4:   args = "echo 1 > /sys/bus/pci/devices/0000:04:00.0/remove" 
            }
            exec.Command("bash", "-c", args).Output()
            time.Sleep(time.Duration(1) * time.Second) 
            */
            if dev < TH4 {  //Elba device
                if bootGoldFW > 0 {
                    LipariWriteU32(LIPARI_FPGA1, ctrl_reg , 0x7)
                } else {
                    LipariWriteU32(LIPARI_FPGA1, ctrl_reg , 0x3)
                }
                LipariWriteU32(LIPARI_FPGA0, ctrl_pwr_reg , 0x53)
                if dev == ELBA0 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI1_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI9_MUXSEL_REG , 0x00)
                } else if dev == ELBA1 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI2_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI10_MUXSEL_REG , 0x00)
                } else if dev == ELBA2 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI3_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI11_MUXSEL_REG , 0x00)
                } else if dev == ELBA3 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI4_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI12_MUXSEL_REG , 0x00)
                } else if dev == ELBA4 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI5_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI13_MUXSEL_REG , 0x00)
                } else if dev == ELBA5 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI6_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI14_MUXSEL_REG , 0x00)
                } else if dev == ELBA6 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI7_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI15_MUXSEL_REG , 0x00)
                } else if dev == ELBA7 {
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI8_MUXSEL_REG , 0x00)
                    LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI16_MUXSEL_REG , 0x00)
                }
            }
            if dev == TH4 {
                LipariWriteU32(LIPARI_FPGA0, FPGA0_TH4_CTRL_REG, 0x1ff) 
                LipariWriteU32(LIPARI_FPGA0, FPGA0_TH4_PWR_CTRL_REG, 0x53) 
            }
        }
        
    }

    if state == POWER_STATE_CYCLE {
        time.Sleep(time.Duration(500) * time.Millisecond)
    }

    //power up if needed
    if state == POWER_STATE_ON || state == POWER_STATE_CYCLE {
        for dev=dev_start;dev<dev_end;dev++ {
            switch(dev){
                case ELBA0: ctrl_pwr_reg = FPGA0_ELBA0_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA0_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA0_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI1_MUXSEL_REG , 0x01)   //trun cpld and qspi mux back to elba
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI9_MUXSEL_REG , 0x01)
                case ELBA1: ctrl_pwr_reg = FPGA0_ELBA1_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA1_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA1_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI2_MUXSEL_REG , 0x01)
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI10_MUXSEL_REG , 0x01)
                case ELBA2: ctrl_pwr_reg = FPGA0_ELBA2_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA2_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA2_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI3_MUXSEL_REG , 0x01)
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI11_MUXSEL_REG , 0x01)
                case ELBA3: ctrl_pwr_reg = FPGA0_ELBA3_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA3_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA3_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI4_MUXSEL_REG , 0x01)
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI12_MUXSEL_REG , 0x01)
                case ELBA4: ctrl_pwr_reg = FPGA0_ELBA4_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA4_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA4_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI5_MUXSEL_REG , 0x01)
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI13_MUXSEL_REG , 0x01)
                case ELBA5: ctrl_pwr_reg = FPGA0_ELBA5_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA5_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA5_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI6_MUXSEL_REG , 0x01)
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI14_MUXSEL_REG , 0x01)
                case ELBA6: ctrl_pwr_reg = FPGA0_ELBA6_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA6_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA6_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI7_MUXSEL_REG , 0x01)
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI15_MUXSEL_REG , 0x01)
                case ELBA7: ctrl_pwr_reg = FPGA0_ELBA7_PWR_CTRL_REG
                            stat_reg = FPGA0_ELBA7_PWR_STAT_REG
                            ctrl_reg = FPGA1_ELBA7_CTRL_REG
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI8_MUXSEL_REG , 0x01)
                            LipariWriteU32(LIPARI_FPGA1, FPGA1_SPI16_MUXSEL_REG , 0x01)
                case TH4:   ctrl_pwr_reg = FPGA0_TH4_PWR_CTRL_REG
                            stat_reg = FPGA0_TH4_PWR_STAT_REG
            }
            //time.Sleep(time.Duration(500) * time.Millisecond) 
            if dev >= ELBA0 || dev <= ELBA7 {
                if nopciscan == 1 {
                    fmt.Printf(" Powering up Elba-%d\n", dev)
                } else {
                    fmt.Printf(" Powering up Elba and Waiting 15 seconds for Elba to boot and enumerate\n")
                }
                LipariWriteU32(LIPARI_FPGA0, ctrl_pwr_reg , 0xD1)
                if bootGoldFW > 0 {
                    LipariWriteU32(LIPARI_FPGA1, ctrl_reg , 0x5)
                } else {
                    LipariWriteU32(LIPARI_FPGA1, ctrl_reg , 0x1)
                }
                
                //time.Sleep(time.Duration(300) * time.Millisecond)
                if bootGoldFW > 0 {
                    LipariWriteU32(LIPARI_FPGA1, ctrl_reg , 0x4)
                } else {
                    LipariWriteU32(LIPARI_FPGA1, ctrl_reg , 0x0)
                }
                //time.Sleep(time.Duration(1000) * time.Millisecond) 
            }
            if dev == TH4 {
                if nopciscan == 1 {
                    fmt.Printf(" Powering up TH4\n")
                } else {
                    fmt.Printf(" Powering up TH4 and Waiting 5 seconds for TH4 to come up and enumerate\n")
                }
                LipariWriteU32(LIPARI_FPGA0, FPGA0_TH4_PWR_CTRL_REG , 0xd1)
                time.Sleep(time.Duration(100) * time.Millisecond)
                LipariWriteU32(LIPARI_FPGA0, FPGA0_TH4_CTRL_REG , 0x1fd)
                time.Sleep(time.Duration(100) * time.Millisecond)
                LipariWriteU32(LIPARI_FPGA0, FPGA0_TH4_CTRL_REG , 0x0)
                data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_TH4_STAT_REG)
                if (data32 & 0x2) != 0x2 {
                    err = fmt.Errorf(" Error: Asic_PowerCycle.  FPGA status indicates TH4 did not power up ok")
                    cli.Printf("e", "%s", err)
                    return
                }
            }
        }

        // Sleep .. duration depends on what is getting reset
        if nopciscan == 0 {
            switch(device){
                case ALL: time.Sleep(time.Duration(15) * time.Second); break
                case ELBA0, ELBA1, ELBA2, ELBA3, ELBA4, ELBA5, ELBA6, ELBA7: time.Sleep(time.Duration(15) * time.Second); break
                case TH4:   time.Sleep(time.Duration(5) * time.Second); break
            }
        } else {
            time.Sleep(time.Duration(1) * time.Second)
        }


        for dev=dev_start;dev<dev_end;dev++ {
            switch(dev){
                case ELBA0: stat_reg = FPGA1_ELBA0_STAT_REG
                case ELBA1: stat_reg = FPGA1_ELBA1_STAT_REG
                case ELBA2: stat_reg = FPGA1_ELBA2_STAT_REG
                case ELBA3: stat_reg = FPGA1_ELBA3_STAT_REG
                case ELBA4: stat_reg = FPGA1_ELBA4_STAT_REG
                case ELBA5: stat_reg = FPGA1_ELBA5_STAT_REG
                case ELBA6: stat_reg = FPGA1_ELBA6_STAT_REG
                case ELBA7: stat_reg = FPGA1_ELBA7_STAT_REG
                case TH4:   stat_reg = FPGA0_TH4_PWR_STAT_REG
            }

            /* NOT WORKING AS OF 3/20/23 FPGA */
            data32, err = LipariReadU32(LIPARI_FPGA1, stat_reg)
            //if (data32 & 0x2) != 0x2 {
            //    err = fmt.Errorf(" Error: Asic_PowerCycle.  FPGA status indicates Device did not power up ok")
            //    cli.Printf("e", "%s", err)
            //    return
            //}
        }
        //Have Linux rescan the PCI bus to enumerate the devices
        if nopciscan == 0 {
            err = LinuxPCIscan()
        }
    }
    return
} 

 
 
// ***********************************************************************************
// *
// *   Scan the PCI Bus for elba or td3 power cycle
// *
// ***********************************************************************************
func LinuxPCIscan() (err error) {
    args := "echo 1 > /sys/bus/pci/rescan"
    _, err = exec.Command("bash", "-c", args).Output()
    if err != nil {
        cli.Println("e", "Linux PCI Scan Failed.. Err = -->",  err)
    }
    return
}

// ***********************************************************************************
// *
// *   Hard power cycle the system by disabling the PSU's
// *
// ***********************************************************************************
func SystemPowerCycle() {

    LipariWriteU32(LIPARI_FPGA0, FPGA0_PSU_CTRL_REG, 0xD1) 
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
    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  FPGA0_PSU_STAT_PRSNT0) == FPGA0_PSU_STAT_PRSNT0) {
        present = true
    }
    if PSUnumber == PSU1 && ( (data32 &  FPGA0_PSU_STAT_PRSNT1) == FPGA0_PSU_STAT_PRSNT1) {
        present = true
    }
    return
}


func PSU_pwrok(PSUnumber uint32) (pwrok bool, err error) {
    var data32 uint32
    pwrok = false

    if PSUnumber > (MAXPSU - 1) {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  FPGA0_PSU_STAT_PWROK0) == FPGA0_PSU_STAT_PWROK0) {
        pwrok = true
    }
    if PSUnumber == PSU1 && ( (data32 &  FPGA0_PSU_STAT_PWROK1) == FPGA0_PSU_STAT_PWROK1) {
        pwrok = true
    }
    return
}


func PSU_check_alert(PSUnumber uint32) (alert bool, err error) {
    var data32 uint32
    alert = false

    if PSUnumber > (MAXPSU - 1) {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  FPGA0_PSU_STAT_ALERT0) == FPGA0_PSU_STAT_ALERT0) {
        alert = true
    }
    if PSUnumber == PSU1 && ( (data32 &  FPGA0_PSU_STAT_ALERT1) == FPGA0_PSU_STAT_ALERT1) {
        alert = true
    }
    return
}


func QSFP_present(QSFPnumber uint32) (present bool, err error) {
    var data32 uint32
    var addr uint64 = FPGA0_QDD_0300_STAT_REG;
    var bitcompare uint32 = 0
    present = false

    if QSFPnumber > (MAXQSFPDD - 1) {
        err = fmt.Errorf(" Error: QSFP_present.  QSP NUMBER PASSED (%d) IS NOT VALID!", QSFPnumber)
        cli.Printf("e", "%s", err)
        return
    }

    switch QSFPnumber {
	case 0,1,2,3:
		addr = FPGA0_QDD_0300_STAT_REG
	case 4,5,6,7:
		addr = FPGA0_QDD_0704_STAT_REG
	case 8,9,10,11:
		addr = FPGA0_QDD_1108_STAT_REG
	case 12,13,14,15:
		addr = FPGA0_QDD_1512_STAT_REG
	case 16,17,18,19:
		addr = FPGA0_QDD_1916_STAT_REG
	case 20,21,22,23:
		addr = FPGA0_QDD_2320_STAT_REG
	case 24,25,26,27:
		addr = FPGA0_QDD_2724_CTRL_REG
    }
    bitcompare = (1 << ((QSFPnumber%4)*8))
    data32, err = LipariReadU32(LIPARI_FPGA0, addr)
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
    var addr uint64 = FPGA1_ELBA0_STAT_REG

    if strings.Contains(devName, "1") == true {
        addr = FPGA1_ELBA1_STAT_REG
    } else if strings.Contains(devName, "2") == true {
        addr = FPGA1_ELBA2_STAT_REG
    } else if strings.Contains(devName, "3") == true {
        addr = FPGA1_ELBA3_STAT_REG
    } else if strings.Contains(devName, "4") == true {
        addr = FPGA1_ELBA4_STAT_REG
    } else if strings.Contains(devName, "5") == true {
        addr = FPGA1_ELBA5_STAT_REG
    } else if strings.Contains(devName, "6") == true {
        addr = FPGA1_ELBA6_STAT_REG
    } else if strings.Contains(devName, "7") == true {
        addr = FPGA1_ELBA7_STAT_REG
    }

    data32, _ = LipariReadU32(LIPARI_FPGA1, addr)

    cli.Printf("i", "%s(%cC)  %d\n", devName, 0xB0, data32 & 0xFF)
    return
}

// ****************************************************************
// *
// * GET ELBA TEMPERATURE
// * 
// ****************************************************************
func GetTemperature(devName string) (temperatures []float64, err int) {
    var data32 uint32
    var addr uint64 = FPGA1_ELBA0_STAT_REG

    if strings.Contains(devName, "1") == true {
        addr = FPGA1_ELBA1_STAT_REG
    } else if strings.Contains(devName, "2") == true {
        addr = FPGA1_ELBA2_STAT_REG
    } else if strings.Contains(devName, "3") == true {
        addr = FPGA1_ELBA3_STAT_REG
    } else if strings.Contains(devName, "4") == true {
        addr = FPGA1_ELBA4_STAT_REG
    } else if strings.Contains(devName, "5") == true {
        addr = FPGA1_ELBA5_STAT_REG
    } else if strings.Contains(devName, "6") == true {
        addr = FPGA1_ELBA6_STAT_REG
    } else if strings.Contains(devName, "7") == true {
        addr = FPGA1_ELBA7_STAT_REG
    }
    data32, _ = LipariReadU32(LIPARI_FPGA1, addr)

    temperatures = append(temperatures, float64(data32))
    return
}



