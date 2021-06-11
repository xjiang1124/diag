package main
/*
//#cgo CFLAGS: -I. -I../../../../lib/util
//// #cgo CFLAGS: -I../../../../../include
//#cgo LDFLAGS: -lutil -lcpld
//#include <util.h> 
// #include <stdlib.h>
// #include "../../../../lib/capricpld/cpld.h" 
import "C"
*/
import (
    //"bufio"
    //"errors"
    "fmt"
    "os"
    "strconv"
    "time"
    "syscall"
    "unsafe"

    "common/cli"
    "device/fpga/taorfpga"
)


const MEM_ACCESS_32  uint32 = 1
const MEM_ACCESS_64  uint32 = 2

/*
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
*/

 
const errhelp = "\nfpgautil:\n" +
        "<dev region> will be 0,1,2, or 3\n" +
        "fpgautil regdump <dev region>\n" +
        "fpgautil r32 <dev region> <addr>\n" +
        "fpgautil w32 <dev region> <addr> <data>\n" +
        "fpgautil mem r32 <addr>\n" +
        "fpgautil mem w32 <addr> <data>\n" +
        "fpgautil i2c bus mux i2c_addr w byte0 [byte1. . . byteN] r len   -- write/read\n" +
        "fpgautil i2c bus mux i2c_addr r len                              -- read\n" +
        "fpgautil i2c bus mux i2c_addr w byte0 [byte1 . . . byteN]        -- write\n" +
        "fpgautil i2c bus mux scan\n" +
        "fpgautil i2c debug enable/disable\n" +
        " \n" +
        "fpgautil flash devid\n" +
        "fpgautil flash program/verify/generateimage <gold/main/allflash> <filename>\n" +
        "fpgautil flash r8/r32/r64 <addr> <length>\n" +
        "fpgautil flash w32/w64 <addr> <data>\n" +
        "fpgautil flash sectorerase <addr>\n" +
        "fpgautil flash bitswapimage <infile> <outfile>\n" +
        " \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> uc \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> devid \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> featurebits \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> featurerow \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> statusreg \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> refresh \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> generateimage <filename>\n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> verifyimage <filename>\n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> program <filename>\n" +
        " \n" +
        "fpgautil power <cycle/on/off> <all/td3/e0/e1>\n" +
        " \n" +
        "fpgautil elba <elba#> flash devid\n" +
        "fpgautil elba <elba#> flash flagstatus/status\n" +
        "fpgautil elba <elba#> flash 4byte enable/disable \n" +
        "fpgautil elba <elba#> flash update/verify <filename>\n" +
        "fpgautil elba <elba#> flash read <addr> <length>\n" +
        "fpgautil elba <elba#> flash w32/w64 <addr> <data>\n" +
        "fpgautil elba <elba#> flash sectorerase <addr>/all\n" +
        "fpgautil elba <elba#> flash generateimage/verifyimage/writeimage uboot0/golduboot/goldfw/allflash <filename>\n" +
         " \n" +
        "fpgautil elba <elba#> cpld uc \n" +
        "fpgautil elba <elba#> cpld devid \n" +
        "fpgautil elba <elba#> cpld featurebits \n" +
        "fpgautil elba <elba#> cpld featurerow \n" +
        "fpgautil elba <elba#> cpld statusreg \n" +
        "fpgautil elba <elba#> cpld refresh \n" +
        "fpgautil elba <elba#> cpld erase <cfg0/cfg1> <filename>\n" +
        "fpgautil elba <elba#> cpld generateimage/verifyimage/erase/program <cfg0/cfg1> <filename>\n" 
        
        


                               

func main() {
    //var rc C.int = 0
    //var data64_C C.uint64_t = 0
    var data32, pcidevid uint32 = 0, 0
    var data64, addr, bar uint64 = 0, 0, 0
    var err error
    //var acc_type C.uint32_t = C.uint32_t(MEM_ACCESS_32)
    var i int = 0

    argc := len(os.Args[0:])
    //fmt.Printf("Arg length is %d\n", argc)

    //for i, a := range os.Args[1:] {
    //    fmt.Printf("Arg %d is %s\n", i+1, a) 
    //}

    if argc < 3 {
        fmt.Printf(" %s \n", errhelp)
        return
    }

    if os.Args[2] == "bitswapimage" && argc == 5 {
        t1 := time.Now()
        taorfpga.FlashBitSwapImage(os.Args[3], os.Args[4]) 
        t2 := time.Now()
        fmt.Println(" Creating bit swap file ", os.Args[4], " took", t2.Sub(t1), " time")
        return
    }

    //moved to init in different file
    /*
    taorfpga.Glob_mmap0, taorfpga.Glob_fd0, err = taorfpga.MMAP_Device(taorfpga.DEV0_BAR, taorfpga.MAP_SIZE)
    taorfpga.Glob_mmap1, taorfpga.Glob_fd1, err = taorfpga.MMAP_Device(taorfpga.DEV1_BAR, taorfpga.MAP_SIZE)
    taorfpga.Glob_mmap2, taorfpga.Glob_fd2, err = taorfpga.MMAP_Device(taorfpga.DEV2_BAR, taorfpga.MAP_SIZE)
    taorfpga.Glob_mmap3, taorfpga.Glob_fd3, err = taorfpga.MMAP_Device(taorfpga.DEV3_BAR, taorfpga.MAP_SIZE)
    defer func() {
        taorfpga.MunMAP_Device(taorfpga.Glob_fd0, taorfpga.Glob_mmap0)
        taorfpga.MunMAP_Device(taorfpga.Glob_fd1, taorfpga.Glob_mmap1)
        taorfpga.MunMAP_Device(taorfpga.Glob_fd2, taorfpga.Glob_mmap2)
        taorfpga.MunMAP_Device(taorfpga.Glob_fd3, taorfpga.Glob_mmap3)
    } ()
    */
    
    
    if os.Args[1] == "bar" {
        pcidevid = 0x80860f31
        err := taorfpga.PCI_get_bar(pcidevid, &bar)
        if err != nil {
            cli.Printf("e", "Failed to find FPGA DevID 0x%x memory bar", pcidevid)
        }
        cli.Printf("i", "memory bar = 0x%x", bar)
        return
    } else if os.Args[1] == "regdump" {
        fpga_region, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        taorfpga.FpgaDumpRegionRegisters(uint32(fpga_region))
        return
    } else if os.Args[1] == "r32" || os.Args[1] == "w32" {
        if (os.Args[1] == "r32") && argc < 4  {
            if argc < 4 {
                fmt.Printf(" ERROR r32:  Not enough args\n"); return
            }
        }
        if (os.Args[2] == "w32") && argc < 5  {
            if argc < 4 {
                fmt.Printf(" ERROR w32:  Not enough args\n"); return
            }
        }
        fpga_region, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        addr, err = strconv.ParseUint(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }

        if (os.Args[1] == "r32") {
            data32, err = taorfpga.TaorReadU32(uint32(fpga_region) , uint64(bar + addr))
            if err != nil {
                cli.Printf("e", "TaorReadU32 Failed")
            }

            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", bar + addr, data32)
        } else {
            data64, err = strconv.ParseUint(os.Args[4], 0, 32)
            err = taorfpga.TaorWriteU32(uint32(fpga_region), uint64(bar + addr), uint32(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.08x\n", bar + addr, uint32(data64))
        }

    } else if os.Args[1] == "mem" {
        //Check the arg count
        if (os.Args[2] == "r32" || os.Args[2] == "r64") && argc < 4  {
            if argc < 4 {
                fmt.Printf(" ERROR fpgautil mem r32/r64:  Not enough args\n"); return
            }
        }
        if (os.Args[2] == "w32" || os.Args[2] == "w64") && argc < 5  {
            if argc < 4 {
                fmt.Printf(" ERROR fpgautil mem w32/w64:  Not enough args\n"); return
            }
        }
        if os.Args[2] == "test" {
            //0x9d004
            
            var data32 uint32 = 0;
            addr, err := strconv.ParseUint(os.Args[3], 0, 64)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            t1 := time.Now()
            data32, _ = taorfpga.ReadU32(uint64(addr))
            t2 := time.Now()
            diff := t2.Sub(t1)
            fmt.Println(" Read with mmap takes ", diff, " time")
            fmt.Printf(" Data32=%x\n", data32)

            
            {
                var fd *os.File = nil
                var mmap []byte
                mmap, fd, err = taorfpga.MMAP_Device(int64(addr), int(syscall.Getpagesize()))
                //fmt.Printf(" Addr[0] = 0x%x\n", mmap[0])
                //fmt.Printf(" Addr[0] = 0x%x\n", *(*uint32)(unsafe.Pointer(&mmap[0])) )
                //fmt.Printf(" Addr[0] = 0x%x\n", *(*uint32)(unsafe.Pointer(&mmap[4])) )
                //fmt.Printf(" Addr[0] = 0x%x\n", *(*uint32)(unsafe.Pointer(&mmap[8])) )
                t1 = time.Now()
                data32 = *(*uint32)(unsafe.Pointer(&mmap[0]))
                t2 = time.Now()
                diff = t2.Sub(t1)
                fmt.Println(" Read with pointer only takes ", diff, " time")
                fmt.Printf(" Data32=%x\n", data32)
                err = taorfpga.MunMAP_Device(fd, mmap)
            }

            t1 = time.Now()
            data32, _ = taorfpga.TaorReadU32(3, 0) 
            t2 = time.Now()
            diff = t2.Sub(t1)
            fmt.Println(" Read with pointer only takes ", diff, " time")
            fmt.Printf(" Data32=%x\n", data32)
        }
        if os.Args[2] == "r32" {
            addr, err = strconv.ParseUint(os.Args[3], 0, 64)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            data32, err = taorfpga.ReadU32(uint64(addr))
            if err != nil {
                return
            }
            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", addr, data32)
        } else if os.Args[2] == "w32" {
            addr, err = strconv.ParseUint(os.Args[3], 0, 64)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            data, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            err = taorfpga.WriteU32(uint64(addr), uint32(data))
            if err != nil {
                return
            }
            fmt.Printf("WR [0x%.08x] = 0x%.08x\n", addr, uint32(data))
        }
    } else if os.Args[1] == "power" {
        //"fpgautil power <cycle/on/off> <all/td3/e0/e1>\n" +
        var state uint32
        var device uint32
        if argc < 4 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        switch os.Args[2] {
            case "on": state = taorfpga.POWER_STATE_ON
            case "off": state = taorfpga.POWER_STATE_OFF
            case "cycle": state = taorfpga.POWER_STATE_CYCLE
            default: fmt.Printf(" Error: arg[2] needs to be cycle, on, or off\n");  return
        }
        switch os.Args[3] {
            case "e0": device = taorfpga.ELBA0
            case "e1": device = taorfpga.ELBA1
            case "td3": device = taorfpga.TD3
            case "all": device = taorfpga.ALL
            default: fmt.Printf(" Error: arg[3] needs to be all, td3, e0, or e1\n");  return
        }
        taorfpga.Asic_PowerCycle(device, state) 
        return
    } else if os.Args[1] == "flash" {

        if os.Args[2] == "devid" {
            value, _ := taorfpga.FlashReadDevIDReg() 
            fmt.Printf(" FLASH DEV ID=%.08x\n", value)
        } else if os.Args[2] == "we" {
            taorfpga.FlashWriteEnable()
            taorfpga.FlashCheckWriteEnable()
        } else if os.Args[2] == "verify" || os.Args[2] == "generateimage" || os.Args[2] == "program"  {
            //"fpgautil flash program/verify/generateimage <gold/main/allflash> <filename>\n" +
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            if os.Args[2] == "program" {
                t1 := time.Now()
                taorfpga.FlashWriteImage(os.Args[3], os.Args[4])

                taorfpga.FlashVerifyImage(os.Args[3], os.Args[4])

                t2 := time.Now()
                fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                return
            }
            if os.Args[2] == "verify" {
                taorfpga.FlashVerifyImage(os.Args[3], os.Args[4])
                return
            }
            if os.Args[2] == "generateimage" {
                t1 := time.Now()
                taorfpga.FlashGenerateImageFromFlash(os.Args[3], os.Args[4]) 
                t2 := time.Now()
                fmt.Println(" Generating the image ", t2.Sub(t1), " time")
                fmt.Printf(" File %s generated\n", os.Args[3])
            }
        } else if os.Args[2] == "r8" || os.Args[2] == "r32" || os.Args[2] == "r64" {
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rdLength, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf("\n")
            for i=0;i<int(rdLength); {
                if (i%16) == 0 {
                    fmt.Printf("\n%.08x: ", uint32(addr) + uint32(i))
                }
                if os.Args[2] == "r8" {
                    data32, _ = taorfpga.FlashReadByte( (uint32(addr) + uint32(i)) ) 
                    fmt.Printf("%.02x ", data32 & 0xff)
                    i++
                } else if os.Args[2] == "r32" {
                    data32, _ = taorfpga.FlashReadFourBytes( (uint32(addr) + uint32(i)) ) 
                    fmt.Printf("%.02x %.02x %.02x %02x ", byte(data32 & 0xff), byte((data32 & 0xff00)>>8), byte((data32 & 0xff0000)>>16), byte((data32 & 0xff000000)>>24))
                    i = i + 4
                } else if os.Args[2] == "r64" {
                    data64, _ = taorfpga.FlashReadEightBytes( (uint32(addr) + uint32(i)) ) 
                    fmt.Printf("%.02x %.02x %.02x %02x ", byte(data64 & 0xff), byte((data64 & 0xff00)>>8), byte((data64 & 0xff0000)>>16), byte((data64 & 0xff000000)>>24))
                    fmt.Printf("%.02x %.02x %.02x %02x ", byte((data64 & 0xff00000000)>>32), byte((data64 & 0xff0000000000)>>40), byte((data64 & 0xff000000000000)>>48), byte((data64 & 0xff00000000000000)>>56) )
                    i = i + 8
                } else {
                    fmt.Printf(" Args[2] is not Valid\n"); return
                }
            }
            fmt.Printf("\n")
        } else if os.Args[2] == "sectorerase" {
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            taorfpga.FlashEraseSector(uint32(addr)) 
            fmt.Printf(" Erased Sector associated with Addr 0x%x\n", uint32(addr))
        } else if os.Args[2] == "w32" {
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            data64, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            taorfpga.FlashWriteFourBytes(uint32(data64), uint32(addr))
            fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
        } else if os.Args[2] == "w64" {
            addr, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            data64, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            taorfpga.FlashWriteEightBytes(data64, uint32(addr))
            fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
        } else {
            fmt.Printf(" ERROR: Invalid Flash Command\n");
        }
    } else if os.Args[1] == "i2c" {
        wrData := []byte{}
        rdData := []byte{}
        var rdSize uint32 = 0

        if argc == 4 {
            if os.Args[3][0] == 'd' {
                taorfpga.TaorWriteU32(1, taorfpga.D1_SCRTCH_3_REG, 0x00)
            } else if os.Args[3][0] == 'e' {
                taorfpga.TaorWriteU32(1, taorfpga.D1_SCRTCH_3_REG, 0xDEBDEB99)
            } else {
                fmt.Printf(" %s \n", errhelp)
            }
            return
        }
        if argc == 5 {   //scan
            matrix := make([]byte, 128)
            bus, err := strconv.ParseUint(os.Args[2], 0, 32)
            if err != nil {
                fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            mux, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            taorfpga.ExecutingScanChain = 1
            for i:=3; i<0x78; i++ {

                //if ((i >= 0x30 && i <= 0x37) || (i >= 0x50 && i <= 0x5F)) {
                    //fmt.Printf("RD(%x) \n", i)
                    rdData, err = taorfpga.I2c_access( uint32(bus), uint32(mux), uint32(i), 0x00, wrData, 1 )
                //} else {
                    //fmt.Printf("WR(%x) \n", i)
                //    rdData, err = I2c_access( uint32(bus), uint32(mux), uint32(i), 0x00, wrData, 0x00 )
                //}
                if err == nil {
                    matrix[i] = byte(i)
                } else {
                    matrix[i] = 0x99
                }
                //time.Sleep(time.Duration(10) * time.Millisecond)  //Sleep 2ms
            }
            taorfpga.ExecutingScanChain = 0
            fmt.Printf("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
            for i:=0; i<0x80; i++ {
                if (i%0x10)==0 { fmt.Printf("\n%.02x:", i) }
                if matrix[i] == 0 { fmt.Printf("   ") 
                } else if matrix[i] == 0x99 { fmt.Printf(" --") 
                } else { fmt.Printf(" %.02x", matrix[i]) }
            }
            fmt.Printf("\n")
            return
        }
        if argc < 6 {
            fmt.Printf(" ERROR: Not Enough ARGS!!\n")
            fmt.Printf(" %s \n", errhelp)
            return
        }
        bus, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        mux, err := strconv.ParseUint(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        i2cAddr, err := strconv.ParseUint(os.Args[4], 0, 32)
        if err != nil {
            fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        if os.Args[5] == "w" || os.Args[5] == "W" {
            for i=6; i<argc; i++ {
                if os.Args[i] == "r" || os.Args[i] == "R" {
                    rdLength, err := strconv.ParseUint(os.Args[i+1], 0, 32)
                    if err != nil {
                        fmt.Printf(" Args[%d] ParseUint is showing ERR = %v.   Exiting Program\n", i+1,  err); return
                    }
                    rdSize = uint32(rdLength)
                    rdData, err = taorfpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, rdSize )
                    if err == nil {
                        if err == nil {
                            fmt.Printf("\nWR: ")
                            for i=0;i<len(wrData);i++ {
                                fmt.Printf("0x%02x ", wrData[i])
                            }
                        }
                        fmt.Printf("\nRD: ")
                        for j:=0; j<len(rdData); j++ {
                            fmt.Printf("0x%.02x ", rdData[j])
                        }
                        fmt.Printf("\n")
                    }
                    return
                } else {
                    dataArg, err := strconv.ParseUint(os.Args[i], 0, 32)
                    if err != nil {
                        fmt.Printf(" Args[%d] ParseUint is showing ERR = %v.   Exiting Program\n", i, err); return
                    }
                    wrData = append(wrData, byte(dataArg))
                }
            }

            rdData, err = taorfpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, rdSize )
            if err == nil {
                fmt.Printf("\nWR: ")
                for i=0;i<len(wrData);i++ {
                    fmt.Printf("0x%02x ", wrData[i])
                }
                fmt.Printf("\n")
            }
        } else {       //read only
            rdLength, err := strconv.ParseUint(os.Args[6], 0, 32)
            if err != nil {
                fmt.Printf(" Args[6] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rdData, err = taorfpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), 0x00, wrData, uint32(rdLength) )
            if err == nil {
                fmt.Printf("\nRD: ")
                for j:=0; j<len(rdData); j++ {
                    fmt.Printf("0x%.02x ", rdData[j])
                }
                fmt.Printf("\n")
            }
        }
    } else if os.Args[1] == "cpld" {
        var cpldNumber uint32
        if argc < 4 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        //"fpgautil cpld <cpu/gpio0/gpio1/gpio2> program <filename>\n" +
        if os.Args[2] == "cpu" {
            cpldNumber = 0
        } else if os.Args[2] == "gpio0" {
            cpldNumber = 3
        } else if os.Args[2] == "gpio1" {
            cpldNumber = 4
        } else if os.Args[2] == "gpio2" {
            cpldNumber = 5
        } else {
            fmt.Printf(" ERROR: CPLD TYPE ENTERED IS NOT VALID\n")
            return
        }

        //cpldNumber, err := strconv.ParseUint(os.Args[2], 0, 32)
        //if err != nil { 
        //    fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return 
        //}
        if os.Args[3] == "uc" {   //run op usercode
            ucode, _ := taorfpga.Spi_cpld_read_usercode(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  UCODE=0x%.08x\n", cpldNumber, ucode)
        } else if os.Args[3] == "devid" {   
            ucode, _ := taorfpga.Spi_cpld_read_device_id(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  Device ID =0x%.08x\n", cpldNumber, ucode)
        } else if os.Args[3] == "refresh" {   
            taorfpga.Spi_cpld_refresh(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  Refresh performed\n", cpldNumber)
        } else if os.Args[3] == "featurebits" {   
            featurebits, _ := taorfpga.Spi_cpld_read_feature_bits(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  Feature BITS =0x%.04x\n", cpldNumber, featurebits)
        } else if os.Args[3] == "featurerow" { 
            data := []byte{}  
            data, _ = taorfpga.Spi_cpld_read_feature_row(uint32(cpldNumber)) 
            fmt.Printf("\n")
            for i:= (len(data) -1); i >= 0; i-- {
                fmt.Printf(" %.02x", data[i])
            }
            fmt.Printf("\n")
            //fmt.Printf(" CPLD-%d  Feature BITS =0x%.04x\n", cpldNumber, featurebits)
        } else if os.Args[3] == "statusreg" {   
            statusreg, _ := taorfpga.Spi_cpld_read_status_reg(uint32(cpldNumber)) 
            fmt.Printf(" CPLD-%d  statusreg =0x%.04x\n", cpldNumber, statusreg)
        } else if os.Args[3] == "generateimage" {   //read flash and make an image from it
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            taorfpga.Spi_cpld_machxO2_generate_image_from_flash(uint32(cpldNumber), os.Args[4])
        } else if os.Args[3] == "verifyimage" {   //read flash and make an image from it
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            taorfpga.Spi_cpld_machxO2_verify_flash_contents(uint32(cpldNumber), os.Args[4])
        } else if os.Args[3] == "program" {   //read flash and make an image from it
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            taorfpga.Spi_cpld_machxO2_program_flash(uint32(cpldNumber), os.Args[4])

        }
    } else if os.Args[1] == "elba" {

        var elbaNumber uint32
        if argc < 5 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        elba, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil { 
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return 
        }
        elbaNumber = uint32(elba)
        if elbaNumber > 2 {
            fmt.Printf(" ERROR: Elba number needs to be 0 or 1\n", err); return 
        }
        if os.Args[3] == "flash" {
            if os.Args[4] == "devid" {
                devid, _ := taorfpga.Spi_elba_flash_read_id(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" FLASH  DevID=0x%.08x\n", devid)
            } else if os.Args[4] == "4byte" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelp)
                    return
                }
                if os.Args[5] == "enable" {
                    taorfpga.Spi_elba_flash_enable_4byte_addr_mode(taorfpga.ELBA0_SPI_BUS + elbaNumber)   
                } else if os.Args[5] == "disable" {
                    taorfpga.Spi_elba_flash_disable_4byte_addr_mode(taorfpga.ELBA0_SPI_BUS + elbaNumber)
                } else {
                    fmt.Printf("ERROR: Argv[5] needs to be disable or enable\n")
                }
            } else if os.Args[4] == "rdextaddr" {
                ext, _ := taorfpga.Spi_elba_flash_read_extended_addr_reg(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" Extended Addr Register=0x%.02x\n", ext)
            } else if os.Args[4] == "wrextaddr" {
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                taorfpga.Spi_elba_flash_set_extended_addr_register(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(addr))
                fmt.Printf(" Wr Extended Addr0x%.08x\n", addr)
            } else if os.Args[4] == "flagstatus" {
                flag, _ := taorfpga.Spi_elba_flash_read_flag_status(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" FLASH  Flag Status Reg=0x%.02x\n", flag)
            } else if os.Args[4] == "status" {
                flag, _ := taorfpga.Spi_elba_flash_read_status(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" FLASH  Flag Status Reg=0x%.02x\n", flag)
            } else if os.Args[4] == "writeimage" || os.Args[4] == "verifyimage" || os.Args[4] == "generateimage"  {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelp)
                    return
                }
                t1 := time.Now()
                if os.Args[4] == "writeimage" {
                    taorfpga.Spi_elba_flash_WriteImage(taorfpga.ELBA0_SPI_BUS + elbaNumber, os.Args[5], os.Args[6]) 
                } else if os.Args[4] == "verifyimage" {
                    taorfpga.Spi_elba_flash_VerifyImage(taorfpga.ELBA0_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                } else if os.Args[4] == "generateimage" {
                    taorfpga.Spi_elba_flash_GenerateImageFromFlash(taorfpga.ELBA0_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                }
                t2 := time.Now()
                fmt.Println(" Function took ", t2.Sub(t1), " time")
            } else if os.Args[4] == "read" || os.Args[4] == "Read" {
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelp)
                    return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                rdLength, err := strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[6] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                fmt.Printf("\n")
                rd_data, _ := taorfpga.Spi_elba_flash_Read_N_Bytes(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(addr), uint32(rdLength)) 
                for x:=0;x<int(rdLength);x++ {
                    if (x%16) == 0 {
                        fmt.Printf("\n%.08x: ", uint32(addr) + uint32(x))
                    }
                    fmt.Printf("%.02x ", rd_data[x] & 0xff)
                }
                fmt.Printf("\n")
            } else if os.Args[4] == "sectorerase" {
                if argc < 5 {
                    fmt.Printf(" %s \n", errhelp)
                    return
                }
                if os.Args[5] == "all" {
                    fmt.Printf(" Erasing the entire flash\n")
                    taorfpga.Spi_elba_flash_erase_all_sectors(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                } else {
                    addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                    if err != nil {
                        fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                    }
                    fmt.Printf(" Erasing Sector associated with addr-%x\n", uint32(addr))
                    taorfpga.Spi_elba_flash_erase_sector(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(addr)) 
                }
            } else if os.Args[4] == "w32" {
                var data32 uint32
                if argc < 6 {
                    fmt.Printf(" Need more args for this command\n");  return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data64, err := strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data32 = uint32(data64)
                data := (*[4]byte)(unsafe.Pointer(&data32))[:]
                taorfpga.Spi_elba_flash_Write_N_Bytes(taorfpga.ELBA0_SPI_BUS + elbaNumber, data, uint32(addr))
                fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
            } else if os.Args[4] == "w64" {
                if argc < 6 {
                    fmt.Printf(" Need more args for this command\n");  return
                }
                addr, err := strconv.ParseUint(os.Args[5], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data64, err := strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                data := (*[8]byte)(unsafe.Pointer(&data64))[:]
                taorfpga.Spi_elba_flash_Write_N_Bytes(taorfpga.ELBA0_SPI_BUS + elbaNumber, data, uint32(addr))
                fmt.Printf(" [WR] Addr 0x%x = %.08x\n", uint32(addr), uint32(data64))
            } else {
                fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
                fmt.Printf(" %s \n", errhelp)
                return
            }
        } else if os.Args[3] == "cpld" {
            if os.Args[4] == "uc" {   //run op usercode
                ucode, _ := taorfpga.Spi_cpldXO3_read_usercode(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  UCODE=0x%.08x\n", elbaNumber, ucode)
            } else if os.Args[4] == "devid" {   
                ucode, _ := taorfpga.Spi_cpldXO3_read_device_id(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  Device ID =0x%.08x\n", elbaNumber, ucode)
            } else if os.Args[4] == "refresh" {   
                taorfpga.Spi_cpldXO3_refresh(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  Refresh performed\n", elbaNumber)
            } else if os.Args[4] == "featurebits" {   
                featurebits, _ := taorfpga.Spi_cpldXO3_read_feature_bits(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLDd  Feature BITS =0x%.04x\n", elbaNumber, featurebits)
            } else if os.Args[4] == "featurerow" { 
                data := []byte{}  
                data, _ = taorfpga.Spi_cpldXO3_read_feature_row(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber) 
                fmt.Printf("\n")
                for i:= (len(data) -1); i >= 0; i-- {
                    fmt.Printf(" %.02x", data[i])
                }
                fmt.Printf("\n")
                //fmt.Printf(" CPLD-%d  Feature BITS =0x%.04x\n", cpldNumber, featurebits)
            } else if os.Args[4] == "statusreg" {   
                statusreg, _ := taorfpga.Spi_cpldXO3_read_status_reg(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber) 
                fmt.Printf(" ELBA-%d CPLD  statusreg =0x%.04x\n", elbaNumber, statusreg)
            } else if os.Args[4] == "erase" {   
                if argc < 5 {
                    fmt.Printf(" %s \n", errhelp)
                    return
                }
                taorfpga.Spi_cpldXO3_erase_flash(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber, os.Args[5])
            } else if os.Args[4] == "generateimage" || os.Args[4] == "verifyimage" || os.Args[4] == "program" {   
                if argc < 7 {
                    fmt.Printf(" %s \n", errhelp)
                    return
                }
                if os.Args[4] == "generateimage" {  //read flash and make an image from it
                    taorfpga.Spi_cpldX03_generate_image_from_flash(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                } else if os.Args[4] == "verifyimage" {   
                    taorfpga.Spi_cpldXO3_verify_flash_contents(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                } else if os.Args[4] == "program" {   
                    taorfpga.Spi_cpldXO3_program_flash(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                }
            }
        } else {
            fmt.Printf(" Args[3] '%s' is incorrect.  See help for the correct arg\n", os.Args[3]); return 
        }
    } else {
        fmt.Printf("\n Incorrect Arg used.  See the help Below!!\n")
        fmt.Printf(" %s \n", errhelp)
        return
    }

    return
}

 
