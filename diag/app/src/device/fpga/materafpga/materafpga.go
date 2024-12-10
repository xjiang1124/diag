package materafpga

import (
    "bufio"
    //"errors"
    "fmt"
    "os"
    "os/exec"
    "strconv"
    "time"
    "math"
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
    MAXSLOT = 10 //Matera MTP has 10 + 1 debug slot.  0 - 10 are valid slots
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

const MVL_STATS_POLICY_BASED   int = 0
const MVL_STATS_MAC_BASED      int = 1

//for policy based counters
const MVL_PORT_IN_DISCARDS              uint8 = 0x10
const MVL_PORT_IN_FILTERED              uint8 = 0x12
const MVL_PORT_OUT_FILTERED             uint8 = 0x13
//for MAC based counters
const MVL_REG_GLOBAL                    uint8 = 0x1B
const MVL_GLOBAL_STATS_OP_REG           uint8 = 0x1D
const MVL_GLOBAL_STATS_COUNTER_3_2_REG  uint8 = 0x1E
const MVL_GLOBAL_STATS_COUNTER_1_0_REG  uint8 = 0x1F
const MVL_GLOBAL_STATS_OP_BUSY          uint16 = 1 << 15
const MVL_GLOBAL_STATS_OP_READ_CAPTURED uint16 = 4 << 12
const MVL_GLOBAL_STATS_OP_CAPTURE_PORT  uint16 = 5 << 12
const MVL_GLOBAL_STATS_OP_FLUSH_ALL     uint16 = 1 << 12
const MVL_GLOBAL_STATS_OP_HIST_RX_TX    uint16 = 3 << 10

type mvlStat struct {
    Name        string
    NumBytes    int
    Offset      uint8
    CounterType int
    counters    [10]uint64 //one for each port
}


var Glob_fd0 *os.File = nil
var Glob_mmap0 []byte
var test uint32


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
            //fmt.Printf("%s\n", execOutput);
            //fmt.Printf("%s\n", tmp);
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
    mmap, err := syscall.Mmap(int(file.Fd()), int64(pageAddr), pageSize, syscall.PROT_READ, syscall.MAP_SHARED)
    file.Close()
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

    mmap, err := syscall.Mmap(int(file.Fd()), int64(pageAddr), pageSize, syscall.PROT_WRITE, syscall.MAP_SHARED)
    file.Close()
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
    fd.Close()
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
    fd.Close()
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
    fd.Close()
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


func PSU_present(PSUnumber uint32) (present bool, err error) {
    var data32 uint32
    present = false

    if PSUnumber > (MAXPSU - 1) {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = MateraReadU32(FPGA_PSU_STAT_REG)
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


func PSU_pwrok(PSUnumber uint32) (pwrok bool, err error) {
    var data32 uint32
    pwrok = false

    if PSUnumber > (MAXPSU - 1) {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = MateraReadU32(FPGA_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  FPGA_PSU_STAT_PWROK0) == FPGA_PSU_STAT_PWROK0) {
        pwrok = true
    }
    if PSUnumber == PSU1 && ( (data32 &  FPGA_PSU_STAT_PWROK1) == FPGA_PSU_STAT_PWROK1) {
        pwrok = true
    }
    return
}


func PSU_alert(PSUnumber uint32) (alert bool, err error) {
    var data32 uint32
    alert = false

    if PSUnumber > (MAXPSU - 1) {
        err = fmt.Errorf(" Error: PSU_present.  PSU NUMBER PASSED (%d) IS NOT VALID!", PSUnumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = MateraReadU32(FPGA_PSU_STAT_REG)
    if err != nil {
        return
    }

    if PSUnumber == PSU0 && ( (data32 &  FPGA_PSU_STAT_ALERT0) == FPGA_PSU_STAT_ALERT0) {
        alert = true
    }
    if PSUnumber == PSU1 && ( (data32 &  FPGA_PSU_STAT_ALERT1) == FPGA_PSU_STAT_ALERT1) {
        alert = true
    }
    return
}


/*********************************************************************
* The FPGA shares signals for JTAG and SPI. 
* USER needs to select which bus type the pins should use 
* i.e. JTAG or SPI 
* 
* Enable the SPI Bus via the FPGA MSIC CONTROL REGISTER and disable JTAG
*  
*********************************************************************/
func SetJTAGbusToSPI(slot uint32) (err error) {
    var data32 uint32 = 0

    if slot > MAXSLOT {
        err = fmt.Errorf("ERROR: SetJTAGbusToSPI: Invalid slot number -> %d \n", slot);
        fmt.Printf("%v", err)
        return
    }

    //Mask in the enable bit
    data32, err = MateraReadU32(FPGA_MISC_CTRL_REG)
    data32 |= (FPGA_MISC_CTRL_SLOT0_SPI_EN << slot) 
    MateraWriteU32(FPGA_MISC_CTRL_REG, data32) 

    return
}


/*********************************************************************
* The FPGA shares signals for JTAG and SPI. 
* USER needs to select which bus type the pins should use 
* i.e. JTAG or SPI 
* 
* Disable the SPI Bus via the FPGA MSIC CONTROL REGISTER and enable JTAG
*  
*********************************************************************/
func SetJTAGbusToJTAG(slot uint32) (err error) {
    var data32 uint32 = 0

    if slot > MAXSLOT {
        err = fmt.Errorf("ERROR: SetJTAGbusToJTAG: Invalid slot number -> %d \n", slot);
        fmt.Printf("%v", err)
        return
    }

    //Mask out the enable bit
    data32, err = MateraReadU32(FPGA_MISC_CTRL_REG)
    data32 = data32 & (^(FPGA_MISC_CTRL_SLOT0_SPI_EN << slot))
    MateraWriteU32(FPGA_MISC_CTRL_REG, data32) 

    return
}



func MdioRead(inst uint8, phy uint8, regAddr uint8) (value uint16, err error) {
    var cmd uint32
    var data uint32
    var retry uint16

    if (inst != 0  && inst != 1) {
        err = fmt.Errorf("Invalid instance number")
        return
    }
    cmd = uint32(regAddr) & MDIO_REG_ADDR_MASK
    cmd |= (uint32(phy) & MDIO_DEV_ADDR_MASK) << MDIO_DEV_ADDR_SHIFT
    cmd |= (MDIO_RD_ENA << MDIO_OP_SHIFT) | MDIO_RUN_BUSY_MASK
    //cli.Printf("i", "addr=0x%x, cmd=0x%x\n", FPGA_E0_SMI_CMD_REG + uint64(inst * 8), cmd)
    err = MateraWriteU32(FPGA_E0_SMI_CMD_REG + uint64(inst * 8), cmd)
    if err != nil {
        return
    }
    for retry = 0; retry < 100; retry++ {
        data, err = MateraReadU32(FPGA_E0_SMI_CMD_REG + uint64(inst * 8))
        if ((data & MDIO_RUN_BUSY_MASK) == 0) {
            data, err = MateraReadU32(FPGA_E0_SMI_DATA_REG + uint64(inst * 8))
            //cli.Printf("i", "addr=0x%x, data=0x%x\n", FPGA_E0_SMI_DATA_REG + uint64(inst * 8), data)
            value = uint16(data & MDIO_DATA_MASK)
            return
        }
        time.Sleep(time.Duration(1) * time.Microsecond)
    }
    err = fmt.Errorf("timeout waiting for operation to complete")
    return
}


func MdioWrite(inst uint8, phy uint8, regAddr uint8, value uint16) (err error) {
    var cmd uint32
    var data uint32
    var retry uint16

    if (inst != 0  && inst != 1) {
        err = fmt.Errorf("Invalid instance number")
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
    }
    err = fmt.Errorf("timeout waiting for operation to complete")
    return
}


var MvlStatCounters [10]uint64 = [10]uint64{math.MaxUint64, math.MaxUint64, math.MaxUint64, math.MaxUint64, math.MaxUint64, math.MaxUint64, math.MaxUint64, math.MaxUint64, math.MaxUint64, math.MaxUint64}
var MvlStatTbl = []mvlStat {
    mvlStat{"InDiscards",       4, 0x10, MVL_STATS_POLICY_BASED, MvlStatCounters},
    mvlStat{"InFiltered",       2, 0x12, MVL_STATS_POLICY_BASED, MvlStatCounters},
    mvlStat{"OutFiltered",      2, 0x13, MVL_STATS_POLICY_BASED, MvlStatCounters},
    //Ingress
    mvlStat{"InGoodOctets",     8, 0x00, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InBadOctets",      4, 0x02, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InUnicast",        4, 0x04, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InBroadcasts",     4, 0x06, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InMulticasts",     4, 0x07, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InPause",          4, 0x16, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InUndersize",      4, 0x18, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InFragments",      4, 0x19, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InOversize",       4, 0x1A, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InJabber",         4, 0x1B, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InRxErr",          4, 0x1C, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"InFCSErr",         4, 0x1D, MVL_STATS_MAC_BASED,    MvlStatCounters},
    //Egress
    mvlStat{"OutOctets",        8, 0x0E, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"OutUnicast",       4, 0x10, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"OutBroadcasts",    4, 0x13, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"OutMulticasts",    4, 0x12, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"OutPause",         4, 0x15, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"Deferred",         4, 0x05, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"Collisions",       4, 0x1E, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"Single",           4, 0x14, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"Multiple",         4, 0x17, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"Excessive",        4, 0x11, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"Late",             4, 0x1F, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"OutFCSErr",        4, 0x03, MVL_STATS_MAC_BASED,    MvlStatCounters},
    //both Ingress and Egress
    mvlStat{"64Octets",         4, 0x08, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"65to127Octets",    4, 0x09, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"128to255Octets",   4, 0x0A, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"256to511Octets",   4, 0x0B, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"512to1023Octets",  4, 0x0C, MVL_STATS_MAC_BASED,    MvlStatCounters},
    mvlStat{"1024toMaxOctets",  4, 0x0D, MVL_STATS_MAC_BASED,    MvlStatCounters},
}


func MvlStatsWait(inst uint8) (err error) {
    var data uint16
    for retry := 0; retry < 100; retry++ {
        data, err = MdioRead(inst, MVL_REG_GLOBAL, MVL_GLOBAL_STATS_OP_REG)
        if err != nil {
            return
        }
        if data & MVL_GLOBAL_STATS_OP_BUSY == 0 {
            return
        } else {
            time.Sleep(time.Duration(1) * time.Microsecond)
        }
    }
    return fmt.Errorf("timeout waiting for operation to complete")
}


// returns a 4-byte long counter
func MvlStatsRead(inst uint8, offset uint8) (value uint32, err error) {
    var data uint16

    err = MdioWrite(inst, MVL_REG_GLOBAL, MVL_GLOBAL_STATS_OP_REG,
                    MVL_GLOBAL_STATS_OP_READ_CAPTURED |
                    MVL_GLOBAL_STATS_OP_HIST_RX_TX |
                    MVL_GLOBAL_STATS_OP_BUSY | uint16(offset))
    if err != nil {
        return
    }
    err = MvlStatsWait(inst)
    if err != nil {
        return
    }

    data, err = MdioRead(inst, MVL_REG_GLOBAL, MVL_GLOBAL_STATS_COUNTER_3_2_REG)
    if err != nil {
        return
    }
    value = uint32(data) << 16
    data, err = MdioRead(inst, MVL_REG_GLOBAL, MVL_GLOBAL_STATS_COUNTER_1_0_REG)
    if err != nil {
        return
    }
    value = value | uint32(data)
    return
}


func MvlPortStatsMacBased(inst uint8, port uint8) (err error) {
    var data32_low, data32_high uint32

    // snapshot all counters for this port
    err = MdioWrite(inst, MVL_REG_GLOBAL, MVL_GLOBAL_STATS_OP_REG,
                    MVL_GLOBAL_STATS_OP_CAPTURE_PORT |
                    MVL_GLOBAL_STATS_OP_HIST_RX_TX |
                    MVL_GLOBAL_STATS_OP_BUSY | uint16(port))
    if err != nil {
        return
    }
    // wait for the snapshot to complete
    err = MvlStatsWait(inst)
    if err != nil {
        return
    }

    // read the captured stats
    for i := 0; i < len(MvlStatTbl); i++ {
        stat := MvlStatTbl[i]
        if stat.CounterType == MVL_STATS_POLICY_BASED {
            continue
        }
        data32_low, err = MvlStatsRead(inst, stat.Offset)
        if err != nil {
            return
        }
        if stat.NumBytes == 8 {
            data32_high, err = MvlStatsRead(inst, stat.Offset + 1)
            if err != nil {
                return
            }
        }
        MvlStatTbl[i].counters[port] = uint64(data32_high) << 32 | uint64(data32_low)
    }
    return
}


func MvlPortStatsPolicyBased(inst uint8, port uint8) (err error) {
    var data16_low, data16_high uint16
    for i := 0; i < len(MvlStatTbl); i++ {
        stat := MvlStatTbl[i]
        if stat.CounterType == MVL_STATS_POLICY_BASED {
            data16_low, err = MdioRead(inst, 0x10 + port, stat.Offset)
            if err != nil {
                return
            }
            if stat.NumBytes == 4 {
                data16_high, err = MdioRead(inst, 0x10 + port, stat.Offset + 1)
                if err != nil {
                    return
                }
            }
            MvlStatTbl[i].counters[port] = uint64(data16_high) << 16 | uint64(data16_low)
        }
    }
    return
}

func MvlPortStatus(inst uint8, port uint8) (err error) {
    data, err := MdioRead(inst, 0x10 + port, 0x0)
    if err != nil {
        return
    }
    fmt.Printf("Port Status Register: 0x%04x\n", data)
    return
}

func MvlPortDump(inst uint8, port uint8) () {
    fmt.Printf("\nstats for Port %d\n", port)
    MvlPortStatus(inst, port)
    MvlPortStatsPolicyBased(inst, port)
    MvlPortStatsMacBased(inst, port)
    for i := 0; i < len(MvlStatTbl); i++ {
        stat := MvlStatTbl[i]
        fmt.Printf("%-15s: %-20v\n", stat.Name, stat.counters[port])
    }
    return
}

func MvlDump(inst uint8, port int8) () {
    if (inst != 0  && inst != 1) {
        cli.Println("e", "Invalid instance number")
        return
    }
    fmt.Printf("MATERA MARVELL instance %d REGISTER DUMP\n", inst)
    // if port is not specified, dump all ports
    if port == -1 {
        for idx := 0; idx < 10; idx++ {
            MvlPortDump(inst, uint8(idx))
        }
    } else {
        MvlPortDump(inst, uint8(port))
    }
}

func MvlClear(inst uint8) () {
    if (inst != 0  && inst != 1) {
        cli.Println("e", "Invalid instance number")
        return
    }
    // flush all counters for this port
    err := MdioWrite(inst, MVL_REG_GLOBAL, MVL_GLOBAL_STATS_OP_REG,
        MVL_GLOBAL_STATS_OP_FLUSH_ALL | MVL_GLOBAL_STATS_OP_BUSY)
    if err != nil {
        return
    }
    // wait for the flush to complete
    MvlStatsWait(inst)
}
