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
    "fmt"
    "regexp"
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
    "os/exec"

    "device/bcm/td3"
    "device/cpu/XeonD"
    "device/fpga/taorfpga"
    "device/powermodule/sn1701022"
    "device/powermodule/tps544c20"
    "device/powermodule/tps53681"
    "device/psu/dps800" 
    "device/fanctrl/adt7462"
    "device/tempsensor/tmp451"
    "device/tempsensor/lm75a"
    
    /*
    
    "device/powermodule/tps549a20"
    
    */ 
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
        cli.Println(string(execOutput))
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


/********************************************************************************* 
*
* Check if network to Elba is up 
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
        dcli.Printf("i","[DEBUG] - Elba-%d Ping Test\n", i)
        err = ElbaPing(i) 
        if err != errType.SUCCESS {
            elbafailmask |= (1<<i)
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
        dcli.Printf("i", "[DEBUG] - Elba-%d Copying over stressapptest_arm\n", i)
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
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

    dcli.Printf("i","[DEBUG] - Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /data;./stressapptest_arm -s %d -M 1024 -m 12 -l stressapptest_arm.log\n", time)
    //errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
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


    //Start Test
    for i=forStart; i < forEnd; i++ {
        dcli.Printf("i", "[DEBUG] - Elba-%d Starting Test\n", i)
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        if  i == ELBA0 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba0_via_console.sh"
        } else if i == ELBA1 {
            cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba1_via_console.sh"
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("i", "Cmd %s failed! %v", cmdStr, errGo)
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
        dcli.Printf("i", "[DEBUG] - Elba-%d Get Results\n", i)
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
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
            return
        } else {
            dcli.Printf("i", "[DEBUG] Elba-%d passed stressapptest\n", i)
        }
    }

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
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
            //fmt.Printf(" ETH DEV FOUND..  %s\n", ethdev)
            netns = true
            break
        }
    }
    if netns == false {
        fmt.Printf("[ERROR] ELBA-%d Firmware List.  Netns device ntb not found, cannot query firmware\n", elba)
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



type VRfunc func(devName string)(err int) 

type VoltageTable struct {
    VoltName  string 
    VRfuncPtr VRfunc 
}


func ShowPower()  (err int)  {
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN"}
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
        volt.VRfuncPtr(volt.VoltName)
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
                                  {"TSENSOR-TD3", td3.GetTemperature},
                                  {"TSENSOR-TD3", td3.GetPeakTemperature},
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
    fmt.Println(outStr)



    for _, temp := range(TemperatureTable) {
        rdTemp := []float64{}
        hwinfo.EnableHubChannelExclusive(temp.TemperatureDevName)
        rdTemp, err = temp.TemperaturefuncPtr(temp.TemperatureDevName)
        if err != errType.SUCCESS {
            fmt.Printf("ERROR: Reading temperature from dev %s failed\n", temp.TemperatureDevName) 
            return;
        }
        if temp.TemperatureDevName == "TSENSOR-TD3" {
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
        fmt.Println(outStr)
    }
    

    return
}

