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
    //"bufio"
    //"os"
    //"strconv"
    //"time"
    //"syscall"
    //"unsafe"
    //"errors"

    "fmt"
    "regexp"
    "strings"
    "common/cli"
    "common/dcli"
    "common/misc"
    "common/errType"
    //"device/fanctrl/adt7462"
    "device/cpld/nicCpldCommon"
    "device/fpga/taorfpga"
    "encoding/json"
    "hardware/i2cinfo"
    "hardware/hwdev"
    "os/exec"
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
    100 : 28800,
    75 : 18500,
    50 : 10400,
    40 : 7300,
    25 : 2100, 
}

var rpm_front_MAP = map[int]int {
    100 : 25450,
    75 : 16500,
    50 : 9250,
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


    if running, _ := Process_Is_Running(process); running == true {
        Process_Kill(process)
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

func Process_Is_Running(process string) (running bool, err int) {
    out, errGo := exec.Command("ps", "-A").Output()
    if errGo != nil {
        fmt.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
    }

    s := strings.Split(string(out), "\n")
    for _, temp := range s {
        if strings.Contains(temp, process)==true {
            running = true
        } else {
            running = false
        }
    }
    return
}

func Process_Kill(process string) (err int) {
    _ , errGo := exec.Command("killall", "-9", process).Output()
    if errGo != nil {
        fmt.Println("[ERROR]", errGo)
        err = errType.FAIL
        return
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
        dcli.Printf("e", "%s DEVICE ID IS WRONG:  EXPECT 0x.02x.   Read 0x%.02x", devName, nicCpldCommon.ID_TAORMINA_ELBA, rdData[0] )
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
        dcli.Printf("e", "%s Register-0x%.02x  Wrote 0x.02x.   Read 0x%.02x", devName, i2cWrData[0][0], i2cWrData[0][1],  rdData[0] )
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
        dcli.Printf("e", "%s Register-0x%.02x  Wrote 0x.02x.   Read 0x%.02x", devName, i2cWrData[1][0], i2cWrData[1][1],  rdData[0] )
        err = errType.FAIL
        return
    }

    return
}
