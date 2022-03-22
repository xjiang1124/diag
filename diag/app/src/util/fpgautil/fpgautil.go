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
    "device/fpga/taorfpga"
    //"platform/taormina"
    "device/bcm/td3"
    //"device/psu/dps800"
    "fmt"
    "os"
    "strconv"
    "time"
    "syscall"
    //"strings"
    "unsafe"

    "common/cli"
    "common/errType"
    "device/sfp"
    "device/qsfp"

    "platform/taormina"

    
    
)


const MEM_ACCESS_32  uint32 = 1
const MEM_ACCESS_64  uint32 = 2

 
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
        "fpgautil <sfp/qsfp> present\n" +
        "fpgautil <sfp/qsfp> dump <#>                 -- sfp# is 1-48  qsfp# is 1-6\n" +
        " \n" +
        "fpgautil inventory\n" +
        "\n" +
        "fpgautil flash devid\n" +
        "fpgautil flash r8/r32/r64 <addr> <length>\n" +
        "fpgautil flash w32/w64 <addr> <data>\n" +
        "fpgautil flash sectorerase <addr>\n" +
        "fpgautil flash bitswapimage <infile> <outfile>\n" +
        "fpgautil flash program/verify/generateimage <primary/secondary/allflash> <filename>\n" +
        " \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> uc/devid/featurebits/featurerow/statusreg \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> refresh \n" +
        "fpgautil cpld <cpu/gpio0/gpio1/gpio2> generateimage/verifyimage/program <filename>\n" +
        " \n" +
        "fpgautil power <cycle/on/off> <all/td3/e0/e1> [nopciscan]\n" +
        " \n" +
        "fpgautil elba <elba#> flash devid/flagstatus/status\n" +
        "fpgautil elba <elba#> flash read <addr> <length>\n" +
        "fpgautil elba <elba#> flash w32/w64 <addr> <data>\n" +
        "fpgautil elba <elba#> flash sectorerase <addr>/all\n" +
        "fpgautil elba <elba#> flash generateimage/verifyimage/writeimage uboot0/golduboot/goldfw/allflash <filename>\n" +
         " \n" +
        "fpgautil elba <elba#> cpld uc/devid/featurebits/featurerow/statusreg \n" +
        "fpgautil elba <elba#> cpld refresh \n" +
        "fpgautil elba <elba#> cpld generateimage/verifyimage/erase/program <cfg0/cfg1/fea> <filename>\n" 
        
        


                               

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

    if argc ==2 {
        if os.Args[1] == "inventory" {
            err1 := taormina.ShowInventory(0)
            if err1 != errType.SUCCESS {
                os.Exit(-1)
            } else { 
                os.Exit(0)
            }
        } else {
           fmt.Printf(" %s \n", errhelp); os.Exit(-1);
        }
    }

    if argc < 3 {
        fmt.Printf(" %s \n", errhelp); os.Exit(-1);
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
        os.Exit(0)
    } else if os.Args[1] == "td3" {  
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            os.Exit(-1)
        }
        if os.Args[2] == "prbs" {
            if argc < 3 { fmt.Printf(" Not enough args... prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>"); os.Exit(-1) }
            time, _ := strconv.ParseUint(os.Args[3], 0, 32)
            td3.Prbs(int(time), os.Args[4])
        }
        if os.Args[2] == "snake" {
            mask, _ := strconv.ParseUint(os.Args[3], 0, 32)
            duration, _ := strconv.ParseUint(os.Args[4], 0, 32)
            taormina.System_Snake_Test(td3.SNAKE_TEST_LINE_RATE, uint32(mask), uint32(duration), os.Args[5], 0, 0, 0, td3.TD3_MAX_TEMP, td3.TD3_MAX_TEMP, 90)
        }
        if os.Args[2] == "checkgb" {
            td3.CheckForRevA_Gearbox()
        }
        if os.Args[2] == "printvlan" {
            td3.PrintBCMShellVLANcmd()
        }
    } else if os.Args[1] == "sfp" {  
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }        
        if os.Args[2] == "present" {
            for i:=0;i<taorfpga.MAXSFP;i++ {
                present, errs := taorfpga.SFP_present(uint32(i))
                if errs != nil { fmt.Printf(" Error getting sfp present status"); os.Exit(0); }
                if present == true {
                    fmt.Printf(" SFP_%d: Present\n", i)
                } else {
                    fmt.Printf(" SFP_%d: Not Present\n", i)
                }
            }
        } else if os.Args[2] == "dump" {
            var sfpDev string
            if argc < 4 { fmt.Printf(" %s \n", errhelp); os.Exit(-1); }
            sfpnum, _ := strconv.Atoi(os.Args[3])
            if sfpnum < 10 {
                sfpDev = "SFP_"+os.Args[3]
            } else {
                sfpDev = "SFP_"+os.Args[3]
            }
            {
                rdData1, erri := sfp.ReadEepromAll(sfpDev) 
                if erri != errType.SUCCESS {
                    fmt.Printf(" ERROR: Read SFP Threw an error\n")
                }
                for i:=0; i<len(rdData1); i++ {
                    if i % 16 == 0 { fmt.Printf("\n %.02x:", i) }
                    fmt.Printf(" %.02x", rdData1[i])
                }
                fmt.Printf("\n")
                err := sfp.VerifyCheckSums(sfpDev)
                _, _, _, _, err1 := sfp.PrintSFPvendorData(sfpDev)
                err = err | err1 | erri
                if err != errType.SUCCESS { 
                    os.Exit(-1)
                } 
            }
        } else {
            fmt.Printf(" Ivalid Args[2] = '%s'\n", os.Args[2]);
            os.Exit(-1)
        }
        os.Exit(0)
    } else if os.Args[1] == "qsfp" {  
        if argc < 3 { fmt.Printf(" %s \n", errhelp); return; }
        if os.Args[2] == "present" {
            for i:=0;i<taorfpga.MAXQSFP;i++ {
                present, errs := taorfpga.QSFP_present(uint32(i))
                if errs != nil { fmt.Printf(" Error getting qsfp present status"); os.Exit(-1); }
                if present == true {
                    fmt.Printf(" QSFP_%d: Present\n", i)
                } else {
                    fmt.Printf(" QSFP_%d: Not Present\n", i)
                }
            }
        } else if os.Args[2] == "dump" {
            var qsfpDev string
            if argc < 4 { fmt.Printf(" %s \n", errhelp); os.Exit(-1); }
            qsfpnum, _ := strconv.Atoi(os.Args[3])
            if qsfpnum < 10 {
                qsfpDev = "QSFP_"+os.Args[3]
            } else {
                qsfpDev = "QSFP_"+os.Args[3]
            }
            {
                rdData1, erri := qsfp.ReadEepromAll(qsfpDev) 
                if erri != errType.SUCCESS {
                    fmt.Printf(" ERROR: Read QSFP Threw an error\n")
                }
                for i:=0; i<len(rdData1); i++ {
                    if i % 16 == 0 { fmt.Printf("\n %.02x:", i) }
                    fmt.Printf(" %.02x", rdData1[i])
                }
                fmt.Printf("\n")
                err := qsfp.VerifyCheckSums(qsfpDev)
                _, _, _, _, err1 := qsfp.PrintQSFPvendorData(qsfpDev)
                err = err | err1 | erri
                if err != errType.SUCCESS { 
                    os.Exit(-1)
                } 
            }
        } else {
            fmt.Printf(" Ivalid Args[2] = '%s'\n", os.Args[2]);
            os.Exit(-1)
        }
        os.Exit(0)
    } else if os.Args[1] == "regdump" {
        fpga_region, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        taorfpga.FpgaDumpRegionRegisters(uint32(fpga_region))
        os.Exit(0)
    } else if os.Args[1] == "r32" || os.Args[1] == "w32" {
        if (os.Args[1] == "r32") && argc < 4  {
            if argc < 4 {
                fmt.Printf(" ERROR r32:  Not enough args\n")
                os.Exit(-1)
            }
        }
        if (os.Args[2] == "w32") && argc < 5  {
            if argc < 4 {
                fmt.Printf(" ERROR w32:  Not enough args\n") 
                os.Exit(-1)
            }
        }
        fpga_region, err := strconv.ParseUint(os.Args[2], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }
        addr, err = strconv.ParseUint(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err)
            os.Exit(-1)
        }

        if (os.Args[1] == "r32") {
            data32, err = taorfpga.TaorReadU32(uint32(fpga_region) , uint64(bar + addr))
            if err != nil {
                cli.Printf("e", "TaorReadU32 Failed")
                os.Exit(-1)
            }
            fmt.Printf("RD [0x%.04x] = 0x%.08x\n", bar + addr, data32)
        } else {
            data64, err = strconv.ParseUint(os.Args[4], 0, 32)
            err = taorfpga.TaorWriteU32(uint32(fpga_region), uint64(bar + addr), uint32(data64))
            fmt.Printf("WR [0x%.04x] = 0x%.08x\n", bar + addr, uint32(data64))
        }
        os.Exit(0)
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
            fmt.Println(" Read with 32-bit pointer only takes ", diff, " time")
            fmt.Printf(" Data32=%x\n", data32)

            t1 = time.Now()
            data8, _ := taorfpga.TaorReadU8(3, 0) 
            t2 = time.Now()
            diff = t2.Sub(t1)
            fmt.Println(" Read with 8-bit pointer only takes ", diff, " time")
            fmt.Printf(" Data8=%x\n", data8)

            t1 = time.Now()
            t2 = time.Now()
            diff = t2.Sub(t1)
            fmt.Println(" Reading Time takes ", diff, " time")
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
        var nopciscan uint32 = 0
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
        if argc == 5 {
            nopciscan = 1
        }
        taorfpga.Asic_PowerCycle(device, state, nopciscan) 
        return
    } else if os.Args[1] == "flash" {

        if os.Args[2] == "devid" {
            value, _ := taorfpga.FlashReadDevIDReg() 
            fmt.Printf(" FLASH DEV ID=%.08x\n", value)
        } else if os.Args[2] == "we" {
            taorfpga.FlashWriteEnable()
            taorfpga.FlashCheckWriteEnable()
        } else if os.Args[2] == "readsr" {
            rd32, _  := taorfpga.FlashReadStatusReg()
            fmt.Printf(" SR=%.02x\n", rd32 & 0xFF)
        } else if os.Args[2] == "writesr" {
            wr32, _ := strconv.ParseUint(os.Args[3], 0, 32)
            taorfpga.FlashWriteStatusReg(uint32(wr32))
            fmt.Printf("WROTE %.02x to SR\n", wr32 & 0xFF)
        } else if os.Args[2] == "fileformatconvertright" {
            if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            taorfpga.FlashConvertImageRight(os.Args[3], os.Args[4])
            return
        } else if os.Args[2] == "fileformatconvertleft" {
            if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            taorfpga.FlashConvertImageLeft(os.Args[3], os.Args[4])
            return
        } else if os.Args[2] == "verify" || os.Args[2] == "generateimage" || os.Args[2] == "program" || os.Args[2] == "test" {
            //"fpgautil flash program/verify/generateimage <gold/main/allflash> <filename>\n" +
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            if os.Args[2] == "test" {
                if argc < 6 {
                    fmt.Printf(" %s \n", errhelp)
                    return
                }
                var err error = nil
                loopcnt, _ := strconv.ParseUint(os.Args[5], 0, 32)
                for i:=0; i<int(loopcnt);i++ {
                    fmt.Printf("Loop-%d\n", i)
                    t1 := time.Now()
                    err = taorfpga.FlashWriteImage(os.Args[3], os.Args[4])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t2 := time.Now()
                    fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                    err = taorfpga.FlashVerifyImage(os.Args[3], os.Args[4])
                    if err != nil {
                        os.Exit(-1)
                    }
                    t3 := time.Now()
                    fmt.Println(" Verifyring the image took ", t3.Sub(t2), " time")
                }
                return
            }
            if os.Args[2] == "program" {
                var err error = nil
                t1 := time.Now()
                err = taorfpga.FlashWriteImage(os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                t2 := time.Now()
                fmt.Println(" Flasing the image took ", t2.Sub(t1), " time")
                err = taorfpga.FlashVerifyImage(os.Args[3], os.Args[4])
                if err != nil {
                    os.Exit(-1)
                }
                t3 := time.Now()
                fmt.Println(" Verifyring the image took ", t3.Sub(t2), " time")
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
            //Disable software WP in the status register
            if addr < 0x800000 {
                err = taorfpga.FlashWriteStatusReg(0x00)   //Clear the software lock 
                if err != nil {
                    return
                }
                time.Sleep(time.Duration(50) * time.Millisecond)  
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
            if os.Args[3] == "reset" {
                bus, err := strconv.ParseUint(os.Args[2], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[2] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                fmt.Printf(" Resetting Bus %d\n", int(bus))
                taorfpga.I2cResetController2(int(bus)) 
            } else if os.Args[3][0] == 'd' {
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

        if os.Args[5] == "b" || os.Args[5] == "b" {
            fmt.Printf(" Attempting to wipe secure key from the eeprom\n")
            wrData = append(wrData, 0xFF)
            for i:=0x100;i<0x1000;i++ {
                fmt.Printf(".")
                rdData, err = taorfpga.I2c_access( uint32(bus), uint32(mux), uint32(i2cAddr), uint32(len(wrData)), wrData, 0 )
                if err != nil {
                    os.Exit(-1)
                }
            }
            os.Exit(0)
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
                        return
                    } else {
                        os.Exit(-1)
                    }
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
            } else {
                os.Exit(-1)
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
            } else {
                os.Exit(-1)
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
        } else if os.Args[2] == "all" {
            cpldNumber = 0xFF
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
            err := taorfpga.Spi_cpld_machxO2_verify_flash_contents(uint32(cpldNumber), os.Args[4])
            if err != nil {
                fmt.Printf("[ERROR] : FAiled\n")
                return
            }
        } else if os.Args[3] == "verifyall" {   //read flash and make an image from it
            if argc < 7 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            loop, _ := strconv.ParseUint(os.Args[6], 0, 32)
            for i:=0; i<int(loop); i++ {
                fmt.Printf("Loop=%d\n", i)
                err := taorfpga.Spi_cpld_machxO2_verify_flash_contents(0, os.Args[4])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
                err = taorfpga.Spi_cpld_machxO2_verify_flash_contents(3, os.Args[5])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
                err = taorfpga.Spi_cpld_machxO2_verify_flash_contents(4, os.Args[5])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
                err = taorfpga.Spi_cpld_machxO2_verify_flash_contents(5, os.Args[5])
                if err != nil {
                    fmt.Printf("[ERROR] : FAiled\n")
                    return
                }
            }
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
        if elbaNumber > 1 {
            fmt.Printf(" ERROR: Elba number needs to be 0 or 1\n", err); return 
        }
        if os.Args[3] == "flash" {
            if os.Args[4] == "devid" {
                devid, _ := taorfpga.Spi_elba_flash_read_id(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" FLASH  DevID=0x%.08x\n", devid)
            } else if os.Args[4] == "volconfig" {
                config, _ := taorfpga.Spi_elba_flash_read_volatile_config(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" FLASH  vol config=0x%.04x\n", config)
            } else if os.Args[4] == "writeenhvolconfig" {
                data, _ := strconv.ParseUint(os.Args[5], 0, 32)
                taorfpga.Spi_elba_flash_write_enh_volatile_config(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(data)) 
                fmt.Printf(" FLASH  WR ENH VOL CONFIG=0x%.02x\n", data)
            } else if os.Args[4] == "writevolconfig" {
                data, _ := strconv.ParseUint(os.Args[5], 0, 32)
                taorfpga.Spi_elba_flash_write_volatile_config(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(data)) 
                fmt.Printf(" FLASH  WR VOL CONFIG=0x%.02x\n", data)
            } else if os.Args[4] == "enhvolconfig" {
                config, _ := taorfpga.Spi_elba_flash_read_enhvolatile_config(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" FLASH  enhanced vol config=0x%.04x\n", config)
            } else if os.Args[4] == "config" {
                config, _ := taorfpga.Spi_elba_flash_read_nonvolatile_config(taorfpga.ELBA0_SPI_BUS + elbaNumber) 
                fmt.Printf(" FLASH  DevID=0x%.04x\n", config)
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
                fmt.Printf(" FLASH  Status Reg=0x%.02x\n", flag)
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
            } else if os.Args[4] == "testread" {
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
                t1 := time.Now()
                taorfpga.Spi_elba_flash_Read_N_Bytes(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(addr), uint32(rdLength), 1) 
                t2 := time.Now()
                fmt.Println(" Function took ", t2.Sub(t1), " time")
                t3 := time.Now()
                taorfpga.Spi_elba_flash_Read_N_Bytes(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(addr), uint32(rdLength), 1) 
                t4 := time.Now()
                fmt.Println(" Function took ", t4.Sub(t3), " time")
                return
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
                rd_data, _ := taorfpga.Spi_elba_flash_Read_N_Bytes(taorfpga.ELBA0_SPI_BUS + elbaNumber, uint32(addr), uint32(rdLength), 1) 
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
                data64, err := strconv.ParseUint(os.Args[6], 0, 64)
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
            if argc < 4 { fmt.Printf(" Need more args for this command\n");  return }
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
                for i:=0; i < len(data); i++ {
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

                t1 := time.Now()
                if os.Args[4] == "generateimage" {  //read flash and make an image from it
                    taorfpga.Spi_cpldX03_generate_image_from_flash(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                } else if os.Args[4] == "verifyimage" {   
                    taorfpga.Spi_cpldXO3_verify_flash_contents(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                } else if os.Args[4] == "program" {   
                    taorfpga.Spi_cpldXO3_program_flash(taorfpga.ELBA0_CPLD_SPI_BUS + elbaNumber, os.Args[5], os.Args[6])
                }
                t2 := time.Now()
                fmt.Println(" Function took ", t2.Sub(t1), " time")
                
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

 
