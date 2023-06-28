package liparifpga


import (
    //"errors"
    "fmt"
    "common/cli"
    //"common/errType"
)


// ***********************************************************************************
// *
// *   Get inner and outer fan RPM from one of the four fan modules
// *
// ***********************************************************************************
func FAN_Get_RPM(fanNumber uint32) (inner uint32, outer uint32, err error) {
    var data32 uint32

    if fanNumber > (MAXFAN - 1) {
        err = fmt.Errorf(" Error: FAN_Get_RPM.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_FAN0_TACH_REG + ( 4 * uint64(fanNumber)) )
    if err != nil {
        return
    }
    inner = (90000*60) / ((data32 & FPGA0_FAN0_TACH_INLET_RPM_MASK) >> FPGA0_FAN0_TACH_INLET_RPM_SHIFT) 
    outer = (90000*60) / ((data32 & FPGA0_FAN0_TACH_OUTLET_RPM_MASK) >> FPGA0_FAN0_TACH_OUTLET_RPM_SHIFT) 

    return
}


func FAN_AirFlow_Direction() (fan_air_direction int, err error) {
    var data32 uint32

    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_STAT_REG)
    if err != nil {
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
// *   Get a fans PWM setting
// *
// ***********************************************************************************
func FAN_Get_PWM(fanNumber uint32) (pwm uint32, err error) {
    var data32 uint32
    var pwmMask, pwmShift uint32

    if fanNumber > (MAXFAN - 1) {
        err = fmt.Errorf(" Error: FAN_Module_present.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_PWM_CTRL_REG)
    if err != nil {
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
// *   See if the FPGA is throwing a fan error or alert
// *
// ***********************************************************************************
func FAN_Get_Fault(fanNumber uint32) (fanErr uint32, err error) {
    var data32 uint32
    var errorMask, alertMask uint32

    if fanNumber > (MAXFAN - 1) {
        err = fmt.Errorf(" Error: FAN_Module_present.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_STAT_REG)
    if err != nil {
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


func FAN_Module_present(fanNumber uint32) (present bool, err error) {
    var data32 uint32

    if fanNumber > (MAXFAN - 1) {
        err = fmt.Errorf(" Error: FAN_Module_present.  FAN NUMBER PASSED (%d) IS NOT VALID!", fanNumber)
        cli.Printf("e", "%s", err)
        return
    }
    data32, err = LipariReadU32(LIPARI_FPGA0, FPGA0_FAN_STAT_REG)
    if err != nil {
        return
    }

    present = false
    //fan present is 0 for present, 1 for not present
    if (data32 &  (FPGA0_FAN_STAT_REG_NOT_PRESENT0 << (FPGA0_FAN_STAT_REG_NOT_PRESENT0_SHIFT + fanNumber))) == 0x00 {
        present = true
    }
    return
}



