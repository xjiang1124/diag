package taorfpga

import (
    "bufio"
    "errors"
    "fmt"
    "os"
    "strconv"
    //"time"
    "syscall"
    "unsafe"

    "common/cli"
)


const MEM_ACCESS_32  uint32 = 1
const MEM_ACCESS_64  uint32 = 2


const TAORMINE_PCI_VENDOR_ID  uint32 = 0x1dd8
const TAORMINE_MAX_PCI_DEV    uint32 = 0x0004
const TAORMINE_PCI_DEV_ID0    uint32 = 0x0003
const TAORMINE_PCI_DEV_ID1    uint32 = 0x0004
const TAORMINE_PCI_DEV_ID2    uint32 = 0x0005
const TAORMINE_PCI_DEV_ID3    uint32 = 0x0006


var Glob_fd0 *os.File = nil
var Glob_fd1 *os.File = nil
var Glob_fd2 *os.File = nil
var Glob_fd3 *os.File = nil
var Glob_mmap0 []byte
var Glob_mmap1 []byte
var Glob_mmap2 []byte
var Glob_mmap3 []byte 


func init () {
    
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
 


func FpgaDumpRegionRegisters(devRegion uint32) error {

    var data32 uint32 = 0
    var err error = nil
    var taor_reg_ptr []TAOR_FPGA_REGISTERS
    

    if uint32(devRegion) >= TAORMINE_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINE_MAX_PCI_DEV -1), devRegion); 
        err = errors.New(" ERROR") 
        return err
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
            return err
        }
        fmt.Printf("%-20s [%.04x] = %.08x\n", entry.Name, entry.Address, data32)
    }
    fmt.Printf("\n");

    return err
}



func TaorReadU32(devID uint32, addr uint64) (value uint32, err error) {
    var bar uint64
    //var pcidevid uint32

    if uint32(devID) >= TAORMINE_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINE_MAX_PCI_DEV -1), devID); 
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
    pcidevid = (TAORMINE_PCI_VENDOR_ID<<16 |  (TAORMINE_PCI_DEV_ID0 + uint32(devID)))
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

    if uint32(devID) >= TAORMINE_MAX_PCI_DEV {
        fmt.Printf(" FPGA ID# must be 0 - %d. You entered %d.  Exiting Program\n", (TAORMINE_MAX_PCI_DEV -1), devID); 
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
    pcidevid = (TAORMINE_PCI_VENDOR_ID<<16 |  (TAORMINE_PCI_DEV_ID0 + uint32(devID)))
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




 
