package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"
    "common/misc"
    "common/spi"    //Marvell reg access functions


    "device/cpld/naples100Cpld"
    "device/cpld/forioCpld"
    "device/cpld/naples25Cpld"
    "device/cpld/naples25swmCpld"
    "device/cpld/vomeroCpld"
)


const MVSW_PORT3    uint8 = 0x13

const MVSW_SW_LED_CTRL_REG	        uint8  = 0x16
const MVSW_SW_LED_CTRL_DATA		    uint16 = (1 << 0)
const MVSW_SW_LED_CTRL_DATA_MASK	uint16 = 0x2FF
const MVSW_SW_LED_CTRL_PTR		    uint16 = (1 << 12)
const MVSW_SW_LED_CTRL_PTR_MASK		uint16 = 0x7
const MVSW_SW_LED_CTRL_UPDATE	    uint16 = (1 << 15)
const MVSW_SW_LED_CTRL_UPDATE_MASK	uint16 = 0x1

//LED CTRL DATA BITS
const MVSW_SW_LED_CTRL_LED1_SHIFT   uint16  = 4
const MVSW_SW_LED_CTRL_LED0_SHIFT   uint16  = 0
const MVSW_SW_LED_CTRL_GIG_LINK     uint16  = 0x3
const MVSW_SW_LED_CTRL_SET_ACT      uint16  = 0x8
const MVSW_SW_LED_CTRL_FORCE_BLINK  uint16  = 0xD
const MVSW_SW_LED_CTRL_FORCE_OFF    uint16  = 0xE
const MVSW_SW_LED_CTRL_FORCE_ON     uint16  = 0xF


const (
	LED_ALL_GRN = iota
	LED_ALL_AMB
	LED_ALL_BLK_GRN
    LED_ALL_BLK_AMB
    LED_ALL_OFF
)


func SetLEDs(port_ctrl uint32, port_rate uint32 , sys_ctrl uint32, led_state uint32) (error int) {
    var pc_val, pr_val, sc_val uint32 = 0, 0, 0
    var err int

    if led_state == LED_ALL_GRN || led_state == LED_ALL_AMB || led_state == LED_ALL_OFF {
        /* No blinnking */
        err = spi.CpldWrite(port_rate, 0x00)
        if err != 0 {
            dcli.Println("e", " ERROR: CPLD WRITE FAILED" )
            return errType.FAIL
        }
    } else {
        err = spi.CpldWrite(port_rate, 0xFF)
        if err != 0 {
            dcli.Println("e", " ERROR: CPLD WRITE FAILED" )
            return errType.FAIL
        }
    }

    switch led_state {
    	case LED_ALL_GRN:
    		dcli.Println("i", " LED: Setting Solid Green" )
            pc_val = 0x05
            pr_val = 0x04
            sc_val = uint32(MVSW_SW_LED_CTRL_UPDATE | (MVSW_SW_LED_CTRL_FORCE_ON << MVSW_SW_LED_CTRL_LED1_SHIFT))
    	case LED_ALL_AMB:
    		dcli.Println("i", " LED: Setting Solid Amber" )
            pc_val = 0x0A
            pr_val = 0x20
            sc_val = uint32(MVSW_SW_LED_CTRL_UPDATE | (MVSW_SW_LED_CTRL_FORCE_ON << MVSW_SW_LED_CTRL_LED0_SHIFT))
        case LED_ALL_BLK_GRN:
            pc_val = 0x05
            pr_val = 0x07
            sc_val = uint32(MVSW_SW_LED_CTRL_UPDATE | (MVSW_SW_LED_CTRL_FORCE_BLINK << MVSW_SW_LED_CTRL_LED1_SHIFT))
        case LED_ALL_BLK_AMB:
    		dcli.Println("i", " LED: Setting Blinking Amber" )
            pc_val = 0x0A
            pr_val = 0x38
            sc_val = uint32(MVSW_SW_LED_CTRL_UPDATE | (MVSW_SW_LED_CTRL_FORCE_BLINK << MVSW_SW_LED_CTRL_LED0_SHIFT))
        case LED_ALL_OFF:
    		dcli.Println("i", " LED: Setting All LED to OFF" )
            pc_val = 0x00
            pr_val = 0x00
            sc_val = uint32(MVSW_SW_LED_CTRL_UPDATE | 
                           (MVSW_SW_LED_CTRL_FORCE_OFF << MVSW_SW_LED_CTRL_LED0_SHIFT) | 
                           (MVSW_SW_LED_CTRL_FORCE_OFF << MVSW_SW_LED_CTRL_LED1_SHIFT))
    	default:
    		return errType.FAIL
	}

    dcli.Println("i", " LED: Setting Green Solid" )
    err = spi.CpldWrite(port_ctrl, pc_val)
    if err != 0 {
        dcli.Println("e", " ERROR: CPLD WRITE FAILED" )
        return errType.FAIL
    }
    err = spi.CpldWrite(sys_ctrl, pr_val)
    if err != 0 {
        dcli.Println("e", " ERROR: CPLD WRITE FAILED" )
        return errType.FAIL
    }
    err = spi.MvlSmiRegWrite(uint32(MVSW_SW_LED_CTRL_REG), sc_val, uint32(MVSW_PORT3)) 
    if err != 0 {
        dcli.Println("e", " ERROR: MARVELL SWITCH WRITE FAILED" )
        return errType.FAIL
    }
    misc.SleepInSec(3)

    return errType.SUCCESS
}

func get_cpld_registers(port_ctrl *uint32, port_rate *uint32, sys_ctrl *uint32) (error int) {
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType
    if (cardType == "NAPLES100") {
        *port_ctrl = naples100Cpld.REG_LED_PORT_CTRL
        *port_rate = naples100Cpld.REG_LED_PORT_RATE
        *sys_ctrl = naples100Cpld.REG_LED_SYS_CTRL
    } else if (cardType == "NAPLES100IBM") {
        *port_ctrl = naples100Cpld.REG_LED_PORT_CTRL
        *port_rate = naples100Cpld.REG_LED_PORT_RATE
        *sys_ctrl = naples100Cpld.REG_LED_SYS_CTRL
    } else if (cardType == "NAPLES100HPE") {
        *port_ctrl = naples100Cpld.REG_LED_PORT_CTRL
        *port_rate = naples100Cpld.REG_LED_PORT_RATE
        *sys_ctrl = naples100Cpld.REG_LED_SYS_CTRL
    } else if (cardType == "FORIO") {
        *port_ctrl = forioCpld.REG_LED_PORT_CTRL
        *port_rate = forioCpld.REG_LED_PORT_RATE
        *sys_ctrl = forioCpld.REG_LED_SYS_CTRL
    } else if (cardType == "VOMERO") {
        *port_ctrl = vomeroCpld.REG_LED_PORT_CTRL
        *port_rate = vomeroCpld.REG_LED_PORT_RATE
        *sys_ctrl = vomeroCpld.REG_LED_SYS_CTRL
    } else if (cardType == "NAPLES25") {
        *port_ctrl = naples25Cpld.REG_LED_PORT_CTRL
        *port_rate = naples25Cpld.REG_LED_PORT_RATE
        *sys_ctrl = naples25Cpld.REG_LED_SYS_CTRL
    } else if (cardType == "NAPLES25OCP") {
        //dcli.Println("f", "Unsupported cardType:", cardType)
        *port_ctrl = naples25swmCpld.REG_LED_PORT_CTRL
        *port_rate = naples25swmCpld.REG_LED_PORT_RATE
        *sys_ctrl = naples25swmCpld.REG_LED_SYS_CTRL
        //return errType.FAIL
    } else if (cardType == "NAPLES25SWM") {
        *port_ctrl = naples25swmCpld.REG_LED_PORT_CTRL
        *port_rate = naples25swmCpld.REG_LED_PORT_RATE
        *sys_ctrl = naples25swmCpld.REG_LED_SYS_CTRL
    } else if (cardType == "NAPLES25WFG") {
        dcli.Println("f", "Unsupported cardType:", cardType)
        return errType.FAIL
    }
    return errType.SUCCESS
}


func LedLedHdl(argList []string) {
    var err int
    var data uint32 = 0
    var port_ctrl, port_rate, sys_ctrl uint32 = 0,0,0

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }


    err = get_cpld_registers(&port_ctrl, &port_rate, &sys_ctrl)
    if err != 0 {
        goto endLedTest
    }

    err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_GRN)
    if err != 0 {
        goto endLedTest
    }
    err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_AMB)
    if err != 0 {
        goto endLedTest
    }
    err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_OFF)
    if err != 0 {
        goto endLedTest
    }
    err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_BLK_GRN)
    if err != 0 {
        goto endLedTest
    }
    err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_BLK_AMB)
    if err != 0 {
        goto endLedTest
    }

    /* SFP OFF, SYS SOLID AMBER, EXTERNAL MGMT PORT BACK TO NORMAL */
    err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_OFF)
    if err != 0 {
        goto endLedTest
    }
    err = spi.CpldWrite(sys_ctrl, 0x40)
    if err != 0 {
        dcli.Println("e", " ERROR: CPLD WRITE FAILED" )
        goto endLedTest
    }
    data = uint32(MVSW_SW_LED_CTRL_UPDATE | 
                 (MVSW_SW_LED_CTRL_SET_ACT << MVSW_SW_LED_CTRL_LED0_SHIFT) |
                 (MVSW_SW_LED_CTRL_GIG_LINK << MVSW_SW_LED_CTRL_LED1_SHIFT))
    err = spi.MvlSmiRegWrite(uint32(MVSW_SW_LED_CTRL_REG), data, uint32(MVSW_PORT3)) 
    if err != 0 {
        dcli.Println("e", " ERROR: MARVELL SWITCH WRITE FAILED" )
        goto endLedTest
    }

endLedTest:
    if err != 0 {
        diagEngine.FuncMsgChan <- errType.FAIL   /* Send return code to diag manager */    
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS  /* Send return code to diag manager */    
    }
    return

}



func LedAllGreenHdl(argList []string) {
    var err int = 0
    var port_ctrl, port_rate, sys_ctrl uint32 = 0,0,0

    err = get_cpld_registers(&port_ctrl, &port_rate, &sys_ctrl)
    if err == errType.SUCCESS {
        err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_GRN)
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func LedAllAmberHdl(argList []string) {
    var err int = 0
    var port_ctrl, port_rate, sys_ctrl uint32 = 0,0,0

    err = get_cpld_registers(&port_ctrl, &port_rate, &sys_ctrl)
    if err == errType.SUCCESS {
        err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_AMB)
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func LedAllOffHdl(argList []string) {
    var err int = 0
    var port_ctrl, port_rate, sys_ctrl uint32 = 0,0,0

    err = get_cpld_registers(&port_ctrl, &port_rate, &sys_ctrl)
    if err == errType.SUCCESS {
        err = SetLEDs(port_ctrl, port_rate , sys_ctrl, LED_ALL_OFF)
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


