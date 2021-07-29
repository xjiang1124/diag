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
    "regexp"
    "unsafe"

    "common/cli"
    "common/dcli"
    "common/errType"

    //"gopkg.in/yaml.v2"
    "encoding/json"
    "device/cpld/nicCpldCommon"

    "hardware/i2cinfo"
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


func init () {
    var cardType string
    
    //quick hack to see if we are a Taormina since diag env is not setup yet
    exists, _ := dir_exists("/etc/openswitch/platform/HPE/Taormina")
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
        Glob_mmap0, Glob_fd0, _ = MMAP_Device(DEV0_BAR, MAP_SIZE)
        Glob_mmap1, Glob_fd1, _ = MMAP_Device(DEV1_BAR, MAP_SIZE)
        Glob_mmap2, Glob_fd2, _ = MMAP_Device(DEV2_BAR, MAP_SIZE)
        Glob_mmap3, Glob_fd3, _ = MMAP_Device(DEV3_BAR, MAP_SIZE)
        //How do we gracefully unmap?   OS should do it, but would be nice to do it in code 
        /*
        defer func() {
            MunMAP_Device(Glob_fd0, Glob_mmap0)
            MunMAP_Device(Glob_fd1, Glob_mmap1)
            MunMAP_Device(Glob_fd2, Glob_mmap2)
            MunMAP_Device(Glob_fd3, Glob_mmap3)
            fmt.Printf(" ADD DEBUG: Munmap\n")
        } () 
        */ 
    }
     
} 
 

// exists returns whether the given file or directory exists
func dir_exists(path string) (bool, error) {
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


func GetResistorStrapping() (value uint32, err error) {

    value, err = TaorReadU32(DEVREGION0, D0_BOARD_REV_ID_REG)
    return
}

func Asic_PowerCycle(device uint32, state uint32, nopciscan uint32) (err error) {
    var args string
    var data32 uint32
    var ctrl_reg, stat_reg uint64 = D1_ELBA0_PWR_CTRL_REG, D1_ELBA0_PWR_STAT_REG
    var dev, dev_start, dev_end int

    if device > ALL {
            err = fmt.Errorf(" Error: Asic_PowerCycle.  Device number passed (%d) is not valid", device)
            fmt.Printf("%s", err)
            return
    }
    if state != POWER_STATE_CYCLE && state != POWER_STATE_OFF && state != POWER_STATE_ON {
            err = fmt.Errorf(" Error: Asic_PowerCycle.  Power Stated passed (%d) is not valid", state)
            fmt.Printf("%s", err)
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
                case ELBA0: ctrl_reg = D1_ELBA0_PWR_CTRL_REG; stat_reg = D1_ELBA0_PWR_STAT_REG
                            fmt.Printf(" Removing Elba0 from Linux PCI Enumeration and Powering Off\n")
                case ELBA1: ctrl_reg = D1_ELBA1_PWR_CTRL_REG; stat_reg = D1_ELBA1_PWR_STAT_REG
                            fmt.Printf(" Removing Elba1 from Linux PCI Enumeration and Powering Off\n")
                case TD3:   ctrl_reg = D1_TD3_PWR_CTRL_REG; stat_reg = D1_TD3_PWR_STAT_REG
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
                TaorWriteU32(DEVREGION1, ctrl_reg, 0x53) 
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
                case ELBA0: ctrl_reg = D1_ELBA0_PWR_CTRL_REG; stat_reg = D1_ELBA0_PWR_STAT_REG
                case ELBA1: ctrl_reg = D1_ELBA1_PWR_CTRL_REG; stat_reg = D1_ELBA1_PWR_STAT_REG
                case TD3:   ctrl_reg = D1_TD3_PWR_CTRL_REG; stat_reg = D1_TD3_PWR_STAT_REG
            }
            if dev == ELBA0 || dev == ELBA1 {
                if nopciscan == 1 {
                    fmt.Printf(" Powering up Elba\n")
                } else {
                    fmt.Printf(" Powering up Elba and Waiting 15 seconds for Elba to boot and enumerate\n")
                }
                TaorWriteU32(DEVREGION1, ctrl_reg, 0xD1) 
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
                    fmt.Printf("%s", err)
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
                fmt.Printf("%s", err)
                return
            }
        }
        //Have Linux rescan the PCI bus to enumerate the devices
        if nopciscan == 0 {
            args = "echo 1 > /sys/bus/pci/rescan"
            _, errGo := exec.Command("bash", "-c", args).Output()
            if errGo != nil {
                cli.Println("e", errGo)
                return errGo
            }
        }
    }

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
    } else {
        fan_air_direction = AIRFLOW_BACK_TO_FRONT
    }
    return
}

func FAN_Module_present(FANnumber uint32) (present bool, err error) {
    var data32 uint32
    present = false

    if FANnumber > FAN5 {
        err = fmt.Errorf(" Error: FAN_Module_present.  FAN NUMBER PASSED (%d) IS NOT VALID!", FANnumber)
        fmt.Printf("%s", err)
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
        fmt.Printf("%s", err)
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
        fmt.Printf("%s", err)
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
        fmt.Printf("%s", err)
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
        fmt.Printf("%s", err)
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


/*
root@Taormina:/fs/nos/home_diag/diag/util# smartctl -a /dev/sda
smartctl 7.0 2018-12-30 r4883 [x86_64-linux-4.19.68-yocto-standard] (local build)
Copyright (C) 2002-18, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF INFORMATION SECTION ===
Device Model:     W6EN064G1TA-S91AA3-2D2.A5
Serial Number:    62419-00007
Firmware Version: TDF08YOW
User Capacity:    64,023,257,088 bytes [64.0 GB]
Sector Size:      512 bytes logical/physical
Rotation Rate:    Solid State Device
Form Factor:      2.5 inches
Device is:        Not in smartctl database [for details use: -P showall]
ATA Version is:   ACS-3 (minor revision not indicated)
SATA Version is:  SATA 3.2, 6.0 Gb/s (current: 6.0 Gb/s)
Local Time is:    Fri Jul  2 21:31:00 2021 UTC
SMART support is: Available - device has SMART capability.
SMART support is: Enabled

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED 
//SMART overall-health self-assessment test result: FAILED! 
....
SMART Error Log Version: 1
No Errors Logged

SMART Self-test log structure revision number 1
No self-tests have been logged.  [To run self-tests, use: smartctl -t]

SMART Selective self-test log data structure revision number 1
 SPAN               MIN_LBA               MAX_LBA  CURRENT_TEST_STATUS
    1  18446560841797907379   4557456277428481196  Not_testing
    2  14974422399512980395  12948822500726794986  Not_testing
    3  12442422526030232250  12370218121369661102  Not_testing
    4  16927471298384620523  13455169492706769594  Not_testing
    5  12587094041287306926  16999845689243937579  Not_testing
38550   4846766193727920216   4846766193727985751  Read_scanning was never started
Selective self-test flags (0xa1a1):
  After scanning selected spans, do NOT read-scan remainder of disk.
If Selective self-test is pending on power-up, resume after 25957 minute delay.

root@Taormina:/fs/nos/home_diag/diag/util# 
 
 

*/
func SSD_Display_Info() (err int) {
    var devModel string
    var sn string
    var size string
    var smartHealth string

    out, errGo := exec.Command("smartctl", "-a", "/dev/sda").Output()
    if errGo != nil {
        cli.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
    }

    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "Device Model:")==true {
            devModel = temp[18:]
        }
        if strings.Contains(temp, "Serial Number:")==true {
            sn = temp[18:]
        }
        if strings.Contains(temp, "User Capacity:")==true {

            re := regexp.MustCompile(`\[([^\[\]]*)\]`)
            submatchall := re.FindAllString(temp, -1)
            for _, element := range submatchall {
                    element = strings.Trim(element, "[")
                    element = strings.Trim(element, "]")
                    size = element
            }
        }
        if strings.Contains(temp, "SMART overall-health self-assessment test result:")==true {
            if strings.Contains(temp, "SMART overall-health self-assessment test result: PASSED")==true {
                smartHealth = "Smart Health PASSED"
                fmt.Printf("SSD MODEL: %s   S/N: %s   Capacity: %s    %s\n", devModel, sn, size, smartHealth)
            } else {
                smartHealth = "Smart Health FAILED"
                fmt.Printf("[ERROR] SSD MODEL: %s   S/N: %s   Capacity: %s    %s\n", devModel, sn, size, smartHealth)
                err = errType.FAIL
            }
        }
    }
    return

}



func DDR_Display_Info() (err int) {
    var size [4]string
    var pn [4]string
    var sn [4]string
    var i int = 0

    out, errGo := exec.Command("dmidecode", "--type", "17").Output()
    if errGo != nil {
        cli.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
    }

    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "Size:")==true {
            temp = strings.TrimSpace(temp)
            size[i] = string(temp[6:12])
        }
        if strings.Contains(temp, "Serial Number:")==true {
            temp = strings.TrimSpace(temp)
            sn[i] = string(temp[14:])
        }
        if strings.Contains(temp, "Part Number:")==true {
            temp = strings.TrimSpace(temp)
            pn[i] = string(temp[12:])
            i = i + 1
        }
        
    }

    for i=0; i<4; i++ {
        if (i%2)==0 {
            if size[i] == "No Mod" {
                fmt.Printf("[ERROR] MEMORY CHANNEL-%d:  NO MODULE DETECTED\n", i)
                err = errType.FAIL
                continue
            } else {
                fmt.Printf("MEMORY CHANNEL-%d:  PN: %s    SN: %s    SIZE: %sMB\n", i, pn[i], sn[i], size[i])
            }
        }
    }
    return
}


func BIOS_Display_Version() (err int) {
    out, errGo := exec.Command("dmidecode", "-s", "bios-version").Output()
    if errGo != nil {
        cli.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
    }
    fmt.Printf("BIOS VERSION: %s", string(out))

    return
}


func HALON_OS_Display_Version() (err int) {
    var show string = "show version"
    out, errGo := exec.Command("vtysh", "-c", show).Output()
    if errGo != nil {
        fmt.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
    }

    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "Build Date")==true {
            fmt.Printf("HALON OS: %s\n", temp)
        }
        if strings.Contains(temp, "Build ID")==true {
            fmt.Printf("HALON OS: %s\n", temp)
        }
    }
    return
}


func Elba_Check_Pci_Link(elba int) (err int) {
    var elb_pci string
    var speed, width bool = false, false
    if elba == ELBA0 {
        elb_pci = ELBA0_PCIBUS
    } else if elba == ELBA1 {
        elb_pci = ELBA1_PCIBUS
    } else {
        fmt.Printf("[ERROR] Elba number passed (%d) is to big\n", elba)
        err = errType.FAIL
        return
    }

    out, errGo := exec.Command("lspci", "-n", "-s", elb_pci).Output()
    if errGo != nil {
        fmt.Println("[ERROR] 1 ", errGo)
        err = errType.FAIL
        return
    }
    if strings.Contains(string(out), elb_pci)==false {
        fmt.Printf("[ERROR] Elba-%d is not enumerated on the PCI bus\n", elba)
        err = errType.FAIL
        return
    }

    out, errGo = exec.Command("lspci", "-s", elb_pci, "-vvv").Output()
    if errGo != nil {
        fmt.Println("[ERROR] 2", errGo)
        err = errType.FAIL
        return
    }
    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "LnkSta:")==true {
            //Example of bad case --> LnkSta: Speed 8GT/s (ok), Width x1 (downgraded)
            temp = strings.TrimSpace(temp)
            if strings.Contains(temp, "8GT/s")==true {
                speed = true
            }
            if strings.Contains(temp, "x4")==true {
                width = true
            }
            if speed == true && width == true {
                fmt.Printf("ELBA-%d %s\n", elba, temp)
            } else {
                fmt.Printf("[ERROR] ELBA-%d LINK SPEED IS NOT 8GT/s x4 -->  %s\n", elba, temp)
                err = errType.FAIL
            }
        }
    }
    return

}


func Elba_Show_Firmware(elba int) (err int) {
    var elb_pci string
    var ethfound bool = false
    var ethdev string

    if elba == ELBA0 {
        elb_pci = ELBA0_ETH_PCIBUS
    } else if elba == ELBA1 {
        elb_pci = ELBA1_ETH_PCIBUS
    } else {
        fmt.Printf("[ERROR] Elba number passed (%d) is to big\n", elba)
        err = errType.FAIL
        return
    }

    //Check if we have an ethernet connection to Elba
    for i:=0; i<NUMBER_ELBAS; i++ {
        
        if i==0 {
            ethdev = "eth1"
        } else {
            ethdev = "eth2"
        }
        out, _ := exec.Command("ethtool", "-i", ethdev).Output()
        s := strings.Split(string(out), "\n")
        for _, temp := range s {
            if strings.Contains(temp, elb_pci)==true {
                //fmt.Printf(" ETH DEV FOUND..  %s\n", ethdev)
                ethfound = true
                break
            }
        }
    }
    if ethfound == false {
        fmt.Printf("[ERROR] ELBA-%d Firmware List.  No ethernet device detected to query firmware info\n", elba)
        err = errType.FAIL
        return
    }


    out, errGo := exec.Command("sshpass","-p","pen123","timeout","500","ssh","-o","LogLevel=ERROR","-o","UserKnownHostsFile=/dev/null","-o","StrictHostKeyChecking=no","root@169.254.13.1","/nic/tools/fwupdate","-l").Output()
    if errGo != nil {
        fmt.Println("[ERROR] 2", errGo)
        err = errType.FAIL
        return
    }
    {
        res := make(map[string]interface{})
        outs := string(out)
        errg := json.Unmarshal([]byte(outs), &res)
        if errg != nil {
            fmt.Printf("[ERROR] Failed to parse fw output.  Error=%s\n", errg)
            err = errType.FAIL
            return
        }
        partitions := []string{"boot0", "mainfwa", "mainfwb", "goldfw", "diagfw"}
        for _, partition := range partitions {
            if _, ok := res[partition]; ok {
                //fmt.Println(res[partition])

                byteKey := []byte(fmt.Sprintf("%v", res[partition].(interface{})))
                //fmt.Println(string(byteKey))
                //fmt.Printf("\n\n")
                
                
                s := strings.Split(string(byteKey), " ")
                //fmt.Println(s)
                for _, temp := range s {
                    if strings.Contains(temp, "software_version:") {
                        s1 := strings.Split(temp, ":")
                        fmt.Printf("ELBA-%d  %s: %s\n", elba, partition, s1[len(s1) -1])
                        break;
                    }
                }
            } else {
                fmt.Printf("ELBA-%d  %s: no version info\n", elba)
            }
        }
        //fmt.Println(res["mainfwa"])
    }
    //fmt.Printf("%s\n", out)
    return

}

//
//nicCpldCommon.ID_TAORMINA_ELBA:
//    ELBA0 = 0
//ELBA1 = 1
//    err = errType.FAIL
func Elba_CPLD_I2C_Sanity_Test(devName string) (err int) {
    var errGo error
    i2cWrData := [][]byte{ {0x0B,0x55} , {0x0C, 0xAA} }
    wrData := []uint8{}
    rdData := []uint8{}

    if devName != "CPLD_ELBA0" && devName != "CPLD_ELBA1" {
        dcli.Printf("e", "DevName %s is not valid\n", devName)
        err = errType.FAIL
        return
    }

    iInfo, rc := i2cinfo.GetI2cInfo(devName)
    if rc != errType.SUCCESS {
        dcli.Println("e", "Failed to obtain I2C info of", devName)
        err = rc
        return
    }

    //read device ID
    wrData = append(wrData, 0x80)
    rdData, errGo = I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 1 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (1) Failed to", devName, " ERROR=",errGo)
        err = errType.FAIL
        return
    }

    if rdData[0] != nicCpldCommon.ID_TAORMINA_ELBA {
        dcli.Printf("e", "%s DEVICE ID IS WRONG:  EXPECT 0x.02x.   Read 0x%.02x", devName, nicCpldCommon.ID_TAORMINA_ELBA, rdData[0] )
        err = errType.FAIL
        return
    }

    _ , errGo = I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cWrData[0])), i2cWrData[0], 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (2) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }
    _ , errGo = I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cWrData[1])), i2cWrData[1], 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (3) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }

    rdData = nil
    wrData[0] = i2cWrData[0][0]
    rdData, errGo = I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), 1, wrData, 1 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (4) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }
    if rdData[0] != i2cWrData[0][1] {
        dcli.Printf("e", "%s Register-0x%.02x  Wrote 0x.02x.   Read 0x%.02x", devName, i2cWrData[0][0], i2cWrData[0][1],  rdData[0] )
        err = errType.FAIL
        return
    }

    rdData = nil
    wrData[0] = i2cWrData[1][0]
    rdData, errGo = I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), 1, wrData, 1 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (4) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }
    if rdData[0] != i2cWrData[1][1] {
        dcli.Printf("e", "%s Register-0x%.02x  Wrote 0x.02x.   Read 0x%.02x", devName, i2cWrData[1][0], i2cWrData[1][1],  rdData[0] )
        err = errType.FAIL
        return
    }

    return
}

