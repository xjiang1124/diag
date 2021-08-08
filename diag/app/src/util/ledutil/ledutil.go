package main

import (
    //"fmt"
    "strconv"
    "flag"
    "common/cli"
    "hardware/i2cinfo"
    "device/cpld/cpld"
    "device/fpga/taorfpga"
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

func ledutil_taor(dev string, subdev string, action string, color string, blink string, rate string, bright string) (err int) {

    var data uint32

    if action == "on" {
        data = 1

	if dev == "sys" && subdev == "loc" {
            data |= (1 << 1)
	} else {
            if color == "g" {
                data |= (1 << 1)
            } else if color == "y" {
            } else {
                cli.Println("e", "Unsupported LED color (g/y)!")
            }
        }

        if blink == "on" {
            data |= (1 << 2)
            if rate == "fast" {
                data |= (1 << 3)
            } else if rate == "slow" {
            } else {
                cli.Println("e", "Unsupported blink rate (slow/fast)!")
            }
        } else if blink == "off" {
        } else {
            cli.Println("e", "Unsupported blink (on/off)!")
        }

        if bright == "half" {
            data |= (1 << 4)
        } else if bright == "full" {
        } else {
            cli.Println("e", "Unsupported brightness (full/half)!")
        }

    } else if action == "off" {
        data = 0
    } else {
        cli.Println("e", "Unsupported LED switch (on/off)!")
    }

    var mask uint32 = 0xff
    var curreg uint32
    switch dev {
    case "sys":
            curreg, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, taorfpga.D0_LED_SYSTEM_REG)
            if subdev == "sys" {
		data = curreg & (^mask) | data
	    } else if subdev == "cha" {
		    data = curreg & (^(mask << 8)) | (data << 8)
	    } else if subdev == "loc" {
		    data = curreg & (^(mask << 16)) | (data << 16)
	    } else if subdev == "all" {
		    data |= (data << 8) | (data << 16)
		    if action == "on" {
		        data |= (1 << 17)    // locate LED set to on for whatever color
	            }
	    } else {
                cli.Println("e", "Unsupported device number (sys/cha/loc/all)!")
	    }
            _ = taorfpga.TaorWriteU32(taorfpga.DEVREGION0, taorfpga.D0_LED_SYSTEM_REG, data)
        case "fan":
            if subdev == "all" {
                data |= data << 8
                _ = taorfpga.TaorWriteU32(taorfpga.DEVREGION0, taorfpga.D0_LED_FAN_1_REG, data)
                data |= data <<16
                _ = taorfpga.TaorWriteU32(taorfpga.DEVREGION0, taorfpga.D0_LED_FAN_0_REG, data)
		return
            }

	    fanport, fanresp := strconv.Atoi(subdev)
            if (fanresp != nil && fanresp.(*strconv.NumError).Err == strconv.ErrSyntax) || fanport < 0 || fanport > 5 {
                cli.Println("e", "Unsupported fan number all/[0 ~ 5]!")
            } else if fanport < 4 {
	        curreg, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, taorfpga.D0_LED_FAN_0_REG)
                data = curreg & (^(mask << uint(fanport *8))) | (data << uint(fanport * 8))
                _ = taorfpga.TaorWriteU32(taorfpga.DEVREGION0, taorfpga.D0_LED_FAN_0_REG, data)
	    } else {
	        curreg, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, taorfpga.D0_LED_FAN_1_REG)
                data = curreg & (^(mask << uint((fanport - 4) * 8))) | (data << uint((fanport - 4) * 8))
                _ = taorfpga.TaorWriteU32(taorfpga.DEVREGION0, taorfpga.D0_LED_FAN_1_REG, data)
	    }
        case "sfp":
            if subdev == "all" {
                data |= (data << 8) | (data << 16) | (data << 24)
		for i := 0; i < 14; i++ {
                    _ = taorfpga.TaorWriteU32(taorfpga.DEVREGION0, taorfpga.D0_LED_CTRL_3_0_REG + uint64(i * 4), data)
                }
		return
            }

	    sfpport, sfpresp := strconv.Atoi(subdev)
            if (sfpresp != nil && sfpresp.(*strconv.NumError).Err == strconv.ErrSyntax) || sfpport < 0 || sfpport > 53 {
                cli.Println("e", "Unsupported fan number all/[0 ~ 53]!")
		return
            } else {
                regOffset, bitOffset := sfpport/4, (sfpport % 4) * 8
                curreg, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, taorfpga.D0_LED_CTRL_3_0_REG + uint64(regOffset * 4))
		data = curreg & (^(mask << uint(bitOffset))) | (data << uint(bitOffset))
                _ = taorfpga.TaorWriteU32(taorfpga.DEVREGION0, taorfpga.D0_LED_CTRL_3_0_REG + uint64(regOffset * 4), data)
            }
        default:
            cli.Println("e", "Unsupported device (sys/fan/sfp)!")
    }
    return
}

func main() {
	var err int

    if i2cinfo.CardType == "TAORMINA" {
        ledDevPtr	:= flag.String("dev",	"",	"LED device [sys | fan | sfp]")
	ledDevNumPtr	:= flag.String("p",	"",	"LED dev port name or #: [all | loc | cha | sys | 0 ~ 5 (fan) | 0 ~ 53 (sfp)]")
        ledSwitchPtr	:= flag.String("a",	"",	"LED action [on | off]")
        ledColorPtr	:= flag.String("c",	"",	"LED color [g | y]")
        ledBrightPtr	:= flag.String("b",	"",	"LED bright [half | full]")
        ledBlinkPtr	:= flag.String("n",	"",	"LED blink [on | off]")
        ledRatePtr	:= flag.String("f",	"",	"LED blink freq [fast | slow]")
        flag.Parse()

        err = ledutil_taor(*ledDevPtr, *ledDevNumPtr, *ledSwitchPtr, *ledColorPtr, *ledBlinkPtr, *ledRatePtr, *ledBrightPtr)

    } else {
        ledDevPtr	:= flag.String("dev",		"",	"LED device sys/qsfp1/qsfp2")
        ledColorPtr	:= flag.String("color",		"",	"LED color g/y")
        ledSwitchPtr	:= flag.String("switch",	"",	"LED switch on/off")
        ledRatePtr	:= flag.Uint("rate",		0,	"LED blink rate 0/1/2/4Hz")
        flag.Parse()

        rate := *ledRatePtr

        err = ledutil(*ledDevPtr, *ledColorPtr, *ledSwitchPtr, rate)
    }

    if err != 0 {
        cli.Println("e", "LED control failed!")
    }
}

