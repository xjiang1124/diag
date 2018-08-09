package main

import (
    //"fmt"
    "flag"
    "common/cli"
    "device/cpld/cpld"
)

func ledutil(dev string, color string, action string, rate uint) (err int) {
//    cpldRegMap := map[string]int {
//        "sysg0":	
//    }
    
    var on, freq uint8
    if action == "on" {
        on = 1
    } else if action == "off" {
        on = 0
    } else {
        cli.Println("e", "Unsupported switch!")
    }
    
    switch rate {
        case 0:
            freq = 0
        case 1:
            freq = 1
        case 2:
            freq = 2
        case 4:
            freq = 3
        default:
            cli.Println("e", "Unsupported rate!")
    }
    
    var data uint8
    switch dev+color {
        case "sysg":
            data, _ = cpld.ReadReg(0x12)
            data &= 0x30
            data |= freq
            _ = cpld.WriteReg(0x12, data)
            // TODO: Capri GPIO control
        case "sysy":
            data, _ = cpld.ReadReg(0x12)
            data &= 0xC0
            data |= freq
            _ = cpld.WriteReg(0x12, data)
            // TODO: Capri GPIO control
        case "qsfp1g":
            data, _ = cpld.ReadReg(0x5)
            data &= 0xFE
            data |= on
            _ = cpld.WriteReg(0x5, data)
            data, _ = cpld.ReadReg(0xF)
            data &= 0xFC
            data |= freq
            _ = cpld.WriteReg(0xF, data)
        case "qsfp1y":
            data, _ = cpld.ReadReg(0x5)
            data &= 0xFD
            data |= on
            _ = cpld.WriteReg(0x5, data)
            data, _ = cpld.ReadReg(0xF)
            data &= 0xF3
            data |= freq
            _ = cpld.WriteReg(0xF, data)
        case "qsfp2g":
            data, _ = cpld.ReadReg(0x5)
            data &= 0xFB
            data |= on
            _ = cpld.WriteReg(0x5, data)
            data, _ = cpld.ReadReg(0xF)
            data &= 0xCF
            data |= freq
            _ = cpld.WriteReg(0xF, data)
        case "qsfp2y":
            data, _ = cpld.ReadReg(0x5)
            data &= 0xF7
            data |= on
            _ = cpld.WriteReg(0x5, data)
            data, _ = cpld.ReadReg(0xF)
            data &= 0x3F
            data |= freq
            _ = cpld.WriteReg(0xF, data)
        default:
            cli.Println("e", "Unsupported device or color!")
    }
    return
}


func main() {
 
    ledDevPtr  			:= flag.String("dev",			"",		"LED device sys/qsfp1/qsfp2")
    ledColorPtr  		:= flag.String("color",			"",		"LED color g/y")
    ledSwitchPtr   		:= flag.String("switch",		"",		"LED switch on/off")
    ledRatePtr    		:= flag.Uint("rate",			0,		"LED blink rate 0/1/2/4Hz")
    flag.Parse()

    rate := *ledRatePtr
    
    err := ledutil(*ledDevPtr, *ledColorPtr, *ledSwitchPtr, rate)
    if err != 0 {
        cli.Println("e", "LED control failed!")
    }
}

