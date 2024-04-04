package liparifpga


import (
    "fmt"
    "math"
    "strconv"
    "common/cli"
    "common/errType"
)


// ***********************************************************************************
// *
// *   Get inner and outer fan RPM from one of the four fan modules
// *
// ***********************************************************************************
func FAN_Get_RPM(fanNumber uint32) (inner uint32, outer uint32, err int) {

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_RPM.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := LipariReadU32(LIPARI_FPGA0, FPGA0_FAN0_TACH_REG + ( 4 * uint64(fanNumber)) )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    inner = (90000*60) / ((data32 & FPGA0_FAN0_TACH_INLET_RPM_MASK) >> FPGA0_FAN0_TACH_INLET_RPM_SHIFT) 
    outer = (90000*60) / ((data32 & FPGA0_FAN0_TACH_OUTLET_RPM_MASK) >> FPGA0_FAN0_TACH_OUTLET_RPM_SHIFT) 

    return
}


// ***********************************************************************************
// *
// *   Get the airflow direction of the fans
// *
// ***********************************************************************************
func FAN_Get_AirFlow_Direction() (fan_air_direction int, err int) {

    data32, errGo := LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_STAT_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }
    //fan present is 0 for present, 1 for not present
    if (data32 &  FPGA0_FAN_STAT_PORT_SIDE_INTAKE_MASK) == FPGA0_FAN_STAT_PORT_SIDE_INTAKE_MASK {
        fan_air_direction = AIRFLOW_FRONT_TO_BACK
    } else if (data32 &  FPGA0_FAN_STAT_PORT_SIDE_INTAKE_MASK) == 0x00 {
        fan_air_direction = AIRFLOW_BACK_TO_FRONT
    } else {
        fan_air_direction = AIRFLOW_MIXED_ERROR
    }
    return
}


// ***********************************************************************************
// *
// *   Set a fans PWM setting
// *
// ***********************************************************************************
func FAN_Set_PWM(fanNumber uint32, pwmPercent uint32) (err int) {

    var pwmMask, pwmShift uint32
    var pwmVal uint32

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Set_PWM.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_PWM_CTRL_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    if pwmPercent > 100 {
        pwmPercent = 100
    }

    pwmVal = uint32(math.Round(float64(pwmPercent * 255) / float64(100)))
    pwmVal = pwmVal & 0xFF

    
    switch fanNumber {
        case 0: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN0_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN0_SHIFT
        case 1: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN1_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN1_SHIFT
        case 2: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN2_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN2_SHIFT
        case 3: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN3_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN3_SHIFT
    }

    data32 = data32 & (^(pwmMask))
    data32 = data32 | ((pwmVal<<pwmShift) & pwmMask)
    LipariWriteU32(LIPARI_FPGA0, FPGA0_FAN_PWM_CTRL_REG, data32)

    return
}


// ***********************************************************************************
// *
// *   Get a fans PWM setting.  This number is 0-255, it is not a percentage
// *
// ***********************************************************************************
func FAN_Get_PWM(fanNumber uint32) (pwm uint32, err int) {
    var pwmMask, pwmShift uint32

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_PWM.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_PWM_CTRL_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    switch fanNumber {
        case 0: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN0_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN0_SHIFT
        case 1: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN1_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN1_SHIFT
        case 2: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN2_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN2_SHIFT
        case 3: 
            pwmMask  = FPGA0_FAN_PWM_CTRL_FAN3_MASK 
            pwmShift = FPGA0_FAN_PWM_CTRL_FAN3_SHIFT
    }

    pwm = ((data32 & pwmMask) >> pwmShift)

    return
}


// ***********************************************************************************
// *
// *   Get a fans power setting.  1 = on, 0 = off
// *
// ***********************************************************************************
func FAN_Get_PowerOn_Status(fanNumber uint32) (powerOn uint32, err int) {
    var powerMask uint32

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_PowerOn_Status.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_CTRL_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    switch fanNumber {
        case 0: 
            powerMask  = FPGA0_FAN_CTRL_FAN_PWR0 
        case 1: 
            powerMask  = FPGA0_FAN_CTRL_FAN_PWR1 
        case 2: 
            powerMask  = FPGA0_FAN_CTRL_FAN_PWR2 
        case 3: 
            powerMask  = FPGA0_FAN_CTRL_FAN_PWR3 
    }

    if (data32 & powerMask) > 0 {
        powerOn = 1
    } else {
        powerOn = 0
    }
    return
}


// ***********************************************************************************
// *
// *   See if the FPGA is throwing a fan error or alert
// *
// ***********************************************************************************
func FAN_Get_Fault(fanNumber uint32) (fanErr uint32, err int) {
    var errorMask, alertMask uint32

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_Fault.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_STAT_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    switch fanNumber {
        case 0: 
            errorMask = FPGA0_FAN_STAT_FAN0_ERROR 
            alertMask = FPGA0_FAN_STAT_FAN0_ALERT
        case 1: 
            errorMask = FPGA0_FAN_STAT_FAN1_ERROR 
            alertMask = FPGA0_FAN_STAT_FAN1_ALERT
        case 2: 
            errorMask = FPGA0_FAN_STAT_FAN2_ERROR 
            alertMask = FPGA0_FAN_STAT_FAN2_ALERT
        case 3: 
            errorMask = FPGA0_FAN_STAT_FAN3_ERROR 
            alertMask = FPGA0_FAN_STAT_FAN3_ALERT
    }

    fanErr = 0
    if (data32 &  errorMask) > 0x00 {
        fanErr = 1
    }
    if (data32 &  alertMask) > 0x00 {
        fanErr = 1
    }
    return
}


// ***********************************************************************************
// *
// *   Check if Fan is present
// *
// ***********************************************************************************
func FAN_Get_Module_present(fanNumber uint32) (present bool, err int) {

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_Module_present.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_STAT_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    present = false
    //fan present is 0 for present, 1 for not present
    if (data32 &  (FPGA0_FAN_STAT_REG_PRESENT0 << (FPGA0_FAN_STAT_REG_PRESENT0_SHIFT + fanNumber))) > 0 {
        present = true
    }
    return
}


// ***********************************************************************************
// *
// *   Set fans to a default RPM
// *
// ***********************************************************************************
func Fan_Init() (err int) {
    var i uint32

    for i=0; i<MAXFAN; i++ {
        present, _ := FAN_Get_Module_present(i)
        if present == false {
            cli.Printf("e", " Error: FanInit.  Fan-%d is showing not present at the fpag", i)
            err = errType.FAIL 
        }
    }


    for i=0; i<MAXFAN; i++ {
        rc := FAN_Set_PWM(i, 102)   //40% PWM
        if rc != errType.SUCCESS {
            cli.Printf("e", " Error: FanInit.  Fan-%d set pwm failed", i)
            err = errType.FAIL 
        }
    }
    return
}


// ***********************************************************************************
// *
// *   Display Fan Status
// *
// * root@sonic:/home/admin/eeupdate# ./fan.bash
// *
// *
// *            prsnt     rev     dir   power   error     pwm   inRPM  outRPM
// *            =====     ===     ===   =====   =====     ===   =====  ======
// * fan0:         1       3     red      on       0    0x40    2779    2374
// * fan1:         1       3     red      on       0    0x40    2720    2390
// * fan2:         1       3     red      on       0    0x40    2644    2351
// * fan3:         1       3     red      on       0    0x40    2750    2405
// *
// ***********************************************************************************
func DispFanStatus(devName string) (err int) {

    //var rc int
    var outStr string
    var i uint32
    FanHeader  := []string {"prsnt","power", "error", "pwm", "inRPM", "outRPM"}
    FanHeader1 := []string {"-----","-----", "-----", "---", "-----", "------"}

    outStr = fmt.Sprintf("%-20s", "NAME")
    for _, title := range(FanHeader) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    cli.Printf("i", "%s\n", outStr)

    outStr = fmt.Sprintf("%-20s", "----")
    for _, title := range(FanHeader1) {
        outStr = outStr + fmt.Sprintf("%-10s", title)
    }
    cli.Printf("i", "%s\n", outStr)

    for i=0; i<MAXFAN; i++ {
        inner, outer, rc := FAN_Get_RPM(i)
        if rc != errType.SUCCESS {
            cli.Printf("i", "%-20s RPM = ERROR READING RPM\n", "FAN_1")
            err = -1
        } 

        present, _ := FAN_Get_Module_present(i)

        powerOn, _ := FAN_Get_PowerOn_Status(i)

        fanErr, _ := FAN_Get_Fault(i) 

        pwm, _ := FAN_Get_PWM(i) 

        fanStr := fmt.Sprintf("FAN-%d", i)
        cli.Printf("i", "%-20s%-10s%-10s%-10s%-10s%-10s%-10s\n", fanStr, strconv.FormatBool(present), strconv.Itoa(int(powerOn)), strconv.Itoa(int(fanErr)),strconv.Itoa(int(pwm)), strconv.Itoa(int(inner)),  strconv.Itoa(int(outer)))
    }

    return
}


