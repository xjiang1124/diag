package materafpga

import (
    "bufio"
    //"errors"
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

const DEV0_BAR int64 =  0x10020300000
const DEV1_BAR int64 =  0x10020200000
const MAP_SIZE int = 1048576



const L_FPGA_PCI_VENDOR_ID    uint32 = 0x1dd8
const MATERA_FPGA0            uint32 = 0x0000
const MATERA_FPGA0_PCI_DEV_ID uint32 = 0x0009

const MDIO_RD_ENA         uint32 = 0x6
const MDIO_WR_ENA         uint32 = 0x5
const MDIO_REG_ADDR_MASK  uint32 = 0x1F
const MDIO_DEV_ADDR_MASK  uint32 = 0x1F
const MDIO_RUN_BUSY_MASK  uint32 = 0x8000
const MDIO_DATA_MASK      uint32 = 0xFFFF
const MDIO_DEV_ADDR_SHIFT uint32 = 5
const MDIO_OP_SHIFT       uint32 = 10

const MVL_REG_GLOBAL                    uint8 = 0x1B
const MVL_GLOBAL_STATS_OP_REG           uint8 = 0x1D
const MVL_GLOBAL_STATS_OP_BUSY          uint16 = 1 << 15
const MVL_GLOBAL_STATS_OP_CAPTURE_PORT  uint16 = 5 << 12
const MVL_GLOBAL_STATS_OP_HIST_RX_TX    uint16 = 3 << 10


var Glob_fd0 *os.File = nil
var Glob_mmap0 []byte


func init () {
    var cardType string
    cardType = os.Getenv("CARD_TYPE")
    
    //quick hack to see if we are a Taormina since diag env is not setup yet
    exists, _ := Path_exists("/etc/openswitch/platform/HPE/10000")
    if exists == true {
        os.Setenv("CARD_TYPE","TAORMINA")
        cardType = "TAORMINA"
    } 
    if cardType == "LIPARI" || cardType == "MTP_MATERA" {
        var bar uint64 =0
        exists, _ := Path_exists("/tmp/fpgabars")

        os.Setenv("CARD_TYPE",cardType)

        //TRY TO STORE THE BAR VALUES IN A FILE.  WE DONT WANT TO SCAN THE PCI AND GET THE BARS EVERYTIME WE USE ONE OF THE DIAG UTILITIES THAT CALLS THIS INIT
        if exists == true {
            file, errGo := os.Open("/tmp/fpgabars")
            if errGo != nil {
                cli.Println("e", "ERROR: Failed to get FPGA BAR VALUE.   GO ERROR=%v", errGo)
                return
            }
            scanner := bufio.NewScanner(file)
            bar, _ = strconv.ParseUint(strings.TrimSuffix(scanner.Text(), "\n"), 0, 64)
            file.Close()
        } else {
            shcmds := []string{ "lspci -s 01:00.0 -v | grep 'Memory at' | awk '{print $3}'"}
            execOutput, errGo := exec.Command("sh", "-c", shcmds[0] ).Output()
            if errGo != nil {
                cli.Println("e", "ERROR: Failed to get FPGA BAR VALUE.   GO ERROR=%v", errGo)
                return
            }
            tmp := "0x" + strings.TrimSuffix(string(execOutput), "\n")
            fmt.Printf("%s\n", execOutput);
            fmt.Printf("%s\n", tmp);
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
        //fmt.Printf("bar=0x%x\n", bar)
        Glob_mmap0, Glob_fd0, _ = MMAP_Device(int64(bar), MAP_SIZE)
        //How do we gracefully unmap?   OS should do it, but would be nice to do it in code 
        //
        //defer func() {
        //    MunMAP_Device(Glob_fd0, Glob_mmap0)
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


func FpgaDumpRegionRegisters() (err error) {

    var data32 uint32 = 0

    fmt.Printf("MATERA FPGA REGISTER DUMP---\n")
    for _, entry := range(MATERA_FPGA_REGISTERS) {

        data32, err = MateraReadU32(uint64(entry.Address))
        if err != nil {
            return
        }
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }
    fmt.Printf("\n");

    return
}



func MateraReadU8(addr uint64) (value uint8, err error) {
    value = *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr]))
    return
}

func MateraReadU32(addr uint64) (value uint32, err error) {
    var bar uint64
    //var pcidevid uint32


    value = *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr]))
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
    
    bar = uint64(DEV0_BAR)
     

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


func MateraWriteU8(addr uint64, data uint8) (err error) {
    *(*uint8)(unsafe.Pointer(&Glob_mmap0[addr])) = data
    return
}

func MateraWriteU16(addr uint64, data uint16) (err error) {
    *(*uint16)(unsafe.Pointer(&Glob_mmap0[addr])) = data
    return
}

func MateraWriteU32(addr uint64, data uint32) (err error) {
    var bar uint64
    //var pcidevid uint32

    *(*uint32)(unsafe.Pointer(&Glob_mmap0[addr])) = data
    return

    /*
    pcidevid = (TAORMINA_PCI_VENDOR_ID<<16 |  (TAORMINA_PCI_DEV_ID0 + uint32(devID)))
    err = PCI_get_bar(pcidevid, &bar)
    if err != nil {
        cli.Printf("e", "Failed to find FPGA DevID 0x%x memory bar", pcidevid)
        return
    }
    */
    bar = uint64(DEV0_BAR)

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


func MdioRead(inst uint8, phy uint8, regAddr uint8) (value uint16, err error) {
    var cmd uint32
    var data uint32
    var retry uint16

    if (inst != 0  && inst != 1) {
        cli.Printf("e", "Invalid instance number")
        return
    }
    cmd = uint32(regAddr) & MDIO_REG_ADDR_MASK
    cmd |= (uint32(phy) & MDIO_DEV_ADDR_MASK) << MDIO_DEV_ADDR_SHIFT
    cmd |= (MDIO_RD_ENA << MDIO_OP_SHIFT) | MDIO_RUN_BUSY_MASK
    err = MateraWriteU32(FPGA_E0_SMI_CMD_REG + uint64(inst * 8), cmd)
    if err != nil {
        return
    }
    for retry = 0; retry < 100; retry++ {
        data, err = MateraReadU32(FPGA_E0_SMI_CMD_REG + uint64(inst * 8))
        if ((data & MDIO_RUN_BUSY_MASK) == 0) {
            data, err = MateraReadU32(FPGA_E0_SMI_DATA_REG + uint64(inst * 8))
            value = uint16(data & MDIO_DATA_MASK)
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)
    }
    cli.Println("e", "timeout waiting for operation to complete")
    return
}


func MdioWrite(inst uint8, phy uint8, regAddr uint8, value uint16) (err error) {
    var cmd uint32
    var data uint32
    var retry uint16

    if (inst != 0  && inst != 1) {
        cli.Println("e", "Invalid instance number")
        return
    }
    err = MateraWriteU32(FPGA_E0_SMI_DATA_REG + uint64(inst * 8), uint32(value))
    if err != nil {
        return
    }
    cmd = uint32(regAddr) & MDIO_REG_ADDR_MASK
    cmd |= (uint32(phy) & MDIO_DEV_ADDR_MASK) << MDIO_DEV_ADDR_SHIFT
    cmd |= (MDIO_WR_ENA << MDIO_OP_SHIFT) | MDIO_RUN_BUSY_MASK
    err = MateraWriteU32(FPGA_E0_SMI_CMD_REG + uint64(inst * 8), cmd)
    if err != nil {
        return
    }
    for retry = 0; retry < 100; retry++ {
        data, err = MateraReadU32(FPGA_E0_SMI_CMD_REG + uint64(inst * 8))
        if ((data & MDIO_RUN_BUSY_MASK) == 0) {
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)
        retry++
    }
    cli.Println("e", "timeout waiting for operation to complete")
    return
}


func MvlDump(inst uint8) (err error) {
    var port uint16
    if (inst != 0  && inst != 1) {
        cli.Println("e", "Invalid instance number")
        return
    }
    fmt.Printf("MATERA MARVELL instance %d REGISTER DUMP\n", inst)
    for port = 0; port < 10; port++ {
        fmt.Printf("  Port %d\n", port)
        // snapshot all counters for this port
        err = MdioWrite(inst, MVL_REG_GLOBAL, MVL_GLOBAL_STATS_OP_REG,
                        MVL_GLOBAL_STATS_OP_CAPTURE_PORT |
                        MVL_GLOBAL_STATS_OP_HIST_RX_TX |
                        MVL_GLOBAL_STATS_OP_BUSY | port)
        if err != nil {
            return
        }
        // wait for the snapshot to complete
        // read the captured stats
    }
    return
}