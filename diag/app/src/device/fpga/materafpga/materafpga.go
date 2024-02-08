package materafpga

import (
    "bufio"
    "errors"
    "fmt"
    "os"
    "os/exec"
    "strconv"
    //"time"
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
    if cardType == "LIPARI" || cardType == "MTP_MATERA" {
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
            shcmds := []string{ "lspci -s 01:00.0 -v | grep 'Memory at' | awk '{print $3}'", 
                                "lspci -s 02:00.0 -v | grep 'Memory at' | awk '{print $3}'"  }
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


func FpgaDumpRegionRegisters() (err error) {

    var data32 uint32 = 0
    var fpgaNumber uint32 = 0

    fmt.Printf("FPGA-%d REGISTER DUMP---\n", fpgaNumber)
    for _, entry := range(MATERA_FPGA_REGISTERS) {

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


