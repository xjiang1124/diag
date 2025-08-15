package panareafpga


import (
    //"errors"
    //"fmt"
    "math"
    "common/cli"
    "common/errType"
)

const (
    //RPM numberator from fpga spec.  Also follows typical fan controller rpm algorigthm.
    RPMNUMERATOR  = 5400000  
)


// ***********************************************************************************
// *
// *   Get inner and outer fan RPM from one of the four fan modules
// *    FAN speed calculation :   
// *    Use this formula to calculate RPM number from TACH values used in FAN related registers.
// *
// *    RPM = 5400000/TACH
// *    example :   TACH=0x21c (540 in decimal) yields 10000 rpm.
// *
// ***********************************************************************************
func FAN_Get_RPM(fanNumber uint32) (inner uint32, outer uint32, err int) {
    inner = 0
    outer = 0

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_RPM.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }

    data32, errGo := ReadU32(FPGA_FAN0_TACH_REG + ( 4 * uint64(fanNumber)) )
    if errGo != nil {
        err = errType.FAIL
        return
    }

    if ((data32 & FPGA_FAN0_TACH_INLET_RPM_MASK) >> FPGA_FAN0_TACH_INLET_RPM_SHIFT) > 0 {
        inner = RPMNUMERATOR / ((data32 & FPGA_FAN0_TACH_INLET_RPM_MASK) >> FPGA_FAN0_TACH_INLET_RPM_SHIFT) 
    }
    if ((data32 & FPGA_FAN0_TACH_OUTLET_RPM_MASK) >> FPGA_FAN0_TACH_OUTLET_RPM_SHIFT)  > 0 {
        outer = RPMNUMERATOR / ((data32 & FPGA_FAN0_TACH_OUTLET_RPM_MASK) >> FPGA_FAN0_TACH_OUTLET_RPM_SHIFT) 
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
    var data32 uint32
    var errGo error
    var FanCtrlReg uint64

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Set_PWM.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }

    //Fan 5 is on control register 1, other 4 are on control register 0
    if fanNumber == (MAXFAN - 1) {
        FanCtrlReg = FPGA_FAN_PWM_CTRL1_REG
    } else {
        FanCtrlReg = FPGA_FAN_PWM_CTRL0_REG
    }

    data32, errGo = ReadU32(FanCtrlReg)
    if errGo != nil {
        return
    }

    if pwmPercent > 100 {
        pwmPercent = 100
    }

    pwmVal = uint32(math.Round(float64(pwmPercent * 255) / float64(100)))
    pwmVal = pwmVal & 0xFF

    
    switch fanNumber {
        case 0: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN0_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN0_SHIFT
        case 1: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN1_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN1_SHIFT
        case 2: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN2_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN2_SHIFT
        case 3: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN3_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN3_SHIFT
        case 4: 
            pwmMask  = FPGA_FAN_PWM_CTRL1_FAN4_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL1_FAN4_SHIFT
    }

    data32 = data32 & (^(pwmMask))
    data32 = data32 | ((pwmVal<<pwmShift) & pwmMask)
    WriteU32(FanCtrlReg, data32)
    return
}


// ***********************************************************************************
// *
// *   Get a fans PWM.  This returns 0-255, not the percentage
// *
// ***********************************************************************************
func FAN_Get_PWM(fanNumber uint32) (pwm uint32, err int) {
    var pwmMask, pwmShift uint32
    var data32 uint32
    var errGo error
    var FanCtrlReg uint64


    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_PWM.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }

    //Fan 5 is on control register 1, other 4 are on control register 0
    if fanNumber == (MAXFAN - 1) {
        FanCtrlReg = FPGA_FAN_PWM_CTRL1_REG
    } else {
        FanCtrlReg = FPGA_FAN_PWM_CTRL0_REG
    }

    data32, errGo = ReadU32(FanCtrlReg)
    if errGo != nil {
        err = errType.FAIL
        return
    }


    switch fanNumber {
        case 0: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN0_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN0_SHIFT
        case 1: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN1_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN1_SHIFT
        case 2: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN2_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN2_SHIFT
        case 3: 
            pwmMask  = FPGA_FAN_PWM_CTRL_FAN3_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL_FAN3_SHIFT
        case 4: 
            pwmMask  = FPGA_FAN_PWM_CTRL1_FAN4_MASK 
            pwmShift = FPGA_FAN_PWM_CTRL1_FAN4_SHIFT
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
    var mask uint32

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_PowerOn_Status.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := ReadU32(FPGA_FAN_PWR_CTRL_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    switch fanNumber {
        case 0: mask = FPGA_FAN_PWR_CTRL_FAN0_EN
        case 1: mask = FPGA_FAN_PWR_CTRL_FAN1_EN
        case 2: mask = FPGA_FAN_PWR_CTRL_FAN2_EN
        case 3: mask = FPGA_FAN_PWR_CTRL_FAN3_EN
        case 4: mask = FPGA_FAN_PWR_CTRL_FAN4_EN
    }

    if (data32 & mask) > 0 {
        powerOn = 1
    } else {
        powerOn = 0
    }
    return
}


// ***********************************************************************************
// *
// *   See if the FPGA is throwing a fan error
// *
// ***********************************************************************************
func FAN_Get_Fault(fanNumber uint32) (fanErr uint32, err int) {
    var errorMask uint32

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_Fault.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := ReadU32(FPGA_FAN_STAT_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    switch fanNumber {
        case 0: 
            errorMask = FPGA_FAN_STAT_REG_NO_FAULT_FAN0 
        case 1: 
            errorMask = FPGA_FAN_STAT_REG_NO_FAULT_FAN1 
        case 2: 
            errorMask = FPGA_FAN_STAT_REG_NO_FAULT_FAN2 
        case 3: 
            errorMask = FPGA_FAN_STAT_REG_NO_FAULT_FAN3 
        case 4: 
            errorMask = FPGA_FAN_STAT_REG_NO_FAULT_FAN4 
    }


    //Logic here is kind of odd.  Bit on is basically fan good (no fault).  So check if it's off for a fault.
    fanErr = 0
    if (data32 &  errorMask) == 0x00 {
        fanErr = 1
    }
    return
}


// ***********************************************************************************
// *
// *   Set fan power enable status (on/off) 
// *
// ***********************************************************************************
func FAN_Set_Power_Enable(fanNumber uint32, enable uint32) (err int) {
    var mask uint32
    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Set_Power_Enable.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }

    data32, errGo := ReadU32(FPGA_FAN_PWR_CTRL_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }


    switch fanNumber {
        case 0: mask = FPGA_FAN_PWR_CTRL_FAN0_EN
        case 1: mask = FPGA_FAN_PWR_CTRL_FAN1_EN
        case 2: mask = FPGA_FAN_PWR_CTRL_FAN2_EN
        case 3: mask = FPGA_FAN_PWR_CTRL_FAN3_EN 
        case 4: mask = FPGA_FAN_PWR_CTRL_FAN4_EN 
    }

    if enable > 0 {
        data32 = data32 | mask
    } else {
        data32 = data32 & (^(mask))
    }
    WriteU32(FPGA_FAN_PWR_CTRL_REG, data32)

    return
}

// ***********************************************************************************
// *
// *   Get power enable status for a fan
// *
// ***********************************************************************************
func FAN_Get_Power_Enable(fanNumber uint32) (enable uint32, err int) {

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Get_Power_Enable.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }

    data32, errGo := ReadU32(FPGA_FAN_PWR_CTRL_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    if (data32 & (FPGA_FAN_PWR_CTRL_FAN0_EN << fanNumber)) > 0 {
        enable = 1
    } else {
        enable = 0
    }

    return
}


// ***********************************************************************************
// *
// *   Check fan module presence
// *
// ***********************************************************************************
func FAN_Get_Module_present(fanNumber uint32) (present bool, err int) {

    if fanNumber > (MAXFAN - 1) {
        cli.Printf("e", " Error: FAN_Module_present.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        err = errType.FAIL
        return
    }
    data32, errGo := ReadU32(FPGA_FAN_STAT_REG)
    if errGo != nil {
        err = errType.FAIL
        return
    }

    present = false
    if (data32 &  (FPGA_FAN_STAT_REG_PRESENT0_BIT << (fanNumber))) ==  (FPGA_FAN_STAT_REG_PRESENT0_BIT << (fanNumber)) {
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
        rc := FAN_Set_PWM(i, 40)   //40% PWM
        if rc != errType.SUCCESS {
            cli.Printf("e", " Error: FanInit.  Fan-%d set pwm failed", i)
            err = errType.FAIL
        }
    }
    return
}



