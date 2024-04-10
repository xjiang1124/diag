/* Notes
 
*/ 
 
package lipari

import (
    "fmt"
    "strconv"
    "strings"
    "common/cli"
    "common/dcli"
    "common/misc"
    "common/errType"
    "device/fpga/liparifpga"
    "device/tempsensor/lm75a"
    "device/tempsensor/tmp451"
    "device/powermodule/isl69247"
    "device/powermodule/mp8796"
    "device/powermodule/tps25990"
    "device/powermodule/tps536c7"
    "device/powermodule/tps53688"
    "device/psu/dps2100" 
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "math"
    "os/exec"
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
}


func Fan_Check_RPM(fanNumber int, fanPWM int, tollerance int) (err int) {
    var innerRPM [liparifpga.MAXFAN]uint32
    var outerRPM [liparifpga.MAXFAN]uint32
    var fanFail int = 0
    var expRPM int

    innerRPM[fanNumber], outerRPM[fanNumber], fanFail =  liparifpga.FAN_Get_RPM(fan_MAP[fanNumber].fanNum) 
    if fanFail != errType.SUCCESS {
        cli.Printf("e", "FAN_Get_RPM Failed on fan-%d  (Silkscreen Number-%d)\n", fan_MAP[fanNumber].fanNum, fan_MAP[fanNumber].silkScreenFan)
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


// Lipari's FPGA will keep the fans at a certain RPM to keep elba from over-heating
// So cannot test below 50% PWM, or the fpga will bring the pwm back up to at least 50%
func Fan_RPM_test(tollerance int)(err int) {
    var pwm_backup [liparifpga.MAXFAN]byte 
    var start_pwm byte
    var pct [liparifpga.MAXFAN]byte 
    var presenceFailMask uint32 = 0
    var fanFail int = errType.SUCCESS
    fanspeed := []int{ 80, 70, 100, 50 }  // Speeds to test with
    var i uint32
    

    dcli.Printf("i", "Switch Fan Test: tollerance=%d%% \n", tollerance)

    //check if fan is present
    for j:=0; j<liparifpga.MAXFAN; j++ {
        present, rc := liparifpga.FAN_Get_Module_present(uint32(j)) 
        if rc != errType.SUCCESS { 
            cli.Printf("e", "Reading Fan Presence Singals failed\n")
            fanFail = errType.FAIL 
        }
        if present == false {
            cli.Printf("e", "Fan Module-%d not present (Silkscreen Number-%d)\n", j, fan_MAP[j].silkScreenFan)
            presenceFailMask = presenceFailMask + (1<<uint32(j))
        }
    }

    //check fan direction (they all need to be the same directional airflow)
    data32, _ := liparifpga.LipariReadU32(liparifpga.LIPARI_FPGA0, liparifpga.FPGA0_FAN_STAT_REG)
    data32 = (data32 >> liparifpga.FPGA0_FAN_STAT_PORT_SIDE_SHIFT)
    for j:=0; j<liparifpga.MAXFAN; j++ {
        if (data32 & (1<<uint32(j))) == (1<<uint32(j)) {
            dcli.Printf("i", "fan-%d (Silkscreen Number-%d): Airflow Direction; Front to Back\n", fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
        } else {
            dcli.Printf("i", "fan-%d (Silkscreen Number-%d): Airflow Direction; Back to Front\n", fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
        }
    }

    data32, _ = liparifpga.LipariReadU32(liparifpga.LIPARI_FPGA0, liparifpga.FPGA0_FAN_STAT_REG)
    if (data32 & liparifpga.FPGA0_FAN_STAT_PORT_SIDE_INTAKE_MASK) != liparifpga.FPGA0_FAN_STAT_PORT_SIDE_INTAKE_MASK {
        if (data32 & liparifpga.FPGA0_FAN_STAT_PORT_SIDE_INTAKE_MASK) != 0x00 {
            cli.Printf("e", "Mismatched Fans for airflow direction.   Check all the fans are front-to-back, or back-to-front\n")
            fanFail = errType.FAIL
        }
    }
            

    //backup rpm values
    for i=0; i<liparifpga.MAXFAN; i++ {
        data32, _ = liparifpga.FAN_Get_PWM(i)
        pwm_backup[i] = uint8(data32)
    }

    //halt here if fans had any error and don't do the pwm testing
    if fanFail == errType.SUCCESS {
        for i:=0; i<len(fanspeed); i++ {
           dcli.Printf("i","Testing Fans at PWM-%d\n", fanspeed[i])
           for j:=0; j<liparifpga.MAXFAN; j++ {
               if i == 0 {
                   start_pwm = pwm_backup[j]     //start pwm is from the backup we read
               } else {
                   start_pwm = byte((fanspeed[i-1] * 255) / 100)     //get the start pwm from the list we use to set the pwm if not the first loop
               }
               pct[j] = byte(int((int(start_pwm) * 100)/255))
           }
           // Set final PWM for test loop
           for j:=0; j<liparifpga.MAXFAN; j++ {
               if (presenceFailMask & (1<<uint32(j))) > 0 {
                   continue
               }
               err = liparifpga.FAN_Set_PWM(fan_MAP[j].fanNum, uint32(fanspeed[i]))
               if err != errType.SUCCESS {
                   cli.Printf("e", "FAN_Set_PWM Failed on fan-%d (Silkscreen Number-%d)\n", fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan)
                   fanFail = errType.FAIL
               }
           }


           misc.SleepInSec(8) //give fan time to change rpm
           for j:=0; j<liparifpga.MAXFAN; j++ {
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
        for j:=0; j<liparifpga.MAXFAN; j++ {
            var pwmPercent uint32 = uint32(math.Round((float64(pwm_backup[j])*100) / float64(255)))
            liparifpga.FAN_Set_PWM(uint32(j), pwmPercent) 
        }

        //check for fan errrors/alerts
        dcli.Printf("i","Checking for Fan Alerts/Errors\n")
        data32, _ = liparifpga.LipariReadU32(liparifpga.LIPARI_FPGA0, liparifpga.FPGA0_FAN_STAT_REG)
        for j:=0; j<liparifpga.MAXFAN; j++ {
            if (data32 & (1<<(liparifpga.FPGA0_FAN_STAT_ALERT_SHIFT + i))) > 0 {
                cli.Printf("e", "FAN ALERT DETECTED fan-%d (Silkscreen Number-%d).  FPGA Reg 0x%x = 0x%x\n", fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan,  liparifpga.FPGA0_FAN_STAT_REG ,data32)
                fanFail = errType.FAIL
            }
            if (data32 & (1<<(liparifpga.FPGA0_FAN_STAT_ERROR_SHIFT + i))) > 0 {
                cli.Printf("e", "FAN ERROR DETECTED fan-%d (Silkscreen Number-%d).  FPGA Reg 0x%x = 0x%x\n", fan_MAP[j].fanNum, fan_MAP[j].silkScreenFan,  liparifpga.FPGA0_FAN_STAT_REG ,data32)
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
        dcli.Printf("i","SWITCH FANRPM TEST PASSED\n")
    } else {
        dcli.Printf("e","SWITCH FANRPM TEST FAILED\n")
    }

    return
}



/********************* 
  root@sonic:/sys/class/hwmon/hwmon1# ls
device  name  power  subsystem  temp1_input  temp1_label  temp2_input  temp2_label  uevent
root@sonic:/sys/class/hwmon/hwmon1#
root@sonic:/sys/class/hwmon/hwmon1#
root@sonic:/sys/class/hwmon/hwmon1#
root@sonic:/sys/class/hwmon/hwmon1# ls | xargs cat
cat: device: Is a directory
k10temp
cat: power: Is a directory
cat: subsystem: Is a directory
27625
Tctl
27625
Tdie 
 
oot@sonic:/sys/class/hwmon/hwmon1# cat name
k10temp
 
*********************/
func CPU_ReadTemp(devName string) (temperature []float64, err int) {

    var args string = "cat /sys/class/hwmon/hwmon1/name"
    output, errGo := exec.Command("sh", "-c", args).Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    if strings.Contains(string(output), "k10temp") == false {
        dcli.Printf("e", " ERROR.. not seeing k10temp for cpu temperature under /sys/class/hwmon/hwmon1\n")
        err = errType.FAIL
        return
    }

    args = "cat /sys/class/hwmon/hwmon1/temp2_input"
    output, errGo = exec.Command("sh", "-c", args).Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    tempF, _ := strconv.ParseFloat(strings.TrimSuffix(string(output), "\n"), 64)
    tempF = tempF / 1000
    temperature = append(temperature, tempF)

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
    fileExists, _ := liparifpga.Path_exists("/fs/nos/home_diag/diag/tools/stressapptest")
    if fileExists == false {
        cli.Printf("e", "Unable to locate stressapptest.  Looking under path /fs/nos/home_diag/diag/tools/stressapptest.   Check that the diag package is installed\n")
        err = errType.FAIL
    }


        //Check that we can find stressapptest_arm in case someone tries to run this without the diag package installed
    fileExists, _ = liparifpga.Path_exists("stressapptest.log")
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

            //rc := X86_DDR_Check_ECC(0)
            //if rc != errType.SUCCESS {
            //    dcli.Printf("e", "ERROR: X86 MEMORY ERROR DETECTED\n")
            //    err = errType.FAIL
            //}
            dcli.Printf("w", "FIXME FIXME FIXME:  NEED TO CHECK FOR ECC CORRECTABLE ERRORS\n")
            dcli.Printf("w", "FIXME FIXME FIXME:  NEED TO CHECK FOR ECC CORRECTABLE ERRORS\n")
            dcli.Printf("w", "FIXME FIXME FIXME:  NEED TO CHECK FOR ECC CORRECTABLE ERRORS\n")
        }
    }

    if err == errType.SUCCESS {
        dcli.Printf("i","CPU MEMORY TEST PASSED\n")
    } else {
        dcli.Printf("e","CPU MEMORY TEST FAILED\n")
    }

    return
}



type VRdispfunc func(devName string)(err int) 

type VoltageTable struct {
    VoltName  string            //device name
    VRdispfuncPtr VRdispfunc    //function pointer to printout
}


func ShowPower()  (err int)  {
    var rc int = errType.SUCCESS
    vrmTitle := []string {"VBOOT", "VOUT", "POUT", "IOUT", "VIN", "PIN", "IIN"}
    voltTable := []VoltageTable { {"PSU_1", dps2100.DispVoltWattAmp},
                                  {"PSU_2", dps2100.DispVoltWattAmp},
                                  {"P12V", tps25990.DispVoltWattAmp},
                                  {"TH4_PDVDD", tps536c7.DispVoltWattAmp},
                                  {"TH4_P0V75_AVDD", tps536c7.DispVoltWattAmp},
                                  {"CPU_VDDCR", isl69247.DispVoltWattAmp},
                                  {"SOC_VDDCR", isl69247.DispVoltWattAmp},
                                  {"MEM_VDDIO", tps53688.DispVoltWattAmp},
                                  {"P3V3", mp8796.DispVoltWattAmp},
                                  {"P3V3S1", tps53688.DispVoltWattAmp},
                                  {"P3V3S2", tps53688.DispVoltWattAmp},
                                }
    var outStr string
    outStr = fmt.Sprintf("%-20s", "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    fmt.Println(outStr)


    for _, volt := range(voltTable) {
        hwinfo.EnableHubChannelExclusive(volt.VoltName)
        rc = volt.VRdispfuncPtr(volt.VoltName)
        if rc != errType.SUCCESS {
            err = rc
            fmt.Printf("%-20s    --------- ERROR READING VALUES -----------\n", volt.VoltName)
        }
    }

    return
}


/**************************************************************************** 
DEVICE      VOLTAGE MARGIN POSSIBLE
----------------------------------- 
P12V            NO  
TH4_PDVDD       YES  
TH4_P0V75_AVDD  YES  
CPU_VDDCR       YES (Need to code)
SOC_VDDCR       YES (Need to code) 
MEM_VDDIO       YES 
P3V3            YES (Need to Code)
P3V3S1          YES 
P3V3S2          YES 
 
ELBA 
---- 
ELBA_CORE       YES (Need to Code) 
ELBA_ARM        YES (Need to Code) 
VDD_DDR         YES (Need to Code)
VDDQ_DDR        YES (Need to Code) 
 
****************************************************************************/
func Margin(devName string, pct int) (err int) {
    var i2cif i2cinfo.I2cInfo
    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        return err
    }

    if pct > 10 || pct < -10 {
        cli.Printf("e", "ERROR: %s Margin is capped at +/-10%", devName)
        return errType.INVALID_PARAM
    }

    if i2cif.Comp == "TPS53688" {
        err = tps53688.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS536C7" {
        err = tps536c7.SetVMargin(devName, pct)
    }  else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
    
}



type TemperatureFunc func(devName string) (temperatures []float64, err int) 

type TemperatureTable struct {
    TemperatureDevName  string 
    TemperaturefuncPtr  TemperatureFunc 
}


func ShowTemperature()  (err int)  {
    TemperatureTitle := []string {"T1", "T2", "T3",}
    TemperatureTable := []TemperatureTable { 
                                  {"CNTR-LM75", lm75a.GetTemperature},
                                  {"REAR-LM75", lm75a.GetTemperature},
                                  {"CPU-FRNT-LM75", lm75a.GetTemperature},
                                  {"CPU-CNTR-LM75", lm75a.GetTemperature},
                                  {"CPU-REAR-LM75", lm75a.GetTemperature},
                                  {"ELBA0_TEMP", tmp451.GetTemperature},
                                  {"ELBA1_TEMP", tmp451.GetTemperature},
                                  {"ELBA2_TEMP", tmp451.GetTemperature},
                                  {"ELBA3_TEMP", tmp451.GetTemperature},
                                  {"ELBA4_TEMP", tmp451.GetTemperature},
                                  {"ELBA5_TEMP", tmp451.GetTemperature},
                                  {"ELBA6_TEMP", tmp451.GetTemperature},
                                  {"ELBA7_TEMP", tmp451.GetTemperature},
                                  {"CPU", CPU_ReadTemp},
                                  {"PSU_1", dps2100.GetTemperature},
                                  {"PSU_2", dps2100.GetTemperature},
                                }

    var outStr string
    var i int
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    outStr = fmt.Sprintf("%-20s", "NAME")
    for _, title := range(TemperatureTitle) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    fmt.Printf("%s\n", outStr)
    //fmt.Printf("-----------------------------\n")

    for _, temp := range(TemperatureTable) {
        rdTemp := []float64{}
        if temp.TemperatureDevName != "CPU" {
            hwinfo.EnableHubChannelExclusive(temp.TemperatureDevName)
        }
        rdTemp, err = temp.TemperaturefuncPtr(temp.TemperatureDevName)
        if err != errType.SUCCESS {
            fmt.Printf("ERROR: Reading temperature from dev %s failed\n", temp.TemperatureDevName) 
            return
        }

        outStr = fmt.Sprintf(fmtNameStr, temp.TemperatureDevName)

        for i=0; i<len(rdTemp);i++ {
            outStrTemp := fmt.Sprintf("%.03f", rdTemp[i])
            outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
        }      
        for  ; i<len(TemperatureTitle);i++ {  
            outStr = outStr + fmt.Sprintf(fmtStr, "-")
        }
        fmt.Printf("%s\n", outStr)
    }

    fmt.Printf("\n")


    

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
    var i uint32
    var psuPresent [liparifpga.MAXPSU]bool
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
    for i=0; i<liparifpga.MAXPSU; i++ {
        psuPresent[i], _ = liparifpga.PSU_present(i) 

    }
    for i=0; i<liparifpga.MAXPSU; i++ {
        if psuPresent[i] {
            str := fmt.Sprintf("PSU_%d", i+1)
            psuFault, rc := dps2100.ReadFanWarnFault(str) 
            if rc != errType.SUCCESS {
                fmt.Printf("%-20s RPM = ERROR READING RPM\n", "PSU_1")
                err = -1
            }

            rpm, rc := dps2100.ReadFanSpeed("PSU_1")
            if rc != errType.SUCCESS {
                fmt.Printf("%-20s RPM = ERROR READING RPM\n", "PSU_1")
                err = -1
            } 

            fmt.Printf("%-20s%-10s%-10s%-10s%-10s%-10s\n", str, "1", strconv.Itoa(int(psuFault))," ", " ",  strconv.Itoa(int(rpm)))
        }
    }

    for i=0; i<liparifpga.MAXFAN; i++ {
        inner, outer, rc := liparifpga.FAN_Get_RPM(i)
        if rc != errType.SUCCESS {
            fmt.Printf("%-20s RPM = ERROR READING RPM\n", "FAN_1")
            err = -1
        } 
        fanErr, _ := liparifpga.FAN_Get_Fault(i) 
        pwm, _ := liparifpga.FAN_Get_PWM(i) 

        fanStr := fmt.Sprintf("FAN-%d", i)
        fmt.Printf("%-20s%-10s%-10s%-10s%-10s%-10s\n", fanStr, "1", strconv.Itoa(int(fanErr)),strconv.Itoa(int(pwm)), strconv.Itoa(int(inner)),  strconv.Itoa(int(outer)))
    }
    

    return
}





