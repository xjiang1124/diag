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
    "device/fanctrl/adt7462"
    "device/fpga/taorfpga"
    "device/powermodule/sn1701022"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544c20"
    "device/powermodule/tps53681"
    "device/powermodule/tps53659"
    "device/psu/dps800" 
    "device/tempsensor/tmp451"
    "device/tempsensor/lm75a"

    "device/sfp"
    "device/qsfp"

    "math/rand"

)


type ElbaMIBstats struct {
    FRAMES_RX_OK           uint64 
    FRAMES_RX_ALL          uint64 
    FRAMES_RX_BAD_FCS      uint64
    FRAMES_RX_BAD_ALL      uint64 
    OCTETS_RX_OK           uint64
    OCTETS_RX_ALL          uint64
    FRAMES_RX_UNICAST      uint64
    FRAMES_RX_MULTICAST    uint64
    FRAMES_RX_BROADCAST    uint64
    FRAMES_RX_PAUSE        uint64   //10
    FRAMES_RX_BAD_LENGTH   uint64
    FRAMES_RX_UNDERSIZED   uint64
    FRAMES_RX_OVERSIZED    uint64
    FRAMES_RX_FRAGMENTS    uint64
    FRAMES_RX_JABBER       uint64
    FRAMES_RX_PRIPAUSE     uint64
    FRAMES_RX_STOMPED_CRC  uint64
    FRAMES_RX_TOO_LONG     uint64
    FRAMES_RX_VLAN_GOOD    uint64
    FRAMES_RX_DROPPED      uint64  //20
    FRAMES_RX_LESS_THAN_64B uint64
    FRAMES_RX_64B          uint64
    FRAMES_RX_65B_127B     uint64
    FRAMES_RX_128B_255B    uint64
    FRAMES_RX_256B_511B    uint64
    FRAMES_RX_512B_1023B   uint64
    FRAMES_RX_1024B_1518B  uint64
    FRAMES_RX_1519B_2047B  uint64
    FRAMES_RX_2048B_4095B  uint64
    FRAMES_RX_4096B_8191B  uint64  //30
    FRAMES_RX_8192B_9215B  uint64
    FRAMES_RX_OTHER        uint64
    FRAMES_TX_OK           uint64
    FRAMES_TX_ALL          uint64
    FRAMES_TX_BAD          uint64
    OCTETS_TX_OK           uint64
    OCTETS_TX_TOTAL        uint64
    FRAMES_TX_UNICAST      uint64
    FRAMES_TX_MULTICAST    uint64
    FRAMES_TX_BROADCAST    uint64  //40
    FRAMES_TX_PAUSE        uint64
    FRAMES_TX_PRIPAUSE     uint64
    FRAMES_TX_VLAN         uint64
    FRAMES_TX_LESS_THAN_64B uint64
    FRAMES_TX_64B          uint64
    FRAMES_TX_65B_127B     uint64
    FRAMES_TX_128B_255B    uint64
    FRAMES_TX_256B_511B    uint64
    FRAMES_TX_512B_1023B   uint64
    FRAMES_TX_1024B_1518B  uint64  //50
    FRAMES_TX_1519B_2047B  uint64
    FRAMES_TX_2048B_4095B  uint64
    FRAMES_TX_4096B_8191B  uint64
    FRAMES_TX_8192B_9215B  uint64
    FRAMES_TX_OTHER        uint64
    FRAMES_TX_PRI_0        uint64
    FRAMES_TX_PRI_1        uint64
    FRAMES_TX_PRI_2        uint64
    FRAMES_TX_PRI_3        uint64
    FRAMES_TX_PRI_4        uint64  //60
    FRAMES_TX_PRI_5        uint64
    FRAMES_TX_PRI_6        uint64
    FRAMES_TX_PRI_7        uint64
    FRAMES_RX_PRI_0        uint64
    FRAMES_RX_PRI_1        uint64
    FRAMES_RX_PRI_2        uint64
    FRAMES_RX_PRI_3        uint64
    FRAMES_RX_PRI_4        uint64
    FRAMES_RX_PRI_5        uint64
    FRAMES_RX_PRI_6        uint64  //70
    FRAMES_RX_PRI_7        uint64
    TX_PRIPAUSE_0_COUNT    uint64
    TX_PRIPAUSE_1_COUNT    uint64
    TX_PRIPAUSE_2_COUNT    uint64
    TX_PRIPAUSE_3_COUNT    uint64
    TX_PRIPAUSE_4_COUNT    uint64
    TX_PRIPAUSE_5_COUNT    uint64
    TX_PRIPAUSE_6_COUNT    uint64
    TX_PRIPAUSE_7_COUNT    uint64
    RX_PRIPAUSE_0_COUNT    uint64  //80
    RX_PRIPAUSE_1_COUNT    uint64
    RX_PRIPAUSE_2_COUNT    uint64
    RX_PRIPAUSE_3_COUNT    uint64
    RX_PRIPAUSE_4_COUNT    uint64
    RX_PRIPAUSE_5_COUNT    uint64
    RX_PRIPAUSE_6_COUNT    uint64
    RX_PRIPAUSE_7_COUNT    uint64
    RX_PAUSE_1US_COUNT      uint64
    FRAMES_TX_TRUNCATED     uint64
    RSFEC_CORRECTABLE_WORD  uint64 //90
    RSFEC_CH_SYMBOL_ERR_CNT uint64
}


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

    GB_LOOPBACK_LINE_SIDE = 0
    GB_LOOPBACK_HOST_SIDE = 1

    GB_DIGITAL_PMD_LOOPBACK = 1
    GB_REMOTE_PMD_LOOPBACK = 2

    GB_LOOPBACK_DISABLE = 0
    GB_LOOPBACK_ENABLE = 1

    SNAKE_GB_NO_LPBK = 0
    SNAKE_GB_LINE_LPBK = 1
    SNAKE_GB_HOST_LPBK = 2

    SNAKE_RETIMER_NO_LPBK = 0
    SNAKE_RETIMER_LINE_LPBK = 1
    SNAKE_RETIMER_HOST_LPBK = 2

    PRBS_GB_LPBK = 1
    PRBS_RETIMER_LPBK = 2
)

const ELBA_MAX_TEMP = 80

var gbLoopbackLevel_map = map[int]string{
    GB_LOOPBACK_LINE_SIDE : "Line",
    GB_LOOPBACK_HOST_SIDE : "Host",
}

var gbLoopbackMode_map = map[int]string{
    GB_DIGITAL_PMD_LOOPBACK : "Digital",
    GB_REMOTE_PMD_LOOPBACK : "Remote",
}



var rpm_rear_MAP = map[int]int {
    100 : 29000,
    90 : 24500, 
    80 : 21500,
    75 : 19800,
    70 : 18000,
    60 : 14900,
    50 : 11300,
    40 : 7300,
    25 : 2100, 
}

var rpm_front_MAP = map[int]int {
    100 : 25400,
    90 : 21500,
    80 : 18750,
    75 : 17200,
    70 : 15800,
    60 : 12900,
    50 : 10000,
    40 : 6500,
    25 : 1800, 
}

type fanDevMap struct{
    dev           string
    fanNum        uint64
    silkScreenFan uint32
}

var fan_MAP = map[int]fanDevMap {
    0 : { dev:"FAN_1" , fanNum:0, silkScreenFan:6 } ,  //fan 1 from presence
    1 : { dev:"FAN_1" , fanNum:1, silkScreenFan:5 } ,  //fan 2 from presence
    2 : { dev:"FAN_1" , fanNum:2, silkScreenFan:4 } ,  //fan 3 from presence
    3 : { dev:"FAN_2" , fanNum:0, silkScreenFan:3 } ,  //fan 4 from presence
    4 : { dev:"FAN_2" , fanNum:1, silkScreenFan:2 } ,  //fan 5 from presence
    5 : { dev:"FAN_2" , fanNum:2, silkScreenFan:1 } ,  //fan 6 from presence
}



func Fan_FIX_Stuck_Fan(fanNumber int, fanPWM int) (err int) {
    var zeroPWM int = 0x00
    var fanStopped [6]int
    var rpm [2]uint64 
    var pct [MAXFANMODULES]byte 
    var changePWMstring string

    cli.Printf("i", "Trying to unstick fan module %d.  PWM setting %d\n", fanNumber, fanPWM)

    //disable all fans
    for j:=0; j<MAXFANMODULES; j++ {
        err = hwdev.FanSpeedSet(fan_MAP[j].dev, zeroPWM, (1<<fan_MAP[j].fanNum))
        if err != errType.SUCCESS {
           cli.Printf("e", "FanSpeedSet Failed on %s, fan-%d  (Silkscreen Number-%d)  \n", fan_MAP[j].dev, fan_MAP[j].fanNum, fan_MAP[fanNumber].silkScreenFan)
           return
        }
    }

    for j:=0; j<MAXFANMODULES; j++ {
        for i:=0; i<40; i++ {
            if fanStopped[j] > 0 {
                continue
            }

            for fanInModule:=0; fanInModule < FANPERMODULE; fanInModule++ {
                rpm[fanInModule], _, err =  hwdev.FanSpeedGet(fan_MAP[j].dev, uint64((int(fan_MAP[j].fanNum) * FANPERMODULE) + fanInModule) ) 
                if err != errType.SUCCESS {
                    cli.Printf("e", "FanSpeedGet Failed on %s, fan-%d   (Silkscreen Number-%d)  \n", fan_MAP[j].dev, fan_MAP[j].fanNum, fan_MAP[fanNumber].silkScreenFan)
                    return
                } 
                
            }
            cli.Printf("i", "Waiting for fan to stop running.  Fan-%d RPM %d/%d\n", j, rpm[0], rpm[1])
            if rpm[0] < 200 && rpm[1] < 200 {
                fanStopped[j] = 1
                continue
            }
            time.Sleep(time.Duration(500) * time.Millisecond) //give fan time to change rpm
        }
    }
    for j:=0; j<MAXFANMODULES; j++ {
        if fanStopped[j] > 0 {
            cli.Printf("i", "Fan-%d Stopped RPM %d/%d\n", j, rpm[0], rpm[1])
        }
    }

    // Set the fans to 60% PWM to start them back up
    for j:=0; j<MAXFANMODULES; j++ {
        pct[j] = 60
        cli.Printf("i", "Fan-%d Setting PWM to %d percent\n", j, pct[j])
        err = hwdev.FanSpeedSet(fan_MAP[j].dev, 60, (1<<fan_MAP[j].fanNum))
        if err != errType.SUCCESS {
           cli.Printf("e", "FanSpeedSet Failed on %s, fan-%d  \n", fan_MAP[j].dev, fan_MAP[j].fanNum)
        }
    }

    misc.SleepInSec(10) //give fan time to change rpm

    // Ramp up PWM if needed. Icnremenets of 5% at a time
    for steps:=0;steps<20;steps++ {
       for j:=0; j<MAXFANMODULES; j++ {
           if pct[j] > byte(fanPWM) {  //fan speed going down, just break
               continue
           }
           if (pct[j] + 5) < byte(fanPWM) {
               pct[j] = pct[j]+5
               s := fmt.Sprintf("%d ", pct[j])
               changePWMstring = changePWMstring + s
               hwdev.FanSpeedSet(fan_MAP[j].dev, int(pct[j]), (1<<fan_MAP[j].fanNum))
           } else {
               continue
           }
       }
    }
    if len(changePWMstring) > 0 {
       cli.Printf("i","%s\n", changePWMstring)
    }

    // Set final PWM for test loop
    for j:=0; j<MAXFANMODULES; j++ {
        cli.Printf("i", "Fan-%d Setting Final PWM to %d percent\n", j, fanPWM)
        err = hwdev.FanSpeedSet(fan_MAP[j].dev, fanPWM, (1<<fan_MAP[j].fanNum))
        if err != errType.SUCCESS {
           cli.Printf("e", "FanSpeedSet Failed on %s, fan-%d  (Silkscreen Number-%d)\n", fan_MAP[j].dev, fan_MAP[j].fanNum, fan_MAP[fanNumber].silkScreenFan)
           return
        }
    }
    misc.SleepInSec(1) //give fan time to change rpm

    return
}

//hwdev.FanDumpReg(devName)
func Fan_Check_RPM(fanNumber int, fanPWM int, tollerance int) (err int) {
    var fanInModule uint64
    var expRPM int
    var rpm [8]uint64
    var s string
    var MaxRetry int = 3
    var fanFail int = 0

    for fanInModule=0; fanInModule < FANPERMODULE; fanInModule++ {
        for retry:=0; retry < MaxRetry; retry++ {
            rpm[fanNumber], _, fanFail =  hwdev.FanSpeedGet(fan_MAP[fanNumber].dev, ((fan_MAP[fanNumber].fanNum * FANPERMODULE) + fanInModule) ) 
            if fanFail != errType.SUCCESS {
                cli.Printf("e", "FanSpeedGet Failed on %s, fan-%d  (Silkscreen Number-%d)\n", fan_MAP[fanNumber].dev, fan_MAP[fanNumber].fanNum, fan_MAP[fanNumber].silkScreenFan)
                err = errType.FAIL
                break
            } else {
                if fanInModule == 0 {
                    expRPM = rpm_rear_MAP[fanPWM]
                } else {
                    expRPM = rpm_front_MAP[fanPWM]
                }

                if fanInModule == 0 {
                    s = fmt.Sprintf(" FanModule#=%d:Rear  Fan Tollerance=%d RPM=%d  expRPM=%d\n", fanNumber, tollerance, rpm[fanNumber], expRPM)
                } else {
                    s = fmt.Sprintf(" FanModule#=%d:Front Fan Tollerance=%d RPM=%d  expRPM=%d\n", fanNumber, tollerance, rpm[fanNumber], expRPM)
                }
                cli.Printf("i", "%s", s)
                if int(rpm[fanNumber]) < expRPM - ((tollerance * expRPM)/100) {
                    if fanInModule == 0 {
                        cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Rear Fan RPM Test at %d PWM Failed.  Read RPM-%d below Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, rpm[fanNumber], expRPM - ((tollerance * expRPM)/100))
                    } else {
                        cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Front Fan RPM Test at %d PWM Failed.  Read RPM-%d below Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, rpm[fanNumber], expRPM - ((tollerance * expRPM)/100))
                    }
                    fanFail = errType.FAIL
                }
                if int(rpm[fanNumber]) > expRPM + ((tollerance * expRPM)/100) {
                    if fanInModule == 0 {
                        cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Rear Fan RPM Test at %d PWM Failed.  Read RPM-%d above Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, rpm[fanNumber], expRPM + ((tollerance * expRPM)/100) )
                    } else {
                        cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Front Fan RPM Test at %d PWM Failed.  Read RPM-%d above Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, rpm[fanNumber], expRPM + ((tollerance * expRPM)/100) )
                    }
                    fanFail = errType.FAIL
                }

                if (rpm[fanNumber] > 40000) { 
                    Fan_FIX_Stuck_Fan(fanNumber, fanPWM)
                }

                if fanFail == errType.SUCCESS {
                    break
                }
                if fanFail != errType.SUCCESS {
                    hwdev.FanDumpReg(fan_MAP[fanNumber].dev)
                    if(retry < (MaxRetry - 1 )) {
                        time.Sleep(time.Duration(200) * time.Millisecond)
                        fanFail = errType.SUCCESS
                    }
                }
            }
        }  //end retry

        if fanFail != errType.SUCCESS {
            fmt.Printf("DEBUG: SET ERR TO FAIL\n");
            err = errType.FAIL
        }
        
    }  //end fanInModule




    return
}


func Fan_RPM_test(tollerance int)(err int) {
    var pwm_backup [MAXFANMODULES]byte 
    var start_pwm byte
    var pwm_ramp_change byte
    var pct [MAXFANMODULES]byte 
    process := "fand"
    var presenceFailMask uint32 = 0
    var fanFail int = errType.SUCCESS
    fanspeed := []int{ 75, 60, 100, 75 }
    fandirection := []int{}
    

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
        fanFail = errType.FAIL 
    }




    //check if fan is present
    for j:=0; j<MAXFANMODULES; j++ {
        present, goerr := taorfpga.FAN_Module_present(uint32(j)) 
        if goerr != nil { 
            cli.Printf("e", "Reading Fan Presence Singals failed\n")
            fanFail = errType.FAIL 
        }
        if present == false {
            cli.Printf("e", "Fan Module-%d not present (Silkscreen Number-%d)\n", j, fan_MAP[j].silkScreenFan)
            presenceFailMask = presenceFailMask + (1<<uint32(j))
        }
    }

    //check fan direction (they all need to be the same directional airflow)
    data32, _ := taorfpga.TaorReadU32(taorfpga.DEVREGION1, taorfpga.D1_FAN_STAT_REG)
    fmt.Printf("DEBUG: data32=%.08x\n", data32)
    data32 = (data32 >> taorfpga.D1_FAN_STAT_PORT_SIDE_SHIFT)
    fmt.Printf("DEBUG: data32=%.08x\n", data32)
    for j:=0; j<MAXFANMODULES; j++ {
        if (data32 & (1<<uint32(j))) == (1<<uint32(j)) {
            fandirection = append(fandirection, 1)
            dcli.Printf("i", "%s, fan-%d (Silkscreen Number-%d): Airflow Direction; Front to Back\n", fan_MAP[j].dev, fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
        } else {
            fandirection = append(fandirection, 0)
            dcli.Printf("i", "%s, fan-%d (Silkscreen Number-%d): Airflow Direction; Back to Front\n", fan_MAP[j].dev, fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
        }
    }

    data32, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION1, taorfpga.D1_FAN_STAT_REG)
    if (data32 & taorfpga.D1_FAN_STAT_PORT_SIDE_INTAKE_MASK) != taorfpga.D1_FAN_STAT_PORT_SIDE_INTAKE_MASK {
        if (data32 & taorfpga.D1_FAN_STAT_PORT_SIDE_INTAKE_MASK) != 0x00 {
            cli.Printf("e", "Mismatched Fans for airflow direction.   Check all the fans are front-to-back, or back-to-front\n")
            fanFail = errType.FAIL
        }
    }
            

    //backup rpm values
    for j:=0; j<MAXFANMODULES; j++ {
        pwm_backup[j] , err = hwdev.FanReadReg(fan_MAP[j].dev, uint32(0xAA + fan_MAP[j].fanNum))
        if err != errType.SUCCESS {
           cli.Printf("e", "FanReadReg Failed on %s, fan-%d (Silkscreen Number-%d) \n", fan_MAP[j].dev, fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
           fanFail = errType.FAIL
        }
    }

    if fanFail == errType.SUCCESS {
        for i:=0; i<len(fanspeed); i++ {
           dcli.Printf("i","Testing Fans at PWM-%d\n", fanspeed[i])
           for j:=0; j<MAXFANMODULES; j++ {
               if i == 0 {
                   start_pwm = pwm_backup[j]     //start pwm is from the backup we read
               } else {
                   start_pwm = byte((fanspeed[i-1] * 255) / 100)     //get the start pwm from the list we use to set the pwm if not the first loop
               }
               pct[j] = byte(int((int(start_pwm) * 100)/255))
           }
           // Ramp up PWM if needed. Icnremenets of 5% at a time
           for steps:=0;steps<20;steps++ {
               var changeString string
               pwm_ramp_change = 0
               for j:=0; j<MAXFANMODULES; j++ {
                   if (presenceFailMask & (1<<uint32(j))) > 0 {
                       continue
                   }
                   if pct[j] > byte(fanspeed[i]) {  //fan speed going down, just break
                       continue
                   }
                   if (pct[j] + 5) < byte(fanspeed[i]) {
                       pct[j] = pct[j]+5
                       s := fmt.Sprintf("%d ", pct[j])
                       changeString = changeString + s
                       hwdev.FanSpeedSet(fan_MAP[j].dev, int(pct[j]), (1<<fan_MAP[j].fanNum))
                       pwm_ramp_change = 1
                   } else {
                       continue
                   }
               }
               if pwm_ramp_change > 0 { 
                   if len(changeString) > 0 {
                       cli.Printf("i","%s\n", changeString)
                   }
               }
           }
           // Set final PWM for test loop
           for j:=0; j<MAXFANMODULES; j++ {
               if (presenceFailMask & (1<<uint32(j))) > 0 {
                   continue
               }
               err = hwdev.FanSpeedSet(fan_MAP[j].dev, fanspeed[i], (1<<fan_MAP[j].fanNum))
               if err != errType.SUCCESS {
                   cli.Printf("e", "FanSpeedSet Failed on %s, fan-%d (Silkscreen Number-%d)\n", fan_MAP[j].dev, fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
                   fanFail = errType.FAIL
               }
           }


           misc.SleepInSec(9) //give fan time to change rpm
           for j:=0; j<MAXFANMODULES; j++ {
               if (presenceFailMask & (1<<uint32(j))) > 0 {
                   continue
               }

               err = Fan_Check_RPM(j, fanspeed[i], tollerance)
               if err != errType.SUCCESS {
                   fanFail = errType.FAIL
               }
           }
        }

        //restore rpm values
        for j:=0; j<MAXFANMODULES; j++ {
            hwdev.FanWriteReg(fan_MAP[j].dev, uint32(0xAA + fan_MAP[j].fanNum), pwm_backup[j])
        }
    } else {
        cli.Printf("e","Init in the fan test Failed.  Skipping Fan Test\n")
    }
    if fanFail != errType.SUCCESS {
        err = errType.FAIL
    }
    if presenceFailMask != 0 {
        err = errType.FAIL
    }

    if err == errType.SUCCESS {
        dcli.Printf("i","SWITCH FANRPM TEST PASSED\n")
    } else {
        dcli.Printf("e","SWITCH FANRPM TEST FAILED\n")
    }

    return
}

func TestTaorFruI2C(devName string) (err int) {
    var errGo error = nil
    var lastElement uint8
    BackupData := []uint8{}
    wrData := []uint8{}
    rdData := []uint8{}
    addr := []uint8{ 0x04, 0x00 }  //0x400 = 1K, nobody uses that section of the eeprom
    randNum := rand.New(rand.NewSource(time.Now().UnixNano()))

    pattern := [][]uint8{
    {0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55},
    {0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA},
    {0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00},
    {0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF},
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00} }

    lastElement = uint8(len(pattern)-1)
    for i:=0; i < len(pattern[lastElement]); i++ {
        pattern[lastElement][i] = uint8(randNum.Uint32() & 0xFF)
    }

    iInfo, rc := i2cinfo.GetI2cInfo(devName)
    if rc != errType.SUCCESS {
        dcli.Println("e", "Failed to obtain I2C info of", devName)
        err = rc
        return
    }

    //Read Test byte to restore afte test
    wrData = append(wrData, addr...)
    BackupData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, uint32(len(pattern[0])) )
    if errGo != nil {
        dcli.Println("e", "I2C Access (1) Failed to", devName, " ERROR=",errGo)
        err = errType.FAIL
        return
    }


    for i:=0; i < len(pattern); i++ {
        wrData = nil
        rdData = nil

        //WRITE ADDR + PATTERN
        wrData = append(wrData, addr...)
        wrData = append(wrData, pattern[i]...)
        rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 0 )
        if errGo != nil {
            dcli.Println("e", "I2C Access (1) Failed to", devName, " ERROR=",errGo)
            err = errType.FAIL
            return
        }

        misc.SleepInUSec(5000)    //atmel spec says max write time is 5ms

        //READ BACK WRITE DATA
        wrData = nil
        wrData = append(wrData, addr...)
        rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, uint32(len(pattern[i])))
        if errGo != nil {
            dcli.Println("e", "I2C Access (2) Failed to", devName)
            err = errType.FAIL
            return
        }

        if len(rdData) != len(pattern[i]) {
            dcli.Printf("e", "I2C Read Lenght is incorrect.  Read Length=%d   Expect=%d   ", len(rdData), len(pattern[i]))
            err = errType.FAIL
            return
        }

        for j:=0; j<len(pattern[i]); j++ {
            if rdData[j] != pattern[i][j] {
                dcli.Printf("e", "I2C Read Data Compare Failed.  Addr=0x%.02x%.02xRead Length=%d   Expect=%d   ", addr[0], addr[1], rdData[j], pattern[i][j])
                err = errType.FAIL
                return
            }

        }
    }

    //RESTORE DATA
    wrData = nil
    wrData = append(wrData, addr...)
    wrData = append(wrData, BackupData...)
    rdData, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 0)
    if errGo != nil {
        dcli.Println("e", "I2C Access (1) Failed to", devName, " ERROR=",errGo)
        err = errType.FAIL
        return
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
            cli.Printf("e","FAN Module-%d (Silkscreen Number-%d): NOT PRESENT\n", i+1, fan_MAP[i].silkScreenFan)
            err = errType.FAIL
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH PRESENT TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH PRESENT TEST FAILED\n")
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
                modules_detected++
                continue
            } else {
                s := fmt.Sprintf("MEMORY CHANNEL-%d:  PN: %s    SN: %s    SIZE: %s MB\n", i, pn[i], sn[i], size[i])
                printf("i", s, useCLI)
                modules_detected++
            }
        }
    }
    if modules_detected != 2 {
        cli.Printf("e", "Only detected %d memory modules", modules_detected)
        err = errType.FAIL
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "CPU DRAMSIZE TEST PASSED\n")
    } else {
        dcli.Printf("e", "CPU DRAMSIZE TEST FAILED\n")
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

func TPM_CHECK(useCLI int) (err int) {
    var cmdStr string
    cmdStr = "dmesg | grep -i tpm"
    output , errGo := exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }
    out := strings.TrimSuffix(string(output), "\n")
    if strings.Contains(out, "tpm_tis 00:08: 1.2 TPM (device-id 0x1B, rev-id 16)")==true {
        s := fmt.Sprintf("TPM INFO --> %s\n", string(out[15:]))
        printf("i", s, useCLI)
    } else {
        err = errType.FAIL
        s := fmt.Sprintf(" ERROR: DMESG DOES NOT CONTAIN VALID TPM INFO")
        printf("e", s, useCLI)
    }
    return
}


func CXOS_Display_Version(useCLI int) (err int) {
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

func CXOS_Get_Build_Date() (year int, month int, err int) {
    var cmdStr string
    year = 0
    month = 0
    cmdStr = "vtysh -c \"show version\" | grep -i \"Build Date\""
    output , errGo := exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }
    s := strings.Split(string(output), "\n")
    for _, temp := range s {
        year64, _ := strconv.ParseUint(strings.TrimLeft(string(temp[15:19]), "0"), 0, 32)
        year = int(year64)
        month64, _ := strconv.ParseUint(strings.TrimLeft(string(temp[20:22]), "0"), 0, 32)
        month = int(month64)
        break
    }
    return
}

func Grep_syslog_wc(search string) (wc int, err int) {
    cmdStr := fmt.Sprintf("grep -i \"%s\" /var/log/messages | wc -l", search)
    output , errGo := exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }
    wc64_t, _ := strconv.ParseUint(strings.TrimSpace(string(output)), 0, 64)
    wc = int(wc64_t)

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
    var cmdStr string
    var newMd5 hash.Hash
    var origMd5 hash.Hash

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
    }

    if err == errType.SUCCESS {

        out, errGo = exec.Command("mkfs.vfat", "/dev/sdb1").Output()
        dcli.Printf("i", "%s", out)
        if errGo != nil {
            dcli.Printf("e", "mkfs.vfat failed.  Err = %s", errGo)
            dcli.Printf("e", "mkfs.vfat failed.  Output=%s", out)
            err = errType.FAIL
            return
        }

        out, errGo = exec.Command("mount", "/dev/sdb1", "/mnt/usb").Output()
        if errGo != nil {
            dcli.Printf("e", "mount /dev/sdb1 /mnt/usb  Err = %s", errGo)
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
        origMd5 = md5.New()
        _, errGo = io.Copy(origMd5, f)
        if errGo != nil {
            cli.Println("e", errGo)
            err = errType.FAIL
            return
        }
        
        for i := 0; i < FileCopies; i++ {
            dcli.Printf("i", "ite=%d, Copying master file to %s\n", i, TaregetfileName+strconv.Itoa(i))
            cmd = exec.Command("cp", fileName, TaregetfileName+strconv.Itoa(i))
            _ = cmd.Run()
            dcli.Printf("i", "sync\n")
            cmd = exec.Command("sync")
            _ = cmd.Run()
            fd, errGo := os.Open(TaregetfileName+strconv.Itoa(i))
            if errGo != nil {
                cli.Println("e", "Opening file ",TaregetfileName+strconv.Itoa(i)," Failed.   Go Error =", errGo)
                err = errType.FAIL
                break
            }
            defer fd.Close()

            dcli.Printf("i", "Calculating MD5\n")
            newMd5 = md5.New()
            _, errGo = io.Copy(newMd5, fd)
            if errGo != nil {
                cli.Println("e", "Calculating Md5 Failed.  Error msg --> ", errGo)
                err = errType.FAIL
                break
            }

            if !bytes.Equal(origMd5.Sum(nil), newMd5.Sum(nil)) {
                dcli.Printf("i", "File %s has an md5sum error.   Expected=%x   Calulated=%x\n", TaregetfileName+strconv.Itoa(i), origMd5.Sum(nil), newMd5.Sum(nil))
                err = errType.FAIL
                break
            }
            cmd = exec.Command("rm", TaregetfileName+strconv.Itoa(i))
            _ = cmd.Run()
            cmd = exec.Command("sync")
            _ = cmd.Run()
        }
        if err == errType.SUCCESS {
            dcli.Printf("i", "%d files copied to the USB stick from /tmp/testfile.  All md5sums match\n", FileCopies)
        }

        cmdStr ="umount -l -f /mnt/usb"
        out, errGo = exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "umount /mnt/usb failed.  Err = %s\n", errGo)
            err = errType.FAIL
        } 
    }

    if err == errType.SUCCESS {
        dcli.Printf("i","CPU USB TEST PASSED\n")
    } else {
        dcli.Printf("e","CPU USB TEST FAILED\n")
    }

    return
}



/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func X86_CPU_MemoryTest(threads uint32, percent_of_free_mem uint32, time uint32, calledFromCLI int) (err int) {
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
        }        
    }

    if err == errType.SUCCESS {
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
            for i=0;i<(time + 10);i++ {
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
    }

    if err == errType.SUCCESS {
        cmdStr = "cat stressapptest.log"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
        } else {
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
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i","CPU MEMORY TEST PASSED\n")
    } else {
        dcli.Printf("e","CPU MEMORY TEST FAILED\n")
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


func ElbaGetConsoleScriptToExecute(elbaNumber uint32) (elbaScript string, err int) {
    var ResistorStrapping uint32 = 4
    var errGo error

    ResistorStrapping, errGo =  taorfpga.GetResistorStrapping()
    if errGo != nil {
        dcli.Printf("e","FAILED TO READ FRU PCA REVISION\n")
    }
    //Board is using FPGA based uart.  Not super I/O
    //Need to call different script to execute commands over the console
    if ResistorStrapping >= 4 {
        if  elbaNumber == ELBA0 {
            elbaScript = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba0_via_fpgaconsole.sh"
        } else if elbaNumber == ELBA1 {
            elbaScript = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba1_via_fpgaconsole.sh"
        }
    } else {
        if  elbaNumber == ELBA0 {
            elbaScript = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba0_via_console.sh"
        } else if elbaNumber == ELBA1 {
            elbaScript = "/fs/nos/home_diag/diag/scripts/taormina/exec_cmd_elba1_via_console.sh"
        } 
    }
    return
}


/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func ElbaEDMA_Test_Console_Only_CXOS_SCRIPT(elbaMask uint32, calledFromCLI int, rdpad_max int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    var forStart, forEnd uint32
    var time uint32 = 90
    var testStarted uint32 = 0
    var passCnt = (rdpad_max / 10) + 3

    var newEDMA uint32 = 0  //new edma does not need bypass memory variables set


    if rdpad_max > 101 {
        t := (rdpad_max - 100) / 10
        t = t * 10
        time = time + uint32(t)
    }


    
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

    dcli.Printf("i", " Starting Elba EMDA Test:  Mask=0x%x\n", elbaMask)


    year, month, _ := CXOS_Get_Build_Date()
    dcli.Printf("i","CXOS Build Date %d-%.02d\n", year, month)
    if (year < 2022) || ((year==2022) && (month < 7)) {
        cli.Printf("e", "CXOS Image build date does not look like it supports EDMA. Date--> %d-%.02d\n", year, month)
        err = errType.FAIL
        return
    }



    //2024-02-02 04:06:46 UTC
    if ((year==2024) && (month > 1)){
        newEDMA=1
    }
    dcli.Printf("i","newEDMA=%d\n", newEDMA)


    for i=forStart; i < forEnd; i++ {
        rc := ElbaCheckECC_via_console(i, 0, 0) 
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        }
    }



    cli.Printf("i","Removing Elba from PCI\n");
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        if  i == ELBA0 {
            exec.Command("bash", "-c", "echo 1 > /sys/bus/pci/devices/0000:0b:00.0/remove").Output() 
        } else {
            exec.Command("bash", "-c", "echo 1 > /sys/bus/pci/devices/0000:05:00.0/remove").Output()
        }
    }

    if (newEDMA == 0) {
        dcli.Printf("i","Setting fwenv vars for mem bypass and rebooting Elba\n")
        cmdStr = fmt.Sprintf("pwd\nfwenv -s mem_bypass_addr 0x1000000000;fwenv -s mem_bypass_size 1073741824;sysreset.sh\n")
        _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
        _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
        for i=forStart; i < forEnd; i++ {
            if elbafailmask & (1<<i) == (1<<i) {
                continue
            }
            testStarted=1
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            }  
            _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
        }
        misc.SleepInSec(15)
    }

   
    dcli.Printf("i","Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /nic/bin;rdpad_max=%d /nic/bin/ddr_test.sh | tee run_edma.log\n", rdpad_max)
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    //cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;rdpad_max=%d /nic/bin/ddr_test.sh | tee run_edma.log\n", rdpad_max)
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
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        }  
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }

    //Sleep.. give it a few extra seconds to finsih as the program needs time to setup/malloc memory
    if (testStarted > 0) {
        for i=0;i<(time);i++ {
            misc.SleepInSec(1)
            if calledFromCLI > 0 { fmt.Printf(".") 
            } else { dcli.Printf("i", ".") }
        }
        if calledFromCLI > 0 { fmt.Printf("\n") }
    }
     
    //Get Results
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }

        dcli.Printf("i", "Elba-%d Get Results\n", i)
        dcli.Printf("i", "Elba-%d Reading the log file\n", i)
        cmdStr = fmt.Sprintf("pwd\ncat /nic/bin/run_edma.log\n")           
        if  i == ELBA0 {
            errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        } else if i == ELBA1 {
            errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        }
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", string(output))

        numbPass := strings.Count(string(output), "PASS")
        fmt.Printf(" NumPASS=%d\n", numbPass)
        if (int(numbPass) != passCnt) {
            dcli.Printf("e","[ERROR] ELBA-%d FAILED EDMA TEST.    Passes read=%d   Expected=%d\n", i, int(numbPass),passCnt)
            elbafailmask |= (1<<i)
        }
        if ( (elbafailmask & (1<<i)) == (1<<i) ) {
            cmdStr = fmt.Sprintf("pwd\ncat /nic/util/ddr_test.log\n")           
            if  i == ELBA0 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", string(output))

            dcli.Printf("i","Creating cmd files for dmesg\n")
            cmdStr = fmt.Sprintf("pwd\ndmesg | tail -n 100\n")           
            if  i == ELBA0 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo = exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", string(output)) 
        }


        rc := ElbaCheckECC_via_console(i, 0, 0)
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        } 
        
    }

    if (newEDMA == 0) {
        dcli.Printf("i","UnSetting fwenv vars for mem bypass and rebooting Elba\n")
        cmdStr = fmt.Sprintf("pwd\nfwenv -R\n")
        _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
        _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
        for i=forStart; i < forEnd; i++ {
            testStarted=1
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            }  
            _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
        }
    }

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
            dcli.Printf("e", "Elba-%d ELBA_EDMA_TEST TEST FAILED\n", i)
        } else {
            dcli.Printf("i", "Elba-%d ELBA_EDMA_TEST TEST PASSED\n", i)
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH ELBA_EDMA_TEST TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH ELBA_EDMA_TEST TEST FAILED\n")
    }

    return
}


/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func ElbaEDMA_Test_Console_Only(elbaMask uint32, calledFromCLI int, rdpad_max int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    var forStart, forEnd uint32
    var time uint32 = 90
    var testStarted uint32 = 0
    var passCnt = (rdpad_max / 10) + 2


    if rdpad_max > 101 {
        t := (rdpad_max - 100) / 10
        t = t * 10
        time = time + uint32(t)
    }


    
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

    dcli.Printf("i", " Starting Elba EMDA Test:  Mask=0x%x\n", elbaMask)


    {
        year, month, _ := CXOS_Get_Build_Date()
        dcli.Printf("i","CXOS Build Date %d-%.02d\n", year, month)
        if (year < 2022) || ((year==2022) && (month < 3)) {
            cli.Printf("e", "CXOS Image build date does not look like it supports EDMA. Date--> %d-%.02d\n", year, month)
            err = errType.FAIL
            return
        }
    }


    for i=forStart; i < forEnd; i++ {
        rc := ElbaCheckECC_via_console(i, 0, 0) 
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        }
    }



    //Check that we can find the run_edma.sh script in case someone tries to run this without the diag package installed
    fileExists, _ := taorfpga.Path_exists("/fs/nos/home_diag/diag/scripts/taormina/run_edma.sh")
    if fileExists == false {
        cli.Printf("e", "Unable to locate run_edma.sh script.  Looking under path /fs/nos/home_diag/diag/scripts/taormina/run_edma.sh.   Check that the diag package is installed\n")
        err = errType.FAIL
        return
    }
    
    //Copy over stressarpptest and delete any old logs
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }

        //First time we run this test, we should be able to ping elba and copy over the script.    
        //If in debug a user wants to loop this test, network will be down on subsequent runs due to the fact we have to set the memory bypass region and reboot elba (which will take down the network)
        //In that case just check if run_edma.sh is already there on elba and continue with the test
        errTemp := ElbaPing(i) 
        if errTemp == errType.SUCCESS {
            dcli.Printf("i", "Elba-%d Copying over run_edma.sh\n", i)
            if  i == ELBA0 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma.sh root@169.254.13.1:/data/nic_util"
            } else if i == ELBA1 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma.sh root@169.254.7.1:/data/nic_util"
            } 
            _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
        } else {
            dcli.Printf("i", "Elba-%d checking for run_edma.sh script\n", i)
            cmdStr = fmt.Sprintf("pwd\nls /data/nic_util/run_edma.sh\n")           
            if  i == ELBA0 {
                errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v\n\n  output='%s'", cmdStr, errGo, string(output))
                err = errType.FAIL
                return
            }
            if strings.Contains(string(output), "No such file or directory") == true {
                dcli.Printf("e","Cannot find /data/nic_util/run_edma.sh on Elba.   You might need to manually copy it over if you want to loop edma test or the network to elba is not up\n")
                elbafailmask |= (1<<i)
            }
        }

        dcli.Printf("i", "Elba-%d Clear any exisitng log files\n", i)
        cmdStr = fmt.Sprintf("pwd\n/bin/rm /data/nic_util/ddr_test.log;/bin/rm /data/nic_util/run_edma.log;sync\n")           
        if  i == ELBA0 {
            errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        } else if i == ELBA1 {
            errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        }
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v\n\n  output='%s'", cmdStr, errGo, string(output))
            err = errType.FAIL
            return
        }
    }


    cli.Printf("i","Removing Elba from PCI\n");
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        if  i == ELBA0 {
            exec.Command("bash", "-c", "echo 1 > /sys/bus/pci/devices/0000:0b:00.0/remove").Output() 
        } else {
            exec.Command("bash", "-c", "echo 1 > /sys/bus/pci/devices/0000:05:00.0/remove").Output()
        }
    }

    dcli.Printf("i","Setting fwenv vars for mem bypass and rebooting Elba\n")
    cmdStr = fmt.Sprintf("pwd\nfwenv -s mem_bypass_addr 0x1000000000;fwenv -s mem_bypass_size 1073741824;sysreset.sh\n")
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }
    misc.SleepInSec(15)


   
    dcli.Printf("i","Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;rdpad_max=%d /data/nic_util/run_edma.sh | tee run_edma.log\n", rdpad_max)
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;rdpad_max=%d /data/nic_util/run_edma.sh | tee run_edma.log\n", rdpad_max)
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
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        }  
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }

    //Sleep.. give it a few extra seconds to finsih as the program needs time to setup/malloc memory
    if (testStarted > 0) {
        for i=0;i<(time);i++ {
            misc.SleepInSec(1)
            if calledFromCLI > 0 { fmt.Printf(".") 
            } else { dcli.Printf("i", ".") }
        }
        if calledFromCLI > 0 { fmt.Printf("\n") }
    }
     
    //Get Results
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }

        dcli.Printf("i", "Elba-%d Get Results\n", i)
        dcli.Printf("i", "Elba-%d Reading the log file\n", i)
        cmdStr = fmt.Sprintf("pwd\ncat /data/nic_util/run_edma.log\n")           
        if  i == ELBA0 {
            errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        } else if i == ELBA1 {
            errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        }
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", string(output))

        numbPass := strings.Count(string(output), "PASS")
        fmt.Printf(" NumPASS=%d\n", numbPass)
        if (int(numbPass) != passCnt) {
            dcli.Printf("e","[ERROR] ELBA-%d FAILED EDMA TEST.    Passes read=%d   Expected=%d\n", i, int(numbPass),passCnt)
            elbafailmask |= (1<<i)
        }
        if ( (elbafailmask & (1<<i)) == (1<<i) ) {
            cmdStr = fmt.Sprintf("pwd\ncat /data/nic_util/ddr_test.log\n")           
            if  i == ELBA0 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", string(output))

            dcli.Printf("i","Creating cmd files for dmesg\n")
            cmdStr = fmt.Sprintf("pwd\ndmesg | tail -n 100\n")           
            if  i == ELBA0 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo = exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", string(output)) 
        }


        rc := ElbaCheckECC_via_console(i, 0, 0)
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        } 
        
    }

    dcli.Printf("i","UnSetting fwenv vars for mem bypass and rebooting Elba\n")
    cmdStr = fmt.Sprintf("pwd\nfwenv -R\n")
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    for i=forStart; i < forEnd; i++ {
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }
    

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
            dcli.Printf("e", "Elba-%d ELBA_EDMA_TEST TEST FAILED\n", i)
        } else {
            dcli.Printf("i", "Elba-%d ELBA_EDMA_TEST TEST PASSED\n", i)
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH ELBA_EDMA_TEST TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH ELBA_EDMA_TEST TEST FAILED\n")
    }

    return
}




/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func ElbaEDMA_Test(elbaMask uint32, calledFromCLI int, rdpad_max int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    err = errType.FAIL
    var forStart, forEnd uint32
    var time uint32 = 90
    var testStarted uint32 = 0
    var passCnt = (rdpad_max / 10) + 2


    if rdpad_max > 101 {
        t := (rdpad_max - 100) / 10
        t = t * 10
        time = time + uint32(t)
    }


    
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

    dcli.Printf("i", " Starting Elba EMDA Test:  Mask=0x%x\n", elbaMask)


    {
        year, month, _ := CXOS_Get_Build_Date()
        dcli.Printf("i","CXOS Build Date %d-%.02d\n", year, month)
        if (year < 2022) || ((year==2022) && (month < 3)) {
            cli.Printf("e", "CXOS Image build date does not look like it supports EDMA. Date--> %d-%.02d\n", year, month)
            err = errType.FAIL
            return
        }
    }


    //Ping Elba to make sure the network is up
    for i=forStart; i < forEnd; i++ {
        dcli.Printf("i","Elba-%d Ping Test\n", i)
        err = ElbaPing(i) 
        if err != errType.SUCCESS {
            dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed\n", i)
            elbafailmask |= (1<<i)
        } else {
            rc := ElbaCheckECC(i, 1, 0, 0) 
            if rc != errType.SUCCESS {
                elbafailmask |= (1<<i)
            }
        }
    }



    //Check that we can find the run_edma.sh script in case someone tries to run this without the diag package installed
    fileExists, _ := taorfpga.Path_exists("/fs/nos/home_diag/diag/scripts/taormina/run_edma.sh")
    if fileExists == false {
        cli.Printf("e", "Unable to locate run_edma.sh script.  Looking under path /fs/nos/home_diag/diag/scripts/taormina/run_edma.sh.   Check that the diag package is installed\n")
        err = errType.FAIL
        return
    }

    //Copy over stressarpptest and delete any old logs
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Copying over run_edma.sh\n", i)
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma.sh root@169.254.13.1:/data/nic_util"
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma.sh root@169.254.7.1:/data/nic_util"
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }

        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 \"/bin/rm /data/nic_util/ddr_test.log;/bin/rm /data/nic_util/run_edma.log\""
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 \"/bin/rm /data/nic_util/ddr_test.log;/bin/rm /data/nic_util/run_edma.log\""
        } 
        _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
    }

    dcli.Printf("i","Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;rdpad_max=%d /data/nic_util/run_edma.sh | tee run_edma.log\n", rdpad_max)
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;rdpad_max=%d /data/nic_util/run_edma.sh | tee run_edma.log\n", rdpad_max)
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
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }

    //Sleep.. give it a few extra seconds to finsih as the program needs time to setup/malloc memory
    if (testStarted > 0) {
        for i=0;i<(time);i++ {
            misc.SleepInSec(1)
            if calledFromCLI > 0 { fmt.Printf(".") 
            } else { dcli.Printf("i", ".") }
        }
        if calledFromCLI > 0 { fmt.Printf("\n") }
    }

    //Get Results
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }

        dcli.Printf("i", "Elba-%d Get Results\n", i)
        dcli.Printf("i", "Elba-%d Copying back the log file\n", i)

        cmdStr = "rm run_edma.log; rm ddr_test.log"
        output , errGo  := exec.Command("sh", "-c", cmdStr).Output()
        
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1:/data/nic_util/run_edma.log ."
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1:/data/nic_util/run_edma.log ."
        } 
        _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1:/data/nic_util/ddr_test.log ."
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1:/data/nic_util/ddr_test.log ."
        } 
        _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }

        cmdStr = "ls -l run_edma.log"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))


        cmdStr = "cat run_edma.log"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))

        cmdStr = "grep -o PASS run_edma.log | wc -l"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        numbPass, _ := strconv.ParseUint(strings.TrimSpace(string(output)), 0, 64)
        if (int(numbPass) != passCnt) {
            dcli.Printf("e","[ERROR] ELBA-%d FAILED EDMA TEST.    Passes read=%d   Expected=%d\n", i, int(numbPass),passCnt)
            elbafailmask |= (1<<i)
        }

        /* 
        cmdStr = "grep -o ERROR ddr_test.log | wc -l"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        numbError, _ := strconv.ParseUint(strings.TrimSpace(string(output)), 0, 64)
        if (numbError != 4) {
            dcli.Printf("e","[ERROR] ELBA-%d FAILED EDMA TEST.  OTHER ERROR's IN THE LOG\n", i)
            elbafailmask |= (1<<i)

            cmdStr = "cat ddr_test.log"
            output , errGo = exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", "%s\n", string(output))
        } 
        */ 



        if ( (elbafailmask & (1<<i)) == (1<<i) ) {
            if  i == ELBA0 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 dmesg | tail -n 75"
            } else if i == ELBA1 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 dmesg | tail -n 75"
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", "%s\n", string(output))
            elbafailmask |= (1<<i)
        }
        
        rc := ElbaCheckECC(i, 1, 0, 0) 
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        }

    }

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
            dcli.Printf("e", "Elba-%d ELBA_EDMA_TEST TEST FAILED\n", i)
        } else {
            dcli.Printf("i", "Elba-%d ELBA_EDMA_TEST TEST PASSED\n", i)
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH ELBA_EDMA_TEST TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH ELBA_EDMA_TEST TEST FAILED\n")
    }

    return
}



/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func ElbaEDMA_Test_WRPAD(elbaMask uint32, calledFromCLI int, wrpad_max int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    var forStart, forEnd uint32
    var time uint32 = 90
    var testStarted uint32 = 0
    var passCnt = (wrpad_max / 10) + 2


    if wrpad_max > 101 {
        t := (wrpad_max - 100) / 10
        t = t * 10
        time = time + uint32(t)
    }


    
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

    dcli.Printf("i", " Starting Elba EMDA Test:  Mask=0x%x\n", elbaMask)


    {
        year, month, _ := CXOS_Get_Build_Date()
        dcli.Printf("i","CXOS Build Date %d-%.02d\n", year, month)
        if (year < 2022) || ((year==2022) && (month < 3)) {
            cli.Printf("e", "CXOS Image build date does not look like it supports EDMA. Date--> %d-%.02d\n", year, month)
            err = errType.FAIL
            return
        }
    }


    for i=forStart; i < forEnd; i++ {
        rc := ElbaCheckECC_via_console(i, 0, 0) 
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        }
    }



    //Check that we can find the run_edma_wrpad.sh script in case someone tries to run this without the diag package installed
    fileExists, _ := taorfpga.Path_exists("/fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh")
    if fileExists == false {
        cli.Printf("e", "Unable to locate run_edma_wrpad.sh script.  Looking under path /fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh.   Check that the diag package is installed\n")
        err = errType.FAIL
        return
    }
    
    //Copy over stressarpptest and delete any old logs
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }

        //First time we run this test, we should be able to ping elba and copy over the script.    
        //If in debug a user wants to loop this test, network will be down on subsequent runs due to the fact we have to set the memory bypass region and reboot elba (which will take down the network)
        //In that case just check if run_edma_wrpad.sh is already there on elba and continue with the test
        errTemp := ElbaPing(i) 
        if errTemp == errType.SUCCESS {
            dcli.Printf("i", "Elba-%d Copying over run_edma_wrpad.sh\n", i)
            if  i == ELBA0 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh root@169.254.13.1:/data/nic_util"
            } else if i == ELBA1 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh root@169.254.7.1:/data/nic_util"
            } 
            _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
        } else {
            dcli.Printf("i", "Elba-%d checking for run_edma_wrpad.sh script\n", i)
            cmdStr = fmt.Sprintf("pwd\nls /data/nic_util/run_edma_wrpad.sh\n")           
            if  i == ELBA0 {
                errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v\n\n  output='%s'", cmdStr, errGo, string(output))
                err = errType.FAIL
                return
            }
            if strings.Contains(string(output), "No such file or directory") == true {
                dcli.Printf("e","Cannot find /data/nic_util/run_edma_wrpad.sh on Elba.   You might need to manually copy it over if you want to loop edma test or the network to elba is not up\n")
                elbafailmask |= (1<<i)
            }
        }

        dcli.Printf("i", "Elba-%d Clear any exisitng log files\n", i)
        cmdStr = fmt.Sprintf("pwd\n/bin/rm /data/nic_util/ddr_test.log;/bin/rm /data/nic_util/run_edma.log;sync\n")           
        if  i == ELBA0 {
            errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        } else if i == ELBA1 {
            errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        }
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v\n\n  output='%s'", cmdStr, errGo, string(output))
            err = errType.FAIL
            return
        }
    }


    cli.Printf("i","Removing Elba from PCI\n");
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        if  i == ELBA0 {
            exec.Command("bash", "-c", "echo 1 > /sys/bus/pci/devices/0000:0b:00.0/remove").Output() 
        } else {
            exec.Command("bash", "-c", "echo 1 > /sys/bus/pci/devices/0000:05:00.0/remove").Output()
        }
    }

    dcli.Printf("i","Setting fwenv vars for mem bypass and rebooting Elba\n")
    cmdStr = fmt.Sprintf("pwd\nfwenv -s mem_bypass_addr 0x1000000000;fwenv -s mem_bypass_size 1073741824;sysreset.sh\n")
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }
    misc.SleepInSec(15)


   
    dcli.Printf("i","Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;wrpad_max=%d /data/nic_util/run_edma_wrpad.sh | tee run_edma.log\n", wrpad_max)
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;wrpad_max=%d /data/nic_util/run_edma_wrpad.sh | tee run_edma.log\n", wrpad_max)
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
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        }  
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }

    //Sleep.. give it a few extra seconds to finsih as the program needs time to setup/malloc memory
    if (testStarted > 0) {
        for i=0;i<(time);i++ {
            misc.SleepInSec(1)
            if calledFromCLI > 0 { fmt.Printf(".") 
            } else { dcli.Printf("i", ".") }
        }
        if calledFromCLI > 0 { fmt.Printf("\n") }
    }
     
    //Get Results
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }

        dcli.Printf("i", "Elba-%d Get Results\n", i)
        dcli.Printf("i", "Elba-%d Reading the log file\n", i)
        cmdStr = fmt.Sprintf("pwd\ncat /data/nic_util/run_edma.log\n")           
        if  i == ELBA0 {
            errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        } else if i == ELBA1 {
            errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
            if errGo != nil {
                dcli.Printf("e", "Unable to write file: %v", errGo)
                err = errType.FAIL
                return
            }
        }
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", string(output))

        numbPass := strings.Count(string(output), "PASS")
        fmt.Printf(" NumPASS=%d\n", numbPass)
        if (int(numbPass) != passCnt) {
            dcli.Printf("e","[ERROR] ELBA-%d FAILED EDMA TEST.    Passes read=%d   Expected=%d\n", i, int(numbPass),passCnt)
            elbafailmask |= (1<<i)
        }
        if ( (elbafailmask & (1<<i)) == (1<<i) ) {
            cmdStr = fmt.Sprintf("pwd\ncat /data/nic_util/ddr_test.log\n")           
            if  i == ELBA0 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", string(output))

            dcli.Printf("i","Creating cmd files for dmesg\n")
            cmdStr = fmt.Sprintf("pwd\ndmesg | tail -n 100\n")           
            if  i == ELBA0 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            } else if i == ELBA1 {
                errGo = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
                if errGo != nil {
                    dcli.Printf("e", "Unable to write file: %v", errGo)
                    err = errType.FAIL
                    return
                }
            }
            cmdStr, err = ElbaGetConsoleScriptToExecute(i)
            if err != errType.SUCCESS {
                dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                return
            } 
            output , errGo = exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", string(output)) 
        }


        rc := ElbaCheckECC_via_console(i, 0, 0)
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        } 
        
    }

    /*
    dcli.Printf("i","UnSetting fwenv vars for mem bypass and rebooting Elba\n")
    cmdStr = fmt.Sprintf("pwd\nfwenv -R\n")
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    _ = ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt", []byte(cmdStr), 0755)
    for i=forStart; i < forEnd; i++ {
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }
    */
    

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
            dcli.Printf("e", "Elba-%d ELBA_EDMA_TEST TEST FAILED\n", i)
        } else {
            dcli.Printf("i", "Elba-%d ELBA_EDMA_TEST TEST PASSED\n", i)
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH ELBA_EDMA_TEST TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH ELBA_EDMA_TEST TEST FAILED\n")
    }

    return
}


/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
/*
func ElbaEDMA_Test_WRPAD(elbaMask uint32, calledFromCLI int, wrpad_max int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    err = errType.FAIL
    var forStart, forEnd uint32
    var time uint32 = 90
    var testStarted uint32 = 0
    var passCnt = (wrpad_max / 10) + 2


    if wrpad_max > 101 {
        t := (wrpad_max - 100) / 10
        t = t * 10
        time = time + uint32(t)
    }


    
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

    dcli.Printf("i", " Starting Elba EMDA Test:  Mask=0x%x\n", elbaMask)


    {
        year, month, _ := CXOS_Get_Build_Date()
        dcli.Printf("i","CXOS Build Date %d-%.02d\n", year, month)
        if (year < 2022) || ((year==2022) && (month < 3)) {
            cli.Printf("e", "CXOS Image build date does not look like it supports EDMA. Date--> %d-%.02d\n", year, month)
            err = errType.FAIL
            return
        }
    }


    //Ping Elba to make sure the network is up
    for i=forStart; i < forEnd; i++ {
        dcli.Printf("i","Elba-%d Ping Test\n", i)
        err = ElbaPing(i) 
        if err != errType.SUCCESS {
            dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed\n", i)
            elbafailmask |= (1<<i)
        } else {
            rc := ElbaCheckECC(i, 1, 0, 0) 
            if rc != errType.SUCCESS {
                elbafailmask |= (1<<i)
            }
        }
    }



    //Check that we can find the run_edma_wrpad.sh script in case someone tries to run this without the diag package installed
    fileExists, _ := taorfpga.Path_exists("/fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh")
    if fileExists == false {
        cli.Printf("e", "Unable to locate run_edma_wrpad.sh script.  Looking under path /fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh.   Check that the diag package is installed\n")
        err = errType.FAIL
        return
    }

    //Copy over stressarpptest and delete any old logs
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }
        dcli.Printf("i", "Elba-%d Copying over run_edma_wrpad.sh\n", i)
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh root@169.254.13.1:/data/nic_util"
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /fs/nos/home_diag/diag/scripts/taormina/run_edma_wrpad.sh root@169.254.7.1:/data/nic_util"
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }

        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 \"/bin/rm /data/nic_util/ddr_test.log;/bin/rm /data/nic_util/run_edma.log\""
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 45 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 \"/bin/rm /data/nic_util/ddr_test.log;/bin/rm /data/nic_util/run_edma.log\""
        } 
        _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
    }

    dcli.Printf("i","Creating cmd files\n")
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;wrpad_max=%d /data/nic_util/run_edma_wrpad.sh | tee run_edma.log\n", wrpad_max)
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    cmdStr = fmt.Sprintf("pwd\ncd /data/nic_util;wrpad_max=%d /data/nic_util/run_edma_wrpad.sh | tee run_edma.log\n", wrpad_max)
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
        testStarted=1
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        }  
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
    }

    //Sleep.. give it a few extra seconds to finsih as the program needs time to setup/malloc memory
    if (testStarted > 0) {
        for i=0;i<(time);i++ {
            misc.SleepInSec(1)
            if calledFromCLI > 0 { fmt.Printf(".") 
            } else { dcli.Printf("i", ".") }
        }
        if calledFromCLI > 0 { fmt.Printf("\n") }
    }

    //Get Results
    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            continue
        }

        dcli.Printf("i", "Elba-%d Get Results\n", i)
        dcli.Printf("i", "Elba-%d Copying back the log file\n", i)

        cmdStr = "rm run_edma.log; rm ddr_test.log"
        output , errGo  := exec.Command("sh", "-c", cmdStr).Output()
        
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1:/data/nic_util/run_edma.log ."
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1:/data/nic_util/run_edma.log ."
        } 
        _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1:/data/nic_util/ddr_test.log ."
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1:/data/nic_util/ddr_test.log ."
        } 
        _ , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }

        cmdStr = "ls -l run_edma.log"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))


        cmdStr = "cat run_edma.log"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))

        cmdStr = "grep -o PASS run_edma.log | wc -l"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        numbPass, _ := strconv.ParseUint(strings.TrimSpace(string(output)), 0, 64)
        if (int(numbPass) != passCnt) {
            dcli.Printf("e","[ERROR] ELBA-%d FAILED EDMA TEST.    Passes read=%d   Expected=%d\n", i, int(numbPass),passCnt)
            elbafailmask |= (1<<i)
        }



        if ( (elbafailmask & (1<<i)) == (1<<i) ) {
            if  i == ELBA0 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 dmesg | tail -n 75"
            } else if i == ELBA1 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 dmesg | tail -n 75"
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", "%s\n", string(output))
            elbafailmask |= (1<<i)
        }
        
        rc := ElbaCheckECC(i, 1, 0, 0) 
        if rc != errType.SUCCESS {
            elbafailmask |= (1<<i)
        }

    }

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
            dcli.Printf("e", "Elba-%d ELBA_EDMA_TEST TEST FAILED\n", i)
        } else {
            dcli.Printf("i", "Elba-%d ELBA_EDMA_TEST TEST PASSED\n", i)
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH ELBA_EDMA_TEST TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH ELBA_EDMA_TEST TEST FAILED\n")
    }

    return
} 
*/ 




/********************************************************************************* 
*
* 
* 
*********************************************************************************/ 
func ElbaMemoryTest(elbaMask uint32, time uint32, percent uint32, calledFromCLI int) (err int) {
    var cmdStr string
    var elbafailmask, i uint32
    err = errType.FAIL
    var forStart, forEnd uint32
    var percentFloat float64 = float64(percent)/100
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

   dcli.Printf("i", " Starting Elba Memory Test:  Mask=0x%x    Time=%d    Percent=%f\n", elbaMask, time, percentFloat)

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
    cmdStr = fmt.Sprintf("pwd\ncd /data;./stressapptest_arm -s %d -M %d -m 12 -l stressapptest_arm.log\n", time, int(float64(freemem[0]) * percentFloat)/1000)
    errGo := ioutil.WriteFile("/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt", []byte(cmdStr), 0755)
    if errGo != nil {
        dcli.Printf("e", "Unable to write file: %v", errGo)
        err = errType.FAIL
        return
    }
    cmdStr = fmt.Sprintf("pwd\ncd /data;./stressapptest_arm -s %d -M %d -m 12 -l stressapptest_arm.log\n", time, int(float64(freemem[1]) * percentFloat)/1000)
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
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
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
        dcli.Printf("i", "Elba-%d Copying back the log file\n", i)
        if  i == ELBA0 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1:/data/stressapptest_arm.log ."
        } else if i == ELBA1 {
            cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 10 scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1:/data/stressapptest_arm.log ."
        } 
        _ , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }

        cmdStr = "ls -l stressapptest_arm.log"
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))


        cmdStr = "cat stressapptest_arm.log"
        output , errGo = exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))
        
        if strings.Contains(string(output), "Status: PASS")==false {
            dcli.Printf("e", "[ERROR] Elba-%d did not pass stressapptest\n", i)
            if  i == ELBA0 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 dmesg | tail -n 75"
            } else if i == ELBA1 {
                cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 dmesg | tail -n 75"
            } 
            output , errGo := exec.Command("sh", "-c", cmdStr).Output()
            if errGo != nil {
                dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                err = errType.FAIL
                return
            }
            dcli.Printf("i", "%s\n", string(output))
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

    for i=forStart; i < forEnd; i++ {
        if elbafailmask & (1<<i) == (1<<i) {
            err = errType.FAIL
            dcli.Printf("e", "Elba-%d ELBA_ARM_MEMORY TEST FAILED\n", i)
        } else {
            dcli.Printf("i", "Elba-%d ELBA_ARM_MEMORY TEST PASSED\n", i)
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH ELBA_ARM_MEMORY TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH ELBA_ARM_MEMORY TEST FAILED\n")
    }
    return
}


/********************************************************************************* 
 
 
////////////////////////////// CONTENTS OF EACH REGISTER IN THE SCRIPT ////////////////
# cat elba_local_read_ecc_reg.sh
#!/bin/bash

/nic/bin/capview << EOF
secure on
read 0x30520020     //CHECK MC0 CORRECTABLE IRQ (See below for bit defines).  
read 0x305a0020     //CHECK MC1 CORRECTABLE IRQ (see below for bit defines). 

read 0x30530464     //BITS[31:0]
read 0x30530468     //BITS[63:32] --> MC0-SYNCD_ADDR[47:40] / MC0-ADDR[39:0]

read 0x3053046C     //BITS[31:0]
read 0x30530470     //BITS[63:32] --> MC0-DATA[63:0]

read 0x30530474     //[BITS31:0]  --> MC0-ECC C ID[16]

read 0x305B0464     //BITS[31:0]
read 0x305B0468     //BITS[63:32] --> MC1-SYNCD_ADDR[47:40] / MC0-ADDR[39:0]

read 0x305B046C     //BITS[31:0]
read 0x305B0470     //BITS[63:32] --> MC1-DATA[63:0]

read 0x305B0474     //[BITS31:0]  --> MC1-ECC C ID[16]

EOF 
 
 
 
 
 
 
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
    wrData := []uint8{ 0x00, 0x00 }
    CPLDdevs := []string{ "CPLD_ELBA0", "CPLD_ELBA1" }

    MCC0EccReg := []EccRegisters { 
        {"ecc_dataout_corrected_1_interrupt", 0 },
        {"ecc_dataout_corrected_0_interrupt", 0 },
        {"MC0-SYNCD_ADDR[47:40] / MC0-ADDR[39:0] ", 0 },
        {"MC0-DATA[63:0]", 0 },
        {"MC0-ECC C ID[16]", 0 },
    }
    MCC1EccReg := []EccRegisters { 
        {"ecc_dataout_corrected_1_interrupt", 0 },
        {"ecc_dataout_corrected_0_interrupt", 0 },
        {"MC1-SYNCD_ADDR[47:40] / MC1-ADDR[39:0] ", 0 },
        {"MC1-DATA[63:0]", 0 },
        {"MC1-ECC C ID[16] ", 0 },
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


    iInfo, rc := i2cinfo.GetI2cInfo(CPLDdevs[elba])
    if rc != errType.SUCCESS {
        dcli.Println("e", "Failed to obtain I2C info of", CPLDdevs[elba])
        err = rc
        return
    }
    wrData[0] = 0x22 
    wrData[1] = 0xA0
    _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access Failed to", CPLDdevs[elba], " ERROR=",errGo); 
        err = errType.FAIL; 
        return
    }
    wrData[0] = 0x21 
    wrData[1] = 0x61
    _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access Failed to", CPLDdevs[elba], " ERROR=",errGo); 
        err = errType.FAIL; 
        return
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

    cmdStr, err = ElbaGetConsoleScriptToExecute(elba)
    if err != errType.SUCCESS {
        dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
        return
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
        MCC0EccReg[0].Val = x
        t = strings.TrimSpace(s[line_number+13][50:len(s[line_number+13])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[1].Val = x
        t = strings.TrimSpace(s[line_number+29][6:len(s[line_number+29])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+33][6:len(s[line_number+33])])
        z,_ :=  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[2].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+37][6:len(s[line_number+37])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+41][6:len(s[line_number+41])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[3].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+45][6:len(s[line_number+45])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[4].Val = x

        t = strings.TrimSpace(s[line_number+26][50:len(s[line_number+26])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[0].Val = x
        t = strings.TrimSpace(s[line_number+27][50:len(s[line_number+27])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[1].Val = x
        t = strings.TrimSpace(s[line_number+49][6:len(s[line_number+49])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+53][6:len(s[line_number+53])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[2].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+57][6:len(s[line_number+57])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+61][6:len(s[line_number+61])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[3].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+65][6:len(s[line_number+65])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[4].Val = x

        {
            for i:=0; i< len(MCC0EccReg); i++ {
                if MCC0EccReg[i].Val > 0 {
                    err = errType.FAIL
                    cli.Printf("e", "ECC ERROR DETECTED: ECC REGISTER SET\n")
                    for j:=0; j< len(MCC0EccReg); j++ {
                        cli.Printf("e", "%s : 0x%x", MCC0EccReg[j].Name, MCC0EccReg[j].Val)
                    }
                    return
                }
            }
        }
        {
            for i:=0; i< len(MCC1EccReg); i++ {
                if MCC1EccReg[i].Val > 0 {
                    err = errType.FAIL
                    cli.Printf("e", "ECC ERROR DETECTED: ECC REGISTER SET\n")
                    for j:=0; j< len(MCC1EccReg); j++ {
                        cli.Printf("e", "%s : 0x%x", MCC1EccReg[j].Name, MCC1EccReg[j].Val)
                    }
                    return
                }
            }
        }
    }
    return
}

/*****************************************************************
#!/bin/bash

/nic/bin/capview << EOF
secure on
read 0x30520020
read 0x305a0020
read 0x30530464
read 0x30530468
read 0x3053046C
read 0x30530470
read 0x30530474
read 0x305B0464
read 0x305B0468
read 0x305B046C
read 0x305B0470
read 0x305B0474

EOF
******************************************************************/ 
func ElbaCheckECC_via_console(elba uint32, calledFromCLI int, InjectError int) (err int) {
    var cmdStr string
    var line_number int 
    var errGo error
    wrData := []uint8{ 0x00, 0x00 }
    CPLDdevs := []string{ "CPLD_ELBA0", "CPLD_ELBA1" }


    const createscript = 
    "pwd\n"+
    "mkdir /data/nic_util\n"+
    "cd /data/nic_util\n"+
    "rm elba_local_read_ecc_reg.sh\n"+
    "echo -e \"#!/bin/bash\" > /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"/nic/bin/capview << EOF\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"secure on\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x30520020\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x305a0020\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x30530464\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x30530468\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x3053046C\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x30530470\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x30530474\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x305B0464\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x305B0468\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x305B046C\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x305B0470\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"read 0x305B0474\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"+ 
    "echo -e \"EOF\" >> /data/nic_util/elba_local_read_ecc_reg.sh\n"
    
    MCC0EccReg := []EccRegisters { 
        {"ecc_dataout_corrected_1_interrupt", 0 },
        {"ecc_dataout_corrected_0_interrupt", 0 },
        {"MC0-SYNCD_ADDR[47:40] / MC0-ADDR[39:0] ", 0 },
        {"MC0-DATA[63:0]", 0 },
        {"MC0-ECC C ID[16]", 0 },
    }
    MCC1EccReg := []EccRegisters { 
        {"ecc_dataout_corrected_1_interrupt", 0 },
        {"ecc_dataout_corrected_0_interrupt", 0 },
        {"MC1-SYNCD_ADDR[47:40] / MC1-ADDR[39:0] ", 0 },
        {"MC1-DATA[63:0]", 0 },
        {"MC1-ECC C ID[16] ", 0 },
    }


    if elba != ELBA0 && elba != ELBA1 {
        fmt.Printf("[ERROR] Elba number passed (%d) is to big\n", elba)
        err = errType.FAIL
        return
    }


    iInfo, rc := i2cinfo.GetI2cInfo(CPLDdevs[elba])
    if rc != errType.SUCCESS {
        dcli.Println("e", "Failed to obtain I2C info of", CPLDdevs[elba])
        err = rc
        return
    }
    wrData[0] = 0x22 
    wrData[1] = 0xA0
    _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access Failed to", CPLDdevs[elba], " ERROR=",errGo); 
        err = errType.FAIL; 
        return
    }
    wrData[0] = 0x21 
    wrData[1] = 0x61
    _ , errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, 0 )
    if errGo != nil {
        dcli.Println("e", "I2C Access Failed to", CPLDdevs[elba], " ERROR=",errGo); 
        err = errType.FAIL; 
        return
    }

    dcli.Printf("i","Making Script on Elba via the console\n")
    if  elba == ELBA0 {
        cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt"
    } else if elba == ELBA1 {
        cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt"
    }     
    file, errGo := os.OpenFile(cmdStr, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if errGo != nil {
        cli.Println("e", "ERROR: Failed to Open %s.   GO ERROR=%v", cmdStr, errGo)
        err = errType.FAIL
        return
    }
    file.WriteString(string(createscript[:]))
    file.Close()
    os.Chmod(cmdStr, 0777)
/*
    cmdStr, err = ElbaGetConsoleScriptToExecute(i)
    if err != errType.SUCCESS {
        dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
        return
    } 
*/    
    cmdStr, err = ElbaGetConsoleScriptToExecute(elba) 
    if err != errType.SUCCESS {
        dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
        return
    }
    output , errGo1 := exec.Command("sh", "-c", cmdStr).Output()
    if errGo1 != nil {
        cli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo1)
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
/*
    cmdStr, err = ElbaGetConsoleScriptToExecute(i)
    if err != errType.SUCCESS {
        dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
        return
    } 
*/
    cmdStr, err = ElbaGetConsoleScriptToExecute(elba)
    if err != errType.SUCCESS {
        dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
        return
    }     
    output , errGo1 = exec.Command("sh", "-c", cmdStr).Output()
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
        MCC0EccReg[0].Val = x
        t = strings.TrimSpace(s[line_number+13][50:len(s[line_number+13])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[1].Val = x
        t = strings.TrimSpace(s[line_number+29][6:len(s[line_number+29])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+33][6:len(s[line_number+33])])
        z,_ :=  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[2].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+37][6:len(s[line_number+37])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+41][6:len(s[line_number+41])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[3].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+45][6:len(s[line_number+45])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC0EccReg[4].Val = x

        t = strings.TrimSpace(s[line_number+26][50:len(s[line_number+26])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[0].Val = x
        t = strings.TrimSpace(s[line_number+27][50:len(s[line_number+27])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[1].Val = x
        t = strings.TrimSpace(s[line_number+49][6:len(s[line_number+49])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+53][6:len(s[line_number+53])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[2].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+57][6:len(s[line_number+57])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        t = strings.TrimSpace(s[line_number+61][6:len(s[line_number+61])])
        z,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[3].Val = x + (z<<32)
        t = strings.TrimSpace(s[line_number+65][6:len(s[line_number+65])])
        x,_ =  strconv.ParseUint(t, 0, 32)
        MCC1EccReg[4].Val = x

        {
            for i:=0; i< len(MCC0EccReg); i++ {
                if MCC0EccReg[i].Val > 0 {
                    err = errType.FAIL
                    cli.Printf("e", "ECC ERROR DETECTED: ECC REGISTER SET\n")
                    for j:=0; j< len(MCC0EccReg); j++ {
                        cli.Printf("e", "%s : 0x%x", MCC0EccReg[j].Name, MCC0EccReg[j].Val)
                    }
                    return
                }
            }
        }
        {
            for i:=0; i< len(MCC1EccReg); i++ {
                if MCC1EccReg[i].Val > 0 {
                    err = errType.FAIL
                    cli.Printf("e", "ECC ERROR DETECTED: ECC REGISTER SET\n")
                    for j:=0; j< len(MCC1EccReg); j++ {
                        cli.Printf("e", "%s : 0x%x", MCC1EccReg[j].Name, MCC1EccReg[j].Val)
                    }
                    return
                }
            }
        }
    }
    return
}

/********************************************************************************************************** 
*  
*  
    PortMap{54, 9  , "ce1",  0, 0, 60, 0},  //Internal Port to ELBA0.3 100G   PHY U1_G0 (LANE 0xF0)    Eth1/2/3 
    PortMap{55, 91 , "ce9",  0, 0, 60, 0},  //Internal Port to ELBA0.2 100G   PHY U1_G0 (LANE 0x0F)    Eth1/2/1
    PortMap{56, 95 , "ce10", 1, 0, 60, 0},  //Internal Port to ELBA1.3 100G   PHY U1_G2 (LANE 0xF0)            Eth1/2/3
    PortMap{57, 13 , "ce2",  1, 0, 60, 0},  //Internal Port to ELBA1.2 100G   PHY U1_G2 (LANE 0x0F)            Eth1/2/1
    PortMap{58, 123, "ce12", 0, 0, 60, 0},  //Internal Port to ELBA0.0 100G   PHY U1_G1 (LANE 0x0F)    Eth1/1/1           
    PortMap{59, 127, "ce13", 1, 0, 60, 0},  //Internal Port to ELBA1.1 100G   PHY U1_G3 (LANE 0xF0)            Eth1/1/3
    PortMap{60, 33,  "ce3",  0, 0, 60, 0},  //Internal Port to ELBA0.1 100G   PHY U1_G1 (LANE 0xF0)    Eth1/1/3
    PortMap{61, 37,  "ce4",  1, 0, 60, 0},  //Internal Port to ELBA1.0 100G   PHY U1_G3 (LANE 0x0F)            Eth1/1/1
*  
*  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
* ID                                      Name      IfIndex     Speed  MAC-Info  FEC       AutoNeg   MTU   Pause  Pause  Debounce  State       Transceiver       NumLinkDown LinkSM              Loopback 
*                                                                                Cfg/Oper  Cfg/Oper        Type   Tx/Rx  (msecs)   Admin/Oper                                                             
* --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
* 01000211-0000-0000-4242-049081002f9a    Eth1/2/1  0x11020001  100G   0/4/2       RS/RS    F/F      9412  NONE    F/F   0           UP/UP     REMOVED           0           UP                  NONE     
* 03000211-0000-0000-4242-049081002f9a    Eth1/2/3  0x11020003  100G   0/6/2       RS/RS    F/F      9412  NONE    F/F   0           UP/UP     REMOVED           0           UP                  NONE     
* 01000111-0000-0000-4242-049081002f9a    Eth1/1/1  0x11010001  100G   0/0/2       RS/RS    F/F      9412  NONE    F/F   0           UP/UP     REMOVED           0           UP                  NONE     
* 03000111-0000-0000-4242-049081002f9a    Eth1/1/3  0x11010003  100G   0/2/2       RS/RS    F/F      9412  NONE    F/F   0           UP/UP     REMOVED           0           UP                  NONE     
* 
* No. of ports : 4
************************************************************************************************************/ 
type LinkFlap_s struct {
    ethDev  string 
    GearBoxNumber int
    GearBoxLanes  uint32
    LinkFlaps     int 
}

func Elba_Check_Link_Flap_Count(elba int, useCLI int) (err int) {
    var ethCount int
    var cmdStr string
    Elba_0_Info := []LinkFlap_s{ { "Eth1/1/1", 1, 0x0F, 0 }, 
                                 { "Eth1/1/3", 1, 0xF0, 0 },
                                 { "Eth1/2/1", 0, 0x0F, 0 },  
                                 { "Eth1/2/3", 0, 0xF0, 0 },  
                               }
    Elba_1_Info := []LinkFlap_s{ { "Eth1/1/1", 3, 0x0F, 0 }, 
                                 { "Eth1/1/3", 3, 0xF0, 0 },
                                 { "Eth1/2/1", 2, 0x0F, 0 },  
                                 { "Eth1/2/3", 2, 0xF0, 0 },  
                               }
    ElbaFlapInfo := Elba_0_Info

    err = errType.SUCCESS

    if  elba == 0 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 /nic/bin/pdsctl show port status"
        cli.Printf("i", "ELBA0 LINK STATUS\n")
    } else if elba == 1 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 /nic/bin/pdsctl show port status"
        cli.Printf("i", "ELBA1 LINK STATUS\n")
        ElbaFlapInfo = Elba_1_Info
    } else {
        cli.Printf("e", "Invalid Elba Number Passed (%d)", elba)
        err = errType.FAIL
        return
    }

    //Ping Elba to make sure the network is up
    err = ElbaPing(uint32(elba)) 
    if err != errType.SUCCESS {
        dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed.  Cannot communicate with elba to check number of link flaps!\n", elba)
        goto endLinkFlapTest
    } else {
        //execute command to get link flap number
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
        }
        cli.Printf("i", "%s\n", output)

        s := strings.Split(string(output), "\n")
        for _, temp := range s {
            if strings.Contains(temp, "Eth")==true {
                ethCount++

                temp_s := strings.TrimSpace(string(temp[155:165]))
                flaps, errGo := strconv.Atoi(string(temp_s))
                if errGo != nil {
                    cli.Printf("e", "strconv atoi failed")
                    err = errType.FAIL
                    goto endLinkFlapTest
                }
                for cnt, elbinfo := range(ElbaFlapInfo) {
                    if strings.Contains(temp, elbinfo.ethDev) == true {
                        ElbaFlapInfo[cnt].LinkFlaps=flaps
                    }
                }

            }
        }
    }


    for number, elbinfo := range(ElbaFlapInfo) {
        var tmpStr string
        if elbinfo.LinkFlaps > 0 {
            err = errType.FAIL
            tmpStr = "FAILED"
        } else {
            tmpStr = "PASSED"
        }
        cli.Printf("i", " Elba-%d Port-%d < -- > GB-%d Lanes 0x%.02x --> Link Flaps = %d (%s)\n", elba, number, elbinfo.GearBoxNumber,elbinfo.GearBoxLanes, elbinfo.LinkFlaps, tmpStr)
    }

    if (ethCount != 4) {
        cli.Printf("e", "Error:  Did not count 4 ethernet devices on Elba\n")
        err = errType.FAIL
        goto endLinkFlapTest
    }


    

endLinkFlapTest:

    if err == errType.SUCCESS {
        cli.Printf("i", "SWITCH LINK FLAP TEST PASSED\n")
    } else {
        cli.Printf("e", "SWITCH LINK FLAP TEST FAILED\n")
    }
    

    return
}


//ce12, ce3, ce9, ce1, ce4, ce13, ce2, ce10
//journalctl -u switchd | grep -e "link_scan_internal" | grep -w "status=0" | grep "port\[1\]" | wc -l
func TD3_Check_Link_Flap() (err int) {

    port_wc_check := []string{
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port\\[123\\]\" | wc -l",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[33]\" | wc -l",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[91]\" | wc -l",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[9]\" | wc -l",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[37]\" | wc -l",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[127]\" | wc -l",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[13]\" | wc -l",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[95]\" | wc -l",
    }

    port_check := []string{
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port\\[123\\]\"",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[33]\"",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[91]\"",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[9]\"",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[37]\"",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[127]\"",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[13]\"",
        "journalctl -u switchd | grep -e \"link_scan_internal\" | grep -w \"status=0\" | grep \"port[95]\"",
    }

    cli.Printf("i", "CHECKING LINK FLAPS FROM TD3 TO EACH ELBA\n")

    for i, _ := range port_wc_check {
        output , errGo := exec.Command("sh", "-c", port_wc_check[i]).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", port_wc_check[i], errGo)
            err = errType.FAIL
            return
        }
        wc64_t, _ := strconv.ParseUint(strings.TrimSpace(string(output)), 0, 64)
        
        if wc64_t > 0 {
            output , errGo := exec.Command("sh", "-c", port_check[i]).Output()
            if errGo != nil {
                dcli.Printf("e","Cmd %s failed! %v", port_check[i], errGo)
                err = errType.FAIL
                return
            }
            cli.Printf("e", "%s\n", output)
            cli.Printf("e", "Error:  Detect TD3 Ports to Elba that link flapped\n")
            
        }

    } //end range loop

    err = errType.SUCCESS



    if err == errType.SUCCESS {
        cli.Printf("i", "TD3 LINK FLAP TEST PASSED\n")
    } else {
        cli.Printf("e", "TD3 LINK FLAP TEST FAILED\n")
    }

    return
}




//journalctl -u switchd | grep -e "link_scan_internal" | grep -w "status=0"


/* 
var gbLoopbackLevel_map = map[int]string{
    GB_LOOPBACK_LINE_SIDE : "Line",
    GB_LOOPBACK_HOST_SIDE : "Host",
} 
*/ 
/* 
Eth1/1/3FRAMES RX OK             0
        FRAMES RX ALL            0
        FRAMES RX BAD FCS        0
        FRAMES RX BAD ALL        0
        OCTETS RX OK             0
        OCTETS RX ALL            0
        FRAMES RX UNICAST        0
        FRAMES RX MULTICAST      0
        FRAMES RX BROADCAST      0
        FRAMES RX PAUSE          0
        FRAMES RX BAD LENGTH     0
        FRAMES RX UNDERSIZED     0
        FRAMES RX OVERSIZED      0
        FRAMES RX FRAGMENTS      0
        FRAMES RX JABBER         0
        FRAMES RX PRIPAUSE       0
        FRAMES RX STOMPED CRC    0
        FRAMES RX TOO LONG       0
        FRAMES RX VLAN GOOD      0
        FRAMES RX DROPPED        0
//20 
        FRAMES RX LESS THAN 64B  0
        FRAMES RX 64B            0
        FRAMES RX 65B 127B       0
        FRAMES RX 128B 255B      0
        FRAMES RX 256B 511B      0
        FRAMES RX 512B 1023B     0
        FRAMES RX 1024B 1518B    0
        FRAMES RX 1519B 2047B    0
        FRAMES RX 2048B 4095B    0
        FRAMES RX 4096B 8191B    0
        FRAMES RX 8192B 9215B    0
        FRAMES RX OTHER          0
        FRAMES TX OK             0
        FRAMES TX ALL            0
        FRAMES TX BAD            0
        OCTETS TX OK             0
        OCTETS TX TOTAL          0
        FRAMES TX UNICAST        0
        FRAMES TX MULTICAST      0
        FRAMES TX BROADCAST      0
 40
        FRAMES TX PAUSE          0
        FRAMES TX PRIPAUSE       0
        FRAMES TX VLAN           0
        FRAMES TX LESS THAN 64B  0
        FRAMES TX 64B            0
        FRAMES TX 65B 127B       0
        FRAMES TX 128B 255B      0
        FRAMES TX 256B 511B      0
        FRAMES TX 512B 1023B     0
        FRAMES TX 1024B 1518B    0
        FRAMES TX 1519B 2047B    0
        FRAMES TX 2048B 4095B    0
        FRAMES TX 4096B 8191B    0
        FRAMES TX 8192B 9215B    0
        FRAMES TX OTHER          0
        FRAMES TX PRI 0          0
        FRAMES TX PRI 1          0
        FRAMES TX PRI 2          0
        FRAMES TX PRI 3          0
        FRAMES TX PRI 4          0
60 
        FRAMES TX PRI 5          0
        FRAMES TX PRI 6          0
        FRAMES TX PRI 7          0
        FRAMES RX PRI 0          0
        FRAMES RX PRI 1          0
        FRAMES RX PRI 2          0
        FRAMES RX PRI 3          0
        FRAMES RX PRI 4          0
        FRAMES RX PRI 5          0
        FRAMES RX PRI 6          0
        FRAMES RX PRI 7          0
        TX PRIPAUSE 0 1US COUNT  0
        TX PRIPAUSE 1 1US COUNT  0
        TX PRIPAUSE 2 1US COUNT  0
        TX PRIPAUSE 3 1US COUNT  0
        TX PRIPAUSE 4 1US COUNT  0
        TX PRIPAUSE 5 1US COUNT  0
        TX PRIPAUSE 6 1US COUNT  0
        TX PRIPAUSE 7 1US COUNT  0
        RX PRIPAUSE 0 1US COUNT  0
 80
        RX PRIPAUSE 1 1US COUNT  0
        RX PRIPAUSE 2 1US COUNT  0
        RX PRIPAUSE 3 1US COUNT  0
        RX PRIPAUSE 4 1US COUNT  0
        RX PRIPAUSE 5 1US COUNT  0
        RX PRIPAUSE 6 1US COUNT  0
        RX PRIPAUSE 7 1US COUNT  0
        RX PAUSE 1US COUNT       0
        FRAMES TX TRUNCATED      0
        RSFEC CORRECTABLE WORD   0
 90
        RSFEC CH SYMBOL ERR CNT  0
 
*/ 


//type ElbaMIBstats struct {
//..Eth1/2/1 --> PORT2
//..Eth1/2/3 --> PORT3
//..Eth1/1/1 --> PORT0
//..Eth1/1/3 --> PORT1
func Elba_Get_Mac_Stats_Into_Struct(elba int, useCLI int) (mibs []ElbaMIBstats, err int) {
    var cmdStr string
    var i,j int = 0,0
    err = errType.SUCCESS
    var port0 ElbaMIBstats
    var port1 ElbaMIBstats
    var port2 ElbaMIBstats
    var port3 ElbaMIBstats
    var port_ptr *ElbaMIBstats 



    if  elba == 0 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 /nic/bin/pdsctl show port statistics"
    } else if elba == 1 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 /nic/bin/pdsctl show port statistics"
        //ElbaFlapInfo = Elba_1_Info
    } else {
        cli.Printf("e", "Invalid Elba Number Passed (%d)", elba)
        err = errType.FAIL
        return
    }

    //Ping Elba to make sure the network is up
    err = ElbaPing(uint32(elba)) 
    if err != errType.SUCCESS {
        dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed.  Cannot communicate with elba to check number of link flaps!\n", elba)
    } else {
        t1 := time.Now()
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
        }
        t2 := time.Now()
        diff := t2.Sub(t1)

        fmt.Println(" Elapsed Time=",diff)

        //cli.Printf("i", "%s\n", output)
        s := strings.Split(string(output), "\n")
        i=0
        j=0
        for cnt, temp := range s {
            if cnt<3 { continue }
            x, _ := strconv.ParseUint(strings.TrimSpace(temp[32:]), 0, 64)
            switch (j) {
                case 0: port_ptr = &port2
                case 1: port_ptr = &port3
                case 2: port_ptr = &port0
                case 3: port_ptr = &port1
            }
            switch (i) {
                case 0: port_ptr.FRAMES_RX_OK = x
                case 1: port_ptr.FRAMES_RX_ALL = x
                case 2: port_ptr.FRAMES_RX_BAD_FCS = x           
                case 3: port_ptr.FRAMES_RX_BAD_ALL = x
                case 4: port_ptr.OCTETS_RX_OK = x
                case 5: port_ptr.OCTETS_RX_ALL = x           
                case 6: port_ptr.FRAMES_RX_UNICAST = x
                case 7: port_ptr.FRAMES_RX_MULTICAST = x
                case 8: port_ptr.FRAMES_RX_BROADCAST = x           
                case 9: port_ptr.FRAMES_RX_PAUSE = x
                case 10: port_ptr.FRAMES_RX_BAD_LENGTH = x
                case 11: port_ptr.FRAMES_RX_UNDERSIZED = x           
                case 12: port_ptr.FRAMES_RX_OVERSIZED = x
                case 13: port_ptr.FRAMES_RX_UNDERSIZED = x           
                case 14: port_ptr.FRAMES_RX_FRAGMENTS = x
                case 15: port_ptr.FRAMES_RX_JABBER = x           
                case 16: port_ptr.FRAMES_RX_STOMPED_CRC = x
                case 17: port_ptr.FRAMES_RX_TOO_LONG = x           
                case 18: port_ptr.FRAMES_RX_VLAN_GOOD = x
                case 19: port_ptr.FRAMES_RX_DROPPED = x     
                case 20: port_ptr.FRAMES_RX_LESS_THAN_64B = x                                     
                case 21: port_ptr.FRAMES_RX_64B = x                                     
                case 22: port_ptr.FRAMES_RX_65B_127B = x                                     
                case 23: port_ptr.FRAMES_RX_128B_255B = x                                     
                case 24: port_ptr.FRAMES_RX_256B_511B = x                                     
                case 25: port_ptr.FRAMES_RX_512B_1023B = x                                     
                case 26: port_ptr.FRAMES_RX_1024B_1518B = x                                     
                case 27: port_ptr.FRAMES_RX_1519B_2047B = x                                     
                case 28: port_ptr.FRAMES_RX_2048B_4095B = x                                     
                case 29: port_ptr.FRAMES_RX_4096B_8191B = x    
                case 30: port_ptr.FRAMES_RX_8192B_9215B = x
                case 31: port_ptr.FRAMES_RX_OTHER = x
                case 32: port_ptr.FRAMES_TX_OK = x
                case 33: port_ptr.FRAMES_TX_ALL = x
                case 34: port_ptr.FRAMES_TX_BAD = x
                case 35: port_ptr.OCTETS_TX_OK = x
                case 36: port_ptr.OCTETS_TX_TOTAL = x
                case 37: port_ptr.FRAMES_TX_UNICAST = x
                case 38: port_ptr.FRAMES_TX_MULTICAST = x
                case 39: port_ptr.FRAMES_TX_BROADCAST = x
                case 40: port_ptr.FRAMES_TX_PAUSE = x
                case 41: port_ptr.FRAMES_TX_PRIPAUSE = x
                case 42: port_ptr.FRAMES_TX_VLAN = x
                case 43: port_ptr.FRAMES_TX_LESS_THAN_64B = x
                case 44: port_ptr.FRAMES_TX_64B = x
                case 45: port_ptr.FRAMES_TX_65B_127B = x
                case 46: port_ptr.FRAMES_TX_128B_255B = x
                case 47: port_ptr.FRAMES_TX_256B_511B = x
                case 48: port_ptr.FRAMES_TX_512B_1023B = x
                case 49: port_ptr.FRAMES_TX_1024B_1518B = x
                case 50: port_ptr.FRAMES_TX_1519B_2047B = x           
                case 51: port_ptr.FRAMES_TX_2048B_4095B = x           
                case 52: port_ptr.FRAMES_TX_4096B_8191B = x           
                case 53: port_ptr.FRAMES_TX_8192B_9215B = x           
                case 54: port_ptr.FRAMES_TX_OTHER = x           
                case 55: port_ptr.FRAMES_TX_PRI_0 = x           
                case 56: port_ptr.FRAMES_TX_PRI_1 = x           
                case 57: port_ptr.FRAMES_TX_PRI_2 = x           
                case 58: port_ptr.FRAMES_TX_PRI_3 = x           
                case 59: port_ptr.FRAMES_TX_PRI_4 = x  
                case 60: port_ptr.FRAMES_TX_PRI_5 = x
                case 61: port_ptr.FRAMES_TX_PRI_6 = x
                case 62: port_ptr.FRAMES_TX_PRI_7 = x
                case 63: port_ptr.FRAMES_RX_PRI_0 = x
                case 64: port_ptr.FRAMES_RX_PRI_1 = x
                case 65: port_ptr.FRAMES_RX_PRI_2 = x
                case 66: port_ptr.FRAMES_RX_PRI_3 = x
                case 67: port_ptr.FRAMES_RX_PRI_4 = x
                case 68: port_ptr.FRAMES_RX_PRI_5 = x
                case 69: port_ptr.FRAMES_RX_PRI_6 = x
                case 70: port_ptr.FRAMES_RX_PRI_7 = x
                case 71: port_ptr.TX_PRIPAUSE_0_COUNT = x
                case 72: port_ptr.TX_PRIPAUSE_1_COUNT = x
                case 73: port_ptr.TX_PRIPAUSE_2_COUNT = x
                case 74: port_ptr.TX_PRIPAUSE_3_COUNT = x
                case 75: port_ptr.TX_PRIPAUSE_4_COUNT = x
                case 76: port_ptr.TX_PRIPAUSE_5_COUNT = x
                case 77: port_ptr.TX_PRIPAUSE_6_COUNT = x
                case 78: port_ptr.TX_PRIPAUSE_7_COUNT = x
                case 79: port_ptr.RX_PRIPAUSE_0_COUNT = x
                case 80: port_ptr.RX_PRIPAUSE_1_COUNT = x
                case 81: port_ptr.RX_PRIPAUSE_2_COUNT = x
                case 82: port_ptr.RX_PRIPAUSE_3_COUNT = x
                case 83: port_ptr.RX_PRIPAUSE_4_COUNT = x
                case 84: port_ptr.RX_PRIPAUSE_5_COUNT = x
                case 85: port_ptr.RX_PRIPAUSE_6_COUNT = x
                case 86: port_ptr.RX_PRIPAUSE_7_COUNT = x
                case 87: port_ptr.RX_PAUSE_1US_COUNT = x
                case 88: port_ptr.FRAMES_TX_TRUNCATED = x
                case 89: port_ptr.RSFEC_CORRECTABLE_WORD = x
                case 90: port_ptr.RSFEC_CH_SYMBOL_ERR_CNT = x            

            }
            i++
            if i>90 {  //91 stats, roll back to next ports stats afte we go through all 91 for a port
                i=0;
                j++;
            }
            if j == 4 {  //4 ports, break once we are done
                break
            }
        }
    }
    mibs = append(mibs, port0) 
    mibs = append(mibs, port1)
    mibs = append(mibs, port2)
    mibs = append(mibs, port3)
    return
}


func Elba_Get_Mac_Stats(elba int) (err int) {
    var cmdStr string
    err = errType.SUCCESS



    if  elba == 0 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 /nic/bin/pdsctl show port statistics"
    } else if elba == 1 {
        cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 /nic/bin/pdsctl show port statistics"
        //ElbaFlapInfo = Elba_1_Info
    } else {
        cli.Printf("e", "Invalid Elba Number Passed (%d)", elba)
        err = errType.FAIL
        return
    }

    //Ping Elba to make sure the network is up
    err = ElbaPing(uint32(elba)) 
    if err != errType.SUCCESS {
        dcli.Printf("e","[ERROR] Elba-%d Ping Test Failed.  Cannot communicate with elba to check number of link flaps!\n", elba)
    } else {
        t1 := time.Now()
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
        }
        t2 := time.Now()
        diff := t2.Sub(t1)

        fmt.Println(" Elapsed Time=",diff)

        //fmt.Printf(" %T\n", output)

        cli.Printf("i", "%s\n", output)
    }

    return
}


func Elba_Check_Pci_Link(elba int, warnOnLinkDownGrade int, useCLI int) (err int) {
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
                if warnOnLinkDownGrade > 0 {
                    s := fmt.Sprintf("[WARN] ELBA-%d LINK SPEED IS NOT 8GT/s x4 -->  %s\n", elba, temp)
                    printf("e", s, useCLI)
                } else {
                    s := fmt.Sprintf("[ERROR] ELBA-%d LINK SPEED IS NOT 8GT/s x4 -->  %s\n", elba, temp)
                    printf("e", s, useCLI)
                    err = errType.FAIL
                }
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
    if err == errType.SUCCESS {
        dcli.Printf("i", "SWITCH ELBA_RTC TEST PASSED\n")
    } else {
        dcli.Printf("e", "SWITCH ELBA_RTC TEST FAILED\n")
    }
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


/********************************************************************************* 
* 
* Get the main board PCA Rev. 
* Needed to see if the board switched from SuperIO UART to FPGA based uart system 
* Example --> pca_rev: '0x07' 
* 
*********************************************************************************/ 
func GetFRU_PCA() (pcaRev int, err int) {
    var cmdStr string
    cmdStr = " vtysh -c \"diag\" -c \"diag mfgread chassis_ul 1\" | grep pca_rev"
    output , errGo := exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
        err = errType.FAIL
        return
    }
    
    //Check if there is a pca_rev.  This will tell us the command executed properly
    //Some older test systems may have a blank pca rev.  i.e. not programmed yet
    //Need to handle that scenario
    if i := strings.Index(string(output), "pca_rev"); i>0 {
        //Check for 0x in the pca rev to get the offset for converting string to an uint
        if i := strings.Index(string(output), "0x"); i>0 {
            pcaRev_s := output[i:i+4]
            pcaRev_t, _ := strconv.ParseUint(string(pcaRev_s), 0, 32)
            pcaRev = int(pcaRev_t)
        } else {
          //Unprogrammed PCA Rev
        dcli.Printf("e","Cmd %s failed! Found PCA Rev, but it appears to be blank.  The chassis FRU needs a valid programmed PCA Rev. --> %s ", cmdStr, output)
        err = errType.FAIL
        }
    } else {
        dcli.Printf("e","Cmd %s failed! Could not find valid PCA Revision in output --> %s ", cmdStr, output)
        err = errType.FAIL
    }
    
    return
} 


func FPGA_Strapping_Test(expected_rev int) (err int) {
    var strapping uint32
    err = errType.SUCCESS

    dcli.Printf("i", "Starting Taor Resistor Strapping Test\n")

    strapping, _ = taorfpga.GetResistorStrapping() 

    dcli.Printf("i", "Strapping Rev=0x%x  Epxected=0x%x\n", strapping , expected_rev)
    if strapping != uint32(expected_rev) {
        dcli.Printf("e", "SWITCH FPGA_STRAPPING TEST FAILED\n")
        err = errType.FAIL
    } else {
        dcli.Printf("i", "SWITCH FPGA_STRAPPING TEST PASSED\n")
    }

    return
}


/********************************************************************************* 
* 
* Need to touch up Trident3 and Elba VRM's to fix some of the sensor output values
* 
*********************************************************************************/ 
func VRMfix() (err int) {

    err = TD3_VRM_FIX("TDNT_PDVDD")
    cli.Printf("i", "\n")
    err |= ElbaVRMfix()
    cli.Printf("i", "\n")
    err |= TD3_Check_AVS_Programming("TDNT_PDVDD")

    if err == errType.SUCCESS {
        cli.Printf("i", "SWITCH VRM_FIX TEST PASSED\n")
    } else {
        cli.Printf("e", "SWITCH VRM_FIX TEST FAILED\n")
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
    var retry, MaxRetry int = 0, 2
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

retrysettingVRM:
    dcli.Printf("i","Writing VRM\n")
    //This file will get executed by the script "exec_cmd_elba0_via_console.sh" below
    cmdStr = fmt.Sprintf("pwd\ni2cset -y -f 0 0x62 0x00 0;i2cset -y -f 0 0x62 0xDA 0x55 0x50 i;i2cset -y -f 0 0x62 0x00 1;i2cset -y -f 0 0x62 0xDA 0x19 0x2A i;i2cset -y -f 0 0x62 0x9A 0x02 0x17 0x00 i;i2cset -y -f 0 0x62 0x9B 0x02 0x64 0x02 i;i2cset -y -f 0 0x62 0x00 0\n")
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
        dcli.Printf("i", "Elba-%d Executing Script to Set Registers in VRM\n", i)
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        } 
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", string(output))
    }


    dcli.Printf("i","Updating Check VRM Script\n")
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
        cmdStr, err = ElbaGetConsoleScriptToExecute(i)
        if err != errType.SUCCESS {
            dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
            return
        }  
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
            err = errType.FAIL
            return
        }
        dcli.Printf("i", "%s\n", string(output))
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
        for x:=0; x<len(expected); x++ {
            dcli.Printf("i"," %x  %x\n", expected[x], read[x])
            if expected[x] != read[x] {
                if retry < MaxRetry {
                    retry++
                    dcli.Printf("i","WARN: Register Mismatch.  Will Try setting the registers again --> VRM Register-0x%x  Read=%x.  Expected=%x", register[x], expected[x], read[x] )
                    goto retrysettingVRM
                } else {
                    dcli.Printf("e","ERROR: VRM Register-%d  Read=%x.  Expected=%x", register[x], expected[x], read[x] )
                    err = errType.FAIL
                    return
                }
            }
        }
    }

    
    //This file will get executed by the script "exec_cmd_elba0_via_console.sh" below
    for i=forStart; i < forEnd; i++ {
    dcli.Printf("i", "Elba-%d Executing Script to Write Changes to NVRAM in VRM\n", i)
        for retry=0; retry<3; retry++ {
            cmdStr = fmt.Sprintf("pwd\ni2cset -y -f 0 0x62 0x00 0;i2cset -y -f 0 0x62 0x11\n")
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
                if elbafailmask & (1<<i) == (1<<i) {
                    continue
                }
                
                cmdStr, err = ElbaGetConsoleScriptToExecute(i)
                if err != errType.SUCCESS {
                    dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
                    return
                } 
                output , errGo := exec.Command("sh", "-c", cmdStr).Output()
                if errGo != nil {
                    dcli.Printf("e","Cmd %s failed! %v", cmdStr, errGo)
                    err = errType.FAIL
                    return
                }
                dcli.Printf("i", string(output))
            }
        }
    }
    //dcli.Printf("i", "err = %d", err)
    return
}

/************************************************************************ 
*  
* Set vref_trim for P3V3 to adjust it to +5% permanently 
* 
/***********************************************************************/ 
func TaorminaP3V3trimFix() (err int) {
    var devName string = "P3V3"
    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to set i2c mux for %s", devName)
        return
    }
    err = tps544c20.TaorminaSetVrefTrim(devName)
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
    var retries int = 5
    var data32 uint32
    var rc int
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

    for i:=0; i<retries; i++ {
        data32, rc = td3.ReadReg("TD3", "TOP_AVS_SEL_REG")
        if rc == errType.SUCCESS {
            break
        }
        if i == (retries -1) {
            if rc != errType.SUCCESS {
                cmdStr := "dmesg | tail -n 150"
                output , errGo := exec.Command("sh", "-c", cmdStr).Output()
                if errGo != nil {
                    dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                    err = errType.FAIL
                    return
                }
                dcli.Printf("i", "%s\n", string(output))

                cmdStr = "ps -A"
                output , errGo = exec.Command("sh", "-c", cmdStr).Output()
                if errGo != nil {
                    dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                    err = errType.FAIL
                    return
                }
                dcli.Printf("i", "%s\n", string(output))

                cmdStr = "journalctl -u switchd"
                output , errGo = exec.Command("sh", "-c", cmdStr).Output()
                if errGo != nil {
                    dcli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                    err = errType.FAIL
                    return
                }
                dcli.Printf("i", "%s\n", string(output))

                dcli.Println("e", "Failed to read TOP_AVS_SEL_REG from the bcm shell")
                err = rc
                return
            } 
        }
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


/* 
 
 
ovs-appctl -t ops-switchd l1/phy_loopback

this should dump the help for the other params

         ds_put_format(ds,
                       "Syntax: <phy_id> <lane_map> <lb_side> <lb_mode> "
                       "<ena_dis>\n");
         ds_put_format(ds, "<phy_id> Phy index 0..6\n");
         ds_put_format(ds, "<lane_map> lane map\n");
         ds_put_format(ds, "<lb_side>  0-line side, 1-host side\n");
         ds_put_format(
             ds, "<lb_mode>  1-digital PMD loopback, 2-remote PMD loopback\n");
         ds_put_format(ds, "<ena_dis>  0-disable, 1-enable\n"); 
 
ovs-appctl l1/phy_loopback 0 0x0F 0 1 1
ovs-appctl l1/phy_loopback 0 0xF0 0 1 1
ovs-appctl l1/phy_loopback 1 0x0F 0 1 1
ovs-appctl l1/phy_loopback 1 0xF0 0 1 1
ovs-appctl l1/phy_loopback 2 0x0F 0 1 1
ovs-appctl l1/phy_loopback 2 0xF0 0 1 1
ovs-appctl l1/phy_loopback 3 0x0F 0 1 1
ovs-appctl l1/phy_loopback 3 0xF0 0 1 1

ovs-appctl l1/phy_loopback 0 0x0F 1 2 1
ovs-appctl l1/phy_loopback 0 0xF0 1 2 1
ovs-appctl l1/phy_loopback 1 0x0F 1 2 1
ovs-appctl l1/phy_loopback 1 0xF0 1 2 1
ovs-appctl l1/phy_loopback 2 0x0F 1 2 1
ovs-appctl l1/phy_loopback 2 0xF0 1 2 1
ovs-appctl l1/phy_loopback 3 0x0F 1 2 1
ovs-appctl l1/phy_loopback 3 0xF0 1 2 1 
 
    GB_LOOPBACK_LINE_SIDE = 0
    GB_LOOPBACK_HOST_SIDE = 1

    GB_DIGITAL_PMD_LOOPBACK = 1
    GB_REMOTE_PMD_LOOPBACK = 2

    GB_LOOPBACK_DISABLE = 0
    GB_LOOPBACK_ENABLE = 1
 
    HOST SIDE IS TD3
    LINE SIDE IS ELBA
*/
func BCM_GearBox_Set_Loopback(loopbackLevel int, loopbackmode int, enable int) (err int) {

    phymask := [][]byte { {0, 0x0F},
                          {0, 0xF0},
                          {1, 0x0F},
                          {1, 0xF0},
                          {2, 0x0F},
                          {2, 0xF0},
                          {3, 0x0F},
                          {3, 0xF0}}

    if ( loopbackLevel > GB_LOOPBACK_HOST_SIDE ) {
        cli.Printf("e", " ERROR BCM_GearBox_Set_Loopback: LOOPBACK LEVEL PASSED (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_LINE_SIDE=%d.  GB_LOOPBACK_HOST_SIDE=%d  ", loopbackLevel, GB_LOOPBACK_LINE_SIDE, GB_LOOPBACK_HOST_SIDE)
        err = errType.FAIL
        return
    }

    if ( loopbackmode != GB_DIGITAL_PMD_LOOPBACK ) && (loopbackmode != GB_REMOTE_PMD_LOOPBACK) {
        cli.Printf("e", " ERROR BCM_GearBox_Set_Loopback: loopbackmode (%d), IS NOT VALID. ARG MUST BE GB_DIGITAL_PMD_LOOPBACK=%d.  GB_REMOTE_PMD_LOOPBACK=%d  ", loopbackmode, GB_DIGITAL_PMD_LOOPBACK, GB_REMOTE_PMD_LOOPBACK)
        err = errType.FAIL
        return
    }

    if ( enable != GB_LOOPBACK_DISABLE ) && (enable != GB_LOOPBACK_ENABLE) {
        cli.Printf("e", " ERROR BCM_GearBox_Set_Loopback: loopbackmode (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_DISABLE=%d.  GB_REMOTE_PMD_LOOPBACK=%d  ", enable, GB_LOOPBACK_DISABLE, GB_LOOPBACK_ENABLE)
        err = errType.FAIL
        return
    }

    if (enable == GB_LOOPBACK_DISABLE) {
        cli.Printf("i", "Clearing %s %s Loopback Level for all GB.\n", gbLoopbackLevel_map[loopbackLevel],  gbLoopbackMode_map[loopbackmode])
    } else {
        cli.Printf("i", "Setting %s %s Loopback Level for all GB.\n", gbLoopbackLevel_map[loopbackLevel],  gbLoopbackMode_map[loopbackmode])
    }
                          
    for _, pair := range(phymask) {
        cmdStr := fmt.Sprintf("ovs-appctl l1/phy_loopback %d 0x%x %d %d %d\n", pair[0], pair[1], loopbackLevel, loopbackmode, enable)
        //fmt.Printf("'%s'\n", cmdStr)

        _, errGo := exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
            err = errType.FAIL
            return
        }
        time.Sleep(time.Duration(1500) * time.Millisecond)
    }

    return
}


/************************************************************************************* 
* 
* NOTE: Uses the same defines as BCM_GearBox_Set_Loopback. 
*       The only difference is the phy number passed to ovs-appctl
*  
*       HOST = TD3
*       LINE = QSFP
*
*      //RETIMER.   LINE SIDE DIGITAL WORKS (0 1 1)
*      //RETIMER.   HOST REMOTEL WORKS (1 2 1)
*
* 
**************************************************************************************/ 
func BCM_Retimer_Set_Loopback(loopbackLevel int, loopbackmode int, enable int) (err int) {

    phymask := [][]byte { {4, 0x0F},
                          {4, 0xF0},
                          {5, 0x0F},
                          {5, 0xF0},
                          {6, 0x0F},
                          {6, 0xF0}}

    if ( loopbackLevel > GB_LOOPBACK_HOST_SIDE ) {
        cli.Printf("e", " ERROR BCM_Retimer_Set_Loopback: LOOPBACK LEVEL PASSED (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_LINE_SIDE=%d.  GB_LOOPBACK_HOST_SIDE=%d  ", loopbackLevel, GB_LOOPBACK_LINE_SIDE, GB_LOOPBACK_HOST_SIDE)
        err = errType.FAIL
        return
    }

    if ( loopbackmode != GB_DIGITAL_PMD_LOOPBACK ) && (loopbackmode != GB_REMOTE_PMD_LOOPBACK) {
        cli.Printf("e", " ERROR BCM_Retimer_Set_Loopback: loopbackmode (%d), IS NOT VALID. ARG MUST BE GB_DIGITAL_PMD_LOOPBACK=%d.  GB_REMOTE_PMD_LOOPBACK=%d  ", loopbackmode, GB_DIGITAL_PMD_LOOPBACK, GB_REMOTE_PMD_LOOPBACK)
        err = errType.FAIL
        return
    }

    if ( enable != GB_LOOPBACK_DISABLE ) && (enable != GB_LOOPBACK_ENABLE) {
        cli.Printf("e", " ERROR BCM_Retimer_Set_Loopback: loopbackmode (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_DISABLE=%d.  GB_REMOTE_PMD_LOOPBACK=%d  ", enable, GB_LOOPBACK_DISABLE, GB_LOOPBACK_ENABLE)
        err = errType.FAIL
        return
    }

    if (enable == GB_LOOPBACK_DISABLE) {
        cli.Printf("i", "Clearing %s %s Loopback Level for all Retimers.\n", gbLoopbackLevel_map[loopbackLevel],  gbLoopbackMode_map[loopbackmode])
    } else {
        cli.Printf("i", "Setting %s %s Loopback Level for all Retimers.\n", gbLoopbackLevel_map[loopbackLevel],  gbLoopbackMode_map[loopbackmode])
    }
                          
    for _, pair := range(phymask) {
        cmdStr := fmt.Sprintf("ovs-appctl l1/phy_loopback %d 0x%x %d %d %d\n", pair[0], pair[1], loopbackLevel, loopbackmode, enable)
        //fmt.Printf("'%s'\n", cmdStr)

        _, errGo := exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
            err = errType.FAIL
            return
        }
        time.Sleep(time.Duration(1500) * time.Millisecond)
    }

    return
}


/*************************************************************************************** 
* 
* NOTE: This is for the snake and prbs test.   So it only check GB Loopback back to TD3.
*       It does not check for loopback in Elba's direction
* 
* ovs-appctl l1/phy_status 0 0xF0 
*  
*  HOST SIDE IS TD3
*  LINE SIDE IS ELBA
*  
*  ovs-appctl l1/phy_status %d | grep 'Digital Loopbac'
*        Digital Loopback status   disabled        **LINE PORT0 0x3
*        Digital Loopback status   disabled        **HOST PORT0 0x0F
*        Digital Loopback status   disabled        **LINE PORT1 0xC
*        Digital Loopback status   disabled        **HOST PORT1 0xF0
*
* 
****************************************************************************************/ 
func BCM_GearBox_Check_Loopback(loopbackLevel int, enable int) (err int) {
    var cmdStr string
    var searchStr string
    var failSearchStr string
    var PortNumber int = 0

    phymask := []byte {0, 1, 2, 3}

    cli.Printf("i", "Checking Loopback Level for all GB\n")

    if ( loopbackLevel > GB_LOOPBACK_HOST_SIDE ) {
        cli.Printf("e", " ERROR BCM_GearBox_Check_Loopback(): LOOPBACK LEVEL PASSED (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_LINE_SIDE=%d.  GB_LOOPBACK_HOST_SIDE=%d  ", loopbackLevel, GB_LOOPBACK_LINE_SIDE, GB_LOOPBACK_HOST_SIDE)
        err = errType.FAIL
        return
    }

    if ( enable != GB_LOOPBACK_DISABLE ) && (enable != GB_LOOPBACK_ENABLE) {
        cli.Printf("e", " ERROR BCM_GearBox_Check_Loopback(): loopbackmode (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_DISABLE=%d.  GB_REMOTE_PMD_LOOPBACK=%d  ", enable, GB_LOOPBACK_DISABLE, GB_LOOPBACK_ENABLE)
        err = errType.FAIL
        return
    }

    if ( enable == GB_LOOPBACK_DISABLE ) {
        searchStr = "disabled"
        failSearchStr = "enabled"
    } else {
        searchStr = "enabled"
        failSearchStr = "disabled"
    }

    for gbNumber, phy := range(phymask) {
        if (loopbackLevel == GB_LOOPBACK_LINE_SIDE) {
            cmdStr = fmt.Sprintf("ovs-appctl l1/phy_status %d | grep 'Digital Loopbac'\n", phy)
        } else {
            cmdStr = fmt.Sprintf("ovs-appctl l1/phy_status %d | grep 'Remote Loopbac'\n", phy)
        }

        out, errGo := exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
            err = errType.FAIL
            return
        }

        split_ps_command := strings.Split(string(out),"\n")
        split_ps_command = split_ps_command[:4]         //strip out extra \n entry with nothing
        PortNumber = 0
        for cnt, status := range(split_ps_command) {    //0,2 are LINE.    1,3 are HOST
            if ( loopbackLevel == GB_LOOPBACK_LINE_SIDE ) {
                if (cnt % 2) == 0 {
                    if strings.Contains(string(status), searchStr) {
                        cli.Printf("i", "GB-%d Port-%d Line Digital Loopback %s\n", gbNumber, PortNumber, searchStr)
                    } else {
                        cli.Printf("e", "ERROR: GB-%d Port-%d Line Digital Loopback %s.  Expecting %s\n", gbNumber, PortNumber, failSearchStr, searchStr)
                        err = errType.FAIL
                    }
                    PortNumber++
                }
            } else {
                if (cnt % 2) != 0 {
                    if strings.Contains(string(status), searchStr) {
                        cli.Printf("i", "GB-%d Port-%d Host Remote Loopback %s\n", gbNumber, PortNumber, searchStr)
                    } else {
                        cli.Printf("e", "ERROR: GB-%d Port-%d Host Remote Loopback %s.  Expecting %s\n", gbNumber, PortNumber, failSearchStr, searchStr)
                        err = errType.FAIL
                    }
                    PortNumber++
                }
            }
            //fmt.Println(cnt,"---- ", string(status))
            
        }
    }
    return
}


/*************************************************************************************** 
* 
* ovs-appctl l1/phy_status 0 0xF0 
*  
*  HOST SIDE IS TD3
*  LINE SIDE IS ELBA
*  
*    10000:/fs/nos/eeupdate# ovs-appctl l1/phy_status 0 | grep "Link status"
*            Line side Link status     1
*            Host side Link status     1
*            Line side Link status     1
*            Host side Link status     1
*
*
* 
****************************************************************************************/ 
func BCM_GearBox_Check_Link(host int, line int) (err int) {
    var cmdStr string
    var PortNumber int = 0

    phymask := []byte {0, 1, 2, 3}

    cli.Printf("i", "Checking Link for all GB\n")

    for gbNumber, phy := range(phymask) {
        cmdStr = fmt.Sprintf("ovs-appctl l1/phy_status %d | grep 'Link status'\n", phy)

        out, errGo := exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
            err = errType.FAIL
            return
        }

        split_ps_command := strings.Split(string(out),"\n")
        split_ps_command = split_ps_command[:4]         //strip out extra \n entry with nothing
        PortNumber = 0
        for cnt, status := range(split_ps_command) {    //0,2 are LINE.    1,3 are HOST
            if ((cnt % 2) == 0) && (line > 0) {
                if strings.Contains(string(status), "1") {
                    cli.Printf("i", "GB-%d Port-%d Line Side Link Up\n", gbNumber, PortNumber)
                } else {
                    cli.Printf("e", "GB-%d Port-%d Line Side Link Down\n", gbNumber, PortNumber)
                    err = errType.FAIL
                }
            }
            if ((cnt % 2) != 0) && (host > 0) {
                if strings.Contains(string(status), "1") {
                    cli.Printf("i", "GB-%d Port-%d Host Side Link Up\n", gbNumber, PortNumber)
                } else {
                    cli.Printf("e", "GB-%d Port-%d Host Side Link Down\n", gbNumber, PortNumber)
                    err = errType.FAIL
                }
                PortNumber++
            }
        }
    }
    return
}


/*************************************************************************************** 
* 
* ovs-appctl l1/phy_status 0 0xF0 
*  
*  HOST SIDE IS TD3
*  LINE SIDE IS ELBA
*  
*  ovs-appctl l1/phy_status %d | grep 'Digital Loopbac'
*        Digital Loopback status   disabled        **LINE PORT0 0x3
*        Digital Loopback status   disabled        **HOST PORT0 0x0F
*        Digital Loopback status   disabled        **LINE PORT1 0xC
*        Digital Loopback status   disabled        **HOST PORT1 0xF0
*
* 
****************************************************************************************/ 
func BCM_Retimer_Check_Loopback(loopbackLevel int, enable int) (err int) {
    var cmdStr string
    var searchStr string
    var failSearchStr string
    var PortNumber int = 0

    phymask := []byte {4, 5, 6}

    cli.Printf("i", "Checking Loopback Level for all Retimers\n")

    if ( loopbackLevel > GB_LOOPBACK_HOST_SIDE ) {
        cli.Printf("e", " ERROR BCM_Retimer_Check_Loopback(): LOOPBACK LEVEL PASSED (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_LINE_SIDE=%d.  GB_LOOPBACK_HOST_SIDE=%d  ", loopbackLevel, GB_LOOPBACK_LINE_SIDE, GB_LOOPBACK_HOST_SIDE)
        err = errType.FAIL
        return
    }

    if ( enable != GB_LOOPBACK_DISABLE ) && (enable != GB_LOOPBACK_ENABLE) {
        cli.Printf("e", " ERROR BCM_Retimer_Check_Loopback(): loopbackmode (%d), IS NOT VALID. ARG MUST BE GB_LOOPBACK_DISABLE=%d.  GB_REMOTE_PMD_LOOPBACK=%d  ", enable, GB_LOOPBACK_DISABLE, GB_LOOPBACK_ENABLE)
        err = errType.FAIL
        return
    }

    if ( enable == GB_LOOPBACK_DISABLE ) {
        searchStr = "disabled"
        failSearchStr = "enabled"
    } else {
        searchStr = "enabled"
        failSearchStr = "disabled"
    }

    for gbNumber, phy := range(phymask) {
        if (loopbackLevel == GB_LOOPBACK_LINE_SIDE) {
            cmdStr = fmt.Sprintf("ovs-appctl l1/phy_status %d | grep 'Digital Loopbac'\n", phy)
        } else {
            cmdStr = fmt.Sprintf("ovs-appctl l1/phy_status %d | grep 'Remote Loopbac'\n", phy)
        }

        out, errGo := exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
            err = errType.FAIL
            return
        }

        split_ps_command := strings.Split(string(out),"\n")
        split_ps_command = split_ps_command[:4]         //strip out extra \n entry with nothing
        PortNumber = 0
        for cnt, status := range(split_ps_command) {    //0,2 are LINE.    1,3 are HOST
            if ( loopbackLevel == GB_LOOPBACK_LINE_SIDE ) {
                if (cnt % 2) == 0 {
                    if strings.Contains(string(status), searchStr) {
                        cli.Printf("i", "Retimer-%d Port-%d Line Digital Loopback %s\n", gbNumber, PortNumber, searchStr)
                    } else {
                        cli.Printf("e", "ERROR: Retimer-%d Port-%d Line Digital Loopback %s.  Expecting %s\n", gbNumber, PortNumber, failSearchStr, searchStr)
                        err = errType.FAIL
                    }
                }
            } else {
                if (cnt % 2) != 0 {
                    if strings.Contains(string(status), searchStr) {
                        cli.Printf("i", "Retimer-%d Port-%d Host Remote Loopback %s\n", gbNumber, PortNumber, searchStr)
                    } else {
                        cli.Printf("e", "ERROR: Retimer-%d Port-%d Host Remote Loopback %s.  Expecting %s\n", gbNumber, PortNumber, failSearchStr, searchStr)
                        err = errType.FAIL
                    }
                }
            }
            //fmt.Println(cnt,"---- ", string(status))
            PortNumber++
        }
    }
    return
}


/*************************************************************************************** 
* 
* ovs-appctl l1/phy_status 0 0xF0 
*  
*  HOST SIDE IS TD3
*  LINE SIDE IS ELBA
*  
*
* 10000:/fs/nos/eeupdate# ovs-appctl l1/phy_status 4 | grep "Link status"
*       Line side Link status     1
*       Host side Link status     1
*       Line side Link status     1
*       Host side Link status     1
*
*
*
* 
****************************************************************************************/ 
func BCM_Retimer_Check_Link(host int, line int) (err int) {
    var cmdStr string
    var PortNumber int = 0

    phymask := []byte {4, 5, 6}

    cli.Printf("i", "Checking Link for all Retimers\n")

    for gbNumber, phy := range(phymask) {
        cmdStr = fmt.Sprintf("ovs-appctl l1/phy_status %d | grep 'Link status'\n", phy)

        out, errGo := exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
            err = errType.FAIL
            return
        }

        split_ps_command := strings.Split(string(out),"\n")
        split_ps_command = split_ps_command[:4]         //strip out extra \n entry with nothing
        PortNumber = 0
        for cnt, status := range(split_ps_command) {    //0,2 are LINE.    1,3 are HOST
            if ((cnt % 2) == 0) && (line > 0) {
                if strings.Contains(string(status), "1") {
                    cli.Printf("i", "Retimer-%d Port-%d Line Side Link Up\n", gbNumber, PortNumber)
                } else {
                    cli.Printf("e", "Retimer-%d Port-%d Line Side Link Down\n", gbNumber, PortNumber)
                    err = errType.FAIL
                }
            }
            if ((cnt % 2) != 0) && (host > 0) {
                if strings.Contains(string(status), "1") {
                    cli.Printf("i", "Retimer-%d Port-%d Host Side Link Up\n", gbNumber, PortNumber)
                } else {
                    cli.Printf("e", "Retimer-%d Port-%d Host Side Link Down\n", gbNumber, PortNumber)
                    err = errType.FAIL
                }
                PortNumber++
            }
        }
    }
    return
}


/****************************************************************************************************** 
* 
* # aapl eye -server localhost -port 9000 -a 3:8.1 -print-vbtc -print-hbtc | grep "Eye height at 1e-06"
* Eye height at 1e-06 BER/0.0625 = Q(4.74):   45 mV
* Eye height at 1e-06 BER/0.0625 = Q(4.74):   53 mV
* Eye height at 1e-06 BER/0.0625 = Q(4.74):   46 mV
* 
* 
*******************************************************************************************************/ 
func Elba_Check_Eye_Height(elba int, serdes_lane int, useCLI int) (err int, mv0 int, mv1 int, mv2 int) {
    var cmdStr string
    var scriptStr string
    //Elba_lane_param := []string{"3:8.0", "3:8.1", "3:8.2", "3:8.3", "3:8.4", "3:8.5", "3:8.6", "3:8.7"}
    i := 0

    const createscript = 
    "pwd\n"+
    "cd /data\n"+
    "rm elb_read_eye.sh\n"+
    "echo -e \"#!/bin/bash\" > /data/elb_read_eye.sh\n"+ 
    "echo -e \"/nic/bin/pdsctl debug aacs-server-start --server-port 9000\" >> /data/elb_read_eye.sh\n"+ 
    "echo -e \"export SERDES_DUT_IP=localhost:9000\" >> /data/elb_read_eye.sh\n"+ 
    "echo -e \"export SERDES_SBUS_RINGS=4\" >> /data/elb_read_eye.sh\n"+ 
    "echo -e \"/nic/bin/aapl eye -server localhost -port 9000  -print-ascii-eye -a 3:8.0 -print-vbtc -print-hbtc\" >> /data/elb_read_eye.sh\n"

    err = errType.SUCCESS

    if (elba > (NUMBER_ELBAS -1)) {
        cli.Printf("e", "Invalid Elba Number Passed (%d)", elba)
        return errType.FAIL, 0, 0, 0
    }
    if (serdes_lane > 7) {
        cli.Printf("e", "Invalid Port Number Passed (%d)", serdes_lane)
        return errType.FAIL, 0, 0, 0
    }

    if (serdes_lane == 0) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.0", 1)
    }
    if (serdes_lane == 1) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.1", 1)
    }
    if (serdes_lane == 2) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.2", 1)
    }
    if (serdes_lane == 3) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.3", 1)
    }
    if (serdes_lane == 4) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.4", 1)
    }
    if (serdes_lane == 5) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.5", 1)
    }
    if (serdes_lane == 6) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.6", 1)
    }
    if (serdes_lane == 7) {
        scriptStr = strings.Replace(createscript, "3:8.0", "3:8.7", 1)
    }

    if  elba == ELBA0 {
        cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt"
    } else if elba == ELBA1 {
        cmdStr = "/fs/nos/home_diag/diag/scripts/taormina/cmd_elba1.txt"
    }     
    file, errGo := os.OpenFile(cmdStr, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if errGo != nil {
        cli.Println("e", "ERROR: Failed to Open %s.   GO ERROR=%v", cmdStr, errGo)
        err = errType.FAIL
        return
    }
    file.WriteString(string(scriptStr[:]))
    file.Close()
    os.Chmod(cmdStr, 0777)
    cmdStr, err = ElbaGetConsoleScriptToExecute(uint32(elba))
    if err != errType.SUCCESS {
        dcli.Printf("e","FAILED TO DETERMINE IF BOARD CONSOLE IS SUPER I/O OR FPGA BASED\n")
        return
    } 
    output , errGo1 := exec.Command("sh", "-c", cmdStr).Output()
    if errGo1 != nil {
        cli.Printf("d", "Cmd %s failed! %v", cmdStr, errGo1)
        err = errType.FAIL
        return
    }


    if  elba == 0 {
        cmdStr = fmt.Sprintf("ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 chmod 777 /data/elb_read_eye.sh")
    } else {
        cmdStr = fmt.Sprintf("ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 chmod 777 /data/elb_read_eye.sh")
    } 
    output , errGo1 = exec.Command("sh", "-c", cmdStr).Output()
    if errGo1 != nil {
        cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo1)
        return errType.FAIL, 0, 0, 0
    }

    //get the eye height
    if  elba == 0 {
        cmdStr = fmt.Sprintf("ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 /data/elb_read_eye.sh | grep \"Eye height at 1e-06\"")
    } else {
        cmdStr = fmt.Sprintf("ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 /data/elb_read_eye.sh | grep \"Eye height at 1e-06\"")
    } 

    output , errGo1 = exec.Command("sh", "-c", cmdStr).Output()
    if errGo1 != nil {
        cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo1)
        return errType.FAIL, 0, 0, 0
    }
    //cli.Printf("i", "%s\n", output)

    s := strings.Split(string(output), "\n")
    for _, temp := range s {
        temp_s := strings.TrimSpace(string(temp[43:46]))
        eyeHeight, errGo := strconv.Atoi(string(temp_s))
        if errGo != nil {
            cli.Printf("e", "strconv atoi failed")
            return errType.FAIL, 0, 0, 0
        }
        switch (i) {
            case 0: 
                mv0 = eyeHeight
            case 1: 
                mv1 = eyeHeight
            case 2: 
                mv2 = eyeHeight
        }
        i++
        if (i > 2) {
            break
        }
    } 
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
/*
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
*/
    return
}

/****************************************************************************************************** 
* 
* This is just a copy of the dsp test so it can be run from a cli without the diag engine
* 
*******************************************************************************************************/ 
func TaorI2cTest() (err int) {
    var ret int = errType.SUCCESS
    ret = errType.SUCCESS
    var i2cTestList []string

    for _, i2cEntry := range(i2cinfo.CurI2cTbl) {
        if (i2cEntry.Flag & i2cinfo.I2C_TEST_ENABLE) == i2cinfo.I2C_TEST_ENABLE {
            i2cTestList = append(i2cTestList, i2cEntry.Name)
        }
    }
    if len(i2cTestList) == 0 {
        cli.Println("f", "Variable i2cTestList is empty.  No tests to run")
        err = errType.INVALID_TEST    
        return
    }

    for _, devName := range(i2cTestList) {
        i2cInfo, err1 := i2cinfo.GetI2cInfo(devName)
        if err1 != errType.SUCCESS {
            cli.Println("e", "I2cI2cHdl: GetI2cInfo failed for device --> ", devName)
            err = errType.FAIL
            return
        }


        taorfpga.SetI2Cmux((i2cInfo.Bus - 1), uint32(i2cInfo.HubPort))
        if running, _ := Process_Is_Running("fand"); running == true {
            cli.Printf("i", "fand is running.. killing it\n")
            Process_Kill("fand")
        }
        if running, _ := Process_Is_Running("powerd"); running == true {
            cli.Printf("i", "powerd is running.. killing it\n")
            Process_Kill("powerd")
        }

        dcli.Println("i", "Starting I2C test on", devName, " / Component", i2cInfo.Comp)
        switch i2cInfo.Comp {
            case "MACHXO3":
                err = Elba_CPLD_I2C_Sanity_Test(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TMP451": 
                err = tmp451.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "ADT7462": 
                err = adt7462.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "DPS-800": 
                err = dps800.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "SN1701022": 
                err = sn1701022.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS53681": 
                err = tps53681.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS544C20": 
                err = tps544c20.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "LM75":
                err = lm75a.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS53659":
                err = tps53659.TestTps53659(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS549A20":
                err = tps549a20.TestTps549a20(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "AT24C02C":
                err = TestTaorFruI2C(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            default:
                {
                    dcli.Println("f", "Unsupported device: ", devName)
                    ret = errType.INVALID_PARAM
                }
        } //end switch
    }  //end for loop

    if ret == errType.SUCCESS {
        dcli.Printf("i","I2C I2C TEST PASSED\n")
    } else {
        dcli.Printf("e","I2C I2C TEST FAILED\n")
        err = ret
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
    } else if fan_air_direction == taorfpga.AIRFLOW_BACK_TO_FRONT {
        printf("i", "FAN AIRFLOW:  BACK TO FRONT\n", useCLI)
    } else {
        printf("e", "FAN AIRFLOW:  ERROR: DETECTING A MIX OF FRONT TO BACK AND BACK TO FRONT\n", useCLI)
        rc = -1
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
    err = TPM_CHECK(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err = SSD_Display_Info(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err = X86_DDR_Display_Info(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    fmt.Printf("\n")
    err = BIOS_Display_Version(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err = CXOS_Display_Version(useCLI)
    if err != errType.SUCCESS { rc = -1 }
    fmt.Printf("\n")
    err = Elba_Check_Pci_Link(taorfpga.ELBA0, 0, useCLI)
    if err != errType.SUCCESS { rc = -1 }
    err = Elba_Check_Pci_Link(taorfpga.ELBA1, 0, useCLI)
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
        dcli.Printf("e", "SWITCH INVENTORY TEST FAILED\n")
        err = errType.FAIL
    } else {
        dcli.Printf("i", "SWITCH INVENTORY TEST PASSED\n")
        err = errType.SUCCESS
    }
    return
}




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
                                  {"TSENSOR-TD3", td3.GetTemperature},
                                  {"TSENSOR-TD3", td3.GetPeakTemperature},
                                  {"TSENSOR-GB", td3.GearboxGetTemperatures},
                                  {"TSENSOR-RETIMER", td3.RetimerGetTemperatures},
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
        fmt.Printf("%s\n", outStr)
    }
    

    return
}


/*
root@sonic:/home/admin/eeupdate# ./fan.bash


           prsnt     rev     dir   power   error     pwm   inRPM  outRPM
           =====     ===     ===   =====   =====     ===   =====  ======
 fan0:         1       3     red      on       0    0x40    2779    2374
 fan1:         1       3     red      on       0    0x40    2720    2390
 fan2:         1       3     red      on       0    0x40    2644    2351
 fan3:         1       3     red      on       0    0x40    2750    2405
*/
func ShowFanSpeed()  (err int)  {
    //var rc int
    var outStr string
    var i int
    var psuPresent [taorfpga.MAXPSU]bool
    FanHeader  := []string {"prsnt","error", "pwm", "inRPM", "outRPM"}
    FanHeader1 := []string {"-----","-----", "---", "-----", "------"}

    outStr = fmt.Sprintf("%-20s", "NAME")
    for _, title := range(FanHeader) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    fmt.Printf("%s\n", outStr)

    outStr = fmt.Sprintf("%-20s", "----")
    for _, title := range(FanHeader1) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    fmt.Printf("%s\n", outStr)

    //MAXPSU
    for i=0; i<taorfpga.MAXPSU; i++ {
        psuPresent[i], _ = taorfpga.PSU_present(uint32(i)) 

    }
    for i=0; i<taorfpga.MAXPSU; i++ {
        if psuPresent[i] {
            str := fmt.Sprintf("PSU_%d", i+1)
            hwinfo.EnableHubChannelExclusive(str)
            psuFault, rc := dps800.ReadFanWarnFault(str) 
            if rc != errType.SUCCESS {
                fmt.Printf("%-20s RPM = ERROR READING RPM\n", str)
                err = -1
            }

            rpm, rc := dps800.ReadFanSpeed(str)
            if rc != errType.SUCCESS {
                fmt.Printf("%-20s RPM = ERROR READING RPM\n", str)
                err = -1
            } 

            fmt.Printf("%-20s%-10s%-10s%-10s%-10s%-10s\n", str, "1", strconv.Itoa(int(psuFault))," ", " ",  strconv.Itoa(int(rpm)))
        }
    }

//    var fan_MAP = map[int]fanDevMap {
//    0 : { dev:"FAN_1" , fanNum:0, silkScreenFan:6 } ,  //fan 1 from presence
//    1 : { dev:"FAN_1" , fanNum:1, silkScreenFan:5 } ,  //fan 2 from presence
//    2 : { dev:"FAN_1" , fanNum:2, silkScreenFan:4 } ,  //fan 3 from presence
//    3 : { dev:"FAN_2" , fanNum:0, silkScreenFan:3 } ,  //fan 4 from presence
//    4 : { dev:"FAN_2" , fanNum:1, silkScreenFan:2 } ,  //fan 5 from presence
//    5 : { dev:"FAN_2" , fanNum:2, silkScreenFan:1 } ,  //fan 6 from presence

    for i=0; i<taorfpga.MAXFAN; i++ {
        fanErr :=0
        var pwm byte
        var inner, outer uint64
        var err int

        hwinfo.EnableHubChannelExclusive(fan_MAP[i].dev)
        inner, _, err =  hwdev.FanSpeedGet(fan_MAP[i].dev, (fan_MAP[i].fanNum * 2)+1)
        if err != errType.SUCCESS {
            fmt.Printf("%-20s RPM = ERROR READING RPM\n", fan_MAP[i].dev)
            err = -1
        } 
        outer, _, err =  hwdev.FanSpeedGet(fan_MAP[i].dev, (fan_MAP[i].fanNum * 2))
        if err != errType.SUCCESS {
            fmt.Printf("%-20s RPM = ERROR READING RPM\n", fan_MAP[i].dev)
            err = -1
        }


        //fanErr, _ := liparifpga.FAN_Get_Fault(i) 
        pwm , err = hwdev.FanReadReg(fan_MAP[i].dev, uint32(0xAA + fan_MAP[i].fanNum))
        if err != errType.SUCCESS {
            fmt.Printf("%-20s RPM = ERROR READING PWM\n", fan_MAP[i].dev)
            err = -1
        }
        fanStr := fmt.Sprintf("FAN-%d", i)
        fmt.Printf("%-20s%-10s%-10s%-10s%-10s%-10s\n", fanStr, "1", strconv.Itoa(int(fanErr)),strconv.Itoa(int(pwm)), strconv.Itoa(int(inner)),  strconv.Itoa(int(outer)))
    }
    

    return
}





/*********************************************************************
*  
*  Mainly used to check link status from the cli.
*  Ports need to be enabled first.  By default they are disabled
*  
**********************************************************************/
func Enable_Trident3_Ports() (err int) {
    //var rc int
    var errGo error
    var data32 uint32
    var addr uint64
    var port25G_s string
    var port100G_s string
    var portGearBox_s string
    var tmp_s string
    var cmdString, command string
    output1 := []byte{}
    

    cli.Printf("i", "Enabling all TD3 Ports\n")
    cmdString = "echo \"conf\nint 1/1/1-1/1/54\nshutdown\nend\n\" | vtysh"
    output1, errGo = exec.Command("bash", "-c", cmdString).Output()
    if errGo != nil {
        cli.Println("e", "Failed to exec command:",cmdString," GoERR=",errGo)
        cli.Printf("e", "OUTPUT='%s'\n", output1)
        err = errType.FAIL
        return
    }
    time.Sleep(time.Duration(2) * time.Second)
    
    err = td3.Set_Pre_Main_Post_25G_EXT(0)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on TD3 25G Ports\n")
        return
    }

    err = td3.RetimerSetSI(0)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on Retimer 100G Ports\n")
        return
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

    for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
        if i == (td3.TAOR_INTERNAL_PORT_START + td3.TAOR_INTERNAL_PORTS - 1) {
            tmp_s = fmt.Sprintf("%s", td3.TaorPortMap[i].Name)
        } else {
            tmp_s = fmt.Sprintf("%s,", td3.TaorPortMap[i].Name)
        }
        portGearBox_s = portGearBox_s + tmp_s
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=true"
    _ , err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=true"
    _ , err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        return
    }

    return

}


/********************************************************** 
  *    @param prbs_mode          User specified polynomial
 *                              0 - PRBS7
 *                              1 - PRBS9
 *                              2 - PRBS11
 *                              3 - PRBS15
 *                              4 - PRBS23
 *                              5 - PRBS31
 *                              6 - PRBS58
***********************************************************/
func Prbs(sleep int, prbs string, LoopbackType int) (err int) {
    var rc int
    var errGo error
    var data32 uint32
    var addr uint64
    var SFPnumber, QSFPnumber, bitcompare uint32
    var port25G_s string
    var port100G_s string
    var portGearBox_s string
    var tmp_s string
    var prbsType string
    var cmdString, command, output string
    output1 := []byte{}
    

    if prbs == "prbs7" {
        prbsType = "0"
    } else if prbs == "prbs9" {
        prbsType = "1"
    } else if prbs == "prbs11" {
        prbsType = "2"
    } else if prbs == "prbs15" {
        prbsType = "3"
    } else if prbs == "prbs23" {
        prbsType = "4"
    } else if prbs == "prbs31" {
        prbsType = "5"
    } else if prbs == "prbs58" {
        prbsType = "6"
    } else {
        cli.Printf("e", "PRBS Parameter passed is not valid. You passed '%s'\n", prbs)
        err = errType.FAIL
        goto endBCMprbs
    }

    /* Check SFP's are present */
    cli.Printf("i", "Checking for SFP Presence\n")
    addr = taorfpga.D0_FP_SFP_STAT_3_0_REG;
    for SFPnumber=0;SFPnumber<taorfpga.MAXSFP;SFPnumber++ {
        addr = addr + ((uint64(SFPnumber)/4) * 4)
        bitcompare = (1 << ((SFPnumber%4)*8))
        data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
        if errGo != nil {
            err = errType.FAIL
            goto endBCMprbs
        }

        //1 = NOT PRESENT
        if (data32 & bitcompare) == bitcompare {
            cli.Printf("e", "SFP-%d is not detecting presence.  Check SFP-%d is present\n", SFPnumber+1, SFPnumber+1)
            err = errType.FAIL
            goto endBCMprbs
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
            goto endBCMprbs
        }

        //1 = NOT PRESENT
        if (data32 & bitcompare) == bitcompare {
            cli.Printf("e", "QSFP-%d is not detecting presence.  Check QSFP-%d is present\n", QSFPnumber+1, QSFPnumber+1)
            err = errType.FAIL
            goto endBCMprbs
        } 
    }

    cli.Printf("i", "Disabling Ports in VTYSH\n")
    cmdString = "echo \"conf\nint 1/1/1-1/1/54\nshutdown\nend\n\" | vtysh"
    output1, errGo = exec.Command("bash", "-c", cmdString).Output()
    if errGo != nil {
        cli.Println("e", "Failed to exec command:",cmdString," GoERR=",errGo)
        cli.Printf("e", "OUTPUT='%s'\n", output1)
        err = errType.FAIL
        goto endBCMprbs
    }
    time.Sleep(time.Duration(2) * time.Second)
    
    err = td3.Set_Pre_Main_Post_25G_EXT(1)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on TD3 25G Ports\n")
        goto endBCMprbs
    }

    err = td3.RetimerSetSI(1)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on Retimer 100G Ports\n")
        goto endBCMprbs
    }

    /* Enable SFP's */
    cli.Printf("i", "Enabling SFP's\n")
    addr = taorfpga.D0_FP_SFP_CTRL_3_0_REG;
    for i:=0;i<taorfpga.MAXSFP;i++ {
        addr = addr + ((uint64(i)/4) * 4)
        errGo = taorfpga.TaorWriteU32( taorfpga.DEVREGION0, addr, 0x06060606)
        if errGo != nil {
            err = errType.FAIL
            goto endBCMprbs
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

    for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
        if i == (td3.TAOR_INTERNAL_PORT_START + td3.TAOR_INTERNAL_PORTS - 1) {
            tmp_s = fmt.Sprintf("%s", td3.TaorPortMap[i].Name)
        } else {
            tmp_s = fmt.Sprintf("%s,", td3.TaorPortMap[i].Name)
        }
        portGearBox_s = portGearBox_s + tmp_s
    }

    //set gearbox loopback 
    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        err = BCM_GearBox_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_ENABLE)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
        err = BCM_GearBox_Check_Loopback(GB_LOOPBACK_HOST_SIDE, GB_LOOPBACK_ENABLE)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }
    if (( LoopbackType & PRBS_RETIMER_LPBK) == PRBS_RETIMER_LPBK) {
        err = BCM_Retimer_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_ENABLE)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
        err = BCM_Retimer_Check_Loopback(GB_LOOPBACK_HOST_SIDE, GB_LOOPBACK_ENABLE)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }


    

    //No return output to check on this command
    cli.Printf("i", "Enabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=true"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=true"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }

    //Check Link
    {
        var link_rc, link_retry int
        var ps_output string
prbslinkcheckretry:
        cli.Printf("i", "Checking Link\n")
        time.Sleep(time.Duration(2) * time.Second)
        ps_output, err = td3.ExecBCMshellCMD("ps", 5)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
        for i:=0; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {
            link_rc = td3.LinkCheck(td3.TaorPortMap[i].Name, ps_output) 
            if link_rc == errType.LINK_UP {
                dcli.Printf("i", "Port-%.02d  %4s: LINK UP\n", i+1, td3.TaorPortMap[i].Name)
            } else if link_rc == errType.LINK_DOWN {
                dcli.Printf("e", "Port-%.02d  %4s: LINK DOWN\n", i+1, td3.TaorPortMap[i].Name)
                rc = -1
            } else if link_rc == errType.LINK_DISABLED {
                dcli.Printf("e", "Port-%.02d  %4s: LINK DISABLED\n", i+1, td3.TaorPortMap[i].Name)
                rc = -1
            } else {
                dcli.Printf("e", "Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, td3.TaorPortMap[i].Name)
                rc = -1
            }
        }
        if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
            for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
                link_rc = td3.LinkCheck(td3.TaorPortMap[i].Name, ps_output) 
                if link_rc == errType.LINK_UP {
                    dcli.Printf("i", "GB Facing Port-%.02d  %4s: LINK UP\n", i+1, td3.TaorPortMap[i].Name)
                } else if link_rc == errType.LINK_DOWN {
                    dcli.Printf("e", "GB Facing Port-%.02d  %4s: LINK DOWN\n", i+1, td3.TaorPortMap[i].Name)
                    rc = -1
                } else if link_rc == errType.LINK_DISABLED {
                    dcli.Printf("e", "GB Facing Port-%.02d  %4s: LINK DISABLED\n", i+1, td3.TaorPortMap[i].Name)
                    rc = -1
                } else {
                    dcli.Printf("e", "Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, td3.TaorPortMap[i].Name)
                    rc = -1
                }
            }
        }

        fmt.Printf("\n")
        if rc != 0 {
            if link_retry < 2 {
                link_retry = link_retry + 1
                rc = 0
                goto prbslinkcheckretry
            }
            err = errType.FAIL
            goto endBCMprbs
        }
    }



    //No return output to check on this command
    cli.Printf("i", "Disabling BCM LinkScan\n")
    command = "LINKscan off"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }



    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 25G Ports\n")
    command = "phy diag " + port25G_s +" prbs set unit=0 p="+prbsType
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }

    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 100G Ports\n")
    command = "phy diag " + port100G_s +" prbs set unit=0 p="+prbsType
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }

    //No return output to check on this command
    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        cli.Printf("i", "Starting PRBS on all Internal Ports to Gearbox\n")
        command = "phy diag " + portGearBox_s +" prbs set unit=0 p="+prbsType
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }
    time.Sleep(time.Duration(2) * (time.Second))
    

    //First time you read status it will show an error, have to read it again later after sleep
    cli.Printf("i", "Read Status to clear errors\n")
    command = "phy diag " + port25G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    command = "phy diag " + port100G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        command = "phy diag " + portGearBox_s +" prbs get unit=0"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }
    time.Sleep(time.Duration(1) * (time.Second))
    command = "phy diag " + port100G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    time.Sleep(time.Duration(1) * (time.Second))
    command = "phy diag " + port100G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        command = "phy diag " + portGearBox_s +" prbs get unit=0"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }


    //cli.Printf("i", "Check 25G Ports Status\n")
    command = "phy diag " + port25G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    for i:=0; i<td3.TAOR_EXTERNAL_25G_PORTS; i++ {
        scanner := bufio.NewScanner(strings.NewReader(output))
        for scanner.Scan() {
            if  strings.Contains(scanner.Text(), "phy diag")==true {
                continue
            }
            if strings.Contains(scanner.Text(), td3.TaorPortMap[i].Name)==true {
                if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                    //cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        rc = -1
    }

    //cli.Printf("i", "Check 100G Ports Status\n")
    command = "phy diag " + port100G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    for i:=td3.TAOR_EXTERNAL_25G_PORTS; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {
        scanner := bufio.NewScanner(strings.NewReader(output))
        for scanner.Scan() {
            if  strings.Contains(scanner.Text(), "phy diag")==true {
                continue
            }
            if strings.Contains(scanner.Text(), td3.TaorPortMap[i].Name)==true {
                if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                    //cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }

    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        command = "phy diag " + portGearBox_s +" prbs get unit=0"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
        for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
            scanner := bufio.NewScanner(strings.NewReader(output))
            for scanner.Scan() {
                if  strings.Contains(scanner.Text(), "phy diag")==true {
                    continue
                }
                if strings.Contains(scanner.Text(), td3.TaorPortMap[i].Name)==true {
                    if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                        //cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                    } else {
                        cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                        err = errType.FAIL
                    }
                }
            }
        }
    }

    //sleep
    cli.Printf("i", "Sleeping for %d seconds to let the test run\n", sleep)
    time.Sleep(time.Duration(sleep/2) * (time.Second))
    _, _, err = td3.CheckTemperatures("TD3", td3.TD3_MAX_TEMP)
    if err != errType.SUCCESS {
        rc = -1
    }
    time.Sleep(time.Duration(sleep/2) * (time.Second))

    /*
    t1 := time.Now()
    for
    {
        t2 := time.Now()
        diff := t2.Sub(t1)
        data32, rc = ReadReg("TD3", "TOP_AVS_SEL_REG")
        //fmt.Printf("AVS REG=%x\n", data32)
        if rc != errType.SUCCESS {
            cli.Printf("e", "ERROR FAILED TO READ TOP_AVS_SEL_REG")
            break
        }
        //fmt.Println(" Elapsed Time=",diff," Duration=",duration," High Temp=", TD3highTemp )
        if uint32(diff.Seconds()) > uint32(sleep) {
            break
        }
    } 
    */ 


    //Check output
    //xe6 (21):  PRBS OK!
    //xe6 (21):  PRBS has -2 errors!
    cli.Printf("i", "Check 25G Ports Status\n")
    command = "phy diag " + port25G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    for i:=0; i<td3.TAOR_EXTERNAL_25G_PORTS; i++ {
        scanner := bufio.NewScanner(strings.NewReader(output))
        for scanner.Scan() {
            if  strings.Contains(scanner.Text(), "phy diag")==true {
                continue
            }
            if strings.Contains(scanner.Text(), td3.TaorPortMap[i].Name)==true {
                if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                    cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        rc = -1
    }
    
    cli.Printf("i", "Check 100G Ports Status\n")
    command = "phy diag " + port100G_s +" prbs get unit=0"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }
    for i:=td3.TAOR_EXTERNAL_25G_PORTS; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {
        scanner := bufio.NewScanner(strings.NewReader(output))
        for scanner.Scan() {
            if  strings.Contains(scanner.Text(), "phy diag")==true {
                continue
            }
            if strings.Contains(scanner.Text(), td3.TaorPortMap[i].Name)==true {
                if strings.Contains(scanner.Text(), "PRBS has -2 errors!")==true {
                    cli.Printf("i", "[WARN] Port-%d seeing 2 errors\n", i+1)
                } else if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                    cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        rc = -1
    }

    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        cli.Printf("i", "Check Internal Gearbox Facing Port Status\n")
        command = "phy diag " + portGearBox_s +" prbs get unit=0"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
        for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
            scanner := bufio.NewScanner(strings.NewReader(output))
            for scanner.Scan() {
                if  strings.Contains(scanner.Text(), "phy diag")==true {
                    continue
                }
                if strings.Contains(scanner.Text(), td3.TaorPortMap[i].Name)==true {
                    if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                        cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                    } else {
                        cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                        err = errType.FAIL
                    }
                }
            }
        }
        if err == errType.FAIL {
            rc = -1
        }
    }

    cli.Printf("i", "Disable 25G PRBS\n")
    command = "phy diag " + port25G_s +" prbs clear"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }

    cli.Printf("i", "Disable 100G PRBS\n")
    command = "phy diag " + port100G_s +" prbs clear"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }

    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        cli.Printf("i", "Disable Internal Facting Gearbox Port PRBS\n")
        command = "phy diag " + portGearBox_s +" prbs clear"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }


    time.Sleep(time.Duration(3) * (time.Second))
    //No return output to check on this command
    cli.Printf("i", "Enabling BCM LinkScan\n")
    command = "LINKscan on"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        goto endBCMprbs
    }

endBCMprbs:

    //disable gearbox loopback 
    if (( LoopbackType & PRBS_GB_LPBK) == PRBS_GB_LPBK){
        err = BCM_GearBox_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_DISABLE)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }
    if (( LoopbackType & PRBS_RETIMER_LPBK) == PRBS_RETIMER_LPBK) {
        err = BCM_Retimer_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_DISABLE)
        if err != errType.SUCCESS {
            goto endBCMprbs
        }
    }

    if rc != 0 {
        err = errType.FAIL
    }
    if err == errType.SUCCESS {
        dcli.Printf("i", "BCM PRBS TEST PASSED\n")
    } else {
        dcli.Printf("e", "BCM PRBS TEST FAILED\n")
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
func System_Snake_Test(test_type uint32, elba_port_mask uint32, duration uint32, loopback_level string, pkt_size uint64, pkt_pattern uint64, dump_temperature uint32, TD3MaxTemp int, ElbaMaxTemp int, Fanspeed int, GBloopback int, Retimerloopback int, PollErrorAtEnd int) (err int) {
    var pwm_backup [MAXFANMODULES]byte
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
    var pct [MAXFANMODULES]byte
    var changePWMstring string
    var ElbaVLANcreatScript = "/fs/nos/home_diag/dssman/run.sh"

    var VlanStart int = 10
    var vlanMap = []int{10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85}

    var link_rc, link_retry int
    var ps_output string
//    var badeyefix int
//    var eye [2][8][3]int

    if test_type == td3.SNAKE_TEST_LINE_RATE {
        cli.Printf("i", "Starting Snake Test.  Line Rate.   Elba Link Mask=%x,  Duration=%d\n", elba_port_mask, duration)
    } else if test_type == td3.SNAKE_TEST_NEXT_PORT_FORWARDING  {
        cli.Printf("i", "Starting Snake Test.. Forward to the Next Port.  Elba Link Mask=%x,  Duration=%d\n", elba_port_mask, duration)
    } else if test_type == td3.SNAKE_TEST_ENVIRONMENT  {
        cli.Printf("i", "Starting Snake Test for Environmental Testing. Line Rate/512 Byte Packets.  Elba Link Mask=%x,  Duration=%d\n", elba_port_mask, duration)
    } else {
        cli.Printf("e", "ERROR: INVALID TEST TYPE PASSED TO SNAKE TEST.  TEST TYPE PASSSED=%d\n", test_type)
        err = errType.FAIL
        return
    }
    if (Fanspeed < 0 || Fanspeed > 100) {
        cli.Printf("e", "ERROR: INVALID FAN SPPED.  PWM MUST BE 0-100.  PWM PASSED=%d\n", Fanspeed)
        err = errType.FAIL
        return
    }
    if (GBloopback > SNAKE_GB_HOST_LPBK) {
        cli.Printf("e", "ERROR: GB Loopback Level is not Valid.  Level passed to snake test is =%d\n", GBloopback)
        err = errType.FAIL
        return
    }
    if (Retimerloopback > SNAKE_RETIMER_HOST_LPBK) {
        cli.Printf("e", "ERROR: RETIMER Loopback Level is not Valid.  Level passed to snake test is =%d\n", Retimerloopback)
        err = errType.FAIL
        return
    }
    cli.Printf("i", "DumpSensors=%d  TD3 Max Temperature=%d   Elba Max Temperature=%d   Fan Speed PWM Percent = %d\n", dump_temperature, TD3MaxTemp, ElbaMaxTemp, Fanspeed)


    if Fanspeed > 60 {
        //backup rpm values
        for j:=0; j<MAXFANMODULES; j++ {
            pwm_backup[j] , err = hwdev.FanReadReg(fan_MAP[j].dev, uint32(0xAA + fan_MAP[j].fanNum))
            if err != errType.SUCCESS {
               cli.Printf("e", "FanReadReg Failed on %s, fan-%d  \n", fan_MAP[j].dev, fan_MAP[j].fanNum)
               return
            }
            pct[j] = byte(int((int(pwm_backup[j]) * 100)/255))
        }
        // Ramp up PWM if needed. Icnremenets of 5% at a time
        for steps:=0;steps<20;steps++ {
           for j:=0; j<MAXFANMODULES; j++ {
               if pct[j] > byte(Fanspeed) {  //fan speed going down, just break
                   continue
               }
               if (pct[j] + 5) < byte(Fanspeed) {
                   pct[j] = pct[j]+5
                   s := fmt.Sprintf("%d ", pct[j])
                   changePWMstring = changePWMstring + s
                   hwdev.FanSpeedSet(fan_MAP[j].dev, int(pct[j]), (1<<fan_MAP[j].fanNum))
                   //time.Sleep(time.Duration(50) * time.Millisecond)
               } else {
                   continue
               }
           }
        }
        if len(changePWMstring) > 0 {
           cli.Printf("i","%s\n", changePWMstring)
        }

        // Set final PWM for test loop
        for j:=0; j<MAXFANMODULES; j++ {
            err = hwdev.FanSpeedSet(fan_MAP[j].dev, Fanspeed, (1<<fan_MAP[j].fanNum))
            if err != errType.SUCCESS {
               cli.Printf("e", "FanSpeedSet Failed on %s, fan-%d  \n", fan_MAP[j].dev, fan_MAP[j].fanNum)
               return
            }
        }
    }


    cli.Printf("i", "Allowing unsupported sfp/qsfp\n")
    cmdString := "echo \"configure\nallow-unsupported-transceiver\nend\n\" | vtysh"
    exec.Command("bash", "-c", cmdString).Output()

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
    _ , _ , err = td3.CheckTemperatures("TD3", TD3MaxTemp)
    if err != errType.SUCCESS {
        err = errType.FAIL
        return
    }

    if Fanspeed > 60 {
        misc.SleepInSec(7) //give fan time to change rpm
        for j:=0; j<MAXFANMODULES; j++ {
            rc = Fan_Check_RPM(j, Fanspeed, 25)
            if rc != errType.SUCCESS {
                err = errType.FAIL
            }
        }
        if err != errType.SUCCESS {
            return
        }
    }



    if (GBloopback == SNAKE_GB_LINE_LPBK  ) {      //ELBA Side
        rc = BCM_GearBox_Set_Loopback(GB_LOOPBACK_LINE_SIDE, GB_DIGITAL_PMD_LOOPBACK, GB_LOOPBACK_ENABLE)
        misc.SleepInSec(1)
        if ( rc == errType.SUCCESS ) {
            rc = BCM_GearBox_Check_Loopback(GB_LOOPBACK_LINE_SIDE, GB_LOOPBACK_ENABLE) 
        }
        
    }
    if (GBloopback == SNAKE_GB_HOST_LPBK  ) {   //TD3 Side
        rc = BCM_GearBox_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_ENABLE)
        misc.SleepInSec(1)
        if ( rc == errType.SUCCESS ) {
            rc = BCM_GearBox_Check_Loopback(GB_LOOPBACK_HOST_SIDE, GB_LOOPBACK_ENABLE) 
        }
    }
    // If GB Loopback failed, return 
    if rc != errType.SUCCESS {
        err = errType.FAIL
        return
    }

    if (Retimerloopback == SNAKE_RETIMER_LINE_LPBK  ) {      //Port Side
        rc = BCM_Retimer_Set_Loopback(GB_LOOPBACK_LINE_SIDE, GB_DIGITAL_PMD_LOOPBACK, GB_LOOPBACK_ENABLE)
        misc.SleepInSec(1)
        if ( rc == errType.SUCCESS ) {
            rc = BCM_Retimer_Check_Loopback(GB_LOOPBACK_LINE_SIDE, GB_LOOPBACK_ENABLE) 
        }
        
    }
    if (Retimerloopback == SNAKE_RETIMER_HOST_LPBK  ) {   //TD3 Side
        rc = BCM_Retimer_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_ENABLE)
        misc.SleepInSec(1)
        if ( rc == errType.SUCCESS ) {
            rc = BCM_Retimer_Check_Loopback(GB_LOOPBACK_HOST_SIDE, GB_LOOPBACK_ENABLE) 
        }
    }
    // If GB Loopback failed, return 
    if rc != errType.SUCCESS {
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
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            return
        }

        //No return output to check on this command
        cli.Printf("i", "Setting Phy Loopback on 100G Ports\n")
        command = "port " + port100G_s +" lb=phy"
        output, err = td3.ExecBCMshellCMD(command, 5)
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
    time.Sleep(time.Duration(5) * time.Second)
    {
        /*
        //FLAP ELBA LINKS ONE TIME
        cli.Printf("i", "Flapping the Elba Links enable=false\n")
        command = "port ce1-ce4,ce9,ce10,ce12,ce13 enable=false"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            return
        }
        time.Sleep(time.Duration(4) * time.Second)
        //FLAP ELBA LINKS ONE TIME
        cli.Printf("i", "Flapping the Elba Links enable=true\n")
        command = "port ce1-ce4,ce9,ce10,ce12,ce13 enable=true"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            return
        }
        time.Sleep(time.Duration(4) * time.Second)

        //FLAP ELBA LINKS ONE TIME
        cli.Printf("i", "Flapping the Elba Links enable=false\n")
        command = "port ce1-ce4,ce9,ce10,ce12,ce13 enable=false"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            return
        }
        time.Sleep(time.Duration(4) * time.Second)
        //FLAP ELBA LINKS ONE TIME
        cli.Printf("i", "Flapping the Elba Links enable=true\n")
        command = "port ce1-ce4,ce9,ce10,ce12,ce13 enable=true"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            return
        }
        time.Sleep(time.Duration(4) * time.Second)

        //No return output to check on this command
        cli.Printf("i", "Flapping the QSFP Links ENABLED=false\n")
        command = "port " + port100G_s +" enable=false"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            return
        }
        time.Sleep(time.Duration(4) * time.Second)

        cli.Printf("i", "Flapping the QSFP Links ENABLED=true\n")
        command = "port " + port100G_s +" enable=true"
        output, err = td3.ExecBCMshellCMD(command, 5)
        if err != errType.SUCCESS {
            return
        }
        time.Sleep(time.Duration(4) * time.Second)
        */
    }

    //set pvlan
    for i:=0; i<(td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS); i++ {
        //pvlan set xe8 10
        if test_type == td3.SNAKE_TEST_NEXT_PORT_FORWARDING  {
            command = fmt.Sprintf("pvlan set %s %d", td3.TaorPortMap[i].Name, (VlanStart + i))
        } else {
            command = fmt.Sprintf("pvlan set %s %d", td3.TaorPortMap[i].Name, vlanMap[i])
        }
        cli.Printf("i", command)
        output, err = td3.ExecBCMshellCMD(command, 5)
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
        output, err = td3.ExecBCMshellCMD(command, 5)
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
            output, err = td3.ExecBCMshellCMD(command, 5)
            if err != errType.SUCCESS {
                return
            }
        }
    }


    //No return output to check on this command
    cli.Printf("i", "Enabling Vlan Translate\n")
    command = "vlan translate on"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling Forwarding on 25G ports\n")
    command = "stg stp 1 " + port25G_s +" forward"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling Forwarding on 100G ports\n")
    command = "stg stp 1 " + port100G_s +" forward"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=true"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=true"
    output, err = td3.ExecBCMshellCMD(command, 5)
    if err != errType.SUCCESS {
        return
    }

    err = td3.Set_Pre_Main_Post_25G_EXT(1)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on TD3 25G Ports\n")
        return
    }

    //err = td3.RetimerSetSI(1)
    //if err != errType.SUCCESS {
    //    cli.Printf("e", "ERROR, Failed to set Pre Post Main on Retimer 100G Ports\n")
    //    return
    //}
    fmt.Printf("DEBUG DEBUG DEBUG: Setting serdes tuning using ovs-appctl\n")
    fmt.Printf("DEBUG DEBUG DEBUG: Setting serdes tuning using ovs-appctl\n")
    fmt.Printf("DEBUG DEBUG DEBUG: Setting serdes tuning using ovs-appctl\n")
    fmt.Printf("DEBUG DEBUG DEBUG: Setting serdes tuning using ovs-appctl\n")
    fmt.Printf("DEBUG DEBUG DEBUG: Setting serdes tuning using ovs-appctl\n")
    {
        exec.Command("sh", "-c", "ovs-appctl l1/phy_tuning 4 0xf0 0 -6 73 0;ovs-appctl l1/phy_tuning 4 0x0f 0 -6 73 0;ovs-appctl l1/phy_tuning 5 0xf0 0 -6 73 0;ovs-appctl l1/phy_tuning 5 0x0f 0 -6 73 0;ovs-appctl l1/phy_tuning 6 0xf0 0 -6 73 0;ovs-appctl l1/phy_tuning 6 0x0f 0 -6 73 0").Output()
    }



    err = td3.TD3_Lane_Config_Disable_UNRELIABLELOS_and_LPDFE(1)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to Disable Unreliable LOS and LP DFE on the retimers\n")
        return
    }

    //Check Link
    //Check Link
    link_rc = 0
    link_retry = 0
snakelinkcheckretry:
    {
        cli.Printf("i", "Checking Link\n")
        time.Sleep(time.Duration(2) * time.Second)
        ps_output, err = td3.ExecBCMshellCMD("ps", 5)
        if err != errType.SUCCESS {
            return
        }
        for i:=0; i<(td3.TAOR_EXTERNAL_25G_PORTS + td3.TAOR_EXTERNAL_100G_PORTS + td3.TAOR_INTERNAL_PORTS); i++ {
            if i >= td3.TAOR_INTERNAL_PORT_START {
                if (elba_port_mask & (1<<uint32(i - td3.TAOR_INTERNAL_PORT_START))) == 0 {
                    continue;
                }
            }
            link_rc = td3.LinkCheck(td3.TaorPortMap[i].Name, ps_output) 
            if link_rc == errType.LINK_UP {
                dcli.Printf("i", "Port-%.02d  %4s: LINK UP\n", i+1, td3.TaorPortMap[i].Name)
            } else if link_rc == errType.LINK_DOWN {
                dcli.Printf("e", "Port-%.02d  %4s: LINK DOWN\n", i+1, td3.TaorPortMap[i].Name)
                rc = -1
            } else if link_rc == errType.LINK_DISABLED {
                dcli.Printf("e", "Port-%.02d  %4s: LINK DISABLED\n", i+1, td3.TaorPortMap[i].Name)
                rc = -1
            } else {
                dcli.Printf("e", "Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, td3.TaorPortMap[i].Name)
                rc = -1
            }
        }
        fmt.Printf("\n")
        if rc != 0 {
            if link_retry < 2 {
                link_retry = link_retry + 1
                rc = 0
                time.Sleep(time.Duration(2) * time.Second)
                goto snakelinkcheckretry
            }
            err = errType.FAIL
            //return
        }
    }

    {
        checkLineLB := 1
        if (GBloopback == SNAKE_GB_HOST_LPBK  ) {
            checkLineLB = 0
        }
        rc = BCM_GearBox_Check_Link(1, checkLineLB)
        if rc != 0 {
            err = errType.FAIL
        }
    }
    if loopbackPhy == 0 {
        checkLineLB := 1
        if (Retimerloopback == SNAKE_RETIMER_HOST_LPBK) {
            checkLineLB = 0
        }
        rc = BCM_Retimer_Check_Link(1, checkLineLB)
        if rc != 0 {
            err = errType.FAIL
        }
    }
    // if we see link failures, exit the test
    if err == errType.FAIL {
        goto snaketestend
    }

/*
    {
        var eyefix int = badeyefix
        //for elbnumber:=0; elbnumber<NUMBER_ELBAS;elbnumber++{ 
        fmt.Printf(" Bad eye count=%d\n", badeyefix)
        for elbnumber:=0; elbnumber<1;elbnumber++{ 
            for lane:=0;lane<8;lane++{
                if ((eye[elbnumber][lane][0]<20) || (eye[elbnumber][lane][1]<20) || (eye[elbnumber][lane][2]<20) ) {
                    fmt.Printf(" Getting eye data for Elba-%d Lane-%d\n", elbnumber, lane)
                    rc, mv0, mv1, mv2 := Elba_Check_Eye_Height(elbnumber, lane, 0)
                    if rc == errType.FAIL {
                        err = errType.FAIL
                        goto snaketestend
                    }
                    eye[elbnumber][lane][0]=mv0
                    eye[elbnumber][lane][1]=mv1
                    eye[elbnumber][lane][2]=mv2
                }
            }
        }


        fmt.Printf("==============================================================\n")
        fmt.Printf("Elba-0\n")
        fmt.Printf("Lane0 | Lane1 | Lane2 | Lane3 | Lane4 | Lane5 | Lane6 | Lane7 \n")
        fmt.Printf(" %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv \n", eye[0][0][0], eye[0][1][0], eye[0][2][0], eye[0][3][0], eye[0][4][0], eye[0][5][0], eye[0][6][0], eye[0][7][0])
        fmt.Printf(" %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv \n", eye[0][0][1], eye[0][1][1], eye[0][2][1], eye[0][3][1], eye[0][4][1], eye[0][5][2], eye[0][6][1], eye[0][7][1])
        fmt.Printf(" %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv \n", eye[0][0][2], eye[0][1][2], eye[0][2][2], eye[0][3][2], eye[0][4][2], eye[0][5][1], eye[0][6][2], eye[0][7][2])
        fmt.Printf("==============================================================\n")
        fmt.Printf("Elba-1\n")
        fmt.Printf("Lane0 | Lane1 | Lane2 | Lane3 | Lane4 | Lane5 | Lane6 | Lane7 \n")
        fmt.Printf(" %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv \n", eye[1][0][0], eye[1][1][0], eye[1][2][0], eye[1][3][0], eye[1][4][0], eye[1][5][0], eye[1][6][0], eye[1][7][0])
        fmt.Printf(" %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv \n", eye[1][0][1], eye[1][1][1], eye[1][2][1], eye[1][3][1], eye[1][4][1], eye[1][5][2], eye[1][6][1], eye[1][7][1])
        fmt.Printf(" %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv |  %dmv \n", eye[1][0][2], eye[1][1][2], eye[1][2][2], eye[1][3][2], eye[1][4][2], eye[1][5][1], eye[1][6][2], eye[1][7][2])
        fmt.Printf("==============================================================\n")

        //ELBA-0 LANE 0 + 1
        if ( (eye[0][0][0] < 20) || (eye[0][0][1] < 20) || (eye[0][0][2] < 20) || (eye[0][1][0] < 20) || (eye[0][1][1] < 20) || (eye[0][1][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-0 GB1 0x0F\n");
            cmdStr := "ovs-appctl l1/phy_loopback 1 0x0F 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            fmt.Printf(" ERROR: Flapping ELBA-0 GB1 0x0F\n");
            cmdStr = "ovs-appctl l1/phy_loopback 1 0x0F 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 1 0x0F 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 1 0x0F 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(10) * time.Second)
            eyefix++
        }

        //ELBA-0 LANE 2 + 3
        if ( (eye[0][2][0] < 20) || (eye[0][2][1] < 20) || (eye[0][2][2] < 20) || (eye[0][3][0] < 20) || (eye[0][3][1] < 20) || (eye[0][3][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-0 GB1 0xF0\n");
            cmdStr := "ovs-appctl l1/phy_loopback 1 0xF0 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            fmt.Printf(" ERROR: Flapping ELBA-0 GB1 0xF0\n");
            cmdStr = "ovs-appctl l1/phy_loopback 1 0xF0 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 1 0xF0 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 1 0xF0 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(10) * time.Second)
            eyefix++
        }

        //ELBA-0 LANE 4 + 5
        if ( (eye[0][4][0] < 20) || (eye[0][4][1] < 20) || (eye[0][4][2] < 20) || (eye[0][5][0] < 20) || (eye[0][5][1] < 20) || (eye[0][5][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-0 GB0 0x0F\n");
            cmdStr := "ovs-appctl l1/phy_loopback 0 0x0F 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            fmt.Printf(" ERROR: Flapping ELBA-0 GB0 0x0F\n");
            cmdStr = "ovs-appctl l1/phy_loopback 0 0x0F 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 0 0x0F 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 0 0x0F 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(10) * time.Second)
            eyefix++
        }

        //ELBA-0 LANE 6 + 7
        if ( (eye[0][6][0] < 20) || (eye[0][6][1] < 20) || (eye[0][6][2] < 20) || (eye[0][7][0] < 20) || (eye[0][7][1] < 20) || (eye[0][7][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-0 GB0 0xF0\n");
            cmdStr := "ovs-appctl l1/phy_loopback 0 0xF0 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 0 0xF0 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 0 0xF0 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 0 0xF0 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(10) * time.Second)
            eyefix++
        }
 
        //ELBA-1 LANE 0 + 1
        if ( (eye[1][0][0] < 20) || (eye[1][0][1] < 20) || (eye[1][0][2] < 20) || (eye[1][1][0] < 20) || (eye[1][1][1] < 20) || (eye[1][1][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-1 GB3 0x0F\n");
            cmdStr := "ovs-appctl l1/phy_loopback 3 0x0F 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            fmt.Printf(" ERROR: Flapping ELBA-1 GB3 0x0F\n");
            cmdStr = "ovs-appctl l1/phy_loopback 3 0x0F 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 3 0x0F 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 3 0x0F 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            eyefix++
        }

        //ELBA-1 LANE 2 + 3
        if ( (eye[1][2][0] < 20) || (eye[1][2][1] < 20) || (eye[1][2][2] < 20) || (eye[1][3][0] < 20) || (eye[1][3][1] < 20) || (eye[1][3][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-1 GB3 0xF0\n");
            cmdStr := "ovs-appctl l1/phy_loopback 3 0xF0 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 3 0xF0 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 3 0xF0 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 3 0xF0 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            eyefix++
        }

        //ELBA-1 LANE 4 + 5
        if ( (eye[1][4][0] < 20) || (eye[1][4][1] < 20) || (eye[1][4][2] < 20) || (eye[1][5][0] < 20) || (eye[1][5][1] < 20) || (eye[1][5][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-1 GB2 0x0F\n");
            cmdStr := "ovs-appctl l1/phy_loopback 2 0x0F 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 2 0x0F 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 2 0x0F 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 2 0x0F 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            eyefix++
        }

        //ELBA-1 LANE 6 + 7
        if ( (eye[1][6][0] < 20) || (eye[1][6][1] < 20) || (eye[1][6][2] < 20) || (eye[1][7][0] < 20) || (eye[1][7][1] < 20) || (eye[1][7][2] < 20) ) {
            fmt.Printf(" ERROR: Flapping ELBA-1 GB2 0xF0\n");
            cmdStr := "ovs-appctl l1/phy_loopback 2 0xF0 0 1 1"
            _, errGo := exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 2 0xF0 0 2 1"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            time.Sleep(time.Duration(1) * time.Second)
            cmdStr = "ovs-appctl l1/phy_loopback 2 0xF0 0 1 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            cmdStr = "ovs-appctl l1/phy_loopback 2 0xF0 0 2 0"
            _, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Printf("e", "%s return error -> %w" , cmdStr, errGo)
                err = errType.FAIL
                return
            }
            eyefix++
        }

        if ((eyefix > badeyefix) && (badeyefix < 20)) {
            badeyefix++
            //go to link check again
            goto snakelinkcheckretry
        }
    }
    //func 
*/

    //Clear stat counters
    cli.Printf("i", "clear c\n")
    command = "clear c\n"
    output, err = td3.ExecBCMshellCMD(command, 5)
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
                for pktsendloop:=0; pktsendloop<4; pktsendloop++ {
                    if td3.TaorPortMap[i].ElbaNumber == 0 {
                        command = fmt.Sprintf("tx 25 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[0].Name, td3.TaorPortMap[i].Name)
                    } else {
                        command = fmt.Sprintf("tx 25 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[16].Name, td3.TaorPortMap[i].Name)
                    }
                    cli.Printf("i", "%s\n", command)
                    output, err = td3.ExecBCMshellCMD(command, 5)
                    if err != errType.SUCCESS {
                        return
                    }
                    time.Sleep(time.Duration(100) * time.Millisecond)
                }
            }
            for i:=0; i<2; i++ {
                for pktsendloop:=0; pktsendloop<4; pktsendloop++ {
                    if i == 0 {
                        command = fmt.Sprintf("tx 75 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[32].Name, td3.TaorPortMap[55].Name)
                    } else {
                        command = fmt.Sprintf("tx 75 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[48].Name, td3.TaorPortMap[55].Name)
                    }
                    cli.Printf("i", "%s\n", command)
                    output, err = td3.ExecBCMshellCMD(command, 5)
                    if err != errType.SUCCESS {
                        return
                    }
                    time.Sleep(time.Duration(100) * time.Millisecond)
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
                output, err = td3.ExecBCMshellCMD(command, 5)
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
                output, err = td3.ExecBCMshellCMD(command, 5)
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
                output, err = td3.ExecBCMshellCMD(command, 5)
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
        var ElbaPortminBandwidth uint64 = 11250000000  //bandwidth calculation using 1000 byte packets
        var Elba0bw, Elba1bw uint64
        var Lag521ExtPortminBandWidth uint64 = 0
        var Lag522ExtPortminBandWidth uint64 = 0
        var rc int = 0
        var printRxBandwidth = 1
        var bwERROR, bwERRORtotal int = 0, 0
        var qsfpSWbug int = 0
        var qsfpSWbugmap = []int{0,0,0,0,0,0,0} 
        var qsfpFCScnt = []int{0,0,0,0,0,0,0} 
        printRxBwTime := time.Now()

        if (int(pkt_size) > 0) && (int(pkt_pattern) > 0) {
            if (int(pkt_size) < 1000) {
                ElbaPortminBandwidth = uint64((float64(pkt_size)/float64(1000)) * float64(ElbaPortminBandwidth)) 
            }
        }
        

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


        if PollErrorAtEnd > 0 {
            fmt.Printf(" Sleeping for %d seconds.  Test will poll errors at the very end of the test\n", duration)
            time.Sleep(time.Duration(duration) * time.Second)
        }

        for {
            var StatRxBytes string
            var StatFCS string
readStatsAgain:
            // Get rx bytes for all ports and check them below 
            StatRxBytes, err = td3.GetRmonStat_AllPorts("CLMIB_RBYT") 
            if err != errType.SUCCESS {
                cli.Printf("e", "Error reading/parsing CLMIB_RBYT for all ports\n")
                rc = errType.FAIL
                goto snaketestend
            }
            // Get FCS error for all ports 
            StatFCS, err = td3.GetRmonStat_AllPorts("CLMIB_RFCS") 
            if err != errType.SUCCESS {
                cli.Printf("e", "Error reading/parsing CLMIB_RFCS for all ports\n")
                rc = errType.FAIL
                goto snaketestend
            }


            //check for s/w isuse that flaps the links on all the qsfp ports.  check if all qsfp ports have low stats
            {
                for i:=48; i < 54; i++ {
                    var RxBytes uint64
                    var FCSerror uint64
                    var MinBandWidth100G uint64 = 11500000000
                    if test_type == td3.SNAKE_TEST_ENVIRONMENT {
                        MinBandWidth100G = 3400000000
                    }
                    RxBytes, err = td3.MacStatRxByteSecond(StatRxBytes, i)
                    if err != errType.SUCCESS {
                        cli.Printf("e", "Port-%d (%s): Error reading/parsing RX Byte Second\n", i+1 , td3.TaorPortMap[i].Name)
                        goto snaketestend
                        rc = errType.FAIL
                    }
                    if RxBytes < MinBandWidth100G {
                        qsfpSWbugmap[i-48] = 1; 
                    }

                    FCSerror, err = td3.MacStatFCSerror(StatFCS, i)
                    if err != errType.SUCCESS {
                        cli.Printf("e", "Port-%d (%s): Error reading/parsing fcs error\n", i+1 , td3.TaorPortMap[i].Name)
                        rc = errType.FAIL
                    }
                    if FCSerror == 1 {
                        qsfpFCScnt[i-48] = 1; 
                    }
                }
                qsfpSWbugmap[6] = qsfpSWbugmap[0] + qsfpSWbugmap[1] + qsfpSWbugmap[2] + qsfpSWbugmap[3] + qsfpSWbugmap[4] + qsfpSWbugmap[5]
                qsfpFCScnt[6] = qsfpFCScnt[0] + qsfpFCScnt[1] + qsfpFCScnt[2] + qsfpFCScnt[3] + qsfpFCScnt[4] + qsfpFCScnt[5]
                if (qsfpSWbugmap[6] == 6) /*&& (qsfpFCScnt[6] == 1)*/ && (qsfpSWbug == 0) {
                    cli.Printf("i", "qsfpSWbugmap=%d qsfpFCScnt=%d qsfpSWbug=%d\n", qsfpSWbugmap, qsfpFCScnt, qsfpSWbug)
                    qsfpSWbug = 1
                    time.Sleep(time.Duration(2000) * time.Millisecond)
                    for j:=48;j<54;j++ {
                        cli.Printf("i", "Clear 100G Counters Ports\n")
                        command = fmt.Sprintf("clear count %s", td3.TaorPortMap[j].Name )
                        output, err = td3.ExecBCMshellCMD(command, 5)
                        if err != errType.SUCCESS {
                            return
                        }
                    }
                    for pktsendloop:=0; pktsendloop<4; pktsendloop++ {
                        command = fmt.Sprintf("tx 75 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", td3.TaorPortMap[48].Name, td3.TaorPortMap[55].Name)
                        cli.Printf("i", "%s\n", command)
                        output, err = td3.ExecBCMshellCMD(command, 5)
                        if err != errType.SUCCESS {
                            return
                        }
                        time.Sleep(time.Duration(1) * time.Second)
                    }
                    
                    time.Sleep(time.Duration(1) * time.Second)
                    time.Sleep(time.Duration(1) * time.Second)
                    time.Sleep(time.Duration(1) * time.Second)
                    time.Sleep(time.Duration(1) * time.Second)
                    time.Sleep(time.Duration(1) * time.Second)
                    goto readStatsAgain
                }
            }
            //end check for s/w isuse on qsfp ports


            

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
                    cli.Printf("e", "Port-%d (%s): Error reading/parsing RX Byte Second\n", i+1 , td3.TaorPortMap[i].Name)
                    goto snaketestend
                    rc = errType.FAIL
                }
                if printRxBandwidth == 1 {
                    fmt.Printf("Port-%d %d/s\n", i, RxBytes)
                }

                if test_type == td3.SNAKE_TEST_LINE_RATE || test_type == td3.SNAKE_TEST_ENVIRONMENT {
                    //lag521
                    if (i < 16) &&  (RxBytes < Lag521ExtPortminBandWidth) { 
                        cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i+1 , td3.TaorPortMap[i].Name, RxBytes, Lag521ExtPortminBandWidth)
                        rc = errType.FAIL
                    }
                    //lag522
                    if (i >= 16) && (i < 31) {
                        if RxBytes < Lag522ExtPortminBandWidth { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i+1 , td3.TaorPortMap[i].Name, RxBytes, Lag522ExtPortminBandWidth)
                            bwERROR = bwERROR + 1
                        }
                    }
                    //TD3 25G Snake ports
                    if (i >= 32) && (i < 48) {
                        if RxBytes < MinBandWidth25G { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i+1 , td3.TaorPortMap[i].Name, RxBytes, MinBandWidth25G)
                            bwERROR = bwERROR + 1
                        }
                    }

                    //TD3 25G Snake ports
                    if (i >= 48) && (i < 54) {
                        if RxBytes < MinBandWidth100G { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i+1 , td3.TaorPortMap[i].Name, RxBytes, MinBandWidth100G)
                            bwERROR = bwERROR + 1
                        }
                    }
                    //Internal Port going to Elba
                    if i >= td3.TAOR_INTERNAL_PORT_START {
                        var port uint32 = uint32(i - td3.TAOR_INTERNAL_PORT_START)
                        if (elba_port_mask & (1<<port)) > 0 {
                            if RxBytes < ElbaPortminBandwidth { 
                                cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i+1 , td3.TaorPortMap[i].Name, RxBytes, ElbaPortminBandwidth)
                                bwERROR = bwERROR + 1
                            }
                        }
                    }
                } else {
                    //lag521
                    if (i < (td3.TAOR_NUMB_EXT_PORT/2)) &&  (RxBytes < Lag521ExtPortminBandWidth) { 
                        cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i+1 , td3.TaorPortMap[i].Name, RxBytes, Lag521ExtPortminBandWidth)
                        bwERROR = bwERROR + 1
                    }
                    //lag522
                    if (i >= (td3.TAOR_NUMB_EXT_PORT/2)) && (i < td3.TAOR_NUMB_EXT_PORT) {
                        if RxBytes < Lag522ExtPortminBandWidth { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i+1 , td3.TaorPortMap[i].Name, RxBytes, Lag522ExtPortminBandWidth)
                            bwERROR = bwERROR + 1
                        }
                    }
                }
                FCSerror, err = td3.MacStatFCSerror(StatFCS, i)
                if err != errType.SUCCESS {
                    cli.Printf("e", "Port-%d (%s): Error reading/parsing fcs error\n", i+1 , td3.TaorPortMap[i].Name)
                    rc = errType.FAIL
                }              
                if FCSerror > 0 {
                    if (i >= 48) && (i < 54) {
                        if (qsfpSWbug == 1 && FCSerror > 1) || (qsfpSWbug==0) {
                            cli.Printf("e", "Port-%d (%s) has %d FCS Errors\n", i+1 , td3.TaorPortMap[i].Name, FCSerror)
                            rc = errType.FAIL
                        }
                    } else {
                        cli.Printf("e", "Port-%d (%s) has %d FCS Errors\n", i+1 , td3.TaorPortMap[i].Name, FCSerror)
                        rc = errType.FAIL
                    }
                }
            } //end for i:=0; i < td3.TAOR_TOTAL_PORTS; i++ 

            //check elba for errors
            {
                for elba:=0;elba<NUMBER_ELBAS;elba++ {
                    mibs, _ := Elba_Get_Mac_Stats_Into_Struct(int(elba), elba) 
                    for portNumber, mibStats := range mibs  {
                        if mibStats.FRAMES_RX_BAD_FCS > 0 {
                            cli.Printf("e", "ELBA-%d Port-%d has %d Rx FCS Errors\n", elba, portNumber, mibStats.FRAMES_RX_BAD_FCS)
                            rc = errType.FAIL
                        }
                        if mibStats.FRAMES_RX_BAD_ALL > 0 {
                            cli.Printf("e", "ELBA-%d Port-%d has %d Rx BAD ALL Errors\n", elba, portNumber, mibStats.FRAMES_RX_BAD_ALL)
                            rc = errType.FAIL
                        }
                    }
                }
            }


            printRxBandwidth = 0
            time.Sleep(time.Duration(500) * time.Millisecond)
            if bwERROR > 0 {
                bwERRORtotal = bwERRORtotal+1
                bwERROR=0
            }
            if bwERRORtotal > 1 {
                rc = errType.FAIL
            }


            //start temp sesnor code
            {
                var TD3highTemp float64 = 0
                //Temperature Check on Trident3
                current_temperatures, _, errtd3 := td3.CheckTemperatures("TD3", TD3MaxTemp /*td3.TD3_MAX_TEMP*/)
                if errtd3 != errType.SUCCESS {
                    cli.Printf("e", "Reading Trident3 Temperatures Failed\n")
                    rc = errType.FAIL
                }
                for i:=0;i<len(current_temperatures);i++ {
                    if current_temperatures[i] > TD3highTemp { TD3highTemp = current_temperatures[i] }
                }

                gbTemperatures, gbRc := td3.GearboxGetTemperatures("TSENSOR-GB")
                if gbRc != errType.SUCCESS {
                    cli.Printf("e", "Reading Gearbox Temperatures Failed\n")
                    rc = errType.FAIL
                } else {
                    for i:=0;i<len(gbTemperatures);i++ {
                        fmt.Printf(" GB-%d %f\n", i, gbTemperatures[i]) 
                        if int(gbTemperatures[i]) > TD3MaxTemp {
                            cli.Printf("e", "BROADCOM GEARBOX-%d (zero based):  Current temperature Reading %d is exceeding threshold of %d\n", i, int(gbTemperatures[i]), TD3MaxTemp)
                            rc = errType.FAIL
                        }
                    }
                }

                retimerTemperatures, retimerRc := td3.RetimerGetTemperatures("TSENSOR-RETIMER")
                if retimerRc != errType.SUCCESS {
                    cli.Printf("e", "Reading Retimer Temperatures Failed\n")
                    rc = errType.FAIL
                } else {
                    for i:=0;i<len(retimerTemperatures);i++ {
                        fmt.Printf(" RETIMER-%d %f\n", i, retimerTemperatures[i])
                        if int(retimerTemperatures[i]) > TD3MaxTemp {
                            cli.Printf("e", "BROADCOM RETIMER-%d (zero based):  Current temperature Reading %d is exceeding threshold of %d\n", i, int(retimerTemperatures[i]), TD3MaxTemp)
                            rc = errType.FAIL
                        }
                    }
                }


                //check elba temperature
                {
                    for i:=0;i<NUMBER_ELBAS;i++ {
                        var tsensor_string string = "TSENSOR-ASIC" + strconv.Itoa(i)
                        ElbaTemp := []float64{}
                        
                        ElbaTemp, _ = taorfpga.GetTemperature(tsensor_string)
                        if int(ElbaTemp[0]) > ElbaMaxTemp {
                            cli.Printf("e", "Elba-%d:  Temperature sensor Current Reading %d is exceeding threshold of %d\n", i, int(ElbaTemp[0]), ElbaMaxTemp)
                            rc = errType.FAIL
                        }
                    }
                }
                t2 := time.Now()
                diff := t2.Sub(t1)
                fmt.Println(" Elapsed Time=",diff," Duration=",duration," TD3 High Temp=", TD3highTemp )

                logstr := fmt.Sprintln("logger Elapsed Time=",diff," Duration=",duration," TD3 High Temp=", TD3highTemp )
                exec.Command("sh", "-c", logstr).Output()
                //TD3MaxTemp, ElbaMaxTemp
                //{"TSENSOR-ASIC0", taorfpga.GetTemperature},
                //{"TSENSOR-ASIC1", taorfpga.GetTemperature},
                //{"TSENSOR-1", tmp451.GetTemperature},
                //{"TSENSOR-2", lm75a.GetTemperature},
                //{"TSENSOR-3", lm75a.GetTemperature},
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
            } //end temp sesnor code

            if rc == errType.FAIL {
                fmt.Printf(" ERR BREAK\n")
                err = errType.FAIL
                break
            }


        } //for loop until duration break or error break

    } //error check bracket

snaketestend:

    if test_type == td3.SNAKE_TEST_LINE_RATE || test_type == td3.SNAKE_TEST_ENVIRONMENT{
        command = "port " + td3.TaorPortMap[0].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[16].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[32].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[48].Name +" enable=false"
        td3.ExecBCMshellCMD(command, 5)
    } else {
        command = "port " + td3.TaorPortMap[0].Name +" enable=false"
        command = command + ";port " + td3.TaorPortMap[((td3.TAOR_EXTERNAL_25G_PORTS+td3.TAOR_EXTERNAL_100G_PORTS)/2)].Name +" enable=false"
        td3.ExecBCMshellCMD(command, 5)
    }

    time.Sleep(time.Duration(2000) * time.Millisecond) 
    Elba_Get_Mac_Stats(0)
    Elba_Get_Mac_Stats(1)
    for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
        td3.PrintPortRmonStats(i)
    }
    for i:=td3.TAOR_INTERNAL_PORT_START; i<(td3.TAOR_INTERNAL_PORT_START+td3.TAOR_INTERNAL_PORTS); i++ {
        td3.PrintPortRmonStats(i)
    }

    //No return output to check on this command
    cli.Printf("i", "Disabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=false"
    td3.ExecBCMshellCMD(command, 5)

    //No return output to check on this command
    cli.Printf("i", "Disabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=false"
    td3.ExecBCMshellCMD(command, 5)




    fmt.Printf("\n")
    td3.DumpRxTxCounters()
    fmt.Printf("\n")

    //Check Elba for memory correctable ecc errors
    if rc = ElbaCheckECC(0, 1, 0, 0); rc != errType.SUCCESS {
        err = errType.FAIL
    }
    if rc = ElbaCheckECC(1, 1, 0, 0); rc != errType.SUCCESS {
        err = errType.FAIL
    } 

    //CLEANUP AFTER TEST IS DONE
    //restore rpm values
    if Fanspeed > 60 {
        for j:=0; j<MAXFANMODULES; j++ {
            hwdev.FanWriteReg(fan_MAP[j].dev, uint32(0xAA + fan_MAP[j].fanNum), pwm_backup[j])
        }
    }
    //disable GB Loopback if it was set
    if (GBloopback == SNAKE_GB_LINE_LPBK  ) {      //ELBA Side
        rc = BCM_GearBox_Set_Loopback(GB_LOOPBACK_LINE_SIDE, GB_DIGITAL_PMD_LOOPBACK, GB_LOOPBACK_DISABLE)
    }
    if (GBloopback == SNAKE_GB_HOST_LPBK  ) {      //TD3 Side
        rc = BCM_GearBox_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_DISABLE)
    } 
    //disable Retimer Loopback if it was set
    if (Retimerloopback == SNAKE_GB_LINE_LPBK  ) {      //Port Side
        rc = BCM_Retimer_Set_Loopback(GB_LOOPBACK_LINE_SIDE, GB_DIGITAL_PMD_LOOPBACK, GB_LOOPBACK_DISABLE)
    }
    if (Retimerloopback == SNAKE_GB_HOST_LPBK  ) {      //TD3 Side
        rc = BCM_Retimer_Set_Loopback(GB_LOOPBACK_HOST_SIDE, GB_REMOTE_PMD_LOOPBACK, GB_LOOPBACK_DISABLE)
    } 

    /* For compile error that var is not used */
    if td3.TaorPortMap[0].ElbaNumber > 100000 {
            fmt.Printf("%s\n", output)
    }
    
    if err == errType.SUCCESS && rc == errType.SUCCESS {
        cli.Printf("i", "SWITCH SNAKE TEST PASSED\n\n")
    } else {
        cli.Printf("e", "SWITCH SNAKE TEST FAILED\n\n")
    }

    return


}
