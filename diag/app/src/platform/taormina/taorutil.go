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
 
package taormina

import (
    "bufio"
    "bytes"
    "crypto/md5"
    "fmt"
    "hash"
    "io"
    "regexp"
    "strconv"
    "strings"
    "common/cli"
    "common/dcli"
    "common/misc"
    "common/errType"
    "device/cpld/nicCpldCommon"
    "encoding/json"
    "hardware/i2cinfo"
    "hardware/hwdev"
    "hardware/hwinfo"
    "io/ioutil"
    "os"
    "os/exec"
    "time"

    "device/bcm/td3"
    "device/cpu/XeonD"
    "device/fpga/taorfpga"
    "device/powermodule/sn1701022"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544c20"
    "device/powermodule/tps53681"
    "device/psu/dps800" 
    "device/fanctrl/adt7462"
    "device/tempsensor/tmp451"
    "device/tempsensor/lm75a"

    "device/sfp"
    "device/qsfp"

)



const (
    MAXPSU = 2
    MAXFANMODULES = 6
    FANPERMODULE = 2

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


var rpm_rear_MAP = map[int]int {
    100 : 29000,
    75 : 19500,
    50 : 11100,
    40 : 7300,
    25 : 2100, 
}

var rpm_front_MAP = map[int]int {
    100 : 25450,
    75 : 17200,
    50 : 10000,
    40 : 6500,
    25 : 1800, 
}

type fanDevMap struct{
    dev         string
    fanNum      uint64
}

var fan_MAP = map[int]fanDevMap {
    0 : { dev:"FAN_1" , fanNum:0 } ,
    1 : { dev:"FAN_1" , fanNum:1 } ,
    2 : { dev:"FAN_1" , fanNum:2 } ,
    3 : { dev:"FAN_2" , fanNum:0 } ,
    4 : { dev:"FAN_2" , fanNum:1 } ,
    5 : { dev:"FAN_2" , fanNum:2 } ,
}


func Fan_RPM_test(tollerance int)(err int) {
    var rpm [8]uint64
    var expRPM int
    process := "fand"
    var presenceFailMask uint32 = 0
    var fanFail int = 0
    fanspeed := []int{ 75, 50, 100, 75 }

    dcli.Printf("i", "Switch Fan Test: tollerance=%d%% \n", tollerance)

    execOutput, errGo := exec.Command("sh", "-c", "cat /fs/nos/home_diag/diag/scripts/taormina/vtysh_port_shutdown.sh | vtysh").Output()
    if errGo != nil {
        cli.Println("e", string(execOutput))
        cli.Println("e", errGo)
        err = errType.FAIL
        //return
    }
    misc.SleepInSec(1)


    if running, _ := Process_Is_Running(process); running == true {
        cli.Printf("i", "fand is running.. killing it\n")
        Process_Kill(process)
        misc.SleepInSec(1)
    } 

    if running, _ := Process_Is_Running(process); running == true {
        cli.Printf("e", "HMM, fand is still running...\n")
        err = errType.FAIL 
    }

    //check if fan is present
    for j:=0; j<MAXFANMODULES; j++ {
        present, goerr := taorfpga.FAN_Module_present(uint32(j)) 
        if goerr != nil { 
            cli.Printf("e", "Reading Fan Presence Singals failed\n")
            err = errType.FAIL 
        }
        if present == false {
            cli.Printf("e", "Fan Module-%d not present\n", j)
            presenceFailMask = presenceFailMask + (1<<uint32(j))
        }
    }

    for i:=0; i<len(fanspeed); i++ {
       dcli.Printf("i","Testing Fans at PWM-%d\n", fanspeed[i])
       for j:=0; j<MAXFANMODULES; j++ {
           if (presenceFailMask & (1<<uint32(j))) > 0 {
               continue
           }
           hwdev.FanSpeedSet(fan_MAP[j].dev, fanspeed[i], (1<<fan_MAP[j].fanNum))
           if err != errType.SUCCESS {
               cli.Printf("e", "FanSpeedSet Failed on %s, fan-%d  \n", fan_MAP[j].dev, fan_MAP[j].fanNum)
               return
           }
       }
       misc.SleepInSec(10) //give fan time to change rpm
       for j:=0; j<MAXFANMODULES; j++ {
           var fanInModule uint64
           if (presenceFailMask & (1<<uint32(j))) > 0 {
               continue
           }
           for fanInModule=0; fanInModule < FANPERMODULE; fanInModule++ {
               rpm[j], err =  hwdev.FanSpeedGet(fan_MAP[j].dev, ((fan_MAP[j].fanNum * FANPERMODULE) + fanInModule) ) 
               if err != errType.SUCCESS {
                   cli.Printf("e", "FanSpeedGet Failed on %s, fan-%d  \n", fan_MAP[j].dev, fan_MAP[j].fanNum)
                   return
               }
               if fanInModule == 0 {
                   expRPM = rpm_rear_MAP[fanspeed[i]]
               } else {
                   expRPM = rpm_front_MAP[fanspeed[i]]
               }
               //fmt.Printf(" J=%d RPM=%d  expRPM=%d\n", j, rpm[j], expRPM)
               if int(rpm[j]) < expRPM - ((tollerance * expRPM)/100) {
                   if (j%2) == 0 {
                       cli.Printf("e", "Fan Module-%d Rear Fan RPM Test at %d PWM Failed.  Read RPM-%d below Thredhold %d\n", j, fanspeed[i], rpm[j], expRPM - ((tollerance * expRPM)/100))
                   } else {
                       cli.Printf("e", "Fan Module-%d Front Fan RPM Test at %d PWM Failed.  Read RPM-%d below Thredhold %d\n", j, fanspeed[i], rpm[j], expRPM - ((tollerance * expRPM)/100))
                   }
                   fanFail = errType.FAIL
               }
               if int(rpm[j]) > expRPM + ((tollerance * expRPM)/100) {
                   if (j%2) == 0 {
                       cli.Printf("e", "Fan Module-%d Rear Fan RPM Test at %d PWM Failed.  Read RPM-%d above Thredhold %d\n", j, fanspeed[i], rpm[j], expRPM + ((tollerance * expRPM)/100) )
                   } else {
                       cli.Printf("e", "Fan Module-%d Front Fan RPM Test at %d PWM Failed.  Read RPM-%d above Thredhold %d\n", j, fanspeed[i], rpm[j], expRPM + ((tollerance * expRPM)/100) )
                   }
                   fanFail = errType.FAIL
               }
           }
       }
    }

    if fanFail != 0 {
        err = errType.FAIL
    }
    if presenceFailMask != 0 {
        err = errType.FAIL
    }

    return
}

//Check for PSU and FAN MODULE PRESENCE
func Presence_Test()(err int) {

    cli.Printf("i", "PSU & Fan Module Presence Test\n")

    for i:=0; i<int(MAXPSU);i++ {
        present, _ := taorfpga.PSU_present(uint32(i))
        if present == true {
            cli.Printf("i","PSU-%d: PRESENT\n", i+1)
        } else {
            cli.Printf("e","PSU-%d: NOT PRESENT\n", i+1)
            err = errType.FAIL
        }
    }

    for i:=0; i<int(MAXFANMODULES);i++ {
        present, _ := taorfpga.FAN_Module_present(uint32(i))
        if present == true {
            cli.Printf("i","FAN Module-%d: PRESENT\n", i+1)
        } else {
            cli.Printf("e","FAN Module-%d: NOT PRESENT\n", i+1)
            err = errType.FAIL
        }
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
func SSD_Display_Info(useCLI int) (err int) {
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
                s := fmt.Sprintf("SSD MODEL: %s   S/N: %s   Capacity: %s    %s\n", devModel, sn, size, smartHealth)
                printf("i", s, useCLI)
            } else {
                smartHealth = "Smart Health FAILED"
                s := fmt.Sprintf("[ERROR] SSD MODEL: %s   S/N: %s   Capacity: %s    %s\n", devModel, sn, size, smartHealth)
                printf("e", s, useCLI)
                err = errType.FAIL
            }
        }
    }
    return

}


//read msr MC8_STATUS which has ecc error indicators
//check dmidecode as well for any errors
func X86_DDR_Check_ECC(useCLI int) (err int) {
    error_info := []string{}
    var i int = 0
    var msr_SR8 uint64
 
    out, errGo := exec.Command("rdmsr", "0x421").Output()
    if errGo != nil {
        cli.Println("e", "executing rdmsr returned error ->", errGo)
        err = errType.FAIL
        return
    }
    tmp := strings.TrimSuffix(string(out), "\n")
    msr_SR8, errGo = strconv.ParseUint(tmp, 0, 64)
    if errGo != nil {
        cli.Println("e", "Error parsing MSR MC8_STATUS ->", errGo)
        err = errType.FAIL
        return
    }
    if msr_SR8 != 0 {
        cli.Printf("e", "Error MC8_STATUS is not 0 indicating a memory issue has occured.  MC8_STATUS = 0x%x\n", msr_SR8)
        err = errType.FAIL
        return
    }


    out, errGo = exec.Command("dmidecode", "--type", "17").Output()
    if errGo != nil {
        cli.Println("e", "executing dmidecode returned error ->", errGo)
        err = errType.FAIL
        return
    }

    //Error Information Handle: No Error
    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "Error Information Handle:")==true {
            error_info = append(error_info, string(temp[26:]))
            i = i + 1
        }
    }

    for i=0; i<len(error_info); i++ {
        if (i%2)==0 {
            if error_info[i] != " No Error" {
                s := fmt.Sprintf("[ERROR] CPU Memory Module DMI Decode indicated an error --> '%s'\n", error_info[i])
                printf("e", s, useCLI)
                err = errType.FAIL
                continue
            }
        }
    }
    return
}

func X86_DDR_Display_Info(useCLI int) (err int) {
    size := []string{}
    var pn [4]string
    var sn [4]string
    var i int = 0
    var modules_detected int = 0;

    out, errGo := exec.Command("dmidecode", "--type", "17").Output()
    if errGo != nil {
        cli.Println("e", "executing dmidecode returned error ->", errGo)
        err = errType.FAIL
        return
    }

    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "Size:")==true {
            temp = strings.TrimSpace(temp)
            size = append(size, string(temp[6:11]))
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


    for i=0; i<len(size); i++ {
        if (i%2)==0 {
            if size[i] == "No Mod" {
                s := fmt.Sprintf("[ERROR] MEMORY CHANNEL-%d:  NO MODULE DETECTED\n", i)
                printf("e", s, useCLI)
                err = errType.FAIL
                continue
            } else if size[i] != "16384" {
                s := fmt.Sprintf("[ERROR] MEMORY CHANNEL-%d:  Incorrect Size detected.  Expect 16384.  Read '%s'\n", i, size[i])
                printf("e", s, useCLI)
                err = errType.FAIL
                continue
            } else {
                s := fmt.Sprintf("MEMORY CHANNEL-%d:  PN: %s    SN: %s    SIZE: %s MB\n", i, pn[i], sn[i], size[i])
                printf("i", s, useCLI)
                modules_detected++
            }
        }
    }
    if modules_detected != 2 {
        cli.Println("e", "Only detected %d memory modules", modules_detected)
        err = errType.FAIL
        return
    }
    return
}


func BIOS_Display_Version(useCLI int) (err int) {
    out, errGo := exec.Command("dmidecode", "-s", "bios-version").Output()
    if errGo != nil {
        cli.Println("e", "dmidecode returned an error -->", errGo)
        err = errType.FAIL
        return
    }
    s := fmt.Sprintf("BIOS VERSION: %s", string(out))
    printf("i", s, useCLI)

    return
}


func HALON_OS_Display_Version(useCLI int) (err int) {
    var show string = "show version"
    out, errGo := exec.Command("vtysh", "-c", show).Output()
    if errGo != nil {
        fmt.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
    }

    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "Build Date")==true ||  strings.Contains(temp, "Build ID")==true {
            s := fmt.Sprintf("HALON OS: %s\n", temp)
            printf("i", s, useCLI)
        }
    }
    return
}

func Process_Is_Running(process string) (running bool, err int) {
    out, errGo := exec.Command("ps", "-A").Output()
    if errGo != nil {
        cli.Println("e", "ERR=", errGo)
        err = errType.FAIL
        return
    }
    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, process)==true {
            running = true
            return
        } else {
            running = false
        }
    }
    return
}

func Process_Kill(process string) (err int) {
    cmdString := "sudo -S pkill -SIGINT " + process
    _, errGo := exec.Command("sh", "-c", cmdString).Output()
    if errGo != nil {
        fmt.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
    }

    return
}


func GetSerialNumbers() (systemSN string, boardSN string, err int) {
    
    out, errGo := exec.Command("sh", "-c", "fruread --chassis 1 | grep -i Serial | awk '{$1=$1};1'").Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }
    s := strings.Split(string(out), "\n")
    //Serial Number: 'FSJ212500DF'
    //TPM Serial Number: 'FSJ2125004F'
    for i, temp := range s {
        if i == 0 {
            systemSN = temp[16:27]
        }
        if i == 1 {
            boardSN = temp[20:31]
        }
    }
    return
}


/******************************************************************************************
* 
*  USB interface is very slow.  Do not use large file sizes.
*  It takes too long to sync the files to the USB stick.  16MB file takes 5 seconds to sync
*  
*   root@10000:/fs/nos/eeupdate# lsusb
    Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
    Bus 001 Device 004: ID 0403:6010 Future Technology Devices International, Ltd FT2232C/D/H Dual UART/FIFO IC
    Bus 001 Device 003: ID 0403:6010 Future Technology Devices International, Ltd FT2232C/D/H Dual UART/FIFO IC
    Bus 001 Device 002: ID 0930:6544 Toshiba Corp. TransMemory-Mini / Kingston DataTraveler 2.0 Stick
    Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

    root@10000:~# lsusb | wc -l
    5
 
    dmesg entry
    [    8.852770] usb-storage 1-1:1.0: USB Mass Storage device detected

 
******************************************************************************/ 
func USBtest(FileSizeMB int, FileCopies int) (err int) {
    var FoundUSBdevice int = 0
    fileName := "/tmp/testfile"
    TaregetfileName := "/mnt/usb/testfile"

    dcli.Printf("i", "Starting CPU USB Interface Test.  File Size=%dMB.  Copies=%d\n", FileSizeMB, FileCopies)

    dcli.Printf("i", "Checking for USB Device\n")
    //check dmesg for usb stick plugged in
    out, errGo := exec.Command("dmesg").Output()
    if errGo != nil {
        dcli.Printf("e", "dmesg failed.  Err = %s", errGo)
        err = errType.FAIL
        return
    }
    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "USB Mass Storage:")==true {
            FoundUSBdevice = 1
            dcli.Printf("i", "Device found via dmesg\n")
        }
    }

    out, errGo = exec.Command("mkfs.vfat", "/dev/sdb1").Output()
    if errGo != nil {
        dcli.Printf("e", "mkfs.vfat failed.  Err = %s", errGo)
        err = errType.FAIL
        return
    }

    out, errGo = exec.Command("mount", "/dev/sdb1", "/mnt/usb").Output()
    if errGo != nil {
        dcli.Printf("e", "mount /dev/sdb1 /mnt/usb  Err = %s", errGo)
        err = errType.FAIL
        return
    }

    //fall back to lsusb if nothing in dmesg in case the system has been in use a while and it's overflowed
    if FoundUSBdevice == 0 {
        cmdStr:="lsusb | wc -l"
        out, errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            err = errType.FAIL
            return
        }
        s := strings.Split(string(out), "\n")
        cnt, _ := strconv.ParseUint(s[0], 0, 32)
        if cnt == 5 {
            FoundUSBdevice = 1
        }
    }

    if FoundUSBdevice == 0 {
        dcli.Printf("e", "No USB Storage Device Stick found from dmesg and lsusb!!\n")
        err = errType.FAIL
        return
    }




    dcli.Printf("i", "Generating Copy File under /tmp\n")
    cmd := exec.Command("dd", "if=/dev/urandom", "of="+fileName, "bs=1M", "count="+strconv.Itoa(FileSizeMB))
    errGo = cmd.Run()
    if errGo != nil {
        cli.Printf("e", "dd failed.  err=%s\n", errGo)
        err = errType.FAIL
        return
    }

    cmd = exec.Command("sync")
    errGo = cmd.Run()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    f, errGo := os.Open(fileName)
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }
    defer f.Close()

    dcli.Printf("i", "Calculating MD5\n")
    origMd5 := md5.New()
    _, errGo = io.Copy(origMd5, f)
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    var newMd5 hash.Hash
    for i := 0; i < FileCopies; i++ {
        dcli.Printf("i", "ite=%d, Copying master file to %s\n", i, TaregetfileName+strconv.Itoa(i))
        cmd = exec.Command("cp", fileName, TaregetfileName+strconv.Itoa(i))
        _ = cmd.Run()
        dcli.Printf("i", "sync\n")
        cmd = exec.Command("sync")
        _ = cmd.Run()
        fd, errGo := os.Open(TaregetfileName+strconv.Itoa(i))
        if errGo != nil {
            cli.Println("e", errGo)
            err = errType.FAIL
            return
        }
        defer fd.Close()

        dcli.Printf("i", "Calculating MD5\n")
        newMd5 = md5.New()
        _, errGo = io.Copy(newMd5, fd)
        if errGo != nil {
            cli.Println("e", errGo)
            err = errType.FAIL
            return
        }

        if !bytes.Equal(origMd5.Sum(nil), newMd5.Sum(nil)) {
            dcli.Printf("i", "File %s has an md5sum error.   Expected=%x   Calulated=%x\n", TaregetfileName+strconv.Itoa(i), origMd5.Sum(nil), newMd5.Sum(nil))
            err = errType.FAIL
            return
        }
        cmd = exec.Command("rm", TaregetfileName+strconv.Itoa(i))
        _ = cmd.Run()
        cmd = exec.Command("sync")
        _ = cmd.Run()
    }
    dcli.Printf("i", "%d files copied to the USB stick from /tmp/testfile.  All md5sums match\n", FileCopies)

    cmdStr:="umount -l -f /mnt/usb"
    out, errGo = exec.Command("bash", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Printf("e", "umount /mnt/usb failed.  Err = %s\n", errGo)
        err = errType.FAIL
        return
    } 
     
    dcli.Printf("i", "Test Passed\n")

    return
}



/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func Taor_CPU_MemoryTest(threads uint32, percent_of_free_mem uint32, time uint32, calledFromCLI int) (err int) {
    var cmdStr string
    var freemem, i uint32
    var percent float64 = (float64(percent_of_free_mem)/100)

    dcli.Printf("i","Starting Memory Test:  Thread=%d   Percernt=%f   Time=%d\n", threads, percent, time)
    cmdStr = "cat /proc/meminfo"
    output , errGo := exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }

    s := strings.Split(string(output), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "MemFree:")==true {
            t := temp[15:25] 
            t = strings.TrimSpace(t)
            x,_ := strconv.Atoi(t)
            freemem = uint32(x)
        }
    }
    dcli.Printf("i","Freemem = %dKB\n", freemem)

    //Check that we can find stressapptest_arm in case someone tries to run this without the diag package installed
    fileExists, _ := taorfpga.Path_exists("/fs/nos/home_diag/diag/tools/stressapptest")
    if fileExists == false {
        cli.Printf("e", "Unable to locate stressapptest.  Looking under path /fs/nos/home_diag/diag/tools/stressapptest.   Check that the diag package is installed\n")
        err = errType.FAIL
        return
    }


        //Check that we can find stressapptest_arm in case someone tries to run this without the diag package installed
    fileExists, _ = taorfpga.Path_exists("stressapptest.log")
    if fileExists == true {
        fmt.Printf(" LOG EXISTS.. ERASING IT\n")
        cmdStr = "rm stressapptest.log"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }        
    }

    cmdStr = fmt.Sprintf("/fs/nos/home_diag/diag/tools/stressapptest -s %d -M %d -m %d -l stressapptest.log\n", time, int(float64(freemem) * percent)/1000, threads)
    if calledFromCLI > 0 {
        cmd := exec.Command("sh", "-c", cmdStr)
        errGo = cmd.Start()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        //Sleep.. give it a few extra seconds to finsih as the program needs time to setup/malloc memory
        for i=0;i<(time + 7);i++ {
            misc.SleepInSec(1)
            if calledFromCLI > 0 { fmt.Printf(".") 
            } else { dcli.Printf("i", ".") }
        }
        fmt.Printf("\n") 
    } else {
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","%s\n", output)
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        fmt.Printf("\n'%s'\n",output) 
    }

    cmdStr = "cat stressapptest.log"
    output , errGo = exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }
    dcli.Printf("i", "%s\n", string(output))

    if strings.Contains(string(output), "Status: PASS")==false {
        dcli.Printf("e", "[ERROR] CPU did not pass stressapptest\n")
        err = errType.FAIL
    } else {
        dcli.Printf("i", "Cpu passed stressapptest\n")
        err = errType.SUCCESS
    }

    rc := X86_DDR_Check_ECC(0)
    if rc != errType.SUCCESS {
        dcli.Printf("e", "ERROR: X86 MEMORY ERROR DETECTED\n")
        err = errType.FAIL
    }

    return
}



/********************************************************************************* 
*
* Check if network to Elba is up
* 
* 
 root@10000:/fs/nos/eeupdate# ip netns exec ntb ping -c 3 169.254.13.1
 ping: connect: Network is unreachable
 root@10000:/fs/nos/eeupdate# ip netns exec ntb ping -c 3 169.254.7.1
 ping: connect: Network is unreachable

* 
*********************************************************************************/ 
func ElbaPing(elba uint32) (err int) {
    var cmdStr string
    err = errType.FAIL

    if  elba == ELBA0 {
        cmdStr = "ip netns exec ntb ping -c 3 169.254.13.1"
    } else if elba == ELBA1 {
        cmdStr = "ip netns exec ntb ping -c 3 169.254.7.1"
    } else {
        fmt.Printf("[ERROR] Elba number passed (%d) is too big\n", elba)
        err = errType.FAIL
        return
    }
    out, errGo := exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        err = errType.FAIL
        return
    }

    if strings.Contains(string(out), "3 received, 0% packet loss") {
        err = errType.SUCCESS
        return
    }
    return
}


/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func ElbaMemoryTest(elbaMask uint32, time uint32, calledFromCLI int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    err = errType.FAIL
    var forStart, forEnd uint32
    freemem := []uint32{0, 0}

    if elbaMask == 1 {
        forStart = 0
        forEnd = 1
    } else if elbaMask == 2 {
        forStart = 1
        forEnd = 2
    } else if elbaMask == 3 {
        forStart = 0
        forEnd = 2
    } else {
        cli.Printf("e", "Elba Mask must be 0x1, 0x2, 0x3 for both elbas.  You entered 0x%x\n", elbaMask)
        err = errType.FAIL
        return
    }

    dcli.Printf("i", "for start=%d   for end=%d\n", forStart, forEnd)


    //Ping Elba to make sure the network is up
    for i=forStart; i < forEnd; i++ {
        dcli.Printf("i","Elba-%d Ping Test\n", i)
        err = ElbaPing(i) 
        if err != errType.SUCCESS {
            dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed\n", i)
            elbafailmask |= (1<<i)
        }
    }

    //Get Elba's memory info to see how much free memory is available to test with
    for i=forStart; i < forEnd; i++ {
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 cat /proc/meminfo"
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 cat /proc/meminfo"
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }

        s := strings.Split(string(output), "\n")
        for _, temp := range s {
            if strings.Contains(temp, "MemFree:")==true {
                t := temp[15:25] 
                t = strings.TrimSpace(t)
                x,_ := strconv.Atoi(t)
                freemem[i] = uint32(x)
            }
        }
    }

    //Check that we can find stressapptest_arm in case someone tries to run this without the diag package installed
    fileExists, _ := taorfpga.Path_exists("/fs/nos/home_diag/diag/tools/stressapptest_arm")
    if fileExists == false {
        cli.Printf("e", "Unable to locate stressapptest_arm.  Looking under path /fs/nos/home_diag/diag/tools/stressapptest_arm.   Check that the diag package is installed\n")
        err = errType.FAIL
        return
    }

    //Copy over stressarpptest and delete any old logs
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Copying over stressapptest_arm\n", i)
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/tools/stressapptest_arm root@169.254.13.1:/data"
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/tools/stressapptest_arm root@169.254.7.1:/data"
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }

        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 /bin/rm /data/stressapptest_arm.log"
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 /bin/rm /data/stressapptest_arm.log"
        } 
        _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
    }

    dcli.Printf("i","Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /data;./stressapptest_arm -s %d -M %d -m 12 -l stressapptest_arm.log\n", time, int(float64(freemem[0]) * .88)/1000)
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    cmdStr = fmt.Sprintf("pwd\ncd /data;./stressapptest_arm -s %d -M %d -m 12 -l stressapptest_arm.log\n", time, int(float64(freemem[1]) * .88)/1000)
    errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }


    //Start Test
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Starting Test\n", i)
        if  i == ELBA0 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba0_via_console.sh"
        } else if i == ELBA1 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba1_via_console.sh"
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }

    //Sleep.. give it a few extra seconds to finsih as the program needs time to setup/malloc memory
    for i=0;i<(time + 7);i++ {
        misc.SleepInSec(1)
        if calledFromCLI > 0 { fmt.Printf(".") 
        } else { dcli.Printf("i", ".") }
    }
    if calledFromCLI > 0 { fmt.Printf("\n") }


    //Get Results
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Get Results\n", i)
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 /bin/cat /data/stressapptest_arm.log"
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 /bin/cat /data/stressapptest_arm.log"
        }  
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))
        
        if strings.Contains(string(output), "Status: PASS")==false {
            dcli.Printf("e", "[ERROR] Elba-%d did not pass stressapptest\n", i)
            elbafailmask |= (1<<i)
        } else {
            dcli.Printf("i", "Elba-%d passed stressapptest\n", i)
        }

        rc := ElbaCheckECC(i, 1, 0, 0) 
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        }
    }

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
        }
    }
    dcli.Printf("i", "MEMTEST ERR = %d\t", err)
    return
}


/********************************************************************************* 
* 
* Below is what gets return from Elba, and then parsed.

# cd /data/nic_util;sh elba_local_read_ecc_reg.sh
0x30520020: mc0_mcc0_int_mcc_intreg
  val: 0x210
  Fields:
    [  10   ] mem_rst_valid_interrupt:             0x0
    [   9   ] controller_busy_interrupt:           0x1
    [   8   ] cntrl_freq_change_req_interrupt:     0x0
    [   7   ] smbus_req_interrupt:                 0x0
    [   6   ] dfi_init_complete_interrupt:         0x0
    [   5   ] ahb_resp_error_interrupt:            0x0
    [   4   ] controller_interrupt:                0x1
    [   3   ] ecc_dataout_uncorrected_1_interrupt: 0x0
    [   2   ] ecc_dataout_uncorrected_0_interrupt: 0x0
    [   1   ] ecc_dataout_corrected_1_interrupt:   0x0
    [   0   ] ecc_dataout_corrected_0_interrupt:   0x0
0x305a0020: mc1_mcc0_int_mcc_intreg
  val: 0x210
  Fields:
    [  10   ] mem_rst_valid_interrupt:             0x0
    [   9   ] controller_busy_interrupt:           0x1
    [   8   ] cntrl_freq_change_req_interrupt:     0x0
    [   7   ] smbus_req_interrupt:                 0x0
    [   6   ] dfi_init_complete_interrupt:         0x0
    [   5   ] ahb_resp_error_interrupt:            0x0
    [   4   ] controller_interrupt:                0x1
    [   3   ] ecc_dataout_uncorrected_1_interrupt: 0x0
    [   2   ] ecc_dataout_uncorrected_0_interrupt: 0x0
    [   1   ] ecc_dataout_corrected_1_interrupt:   0x0
    [   0   ] ecc_dataout_corrected_0_interrupt:   0x0
0x30530464: mc0_mcc0_dhs_mc_entry__S[281/0x119]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x30530468: mc0_mcc0_dhs_mc_entry__S[282/0x11a]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x3053046c: mc0_mcc0_dhs_mc_entry__S[283/0x11b]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x30530470: mc0_mcc0_dhs_mc_entry__S[284/0x11c]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x30530474: mc0_mcc0_dhs_mc_entry__S[285/0x11d]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x305b0464: mc1_mcc0_dhs_mc_entry__S[281/0x119]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x305b0468: mc1_mcc0_dhs_mc_entry__S[282/0x11a]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x305b046c: mc1_mcc0_dhs_mc_entry__S[283/0x11b]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x305b0470: mc1_mcc0_dhs_mc_entry__S[284/0x11c]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
0x305b0474: mc1_mcc0_dhs_mc_entry__S[285/0x11d]
  val: 0x0
  Fields:
    [ 31:0  ] data: 0x0
#
* 
* 
*********************************************************************************/ 

type EccRegisters struct {
    Name string 
    Val  uint64 
}

func ElbaCheckECC(elba uint32, SkipPing int, calledFromCLI int, InjectError int) (err int) {
    var cmdStr string
    var line_number int 
    var errGo error

    Elba0EccReg := []EccRegisters { 
        {"ecc_dataout_corrected_1_interrupt", 0 },
        {"ecc_dataout_corrected_0_interrupt", 0 },
        {"MC0-SYNCD_ADDR[47:40] / MC0-ADDR[39:0] ", 0 },
        {"MC0-DATA[63:0]", 0 },
        {"MC0-ECC C ID[16]", 0 },
    }
    Elba1EccReg := []EccRegisters { 
        {"ecc_dataout_corrected_1_interrupt", 0 },
        {"ecc_dataout_corrected_0_interrupt", 0 },
        {"MC0-SYNCD_ADDR[47:40] / MC0-ADDR[39:0] ", 0 },
        {"MC0-DATA[63:0]", 0 },
        {"MC0-ECC C ID[16] ", 0 },
    }


    if elba != ELBA0 && elba != ELBA1 {
        fmt.Printf("[ERROR] Elba number passed (%d) is to big\n", elba)
        err = errType.FAIL
        return
    }


    //Check the network to Elba is up
    if SkipPing == 0 {
        cli.Printf("i","Elba-%d Ping Test\n", elba)
        err = ElbaPing(elba) 
        if err != errType.SUCCESS {
            cli.Printf("e","[ERROR] Elba-%d Ping Test Failed\n", elba)
            return
        }
    }
    // Create directory if it doesn't exist 
    if  elba == ELBA0 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 mkdir /data/nic_util"
    } else if elba == ELBA1 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 mkdir /data/nic_util"
    } 
    _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
    

    dcli.Printf("i", "Elba-%d Copying over script to read ecc data\n", elba)
    if  elba == ELBA0 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/elba_local_read_ecc_reg.sh root@169.254.13.1:/data/nic_util"
    } else if elba == ELBA1 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/elba_local_read_ecc_reg.sh root@169.254.7.1:/data/nic_util"
    } 
    _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }

    cli.Printf("i", "Elba-%d Running script to dump ecc data\n", elba)
    if  elba == ELBA0 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/elba_local_read_ecc_reg.sh root@169.254.13.1:/data/nic_util"
    } else if elba == ELBA1 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/elba_local_read_ecc_reg.sh root@169.254.7.1:/data/nic_util"
    } 
    _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }


    dcli.Printf("i","Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;sh elba_local_read_ecc_reg.sh\n")
    errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        cli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;sh elba_local_read_ecc_reg.sh\n")
    errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        cli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }

    if  elba == ELBA0 {
        cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba0_via_console.sh"
    } else if elba == ELBA1 {
        cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba1_via_console.sh"
    } 
    output , errGo1 := exec.Command("sh", "-c", cmdStr).Output()
    if errGo1 != nil {
        cli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo1)
        err = errType.FAIL
        return
    }

    //get a reference point in the output.  Needed to parse the data below
    dcli.Printf("i","Checking Registers\n")
    s := strings.Split(string(output), "\n")
    for i, temp := range s {
        if strings.Contains(temp, "mc0_mcc0_int_mcc_intreg")==true {
            line_number = i
        }
    }

    if InjectError > 0 {
        s[line_number+12] = s[line_number+12][:53] + "1" + s[line_number+12][55:]
        s[line_number+29] = s[line_number+29][:9] + "1122ABCD"
        s[line_number+33] = s[line_number+33][:9] + "3344"
        s[line_number+37] = s[line_number+37][:9] + "1122ABCD"
        s[line_number+41] = s[line_number+41][:9] + "FEDC3344"
    }

    if len(s) < 66 {
        err = errType.FAIL
        cli.Printf("e", "Failed to get all the register read data back.  LEngth = %d \n", len(s))
        cli.Println("e", string(output))
    } else { 
        t := strings.TrimSpace(s[line_number+12][50:len(s[line_number+12])])
        x,_ :=  strconv.ParseUint(t, 0, 32)
        Elba0EccReg[0].Val = x
        t = strings.TrimSpace(s[line_number+13][50:len(s[line_number+13])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        Elba0EccReg[1].Val = x
        t = strings.TrimSpace(s[line_number+29][6:len(s[line_number+29])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+33][6:len(s[line_number+33])])
        z,_ :=  strconv.ParseUint(t, 0, 32)
        Elba0EccReg[2].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+37][6:len(s[line_number+37])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+41][6:len(s[line_number+41])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        Elba0EccReg[3].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+45][6:len(s[line_number+45])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        Elba0EccReg[4].Val = x

        t = strings.TrimSpace(s[line_number+26][50:len(s[line_number+26])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        Elba1EccReg[0].Val = x
        t = strings.TrimSpace(s[line_number+27][50:len(s[line_number+27])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        Elba1EccReg[1].Val = x
        t = strings.TrimSpace(s[line_number+49][6:len(s[line_number+49])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+53][6:len(s[line_number+53])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        Elba1EccReg[2].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+57][6:len(s[line_number+57])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+61][6:len(s[line_number+61])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        Elba1EccReg[3].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+65][6:len(s[line_number+65])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        Elba1EccReg[4].Val = x

        if elba == 0 {
            for i:=0; i< len(Elba0EccReg); i++ {
                if Elba0EccReg[i].Val > 0 {
                    err = errType.FAIL
                    cli.Printf("e", "ECC ERROR DETECTED: ECC REGISTER SET\n")
                    for j:=0; j< len(Elba0EccReg); j++ {
                        cli.Printf("e", "%s : 0x%x", Elba0EccReg[j].Name, Elba0EccReg[j].Val)
                    }
                    return
                }
            }
        }
        if elba == 1 {
            for i:=0; i< len(Elba1EccReg); i++ {
                if Elba1EccReg[i].Val > 0 {
                    err = errType.FAIL
                    cli.Printf("e", "ECC ERROR DETECTED: ECC REGISTER SET\n")
                    for j:=0; j< len(Elba1EccReg); j++ {
                        cli.Printf("e", "%s : 0x%x", Elba1EccReg[j].Name, Elba1EccReg[j].Val)
                    }
                    return
                }
            }
        }
    }
    return
}


func Elba_Check_Pci_Link(elba int, useCLI int) (err int) {
    var elb_pci string
    var speed, width bool = false, false
    if elba == ELBA0 {
        elb_pci = ELBA0_PCIBUS
    } else if elba == ELBA1 {
        elb_pci = ELBA1_PCIBUS
    } else {
        cli.Printf("e", "Elba number passed (%d) is to big\n", elba)
        err = errType.FAIL
        return
    }

    out, errGo := exec.Command("lspci", "-n", "-s", elb_pci).Output()
    if errGo != nil {
        cli.Printf("e", "lspci 1 failed --> ", errGo)
        err = errType.FAIL
        return
    }
    if strings.Contains(string(out), elb_pci)==false {
        cli.Printf("e", "[ERROR] Elba-%d is not enumerated on the PCI bus\n", elba)
        err = errType.FAIL
        return
    }

    out, errGo = exec.Command("lspci", "-s", elb_pci, "-vvv").Output()
    if errGo != nil {
        cli.Printf("e", "lspci 2 failed --> ", errGo)
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
                s := fmt.Sprintf("ELBA-%d %s\n", elba, temp)
                printf("i", s, useCLI)
            } else {
                s := fmt.Sprintf("[ERROR] ELBA-%d LINK SPEED IS NOT 8GT/s x4 -->  %s\n", elba, temp)
                printf("e", s, useCLI)
                err = errType.FAIL
            }
        }
    }
    return
}


/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func ElbaRTCtest(elbaMask uint32, calledFromCLI int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    err = errType.FAIL
    var forStart, forEnd uint32

    if elbaMask == 1 {
        forStart = 0
        forEnd = 1
    } else if elbaMask == 2 {
        forStart = 1
        forEnd = 2
    } else if elbaMask == 3 {
        forStart = 0
        forEnd = 2
    } else {
        cli.Printf("e", "Elba Mask must be 0x1, 0x2, 0x3 for both elbas.  You entered 0x%x\n", elbaMask)
        err = errType.FAIL
        return
    }

    dcli.Printf("i", "for start=%d   for end=%d\n", forStart, forEnd)


    //Ping Elba to make sure the network is up
    for i=forStart; i < forEnd; i++ {
        dcli.Printf("i","Elba-%d Ping Test\n", i)
        err = ElbaPing(i) 
        if err != errType.SUCCESS {
            dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed\n", i)
            elbafailmask |= (1<<i)
        }
    }

    //Check that we can find stressapptest_arm in case someone tries to run this without the diag package installed
    fileExists, _ := taorfpga.Path_exists("/fs/nos/home_diag/nic_diag/diag/util/rtcutil")
    if fileExists == false {
        cli.Printf("e", "Unable to locate rtcutil.  Looking under path /fs/nos/home_diag/nic_diag/diag/util/rtcutil.   Check that the arm diag package is installed\n")
        err = errType.FAIL
        return
    }

    //Copy over stressarpptest and delete any old logs
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Copying over rtcutil\n", i)
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/nic_diag/diag/util/rtcutil root@169.254.13.1:/data/nic_util"
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/nic_diag/diag/util/rtcutil root@169.254.7.1:/data/nic_util"
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }

    //Run Test & Get Results
    /*
    [INFO]    [2021-12-01-17:44:27.644] RTC 1st reading: 01/12/00(m/d/n) 21:38:50(h:m:s)
    [INFO]    [2021-12-01-17:44:32.646] RTC 2nd reading: 01/12/00(m/d/n) 21:38:55(h:m:s)
    [INFO]    [2021-12-01-17:44:32.646] RTC Test on RTC Passed.
    */
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Running Test\n", i)
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 \"export CARD_TYPE=ORTANO2;/data/nic_util/rtcutil -dev RTC -test\""
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 \"export CARD_TYPE=ORTANO2;/data/nic_util/rtcutil -dev RTC -test\""
        }  
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s", string(output))
        
        if strings.Contains(string(output), "Test on RTC Passed")==false {
            dcli.Printf("e", "[ERROR] Elba-%d did not pass it's RTC test\n", i)
            elbafailmask |= (1<<i)
            return
        } else {
            dcli.Printf("i", "Elba-%d passed RTC test\n", i)
        }
    }

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
        }
    }
    dcli.Printf("i", "err = %d", err)
    return
}



func Elba_Show_Firmware(elba int, useCLI int) (err int) {
    var ip string
    var netns bool = false
    /*
    var elb_pci string
    

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
    */



    out, _ := exec.Command("ip", "netns").Output()
    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, "ntb")==true {
            netns = true
            break
        }
    }
    if netns == false {
        cli.Printf("e", "[ERROR] ELBA-%d Firmware List.  Netns device ntb not found, cannot query firmware\n", elba)
        err = errType.FAIL
        return
    }

    if elba == ELBA0 {
        ip = "root@169.254.13.1"
    } else {
        ip = "root@169.254.7.1"
    }

    out, errGo := exec.Command("ip", "netns", "exec", "ntb", "sshpass", "-p", "pen123", "timeout", "500", "ssh", "-o", "LogLevel=ERROR", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", ip, "/nic/tools/fwupdate", "-l").Output()
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
            cli.Printf("e", "[ERROR] Failed to parse fw output.  Error=%v\n", errg)
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
                        s := fmt.Sprintf("ELBA-%d  %s: %s\n", elba, partition, s1[len(s1) -1])
                        printf("i", s, useCLI)
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


func FPGA_Strapping_Test(expected_rev int) (err int) {
    var strapping uint32
    err = errType.SUCCESS

    dcli.Printf("i", "Starting Taor Resistor Strapping Test\n")

    strapping, _ = taorfpga.GetResistorStrapping() 

    dcli.Printf("i", "Strapping Rev=0x%x  Epxected=0x%x\n", strapping , expected_rev)
    if strapping != uint32(expected_rev) {
        dcli.Printf("e", " Taor Resistor Strapping Test FAILED\n")
        err = errType.FAIL
    } else {
        dcli.Printf("i", " Taor Resistor Strapping Test PASSED\n")
    }

    return
}



/********************************************************************************* 
*
i2cset -y -f 0 0x62 0x00 0
i2cset -y -f 0 0x62 0xDA 0x55 0x50 i

i2cset -y -f 0 0x62 0x00 1
i2cset -y -f 0 0x62 0xDA 0x19 0x2A i

i2cset -y -f 0 0x62 0x9A 0x02 0x17 0x00 i
i2cset -y -f 0 0x62 0x9B 0x02 0x64 0x02 i 
 
i2cset -y -f 0 0x62 0x00 0 
i2cset -y -f 0 0x62 0x00 0x11 
 
 
i2cset -y -f 0 0x62 0x00 0
i2cget -y -f 0 0x62 0xDA w
i2cset -y -f 0 0x62 0x00 1
i2cget -y -f 0 0x62 0xDA w
i2cget -y -f 0 0x62 0x9A w
i2cget -y -f 0 0x62 0x9b w 
* 
*********************************************************************************/ 
func ElbaVRMfix() (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    err = errType.FAIL
    var forStart, forEnd uint32 = 0,2
    register := []uint32{0xDA,   0xDA,   0x9A,   0x9B}
    expected := []uint32{0x5055, 0x2a19, 0x1702, 0x6402}

    dcli.Printf("i", "for start=%d   for end=%d\n", forStart, forEnd)


    //Ping Elba to make sure the network is up
    for i=forStart; i < forEnd; i++ {
        dcli.Printf("i","Elba-%d Ping Test\n", i)
        err = ElbaPing(i) 
        if err != errType.SUCCESS {
            dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed\n", i)
            elbafailmask |= (1<<i)
        }
    }

    dcli.Printf("i","Writing VRM\n")
    //This file will get executed by the script "exec_cmd_elba0_via_console.sh" below
    cmdStr = fmt.Sprintf("pwd\ni2cset -y -f 0 0x62 0x00 0;i2cset -y -f 0 0x62 0xDA 0x55 0x50 i;i2cset -y -f 0 0x62 0x00 1;i2cset -y -f 0 0x62 0xDA 0x19 0x2A i;i2cset -y -f 0 0x62 0x9A 0x02 0x17 0x00 i;i2cset -y -f 0 0x62 0x9B 0x02 0x64 0x02 i;i2cset -y -f 0 0x62 0x00 0;i2cset -y -f 0 0x62 0x11\n")
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Executing Script to Write VRM\n", i)
        if  i == ELBA0 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba0_via_console.sh"
        } else if i == ELBA1 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba1_via_console.sh"
        }
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", string(output))
    }


    dcli.Printf("i","Checking VRM\n")
    //This file will get executed by the script "exec_cmd_elba0_via_console.sh" below
    cmdStr = fmt.Sprintf("pwd\ni2cset -y -f 0 0x62 0x00 0;i2cget -y -f 0 0x62 0xDA w;i2cset -y -f 0 0x62 0x00 1;i2cget -y -f 0 0x62 0xDA w;i2cget -y -f 0 0x62 0x9A w;i2cget -y -f 0 0x62 0x9b w\n")
    errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }



    for i=forStart; i < forEnd; i++ {
        read := []uint32{}
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Check VRM\n", i)
        if  i == ELBA0 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba0_via_console.sh"
        } else if i == ELBA1 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba1_via_console.sh"
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        //dcli.Printf("i", "%s\n", string(output))
        s := strings.Split(string(output), "\n")
        for _, temp := range s {
            if temp[0] == '0' && temp[1] == 'x' {
                data32, _ := strconv.ParseUint(temp[0:6], 0, 32)
                fmt.Printf(" Data32=%x\n", data32)
                read = append(read, uint32(data32))
            }
        }
        if len(read) != len(expected) {
            dcli.Printf("e","ERROR: Did not get all the I2C reads.  Read Len=%d.  Expected=%d", len(read), len(expected) )
            err = errType.FAIL
            return
        }
        for i:=0; i<len(expected); i++ {
            dcli.Printf("i"," %x  %x\n", expected[i], read[i])
            if expected[i] != read[i] {
                dcli.Printf("e","ERROR: VRM Register-%d  Read=%x.  Expected=%x", register[i], expected[i], read[i] )
                err = errType.FAIL
                return
            }
        }
    }

    dcli.Printf("i", "err = %d", err)
    return
}



/************************************************************************ 
*  
* FIX POUT AND IOUT READING ON TPS53681 FOR TD3 
* 
* 
FIX FIX 
./taorfpga i2c 0 3 0x60 w 0x00 00
./taorfpga i2c 0 3 0x60 w 0xda 0xc8 0x25
./taorfpga i2c 0 3 0x60 w 0xdc 0x70 0xd5
./taorfpga i2c 0 3 0x60 w 0x00 01
./taorfpga i2c 0 3 0x60 w 0xda 0x1E 0x0f
./taorfpga i2c 0 3 0x60 w 0xdc 0xf0 0x07
./fpgautil i2c 0 3 0x60 w 0x9a 0x02 0x17 0x00
./fpgautil i2c 0 3 0x60 w 0x9b 0x02 0x62 0x02
./taorfpga i2c 0 3 0x60 w 0x11


./taorfpga i2c 0 3 0x60 w 0x00 00
./taorfpga i2c 0 3 0x60 w 0xda 0xc8 0x50
./taorfpga i2c 0 3 0x60 w 0xdc 0x70 0xd5
./taorfpga i2c 0 3 0x60 w 0x00 01
./taorfpga i2c 0 3 0x60 w 0xda 0x1E 0x20
./taorfpga i2c 0 3 0x60 w 0xdc 0xf0 0x07
./fpgautil i2c 0 3 0x60 w 0x9a 0x02 0x00 0x00
./fpgautil i2c 0 3 0x60 w 0x9b 0x02 0x62 0x00
./taorfpga i2c 0 3 0x60 w 0x11
* 
************************************************************************/
func TD3_VRM_FIX(devName string) (err int) {
    var errGo error
    var NeedsUpdate int = 0 
    i2cCmds := [][]byte{  {0x00, 0x00},
                          {0xDA, 0xC8, 0x25},
                          {0xDC, 0x70, 0xd5},
                          {0x9A, 0x02, 0x17, 0x00},
                          {0x9B, 0x02, 0x62, 0x02},
                          {0x00, 0x01},
                          {0xDA, 0x1E, 0x0F},
                          {0xDC, 0xF0, 0x07}}
    wrData := []uint8{ 0x00 }
    rdData := []uint8{}

    iInfo, rc := i2cinfo.GetI2cInfo(devName)
    if rc != errType.SUCCESS {
        dcli.Println("e", "Failed to obtain I2C info of", devName)
        err = rc
        return
    }

    cli.Printf("i","Checking if VRM needs updating\n")
    for i:=0; i<len(i2cCmds); i++ {
        //set the page to read from
        if i2cCmds[i][0] == 0x00 {
            _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cCmds[i])), i2cCmds[i], 0 )
            if errGo != nil {
                dcli.Println("e", "I2C Access (3) Failed to", devName, " ERROR=",errGo); 
                err = errType.FAIL; 
                return
            }
        } else {
            wrData[0] = i2cCmds[i][0]   //set register in the write data
            rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), 1, wrData, uint32(len(i2cCmds[i]) - 1) )
            if errGo != nil {
                dcli.Println("e", "I2C Access (4) Failed to", devName, " ERROR=",errGo); 
                err = errType.FAIL; 
                return
            }
            for j:=0; j<(len(i2cCmds[i])-1); j++ {
                if i2cCmds[i][j+1] != rdData[j] {
                    NeedsUpdate = 1
                    break
                }
            }
        }
    }

    if NeedsUpdate == 0 {
        cli.Printf("i","TD3 VRM is up to date\n")
        return
    }

    cli.Printf("i", "Writing TD3 VRM to fix POUT AND IOUT\n")
    for i:=0; i<len(i2cCmds); i++ {
        _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cCmds[i])), i2cCmds[i], 0 )
        if errGo != nil {
            dcli.Println("e", "I2C Access (2) Failed to", devName, " ERROR=",errGo); 
            err = errType.FAIL; 
            return
        }
    }

    cli.Printf("i", "Checking Registers before having VRM save it's config\n")
    for i:=0; i<len(i2cCmds); i++ {
        //set the page to read from
        if i2cCmds[i][0] == 0x00 {
            _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cCmds[i])), i2cCmds[i], 0 )
            if errGo != nil {
                dcli.Println("e", "I2C Access (3) Failed to", devName, " ERROR=",errGo); 
                err = errType.FAIL; 
                return
            }
        } else {
            wrData[0] = i2cCmds[i][0]   //set register in the write data
            rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), 1, wrData, uint32(len(i2cCmds[i]) - 1) )
            if errGo != nil {
                dcli.Println("e", "I2C Access (4) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
            }
            for j:=0; j<(len(i2cCmds[i])-1); j++ {
                if i2cCmds[i][j+1] != rdData[j] {
                    dcli.Printf("e", "Checking Write data before writing config failed.  VRM Reg=%x  WR[%d]=%x  RD=%x\n", i2cCmds[i][0], j, i2cCmds[i][j+1],rdData[j])
                    err = errType.FAIL; 
                    return
                }
            }
        }
    }

    wrData[0] = 0x11
    _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (2) Failed to", devName, " ERROR=",errGo); 
        err = errType.FAIL; 
        return
    }
    cli.Printf("i","TD3 VRM Update PASSED\n")
    return
}

/************************************************************************ 
* 
* Check AVS is programmed on Trident3.   Take TOPS_AVS_SEL_REG, run it 
* through the equiation and check the VRM.
 
    BCM.0> g TOP_AVS_SEL_REG
    TOP_AVS_SEL_REG.top0[7][0x2009800]=0x7e: <RESERVED_0=0,AVS_SEL=0x7e>

      255–(1.52-(1.6-(126-2)*0.00625))/0.005 = 0x74
 
         #SET VID
        ./taorfpga i2c 0 3 0x60 w 0x00 0x00 > /dev/null
        ./taorfpga i2c 0 3 0x60 w 0x21 $VID 0x00 > /dev/null
        ./taorfpga i2c 0 3 0x60 w 0xDB $VID > /dev/null
        ./taorfpga i2c 0 3 0x60 w 0x11 > /dev/null

* 
************************************************************************/
func TD3_Check_AVS_Programming(devName string) (err int) {
    var errGo error
    i2cCmds := [][]byte{  {0x00, 0x00},
                          {0x21, 0x74, 0x00},
                          {0xDB, 0x74} }
    wrData := []uint8{ 0x00 }
    rdData := []uint8{}

    cli.Printf("i","Testing TD3 AVS Programming at the VRM\n")

    iInfo, rc := i2cinfo.GetI2cInfo(devName)
    if rc != errType.SUCCESS {
        dcli.Println("e", "Failed to obtain I2C info of", devName)
        err = rc
        return
    }

    data32, rc := td3.ReadReg("TD3", "TOP_AVS_SEL_REG")
     if rc != errType.SUCCESS {
        dcli.Println("e", "Failed to read TOP_AVS_SEL_REG from the bcm shell")
        err = rc
        return
    } 
    cli.Printf("i", "TD3 TOP AVS SEL REG=0x%x\n", data32)
    {
        var fdata float64 = float64(data32)
        fdata = 255 - ((1.52 - (1.6 - (fdata-2) * 0.00625))/0.005)
        data32 = uint32(fdata)
    } 
    cli.Printf("i", "CONVERTED VRM VALUE=0x%x\n", data32)
    
    for i:=0; i<len(i2cCmds); i++ {
        //set the page to read from
        if i2cCmds[i][0] == 0x00 {
            _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cCmds[i])), i2cCmds[i], 0 )
            if errGo != nil {
                cli.Println("e", "I2C Access (3) Failed to", devName, " ERROR=",errGo); 
                err = errType.FAIL; 
                return
            }
        } else {
            wrData[0] = i2cCmds[i][0]   //set register to read in the write data
            rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), 1, wrData, uint32(len(i2cCmds[i]) - 1) )
            if errGo != nil {
                cli.Println("e", "I2C Access (4) Failed to", devName, " ERROR=",errGo); 
                err = errType.FAIL; 
                return
            }
            if rdData[0] != uint8(data32) {
                cli.Printf("e", "TD3 VOUT NOT SET CORRECTLY ON VRM.   VRM REG 0x%x.   EXPECTED=0x%x   READ=0x%x\n", i2cCmds[i][0], data32, rdData[0])
                err = errType.FAIL; 
                return
            }
        }
    }
    cli.Printf("i","TD3 AVS Programming Passed\n")
    return
}


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
    rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 1 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (1) Failed to", devName, " ERROR=",errGo)
        err = errType.FAIL
        return
    }

    if rdData[0] != nicCpldCommon.ID_TAORMINA_ELBA {
        dcli.Printf("e", "%s DEVICE ID IS WRONG:  EXPECT 0x%.02x.   Read 0x%.02x", devName, nicCpldCommon.ID_TAORMINA_ELBA, rdData[0] )
        err = errType.FAIL
        return
    }

    _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cWrData[0])), i2cWrData[0], 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (2) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }
    _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(i2cWrData[1])), i2cWrData[1], 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (3) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }

    rdData = nil
    wrData[0] = i2cWrData[0][0]
    rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), 1, wrData, 1 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (4) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }
    if rdData[0] != i2cWrData[0][1] {
        dcli.Printf("e", "%s Register-0x%.02x  Wrote 0x%.02x.   Read 0x%.02x", devName, i2cWrData[0][0], i2cWrData[0][1],  rdData[0] )
        err = errType.FAIL
        return
    }

    rdData = nil
    wrData[0] = i2cWrData[1][0]
    rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), 1, wrData, 1 )
    if errGo != nil {
        dcli.Println("e", "I2C Access (4) Failed to", devName, " ERROR=",errGo); err = errType.FAIL; return
    }
    if rdData[0] != i2cWrData[1][1] {
        dcli.Printf("e", "%s Register-0x%.02x  Wrote 0x%.02x.   Read 0x%.02x", devName, i2cWrData[1][0], i2cWrData[1][1],  rdData[0] )
        err = errType.FAIL
        return
    }

    return
}


func printf(t string, s string, useCLI int) {
    if useCLI > 0 {
        cli.Printf(t,s)
    } else {
        fmt.Printf(s)
    }
}


/************************************************************************************************************
* 
* This gets called from both a binary utility from the linux shell, and it's used by the switch DSP 
* There is a flag to switch what printf it uses (cli vs fmt).  DSP uses CLI, Binary uses fmt 
* 
*************************************************************************************************************/ 
func ShowInventory(useCLI int) (err int) {
    var s string
    var data32 uint32 = 0
    var rc int = 0
    fmt.Printf("\n")

    //EEPROM
    systemSN, boardSN, err1 := GetSerialNumbers() 
    if err1 != errType.SUCCESS { 
        printf("e", "System SN: [ERROR RETREIVING DATA]\n", useCLI)
        printf("e", "Board  SN: [ERROR RETREIVING DATA]\n\n", useCLI)
        rc = -1
    } else {
        s = fmt.Sprintf("System SN: %s\n", systemSN)
        printf("i", s, useCLI)
        s = fmt.Sprintf("Board  SN: %s\n\n", boardSN)
        printf("i", s, useCLI)
    }

    //PSU's
    err=dps800.DisplayManufacturingInfo("PSU_1", useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err=dps800.DisplayManufacturingInfo("PSU_2", useCLI)
    if err != errType.SUCCESS { rc = -1 }
    for i:=0; i<int(taorfpga.MAXFAN);i++ {
        present, _ := taorfpga.FAN_Module_present(uint32(i))
        if present == true {
            s = fmt.Sprintf("FAN-%d: PRESENT\n", i+1)
            printf("i", s, useCLI)
        } else {
            s = fmt.Sprintf("FAN-%d: NOT PRESENT\n", i+1)
            printf("e", s, useCLI)
            rc = -1
        }
    }
    fan_air_direction, _ := taorfpga.FAN_AirFlow_Direction()
    if fan_air_direction == taorfpga.AIRFLOW_FRONT_TO_BACK {
        printf("i", "FAN AIRFLOW:  FRONT TO BACK\n", useCLI)
    } else {
        printf("i", "FAN AIRFLOW:  BACK TO FRONT\n", useCLI)
    }
    printf("i", "\n", useCLI)
    ucode, errGo := taorfpga.Spi_cpldXO3_read_usercode(uint32(1)) 
    if errGo != nil { 
        s = fmt.Sprintf("CPLD-E1 READ ERROR --> %v ", errGo)
        printf("e", s, useCLI)
        rc = -1 
    } else {
        s = fmt.Sprintf("CPLD-E0 REVISION: 0x%.08x\n", ucode)
        printf("i", s, useCLI)
    }
    ucode, errGo = taorfpga.Spi_cpldXO3_read_usercode(uint32(2)) 
    if errGo != nil { 
        s = fmt.Sprintf("CPLD-E1 READ ERROR --> %v ", errGo)
        printf("e", s, useCLI)
        rc = -1 
    } else {
        s = fmt.Sprintf("CPLD-E1 REVISION: 0x%.08x\n", ucode)
        printf("i", s, useCLI)
    }
    ucode, errGo = taorfpga.Spi_cpld_read_usercode(uint32(0)) 
    if errGo != nil { 
        s = fmt.Sprintf("CPLD-CPU READ ERROR --> %v ", errGo)
        printf("e", s, useCLI)
        rc = -1 
    } else {
        s = fmt.Sprintf("CPLD-C  REVISION: 0x%.08x\n", ucode)
        printf("i", s, useCLI)
    }
    ucode, errGo = taorfpga.Spi_cpld_read_usercode(uint32(3)) 
    if errGo != nil { 
        s = fmt.Sprintf("CPLD-G0 READ ERROR --> %v ", errGo)
        printf("e", s, useCLI)
        rc = -1 
    } else {
        s = fmt.Sprintf("CPLD-G0 REVISION: 0x%.08x\n", ucode)
        printf("i", s, useCLI)
    }
    ucode, errGo = taorfpga.Spi_cpld_read_usercode(uint32(4)) 
    if errGo != nil { 
        s = fmt.Sprintf("CPLD-G0 READ ERROR --> %v ", errGo)
        printf("e", s, useCLI)
        rc = -1 
    } else {
        s = fmt.Sprintf("CPLD-G1 REVISION: 0x%.08x\n", ucode)
        printf("i", s, useCLI)
    }
    ucode, errGo = taorfpga.Spi_cpld_read_usercode(uint32(5)) 
    if errGo != nil { 
        s = fmt.Sprintf("CPLD-G0 READ ERROR --> %v ", errGo)
        printf("e", s, useCLI)
        rc = -1  
    } else {
        s = fmt.Sprintf("CPLD-G2 REVISION: 0x%.08x\n", ucode)
        printf("i", s, useCLI)
    }

    
    data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, taorfpga.D0_FPGA_REV_ID_REG)
    s = fmt.Sprintf("FPGA    REVISION: 0x%.08x\n", data32)
    printf("i", s, useCLI)
    printf("i", "\n", useCLI)
    err = SSD_Display_Info(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err = X86_DDR_Display_Info(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    fmt.Printf("\n")
    err = BIOS_Display_Version(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err = HALON_OS_Display_Version(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    fmt.Printf("\n")
    err = Elba_Check_Pci_Link(taorfpga.ELBA0, useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err = Elba_Check_Pci_Link(taorfpga.ELBA1, useCLI)
    if err != errType.SUCCESS { rc = -1 }
    Elba_Show_Firmware(taorfpga.ELBA0, useCLI)
    Elba_Show_Firmware(taorfpga.ELBA1, useCLI)
    //fmt.Printf("===================================================================================================\n")
    for i:=0; i<taorfpga.MAXSFP; i++ {
        var devName string 
        devName = fmt.Sprintf("SFP_%d", i+1)
        present, _ := taorfpga.SFP_present(uint32(i)) 
        if present == true {
            pn, err1 := sfp.ReadPN(devName)
            if err1 != errType.SUCCESS { rc = -1 }
            pn = strings.TrimSpace(pn)
            sn, err2 := sfp.ReadSerialNumber(devName)
            if err2 != errType.SUCCESS { rc = -1 }
            vendor, err3 := sfp.ReadVendorName(devName)
            if err3 != errType.SUCCESS { rc = -1 }
            vendor = strings.TrimSpace(vendor)
            baudrate, err4 := sfp.GetBitSpeed(devName)
            if err4 != errType.SUCCESS { rc = -1 }
            s := fmt.Sprintf("SFP-%.2d   %-12s  PN: %-12s  SN: %-16s    BITRATE: %.01f Gb/s\n", i+1, vendor, pn, sn, baudrate)
            printf("i", s, useCLI)
        } else {
            s := fmt.Sprintf("SFP-%.2d   NOT PRESENT\n", i+1)
            printf("i", s, useCLI)
        }
    }
    printf("i", "\n", useCLI)
    for i:=0; i<taorfpga.MAXQSFP; i++ {
        var devName string 
        devName = fmt.Sprintf("QSFP_%d", i+1)
        present, _ := taorfpga.QSFP_present(uint32(i)) 
        if present == true {
            pn, err1 := qsfp.ReadPN(devName)
            if err1 != errType.SUCCESS { rc = -1 }
            pn = strings.TrimSpace(pn)
            sn, err2 := qsfp.ReadSerialNumber(devName)
            if err2 != errType.SUCCESS { rc = -1 }
            vendor, err3 := qsfp.ReadVendorName(devName)
            if err3 != errType.SUCCESS { rc = -1 }
            vendor = strings.TrimSpace(vendor)
            baudrate, err4 := qsfp.GetBitSpeed(devName)
            if err4 != errType.SUCCESS { rc = -1 }
            s := fmt.Sprintf("QSFP-%.2d  %-12s  PN: %-12s  SN: %-16s    BITRATE: %.01f Gb/s\n", i+1, vendor, pn, sn, baudrate)
            printf("i", s, useCLI)
        } else {
            s := fmt.Sprintf("QSFP-%.2d  NOT PRESENT\n", i+1)
            printf("i", s, useCLI)
        }
    }
    if rc != 0 {
        return errType.FAIL
    } else {
        return errType.SUCCESS
    }
}


/*    
    I2cInfo {"P0V8AVDD_GB_A",  "TPS549A20",   1,   0x1C,    0x0,    "FPGA_HUB_0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"P0V8AVDD_GB_B",  "TPS549A20",   1,   0x1b,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"P0V8RT_B",       "TPS549A20",   1,   0x1e,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    //ON P0 BOARDS, 0x4C TEMP SENSOR IS LOCATED HERE AT 0x48
    //I2cInfo {"TSENSOR-1",      "LM75",        3,   0x48,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TSENSOR-1",      "TMP451",      3,   0x4C,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TSENSOR-2",      "LM75",        3,   0x49,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TSENSOR-3",      "LM75",        3,   0x4A,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"P0V8RT_A",       "TPS544C20",   1,   0x04,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"P3V3",           "TPS544C20",   1,   0x08,    0x0,    "FPGA_HUB_0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"P3V3S",          "TPS544C20",   1,   0x09,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"TDNT_PDVDD",     "TPS53681",    1,   0x60,    0x0,    "FPGA_HUB_0_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"TDNT_P0V8_AVDD", "TPS53681",    1,   0x60,    0x1,    "FPGA_HUB_0_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_P1V2_VDDQ",     "SN1701022", 1,  0x77,    0x0,    "FPGA_HUB_0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_P1V05_COMBINED","SN1701022", 1,  0x77,    0x1,    "FPGA_HUB_0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_PVCCIN",        "SN1701022", 1,  0x6B,    0x0,    "FPGA_HUB_0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_P1V05_VCCSCSUS","SN1701022", 1,  0x6B,    0x1,    "FPGA_HUB_0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_1",           "DPS-800",    2,   0x58,    0x0,    "FPGA_HUB_1_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_2",           "DPS-800",    2,   0x58,    0x0,    "FPGA_HUB_1_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"FAN_1",           "ADT7462",    2,   0x58,    0x0,    "FPGA_HUB_1_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"FAN_2",           "ADT7462",    2,   0x5C,    0x0,    "FPGA_HUB_1_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"TD3",             "TRIDENT3",   2,   0x44,    0x0,    "FPGA_HUB_1_3",  3,    0},
    I2cInfo {"FRU_EE",          "AT24C02C",   3,   0x50,    0x0,    "FPGA_HUB_2_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FRU_CERT",        "AT24C02C",   3,   0x51,    0x0,    "FPGA_HUB_2_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA0",      "MACHXO3",    3,   0x4A,    0x0,    "FPGA_HUB_2_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA1",      "MACHXO3",    3,   0x4A,    0x0,    "FPGA_HUB_2_3",  3,    I2C_TEST_ENABLE},
*/



type VRmarginFunc func(devName string, pct int)(err int) 

type VoltageMarginTable struct {
    VoltName  string 
    VRmarginFuncPtr VRmarginFunc 
}


func VoltageMargin(percent int)  (err int)  {
    voltTable := []VoltageMarginTable { {"CPU_P1V2_VDDQ", sn1701022.SetVMargin},
                                  {"CPU_P1V05_COMBINED", sn1701022.SetVMargin},
                                  {"CPU_PVCCIN", sn1701022.SetVMargin},
                                  {"CPU_P1V05_VCCSCSUS", sn1701022.SetVMargin},
                                  {"TDNT_PDVDD", tps53681.SetVMargin},
                                  {"TDNT_P0V8_AVDD", tps53681.SetVMargin},
                                  {"P0V8RT_A", tps544c20.SetVMargin},
                                  {"P0V8RT_B", tps549a20.SetVMargin},
                                  //{"P0V8AVDD_GB_A", TPS549A20.SetVMargin},
                                  //{"P0V8AVDD_GB_B", TPS549A20.SetVMargin},
                                  {"P3V3", tps544c20.SetVMargin},
                                  {"P3V3S", tps544c20.SetVMargin},
                                  
                                }


    for _, volt := range(voltTable) {
        hwinfo.EnableHubChannelExclusive(volt.VoltName)
        err = volt.VRmarginFuncPtr(volt.VoltName, percent)
        if err != 0 {
            fmt.Printf("ERROR: Failed to Voltage Margin %s %d percent \n", volt.VoltName, percent) 
        }
    }

    return
}



type VRdispfunc func(devName string)(err int) 

type VoltageTable struct {
    VoltName  string 
    VRdispfuncPtr VRdispfunc 
}


func ShowPower()  (err int)  {
    vrmTitle := []string {"VBOOT", "VOUT", "POUT", "IOUT", "VIN", "PIN", "IIN"}
    voltTable := []VoltageTable { {"CPU_P1V2_VDDQ", sn1701022.DispVoltWattAmp},
                                  {"CPU_P1V05_COMBINED", sn1701022.DispVoltWattAmp},
                                  {"CPU_PVCCIN", sn1701022.DispVoltWattAmp},
                                  {"CPU_P1V05_VCCSCSUS", sn1701022.DispVoltWattAmp},
                                  {"TDNT_PDVDD", tps53681.DispVoltWattAmp},
                                  {"TDNT_P0V8_AVDD", tps53681.DispVoltWattAmp},
                                  {"PSU_1", dps800.DispVoltWattAmp},
                                  {"PSU_2", dps800.DispVoltWattAmp},
                                  {"P0V8RT_A", tps544c20.DispVoltWattAmp},
                                  {"P3V3", tps544c20.DispVoltWattAmp},
                                  {"P3V3S", tps544c20.DispVoltWattAmp},
                                  
                                }

    var outStr string
    outStr = fmt.Sprintf("%-20s", "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    fmt.Println(outStr)


    for _, volt := range(voltTable) {
        hwinfo.EnableHubChannelExclusive(volt.VoltName)
        volt.VRdispfuncPtr(volt.VoltName)
    }

    return
}


type TemperatureFunc func(devName string) (temperatures []float64, err int) 

type TemperatureTable struct {
    TemperatureDevName  string 
    TemperaturefuncPtr  TemperatureFunc 
}


func ShowTemperature ()  (err int)  {
    TemperatureTitle := []string {"T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"}
    TemperatureTable := []TemperatureTable { {"CPU_P1V2_VDDQ", sn1701022.GetTemperature},
                                  {"CPU_P1V05_COMBINED", sn1701022.GetTemperature},
                                  {"CPU_PVCCIN", sn1701022.GetTemperature},
                                  {"CPU_P1V05_VCCSCSUS", sn1701022.GetTemperature},
                                  {"TDNT_PDVDD", tps53681.GetTemperature},
                                  {"TDNT_P0V8_AVDD", tps53681.GetTemperature},
                                  {"TSENSOR-1", tmp451.GetTemperature},
                                  {"TSENSOR-2", lm75a.GetTemperature},
                                  {"TSENSOR-3", lm75a.GetTemperature},
                                  {"FAN_1", adt7462.GetTemperature},
                                  {"FAN_2", adt7462.GetTemperature},
                                  {"PSU_1", dps800.GetTemperature},
                                  {"PSU_2", dps800.GetTemperature},
                                  {"TSENSOR-ASIC0", taorfpga.GetTemperature},
                                  {"TSENSOR-ASIC1", taorfpga.GetTemperature},
                                  {"TSENSOR-CPU", XeonD.GetTemperature},
                                  {"TSENSOR-BCM", td3.GetTemperature},
                                  {"TSENSOR-BCM", td3.GetPeakTemperature},
                                }

    var TD3count int = 0
    var outStr string
    var i int
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"


    outStr = fmt.Sprintf("%-20s", "NAME")
    for _, title := range(TemperatureTitle) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    fmt.Printf("%s\n", outStr)



    for _, temp := range(TemperatureTable) {
        rdTemp := []float64{}
        hwinfo.EnableHubChannelExclusive(temp.TemperatureDevName)
        rdTemp, err = temp.TemperaturefuncPtr(temp.TemperatureDevName)
        if err != errType.SUCCESS {
            fmt.Printf("ERROR: Reading temperature from dev %s failed\n", temp.TemperatureDevName) 
            return;
        }
        if temp.TemperatureDevName == "TSENSOR-BCM" {
            TD3count++
        }
        if TD3count == 2 {
            outStr = fmt.Sprintf(fmtNameStr, temp.TemperatureDevName+"PEAK")
        } else {
            outStr = fmt.Sprintf(fmtNameStr, temp.TemperatureDevName)
        
        }

        for i=0; i<len(rdTemp);i++ {
            outStrTemp := fmt.Sprintf("%.03f", rdTemp[i])
            outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        }      
        for  ; i<len(TemperatureTitle);i++ {  
            outStr = outStr + fmt.Sprintf(fmtStr, "-")
        }
        fmt.Printf("%s\n", outStr)
    }
    

    return
}







/*********************************************************************************************************** 
*  
* LINE RATE: 
*     CURRENTLY WITH DSC MANAGER IT ALLOCATES VLAN[36:10] TO LAG521/ELBA0, AND VLAN[56:37] TO LAG521/ELBA1
* 
*     In This test there are 4 vlan loops. 
*     1) ELBA0 on ports 0-15 
*     2) ELBA1 on ports 16-31 
*     3) TD3 25G ports 32-47 
*     4) TD3 100G ports 48-53 
*  
*     The VLAN setup is a bit messy since the vlans are not contiguous due to how the VLANS are 
*     allocated in DSC MANAGER. 
*  
* FORWARDING SNAKE TEST: 
*     FORWARD TO THE NEXT PORT. SPLIT INTO TWO PORT SEGMENTS.
*     1) VLAN 10-36 GO TO ELBA0 (LAG521)
*     2) VLAN 37-64 GO TO ELBA1 (LAG522)
*  
*  
*  
***********************************************************************************************************/ 
func System_Snake_Test(test_type uint32, elba_port_mask uint32, duration uint32, loopback_level string, pkt_size uint64, pkt_pattern uint64, dump_temperature uint32) (err int) {
    var rc int = errType.SUCCESS
    var errGo error
    var data32 uint32
    var addr uint64
    var SFPnumber, QSFPnumber, bitcompare uint32
    var port25G_s string
    var port100G_s string
    var tmp_s string
    var command string
    var output string
    var loopbackPhy uint32 = 0
    var ElbaVLANcreatScript = "/fs/nos/home_diag/dssman/run.sh"

    var VlanStart int = 10
    var vlanMap = []int{10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85}

    if test_type == td3.SNAKE_TEST_LINE_RATE {
        cli.Printf("i", "Starting Snake Test.  Line Rate.   Elba Link Mask=%x,  Duration=%d", elba_port_mask, duration)
    } else if test_type == td3.SNAKE_TEST_NEXT_PORT_FORWARDING  {
        cli.Printf("i", "Starting Snake Test.. Forward to the Next Port.  Elba Link Mask=%x,  Duration=%d", elba_port_mask, duration)
    } else if test_type == td3.SNAKE_TEST_ENVIRONMENT  {
        cli.Printf("i", "Starting Snake Test for Environmental Testing. Line Rate/512 Byte Packets.  Elba Link Mask=%x,  Duration=%d", elba_port_mask, duration)
    } else {
        cli.Printf("e", "ERROR: INVALID TEST TYPE PASSED TO SNAKE TEST.  TEST TYPE PASSSED=%d", test_type)
        err = errType.FAIL
        return
    }

    if loopback_level == "phy" {
        loopbackPhy = 1
        cli.Printf("i", "Phy Loopback Selected\n")
    } else {
        cli.Printf("i", "External Loopback Selected\n")
        /* Check SFP's are present */
        cli.Printf("i", "Checking for SFP Presence\n")
        addr = taorfpga.D0_FP_SFP_STAT_3_0_REG;
        for SFPnumber=0;SFPnumber<taorfpga.MAXSFP;SFPnumber++ {
            addr = addr + ((uint64(SFPnumber)/4) * 4)
            bitcompare = (1 << ((SFPnumber%4)*8))
            data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
            if errGo != nil {
                err = errType.FAIL
                return
            }

            //1 = NOT PRESENT
            if (data32 & bitcompare) == bitcompare {
                cli.Printf("e", "SFP-%d is not detecting presence.  Check SFP-%d is present\n", SFPnumber+1, SFPnumber+1)
                err = errType.FAIL
                return
            } 
        }


        /* Check QSFP's are present */
        cli.Printf("i", "Checking for QSFP Presence\n")
        addr = taorfpga.D0_FP_QSFP_STAT_51_48_REG;
        for QSFPnumber=0;QSFPnumber<taorfpga.MAXSFP;QSFPnumber++ {
            addr = addr + ((uint64(QSFPnumber)/4) * 4)
            bitcompare = (1 << ((QSFPnumber%4)*8))
            data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
            if errGo != nil {
                err = errType.FAIL
                return
            }

            //1 = NOT PRESENT
            if (data32 & bitcompare) == bitcompare {
                cli.Printf("e", "QSFP-%d is not detecting presence.  Check QSFP-%d is present\n", QSFPnumber+1, QSFPnumber+1)
                err = errType.FAIL
                return
            } 
        }

        /* Enable SFP's */
        cli.Printf("i", "Enabling SFP's\n")
        addr = taorfpga.D0_FP_SFP_CTRL_3_0_REG;
        for i:=0;i<taorfpga.MAXSFP;i++ {
            addr = addr + ((uint64(i)/4) * 4)
            errGo = taorfpga.TaorWriteU32( taorfpga.DEVREGION0, addr, 0x06060606)
            if errGo != nil {
                err = errType.FAIL
                return
            }
        }

        /* Enable QSFP's */
        cli.Printf("i", "Enabling QSFP's\n")
        addr = taorfpga.D0_FP_QSFP_CTRL_51_48_REG;
        for i:=0;i<taorfpga.MAXQSFP;i++ {
            addr = addr + ((uint64(i)/4) * 4)
            data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
            data32 = (data32 & 0xFEFEFEFE)  //mask out reset bit
            taorfpga.TaorWriteU32( taorfpga.DEVREGION0, addr, data32)
        }
    }


    //Temperature Check.. return if failed.  Had some issue's with heatsinks.. return if temp to high 
    if err = td3.CheckTemperatures("TD3", td3.TD3_MAX_TEMP); err != errType.SUCCESS {
        err = errType.FAIL
        return
    }


    for i:=0; i<td3.TAOR_EXTERNAL_25G_PORTS; i++ {
        if i == (td3.TAOR_EXTERNAL_25G_PORTS - 1) {
            tmp_s = fmt.Sprintf("%s", td3.TaorPortMap[i].Name)
        } else {
            tmp_s = fmt.Sprintf("%s,", td3.TaorPortMap[i].Name)
        }
        port25G_s = port25G_s + tmp_s
    }
    for i:=td3.TAOR_EXTERNAL_25G_PORTS; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {
        if i == (td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS - 1) {
            tmp_s = fmt.Sprintf("%s", td3.TaorPortMap[i].Name)
        } else {
            tmp_s = fmt.Sprintf("%s,", td3.TaorPortMap[i].Name)
        }
        port100G_s = port100G_s + tmp_s
    }
    
    if loopbackPhy > 0 {
        cli.Printf("i", "Setting Phy Loopback on 25G Ports\n")
        command = "port " + port25G_s +" lb=phy"
        output, err = td3.ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }

        //No return output to check on this command
        cli.Printf("i", "Setting Phy Loopback on 100G Ports\n")
        command = "port " + port100G_s +" lb=phy"
        output, err = td3.ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
    }

    //quick sanity check to make sure the file exists
    currDir, _ := os.Getwd()
    os.Chdir("/fs/nos/home_diag/dssman")
    
    cli.Printf("i", "Executing dssman setup\n")
    exists, _ := taorfpga.Path_exists(ElbaVLANcreatScript)
    if exists == false {
        cli.Printf("e", "Script is missing --> \n", ElbaVLANcreatScript)
        err = errType.FAIL
        return
    }
    {
        execOutput, errGo := exec.Command("/bin/sh", ElbaVLANcreatScript).Output()
        if errGo != nil {
            cli.Println("e",string(execOutput))
            cli.Println("e", errGo)
            err = errType.FAIL
            //return
        }
        cli.Println("i", string(execOutput))
    }
    os.Chdir(currDir)
    
    //set pvlan
    for i:=0; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {
        //pvlan set xe8 10
        if test_type == td3.SNAKE_TEST_NEXT_PORT_FORWARDING  {
            command = fmt.Sprintf("pvlan set %s %d", td3.TaorPortMap[i].Name, (VlanStart + i))
        } else {
            command = fmt.Sprintf("pvlan set %s %d", td3.TaorPortMap[i].Name, vlanMap[i])
        }
        cli.Printf("i", command)
        output, err = td3.ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
        cli.Printf("i", "%s\n", command)
    }

    /*
      VLAN SETUP
      FORWARDING TEST:
        set vlans 10-63 for the elba front panel ports
        vlan 10-36 will go to lag521 (Elba0)
        vlan 37-63 will go to lag522 (Elba1)
        All front panel ingress packets get forwarded to an Elba
      LINE_RATE_TEST:
        vlan 10-25 will go to lag521 (Elba0)  FP Port 0-15
        vlan 37-52 will go to lag522 (Elba1)  FP port 16 - 31
        vlan 64-79 to front panel ports 32-47 (ones based, bypasses ELBA)
        vlan 80-85 to 100G ports 48-53 (bypasses ELBA)
      
    */
    for i:=0; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {

        if test_type == td3.SNAKE_TEST_NEXT_PORT_FORWARDING  {
            //vlan add 10 pbm=xe8,xe9 ubm=xe8,xe9
            if i == (((td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS)/2)-1) {  //port 27 needs to vlan with port 0 to create the vlan snake for lag521 (elba0)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), td3.TaorPortMap[i].Name, td3.TaorPortMap[0].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[0].Name )
            } else if i == ((td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS)-1) { //Last entry needs to map back to port 28 to creat the vlan snake for lag522 (elba1)
                entry := ((td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS)/2)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), td3.TaorPortMap[i].Name, td3.TaorPortMap[entry].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[entry].Name )
            } else {  
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), td3.TaorPortMap[i].Name, td3.TaorPortMap[i+1].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[i+1].Name )
            }
        } else {
        //vlan add 10 pbm=xe8,xe9 ubm=xe8,xe9
            if i == 15 {  //port 15 needs to vlan with port 0 to create the vlan snake for lag521 (elba0)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], td3.TaorPortMap[i].Name, td3.TaorPortMap[0].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[0].Name )
            } else if i == 31 { //31 back to 16 for lag522 (elba1)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], td3.TaorPortMap[i].Name, td3.TaorPortMap[16].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[16].Name )
            } else if i == 47 { //47 back to 32
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], td3.TaorPortMap[i].Name, td3.TaorPortMap[32].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[32].Name )
            } else if i == 53 { //53 back to 48
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], td3.TaorPortMap[i].Name, td3.TaorPortMap[48].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[48].Name )
            } else {  
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], td3.TaorPortMap[i].Name, td3.TaorPortMap[i+1].Name, td3.TaorPortMap[i].Name, td3.TaorPortMap[i+1].Name )
            }
        }
        cli.Printf("i", "%s\n", command)
        output, err = td3.ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
    }

    if test_type == td3.SNAKE_TEST_LINE_RATE || test_type == td3.SNAKE_TEST_ENVIRONMENT{
        //VLAN SETUP
        //NEED TO REMOVE ELBA PORTS FROM FRONT PANEL PORTS 32-53.   THESE PORTS WILL NOT FORWARD TO ELBA, AND WILL VLAN SNAKE JUST ON TD3
        //vlan remove 64 pbm=ce1-ce4,ce9-ce10,ce12-ce13
        for i:=32; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {
            command = fmt.Sprintf("vlan remove %d pbm=ce1-ce4,ce9-ce10,ce12-ce13", vlanMap[i])
            cli.Printf("i", "%s\n", command)
            output, err = td3.ExecBCMshellCMD(command)
            if err != errType.SUCCESS {
                return
            }
        }
    }


    err = td3.Set_Pre_Main_Post()
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling Vlan Translate\n")
    command = "vlan translate on"
    output, err = td3.ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling Forwarding on 25G ports\n")
    command = "stg stp 1 " + port25G_s +" forward"
    output, err = td3.ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling Forwarding on 100G ports\n")
    command = "stg stp 1 " + port100G_s +" forward"
    output, err = td3.ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=true"
    output, err = td3.ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=true"
    output, err = td3.ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //Check Link
    cli.Printf("i", "Checking Link\n")
    time.Sleep(time.Duration(1) * time.Second)
    ps_output, err := td3.ExecBCMshellCMD("ps")
    if err != errType.SUCCESS {
        return
    }
    for i:=0; i<(td3.TAOR_EXTERNAL_25G_PORTS + td3.TAOR_EXTERNAL_100G_PORTS + td3.TAOR_INTERNAL_PORTS); i++ {
        if i >= td3.TAOR_INTERNAL_PORT_START {
            if (elba_port_mask & (1<<uint32(i - td3.TAOR_INTERNAL_PORT_START))) == 0 {
                continue;
            }
        }
        link_rc := td3.LinkCheck(td3.TaorPortMap[i].Name, ps_output) 
        if link_rc == errType.LINK_UP {
            cli.Printf("i", "Port-%.02d  %4s: LINK UP\n", i+1, td3.TaorPortMap[i].Name)
        } else if link_rc == errType.LINK_DOWN {
            cli.Printf("e", "Port-%.02d  %4s: LINK DOWN\n", i+1, td3.TaorPortMap[i].Name)
            rc = -1
        } else if link_rc == errType.LINK_DISABLED {
            cli.Printf("e", "Port-%.02d  %4s: LINK DISABLED\n", i+1, td3.TaorPortMap[i].Name)
            rc = -1
        } else {
            cli.Printf("e", "Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, td3.TaorPortMap[i].Name)
            rc = -1
        }
    }
    fmt.Printf("\n")
    if rc != 0 {
        err = errType.FAIL
        return
    }

    //Clear stat counters
    cli.Printf("i", "clear c\n")
    command = "clear c\n"
    output, err = td3.ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    time.Sleep(time.Duration(5) * time.Second)

    //Inject Packets
    {
        var internal_port uint32 = 0
        for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
            fileData := []byte{}
            WRdata := []byte{}
            filename := fmt.Sprintf("/fs/nos/home_diag/dssman/packet.hex.%s", td3.TaorPortMap[i].Name)
            f, errGo := os.Open(filename)
            if errGo != nil {
                fmt.Printf("[ERROR] Failed to open filename=%s.   ERR=%s\n", filename, errGo)
                err = errType.FAIL
                return
            }
            scanner := bufio.NewScanner(f)
            scanner.Split(bufio.ScanBytes)

            // Use For-loop.
            for scanner.Scan() {
                b := scanner.Bytes()
                fileData = append(fileData, b[0])
            }
            f.Close()
            //fmt.Printf(" Length File Data = %d\n", len(fileData))

            filename = fmt.Sprintf("/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[i].Name)
            outF, errGo1 := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
            if errGo1 != nil {
                fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, errGo1)
                return
            }
            if (int(pkt_size) > 0) && (int(pkt_pattern) > 0) {
                WRdata = append(fileData[0:96])
                outF.WriteString(string(WRdata[:]))
                for z:=(96/2);z<int(pkt_size);z+=4 {
                    fmt.Fprintf(outF, "%02x", uint8((pkt_pattern & 0xFF000000) >> 24))
                    fmt.Fprintf(outF, "%02x", uint8((pkt_pattern & 0xFF0000) >> 16))
                    fmt.Fprintf(outF, "%02x", uint8((pkt_pattern & 0xFF00) >> 8))
                    fmt.Fprintf(outF, "%02x", uint8(pkt_pattern & 0xFF))
                }            
                outF.Close()
            } else {
                outF.WriteString(string(fileData[:]))
                outF.Close()
            }
        }

        if test_type == td3.SNAKE_TEST_LINE_RATE {
            for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
                if (elba_port_mask & (1<<internal_port)) == 0 {
                    internal_port++
                    continue;
                }
                internal_port++

                if td3.TaorPortMap[i].ElbaNumber == 0 {
                    command = fmt.Sprintf("tx 100 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[0].Name, td3.TaorPortMap[i].Name)
                } else {
                    command = fmt.Sprintf("tx 100 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[16].Name, td3.TaorPortMap[i].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = td3.ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(4) * time.Second)
            }
            for i:=0; i<2; i++ {
                if i == 0 {
                    command = fmt.Sprintf("tx 300 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[32].Name, td3.TaorPortMap[55].Name)
                } else {
                    command = fmt.Sprintf("tx 300 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[48].Name, td3.TaorPortMap[55].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = td3.ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(5) * time.Second)
            }
        } else if test_type == td3.SNAKE_TEST_ENVIRONMENT {
            for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
                if (elba_port_mask & (1<<internal_port)) == 0 {
                    internal_port++
                    continue;
                }
                internal_port++

                if td3.TaorPortMap[i].ElbaNumber == 0 {
                    command = fmt.Sprintf("tx 16 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[0].Name, td3.TaorPortMap[i].Name)
                } else {
                    command = fmt.Sprintf("tx 16 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[16].Name, td3.TaorPortMap[i].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = td3.ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(4) * time.Second)
            }
            for i:=0; i<2; i++ {
                if i == 0 {
                    command = fmt.Sprintf("tx 14 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[32].Name, td3.TaorPortMap[55].Name)
                } else {
                    command = fmt.Sprintf("tx 26 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[48].Name, td3.TaorPortMap[55].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = td3.ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(5) * time.Second)
            }

        } else {
            //var internal_port uint32 = 0
            for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
                if (elba_port_mask & (1<<internal_port)) == 0 {
                    //fmt.Printf("[ERROR] Elba Port Mask = 0x%x...  mask=%x\n", elba_port_mask, (1<<internal_port))
                    internal_port++
                    continue;
                }
                internal_port++

                //First half of VLANS go to Elba 0 (lag521).    Elba 1 (lag 522) VLANS need t start on port27 which starts the 2nd half of the vlans   
                if td3.TaorPortMap[i].ElbaNumber == 0 {
                    command = fmt.Sprintf("tx 60 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.%s", td3.TaorPortMap[0].Name, td3.TaorPortMap[i].Name)
                } else {
                    entry := ((td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS)/2)
                    command = fmt.Sprintf("tx 60 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.%s", td3.TaorPortMap[entry].Name, td3.TaorPortMap[i].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = td3.ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(4) * time.Second)
            }
        }
    }


    //CHECK STATS & TEMPERATURE
    {
        t1 := time.Now()
        var ElbaPortminBandwidth uint64 = 11250000000//12000000000
        var Elba0bw, Elba1bw uint64
        var Lag521ExtPortminBandWidth uint64 = 0
        var Lag522ExtPortminBandWidth uint64 = 0
        var rc int = 0
        var printRxBandwidth = 1
        printRxBwTime := time.Now()

        if test_type == td3.SNAKE_TEST_ENVIRONMENT {
            ElbaPortminBandwidth = 3000000000
        }

        for i:=0; i<td3.TAOR_INTERNAL_PORTS; i++ {
            var port uint32 = uint32(i)
            if (elba_port_mask & (1<<port)) ==  (1<<port) {
                if td3.TaorPortMap[(i + td3.TAOR_INTERNAL_PORT_START)].ElbaNumber == 0 {
                    Elba0bw = Elba0bw + ElbaPortminBandwidth
                } else {
                    Elba1bw = Elba1bw + ElbaPortminBandwidth
                }
            }
        }

        
        if test_type == td3.SNAKE_TEST_LINE_RATE  {
            Lag521ExtPortminBandWidth = Elba0bw / (16)
            Lag522ExtPortminBandWidth = Elba1bw / (16)
        } else if test_type == td3.SNAKE_TEST_ENVIRONMENT {
            Lag521ExtPortminBandWidth = Elba0bw / (16)
            Lag522ExtPortminBandWidth = Elba1bw / (16)
        } else {
            Lag521ExtPortminBandWidth = Elba0bw / (td3.TAOR_NUMB_EXT_PORT / 2)
            Lag522ExtPortminBandWidth = Elba1bw / (td3.TAOR_NUMB_EXT_PORT / 2)
        }
        fmt.Printf(" Elba0bw bandwidth = %d\n", Elba0bw)
        fmt.Printf(" Elba1bw bandwidth = %d\n", Elba1bw)
        fmt.Printf(" Lag521 min bandwidth = %d\n", Lag521ExtPortminBandWidth)
        fmt.Printf(" Lag522 min bandwidth = %d\n", Lag522ExtPortminBandWidth)

        for {
            var StatRxBytes string
            var StatFCS string

            // Get rx bytes for all ports and check them below 
            StatRxBytes, err = td3.GetRmonStat_AllPorts("CLMIB_RBYT") 
            if err != errType.SUCCESS {
                return
            }
            // Get FCS error for all ports 
            StatFCS, err = td3.GetRmonStat_AllPorts("CLMIB_RFCS") 
            if err != errType.SUCCESS {
                return
            }

            

            for i:=0; i < td3.TAOR_TOTAL_PORTS; i++ {
                var RxBytes uint64
                var FCSerror uint64
                var MinBandWidth25G uint64  =  2900000000
                var MinBandWidth100G uint64 = 11500000000

                if test_type == td3.SNAKE_TEST_ENVIRONMENT {
                    MinBandWidth25G  =  900000000
                    MinBandWidth100G = 3400000000
                }
                
                RxBytes, err = td3.MacStatRxByteSecond(StatRxBytes, i)
                if err != errType.SUCCESS {
                    return
                }
                if printRxBandwidth == 1 {
                    fmt.Printf("Port-%d %d/s\n", i, RxBytes)
                }

                if test_type == td3.SNAKE_TEST_LINE_RATE || test_type == td3.SNAKE_TEST_ENVIRONMENT {
                    //lag521
                    if (i < 16) &&  (RxBytes < Lag521ExtPortminBandWidth) { 
                        cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , td3.TaorPortMap[i].Name, RxBytes, Lag521ExtPortminBandWidth)
                        rc = errType.FAIL
                    }
                    //lag522
                    if (i >= 16) && (i < 31) {
                        if RxBytes < Lag522ExtPortminBandWidth { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , td3.TaorPortMap[i].Name, RxBytes, Lag522ExtPortminBandWidth)
                            rc = errType.FAIL
                        }
                    }
                    //TD3 25G Snake ports
                    if (i >= 32) && (i < 48) {
                        if RxBytes < MinBandWidth25G { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , td3.TaorPortMap[i].Name, RxBytes, MinBandWidth25G)
                            rc = errType.FAIL
                        }
                    }

                    //TD3 25G Snake ports
                    if (i >= 48) && (i < 54) {
                        if RxBytes < MinBandWidth100G { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , td3.TaorPortMap[i].Name, RxBytes, MinBandWidth100G)
                            rc = errType.FAIL
                        }
                    }
                    //Internal Port going to Elba
                    if i >= td3.TAOR_INTERNAL_PORT_START {
                        var port uint32 = uint32(i - td3.TAOR_INTERNAL_PORT_START)
                        if (elba_port_mask & (1<<port)) > 0 {
                            if RxBytes < ElbaPortminBandwidth { 
                                cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , td3.TaorPortMap[i].Name, RxBytes, ElbaPortminBandwidth)
                                rc = errType.FAIL
                            }
                        }
                    }
                } else {
                    //lag521
                    if (i < (td3.TAOR_NUMB_EXT_PORT/2)) &&  (RxBytes < Lag521ExtPortminBandWidth) { 
                        cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , td3.TaorPortMap[i].Name, RxBytes, Lag521ExtPortminBandWidth)
                        rc = errType.FAIL
                    }
                    //lag522
                    if (i >= (td3.TAOR_NUMB_EXT_PORT/2)) && (i < td3.TAOR_NUMB_EXT_PORT) {
                        if RxBytes < Lag522ExtPortminBandWidth { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , td3.TaorPortMap[i].Name, RxBytes, Lag522ExtPortminBandWidth)
                            rc = errType.FAIL
                        }
                    }
                }
                FCSerror, err = td3.MacStatFCSerror(StatFCS, i)
                if err != errType.SUCCESS {
                    return
                }
                if FCSerror > 0 {
                    cli.Printf("e", "Port-%d (%s) has %d FCS Errors\n", i , td3.TaorPortMap[i].Name, FCSerror)
                    rc = errType.FAIL
                }
            }
            printRxBandwidth = 0

            //Temperature Check
            if err = td3.CheckTemperatures("TD3", td3.TD3_MAX_TEMP); err != errType.SUCCESS {
                rc = errType.FAIL
            }

            if rc == errType.FAIL {
                fmt.Printf(" ERR BREAK\n")
                err = errType.FAIL
                break
            }
            {
                var highTemp float64 = 0
                current_temperatures, _ := td3.GetTemperature("TD3")
                for i:=0;i<len(current_temperatures);i++ {
                    if current_temperatures[i] > highTemp { highTemp = current_temperatures[i] }
                }
                t2 := time.Now()
                diff := t2.Sub(t1)
                fmt.Println(" Elapsed Time=",diff," Duration=",duration," High Temp=", highTemp )
                if uint32(diff.Seconds()) > duration {
                    fmt.Printf(" DUATION BREAK\n")
                    break
                }
                diff = t2.Sub(printRxBwTime)
                if uint32(diff.Seconds()) > 10 {
                    printRxBandwidth = 1
                    printRxBwTime = time.Now()
                    if dump_temperature > 0 {
                        ShowTemperature()
                    }
                }
            }

        }
    }

    //Check Elba for memory correctable ecc errors
    if rc = ElbaCheckECC(0, 1, 0, 0); rc != errType.SUCCESS {
        err = errType.FAIL
    }
    if rc = ElbaCheckECC(1, 1, 0, 0); rc != errType.SUCCESS {
        err = errType.FAIL
    } 
    


    if test_type == td3.SNAKE_TEST_LINE_RATE || test_type == td3.SNAKE_TEST_ENVIRONMENT{
        command = "port " + td3.TaorPortMap[0].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[16].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[32].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[48].Name +" enable=false"
        td3.ExecBCMshellCMD(command)
    } else {
        command = "port " + td3.TaorPortMap[0].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[((td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS)/2)].Name +" enable=false"
        td3.ExecBCMshellCMD(command)
    }

    //No return output to check on this command
    cli.Printf("i", "Disabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=false"
    td3.ExecBCMshellCMD(command)

    //No return output to check on this command
    cli.Printf("i", "Disabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=false"
    td3.ExecBCMshellCMD(command)

    fmt.Printf("\n")
    td3.DumpRxTxCounters()
    fmt.Printf("\n")

    /* For compile error that var is not used */
    if td3.TaorPortMap[0].ElbaNumber > 100000 {
            fmt.Printf("%s\n", output)
    }
    
    if err == errType.SUCCESS && rc == errType.SUCCESS {
        cli.Printf("i", "Snake Test PASSED\n\n")
    } else {
        cli.Printf("e", "Snake Test FAILED\n\n")
    }

    return


}
