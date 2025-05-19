/* Notes
 
*/ 
 
package matera

import (
    "common/cli"
    "common/dcli"
    "common/errType"
    "common/misc"
    "device/fpga/materafpga"
    "device/psu/dps2100" 
    "fmt"
    "math"
    "os"
    "sort"
    "strconv"
    "time"
)


const (
    MAXPSU = 2
    FANPERMODULE = 2
)


//fan closer to the interior of the chassis (closest to the connector)
var rpm_inner_fan_MAP = map[int]int {
    100 : 12200,
    90 : 10750, 
    80 : 9575,
    70 : 8300,
    60 : 7100,
    50 : 5850,
    40 : 4600,
    30 : 3400,
    20 : 2100,
}


//fan closest to the rear of the chassis (air exhaust)
var rpm_outer_fan_MAP = map[int]int {
    100 : 10400,
    90 : 9350,
    80 : 8300,
    70 : 7200,
    60 : 6200,
    50 : 5500,
    40 : 4000,
    30 : 2900,
    20 : 1900,
}

type fanDevMap struct{
    fanNum        uint32
    silkScreenFan uint32
}

var fan_MAP = map[int]fanDevMap {
    0 : { fanNum:0, silkScreenFan:0 } ,  //fan 0 from presence
    1 : { fanNum:1, silkScreenFan:1 } ,  //fan 1 from presence
    2 : { fanNum:2, silkScreenFan:2 } ,  //fan 2 from presence
    3 : { fanNum:3, silkScreenFan:3 } ,  //fan 3 from presence
    4 : { fanNum:4, silkScreenFan:4 } ,  //fan 4 from presence
}


func Fan_Check_RPM(fanNumber int, fanPWM int, tollerance int) (err int) {
    var innerRPM [materafpga.MAXFAN]uint32
    var outerRPM [materafpga.MAXFAN]uint32
    var fanFail int = 0
    var expRPM int

    innerRPM[fanNumber], outerRPM[fanNumber], fanFail =  materafpga.FAN_Get_RPM(fan_MAP[fanNumber].fanNum) 
    if fanFail != errType.SUCCESS {
        cli.Printf("e", "FanSpeedGet Failed on fan-%d  (Silkscreen Number-%d)\n", fan_MAP[fanNumber].fanNum, fan_MAP[fanNumber].silkScreenFan)
        err = errType.FAIL
    } else {
        cli.Printf("i", " FanModule#=%d:Inner Fan Tollerance=%d%% RPM=%d  expRPM=%d\n", fanNumber, tollerance, innerRPM[fanNumber], rpm_inner_fan_MAP[fanPWM])
        cli.Printf("i", " FanModule#=%d:Outer Fan Tollerance=%d%% RPM=%d  expRPM=%d\n", fanNumber, tollerance, outerRPM[fanNumber], rpm_outer_fan_MAP[fanPWM])

        expRPM = rpm_inner_fan_MAP[fanPWM]
        if int(innerRPM[fanNumber]) < expRPM - ((tollerance * expRPM)/100) {
            cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Inner Fan RPM Test at %d PWM Failed.  Read RPM-%d below Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, innerRPM[fanNumber], expRPM - ((tollerance * expRPM)/100))
            fanFail = errType.FAIL
        }
        if int(innerRPM[fanNumber]) > expRPM + ((tollerance * expRPM)/100) {
            cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Inner Fan RPM Test at %d PWM Failed.  Read RPM-%d above Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, innerRPM[fanNumber], expRPM + ((tollerance * expRPM)/100) )
            fanFail = errType.FAIL
        }

        expRPM = rpm_outer_fan_MAP[fanPWM]
        if int(outerRPM[fanNumber]) < expRPM - ((tollerance * expRPM)/100) {
            cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Outer Fan RPM Test at %d PWM Failed.  Read RPM-%d below Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, outerRPM[fanNumber], expRPM - ((tollerance * expRPM)/100))
            fanFail = errType.FAIL
        }
        if int(outerRPM[fanNumber]) > expRPM + ((tollerance * expRPM)/100) {
            cli.Printf("e", "Fan Module-%d (Silkscreen Number-%d) Outer Fan RPM Test at %d PWM Failed.  Read RPM-%d above Threshold %d\n", fanNumber, fan_MAP[fanNumber].silkScreenFan, fanPWM, outerRPM[fanNumber], expRPM + ((tollerance * expRPM)/100) )
            fanFail = errType.FAIL
        }
    }

    if fanFail != errType.SUCCESS {
        fmt.Printf("DEBUG: SET ERR TO FAIL\n");
        err = errType.FAIL
    }
        
    return
}


func Fan_RPM_test(tollerance int)(err int) {
    var pwm_backup [materafpga.MAXFAN]byte 
    var start_pwm byte
    var pct [materafpga.MAXFAN]byte 
    var presenceFailMask uint32 = 0
    var fanFail int = errType.SUCCESS
    fanspeed := []int{ 100, 80, 60, 100, 50 }  // Speeds to test with
    var data32, i uint32
    

    dcli.Printf("i", "Switch Fan Test: tollerance=%d%% \n", tollerance)

    //check if fan is present
    for j:=0; j < materafpga.MAXFAN; j++ {
        present, rc := materafpga.FAN_Get_Module_present(uint32(j)) 
        if rc != errType.SUCCESS { 
            cli.Printf("e", "Reading Fan Presence Singals failed\n")
            fanFail = errType.FAIL 
        }
        if present == false {
            cli.Printf("e", "Fan Module-%d not present (Silkscreen Number-%d)\n", j, fan_MAP[j].silkScreenFan)
            presenceFailMask = presenceFailMask + (1<<uint32(j))
        }
    } 
            

    //backup rpm values
    for i=0; i<materafpga.MAXFAN; i++ {
        data32, _ = materafpga.FAN_Get_PWM(i)
        pwm_backup[i] = uint8(data32)
    }

    //halt here if fans had any error and don't do the pwm testing
    if fanFail == errType.SUCCESS {
        for i:=0; i<len(fanspeed); i++ {
           dcli.Printf("i","Testing Fans at PWM-%d\n", fanspeed[i])
           for j:=0; j<materafpga.MAXFAN; j++ {
               if i == 0 {
                   start_pwm = pwm_backup[j]     //start pwm is from the backup we read
               } else {
                   start_pwm = byte((fanspeed[i-1] * 255) / 100)     //get the start pwm from the list we use to set the pwm if not the first loop
               }
               pct[j] = byte(int((int(start_pwm) * 100)/255))
           }
           // Set final PWM for test loop
           for j:=0; j<materafpga.MAXFAN; j++ {
               if (presenceFailMask & (1<<uint32(j))) > 0 {
                   continue
               }
               err = materafpga.FAN_Set_PWM(fan_MAP[j].fanNum, uint32(fanspeed[i]))
               if err != errType.SUCCESS {
                   cli.Printf("e", "FanSpeedSet Failed on fan-%d (Silkscreen Number-%d)\n", fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
                   fanFail = errType.FAIL
               }
           }


           misc.SleepInSec(8) //give fan time to change rpm
           for j:=0; j<materafpga.MAXFAN; j++ {
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
        for j:=0; j<materafpga.MAXFAN; j++ {
            var pwmPercent uint32 = uint32(math.Round((float64(pwm_backup[j])*100) / float64(255)))
            materafpga.FAN_Set_PWM(uint32(j), pwmPercent) 
        }

        //check for fan fault
        dcli.Printf("i","Checking for Fan Fault\n")
        data32, _ = materafpga.MateraReadU32(materafpga.FPGA_FAN_STAT_REG)
        for j:=0; j<materafpga.MAXFAN; j++ {
            if (data32 & (1<<(materafpga.FPGA_FAN_STAT_REG_NO_FAULT_FAN0 + i))) == 0 {
                cli.Printf("e", "FAN FAULT DETECTED fan-%d (Silkscreen Number-%d).  FPGA Reg 0x%x = 0x%x\n", fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan,  materafpga.FPGA_FAN_STAT_REG ,data32)
                fanFail = errType.FAIL
            }
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
        dcli.Printf("i","MATERA FANRPM TEST PASSED\n")
    } else {
        dcli.Printf("e","MATERA FANRPM TEST FAILED\n")
    }

    return
}


func ShowFanInfo()  (err int)  {
    //var rc int
    var outStr string
    var i uint32
    var b2i = map[bool]int{false: 0, true: 1}
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
    for i=0; i<materafpga.MAXPSU; i++ {
            var rpm, psuFault uint32
            var rc int
            PSUdevStr := fmt.Sprintf("PSU_%d", i+1)
            psuPresentBool, _ := materafpga.PSU_present(i)
            if psuPresentBool {
                psuFault, rc = dps2100.ReadFanWarnFault(PSUdevStr) 
                if rc != errType.SUCCESS {
                    fmt.Printf("%-20s RPM = ERROR READING RPM\n", PSUdevStr)
                    err = -1
                }
                rpm, rc = dps2100.ReadFanSpeed(PSUdevStr)
                if rc != errType.SUCCESS {
                    fmt.Printf("%-20s RPM = ERROR READING RPM\n", PSUdevStr)
                    err = -1
                } 
            }
            fmt.Printf("%-20s%-10s%-10s%-10s%-10s%-10s\n", PSUdevStr, strconv.Itoa(int(b2i[psuPresentBool])), strconv.Itoa(int(psuFault))," ", " ",  strconv.Itoa(int(rpm)))
    }

    for i=0; i<materafpga.MAXFAN; i++ {
        FANdevStr := fmt.Sprintf("FAN-%d", i+1)
        inner, outer, rc := materafpga.FAN_Get_RPM(i)
        if rc != errType.SUCCESS {
            fmt.Printf("%-20s RPM = ERROR READING RPM\n", FANdevStr)
            err = -1
        } 
        fanErr, _ := materafpga.FAN_Get_Fault(i) 
        fanPresent, _ := materafpga.FAN_Get_Module_present(i) 
        pwm, _ := materafpga.FAN_Get_PWM(i) 

        fmt.Printf("%-20s%-10s%-10s%-10s%-10s%-10s\n", FANdevStr, strconv.Itoa(int(b2i[fanPresent])), strconv.Itoa(int(fanErr)),strconv.Itoa(int(pwm)), strconv.Itoa(int(inner)),  strconv.Itoa(int(outer)))
    }
    

    return
}


func TestPowercycleCPLDready(slot uint32, loopcount int) (err error) {
    var data32 uint32
    var ns int64
    wrData := []byte{0x01}
    TestTime := []int{}

    for i:=0; i<loopcount; i++ {
        fmt.Printf("Loop - %.04d", i)
        //Power off slot 
        data32, _ = materafpga.MateraReadU32(materafpga.FPGA_RESET_CONTROL_REG)
        data32 = data32 & (^(1<<slot))
        materafpga.MateraWriteU32(materafpga.FPGA_RESET_CONTROL_REG, data32)
        data32, _ = materafpga.MateraReadU32(materafpga.FPGA_P12_CONTROL_REG)
        data32 = data32 & (^(1<<slot))
        materafpga.MateraWriteU32(materafpga.FPGA_P12_CONTROL_REG, data32)
        data32, _ = materafpga.MateraReadU32(materafpga.FPGA_P03_CONTROL_REG)
        data32 = data32 & (^(1<<slot))
        materafpga.MateraWriteU32(materafpga.FPGA_P03_CONTROL_REG, data32)

        time.Sleep(time.Duration(1) * time.Second)


        //Power on slot
        data32, _ = materafpga.MateraReadU32(materafpga.FPGA_P03_CONTROL_REG)
        data32 = data32 | (1<<slot)
        materafpga.MateraWriteU32(materafpga.FPGA_P03_CONTROL_REG, data32)
        t1 := time.Now()

        //time.Sleep(time.Duration(2) * time.Second)

        data32, _ = materafpga.MateraReadU32(materafpga.FPGA_P12_CONTROL_REG)
        data32 = data32 | (1<<slot)
        materafpga.MateraWriteU32(materafpga.FPGA_P12_CONTROL_REG, data32)
        data32, _ = materafpga.MateraReadU32(materafpga.FPGA_RESET_CONTROL_REG)
        data32 = data32 | (1<<slot)
        materafpga.MateraWriteU32(materafpga.FPGA_RESET_CONTROL_REG, data32)
        for j:=0;j<60;j++ {
            //time.Sleep(time.Duration(50) * time.Millisecond)
            //i2cset -y $(($slot+2)) 0x4b 0x41 ${bifValue[$i]}

            // Open /dev/null
            nullFile, errGo := os.Open(os.DevNull)
            if errGo != nil {
        	fmt.Println("Error:", errGo)
        	return
            }

            // Store original stdout and stderr
            originalStdout := os.Stdout
            originalStderr := os.Stderr

            // Redirect stdout and stderr to /dev/null
            os.Stdout = nullFile
            os.Stderr = nullFile

            // Redirect log output to /dev/null
            //log.SetOutput(nullFile)
            _ , err := materafpga.I2c_access( slot, 0, 0x4B, uint32(len(wrData)), wrData, 0 )
            fmt.Printf("err=%v\n", err)

            // Restore original stdout and stderr
            os.Stdout = originalStdout
            os.Stderr = originalStderr
            nullFile.Close()
            if err == nil {
                break;
            }
            

        }

        elapsed := time.Since(t1)
        ns = int64(elapsed)

        //fmt.Printf("Execution time: %d ns\n", ns)
        ns = ns / 1000000
        //fmt.Printf("Execution time: %d ms\n", ns)
        TestTime = append(TestTime, int(ns))

	//fmt.Printf("Execution time: %lld ms\n", elapsed.Milliseconds)
    }

    sort.Ints(TestTime)
    for i:=0;i<len(TestTime);i++ {
        fmt.Printf("%d ms\n", TestTime[i])
    }

    //data32, _ = materafpga.MateraReadU32(materafpga.FPGA_FAN_STAT_REG)
    // MateraWriteU32(FPGA_MISC_CTRL_REG, data32)
    return
}



