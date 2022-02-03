package main

import (
    //"device/fpga/taorfpga"
    "os"
    "fmt"
    "strconv"
    //"common/cli"
    "common/errType"
    //"hardware/hwinfo"
    "device/bcm/td3"
    "platform/taormina"
)


const errhelp = "\nswitch:\n" +
        "switch fantest\n" +
        "\n" +
        "switch td3 prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>\n" +
        "switch td3 snake <elbPortMask> <time> <phy/ext> [pktsize] [32-bit pattern] -temp\n" +
        "switch td3 snakeforward <elbPortMask> <time> <phy/ext> -temp\n" +
        "switch td3 snakecompliance <elbPortMask> <time> <phy/ext> -temp\n" +
        "switch td3 vrmfix\n" +
        "\n" + 
        "switch elba memtest <elba mask 0x1/0x2/0x3> <time in seconds> \n" +
        "switch elba rtctest <elba mask 0x1/0x2/0x3>\n" +
        "switch elba checkecc <elba#>\n" +
        "\n" +
        "switch cpu usbtest <file size in MB> <# of files to generate>\n" +
        "switch cpu memtest <# test threads> <percent of mem to test 1-100> <time>\n" +
        "switch cpu pciscan -noelba\n" +
        "switch cpu ecc\n" +
        "\n" +
        "switch show power/temp/link\n" +
        "switch voltage margin <+/-percent>\n" +
        "\n"
        

                               

func main() {
    argc := len(os.Args[0:])

    if argc < 2 {
        fmt.Printf(" %s \n", errhelp)
        return
    }
    if os.Args[1] == "fantest" {
        fmt.Printf(" FAN TEST\n")
        taormina.Fan_RPM_test(10)

        return
    } else if os.Args[1] == "resistor" {  
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        strapping, _ := strconv.ParseUint(os.Args[2], 0, 32)
        taormina.FPGA_Strapping_Test(int(strapping))
        return
    } else if os.Args[1] == "td3" {  
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        if os.Args[2] == "tl" {
            testnumber, _ := strconv.ParseUint(os.Args[3], 0, 32)
            loop, runcnt, passcnt, failcnt, _ := td3.BCMshell_Test_Results(int(testnumber))
            fmt.Printf(" LoopCnt=%d\n", loop)
            fmt.Printf(" runcnt=%d\n", runcnt)
            fmt.Printf(" passcnt=%d\n", passcnt)
            fmt.Printf(" failcnt=%d\n", failcnt)
            return
        } else if os.Args[2] == "flashtest" {
            cycles, _ := strconv.ParseUint(os.Args[3], 0, 32)
            err := td3.TD3FlashTest(int(cycles)) 
            if err != errType.SUCCESS { os.Exit(-1) }
        } else if os.Args[2] == "avscheck" {
            taormina.TD3_Check_AVS_Programming("TDNT_PDVDD")
            return
        } else if os.Args[2] == "regread" {
            data32, _ := td3.ReadReg("TD3", os.Args[3])
            fmt.Printf(" Reg Value = 0x%x\n", data32)
            return
        } else if os.Args[2] == "retimer_temperatures" {
            fmt.Printf("IN RETIMER TEMP\n")
            temps, _ := td3.RetimerGetTemperatures()
            for i:=0;i<len(temps);i++ {
                fmt.Printf("Retimer-%d  Temp=%fC\n", i, temps[i])
            }
        } else if os.Args[2] == "gearbox_temperatures" {
            fmt.Printf("IN GEARBOX TEMP\n")
            temps, _ := td3.GearboxGetTemperatures()
            for i:=0;i<len(temps);i++ {
                fmt.Printf("Gearbox-%d  Temp=%fC\n", i, temps[i])
            }
        } else if os.Args[2] == "vrmfix" {

            rc := taormina.TD3_VRM_FIX("TDNT_PDVDD")
            fmt.Printf(" VRM FIX RC=%d\n", rc);
        } else if os.Args[2] == "prbs" {
            if argc < 4 { fmt.Printf(" Not enough args... prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>"); return; }
            time, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            td3.Prbs(int(time), os.Args[4])
        } else if os.Args[2] == "snakeforward" {
            var dumptemperature uint32
            if argc < 6 { fmt.Printf(" Not enough args..."); return; }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            duration, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            if contains(os.Args, "-temp") {
                dumptemperature = 1
            }
            taormina.System_Snake_Test(td3.SNAKE_TEST_NEXT_PORT_FORWARDING , uint32(mask), uint32(duration), os.Args[5], 0, 0, dumptemperature)
        } else if os.Args[2] == "snakecompliance" {
            var dumptemperature uint32
            if argc < 6 { fmt.Printf(" Not enough args..."); return; }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            duration, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            if contains(os.Args, "-temp") {
                dumptemperature = 1
            }
            taormina.System_Snake_Test(td3.SNAKE_TEST_ENVIRONMENT , uint32(mask), uint32(duration), os.Args[5], 0, 0, dumptemperature)
        } else if os.Args[2] == "snake" {
            var dumptemperature uint32
            var pkt_length, pkt_pattern uint64 
            if argc < 6 { fmt.Printf(" Not enough args..."); return; }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            duration, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf(" argc=%d\n", argc)
            if argc == 8 {
                pkt_length, err = strconv.ParseUint(os.Args[6], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[6] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
                pkt_pattern, err = strconv.ParseUint(os.Args[7], 0, 32)
                if err != nil {
                    fmt.Printf(" Args[7] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
                }
            }
            if contains(os.Args, "-temp") {
                dumptemperature = 1
            }
            taormina.System_Snake_Test(td3.SNAKE_TEST_LINE_RATE, uint32(mask), uint32(duration), os.Args[5], pkt_length, pkt_pattern, dumptemperature)
        } else if os.Args[2] == "checkgb" {
            td3.CheckForRevA_Gearbox()
        } else if os.Args[2] == "printvlan" {
            td3.PrintBCMShellVLANcmd()
        }
    } else if os.Args[1] == "elba" {
        if os.Args[2] == "vrmfix" {
            taormina.ElbaVRMfix()
        } else if os.Args[2] == "checkecc" {
            elba, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf(" Checkking for ECC Errors:\n"); 
            e := taormina.ElbaCheckECC(uint32(elba),0, 1, 0) 
            if e == 0 {
                fmt.Printf(" passed\n")
            } else {
                fmt.Printf(" failed\n")
            }
        } else if os.Args[2][0] == 'm' || os.Args[2][0] == 'M' {  //memtest
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            time, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }

            taormina.ElbaMemoryTest(uint32(mask), uint32(time), 1) 
            return
        } else if os.Args[2][0] == 'r' || os.Args[2][0] == 'R' {  //rtctest
            if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            taormina.ElbaRTCtest(uint32(mask), 1) 
            return
        } else {
            fmt.Printf(" Bad ARG--> ARGV[2]=%s\n", os.Args[2])
            return
        }
    } else if os.Args[1] == "cpu" {
        if os.Args[2][0] == 'u' || os.Args[2][0] == 'U' {  //usbtest
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                os.Exit(-1)
            }
            mb, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            itterations, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            err1 := taormina.USBtest(int(mb), int(itterations)) 
            if err1 != errType.SUCCESS {
                os.Exit(-1)
            } else { 
                os.Exit(0)
            }
        } else if os.Args[2][0] == 'm' || os.Args[2][0] == 'M' {  //memtest
            if argc < 5 {
                fmt.Printf(" %s \n", errhelp)
                os.Exit(-1)
            }
            threads, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            percent, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            if percent > 100 {
                fmt.Printf(" Percent of memory to test cannot be more than 100%.  You entered %d percent\n", percent); os.Exit(-1)
            }
            time, err := strconv.ParseUint(os.Args[5], 0, 32)
            if err != nil {
                fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            err1 := taormina.X86_CPU_MemoryTest(uint32(threads), uint32(percent), uint32(time), 1) 
            if err1 != errType.SUCCESS {
                os.Exit(-1)
            } else { 
                os.Exit(0)
            }
        } else if os.Args[2][0] == 'e' || os.Args[2][0] == 'E' {  //ecctest
            err1 := taormina.X86_DDR_Check_ECC(1)
            if err1 != errType.SUCCESS {
                fmt.Printf(" Errors Detected\n")
                os.Exit(-1)
            } else { 
                fmt.Printf(" No Errors Detected\n")
                os.Exit(0)
            }
        } else if os.Args[2][0] == 'p' || os.Args[2][0] == 'P' {  //pci scan
            var skipelba uint32 
            if contains(os.Args, "-noelba") {
                skipelba = 1
            }


            err1 := taormina.Pci_scan(skipelba)

            if err1 != errType.SUCCESS {
                fmt.Printf(" PCI Scan Failed\n")
                os.Exit(-1)
            } else { 
                fmt.Printf(" PCI Scan Passed\n")
                os.Exit(0)
            }
        } else {
            fmt.Printf(" Bad ARG--> ARGV[2]=%s\n", os.Args[2])
            return
        }
    } else if os.Args[1] == "voltage" {
        if argc < 4 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        percent, err := strconv.ParseInt(os.Args[3], 0, 32)
        if err != nil {
            fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
        }
        taormina.VoltageMargin(int(percent))
        fmt.Printf(" Voltage Margined Toarmina's applicable VRM's to %d percent\n", percent)
        return 
    } else if os.Args[1] == "show" {
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        if os.Args[2][0] == 'l' || os.Args[2][0] == 'L' {
            ps_output, err := td3.ExecBCMshellCMD("ps")
            if err != errType.SUCCESS {
                return
            }
            fmt.Printf("\n")
            for i , entry := range(td3.TaorPortMap) {
                rc := td3.LinkCheck(entry.Name, ps_output) 
                if rc == errType.LINK_UP {
                    fmt.Printf("Port-%.02d  %4s: LINK UP\n", i+1, entry.Name)
                } else if rc == errType.LINK_DOWN {
                    fmt.Printf("Port-%.02d  %4s: LINK DOWN\n", i+1, entry.Name)
                } else if rc == errType.LINK_DISABLED {
                    fmt.Printf("Port-%.02d  %4s: LINK DISABLED\n", i+1, entry.Name)
                } else {
                    fmt.Printf("Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, entry.Name)
                }
            }
            fmt.Printf("\n")
            
            return
        } else if os.Args[2][0] == 'p' || os.Args[2][0] == 'P' { 
            taormina.ShowPower()
        } else if os.Args[2][0] == 't' || os.Args[2][0] == 'T' { 
            taormina.ShowTemperature()
        } else {
            fmt.Printf(" Bad ARG--> ARGV[2]=%s\n", os.Args[2])
            return
        }

    }
    return
}


func contains(s []string, str string) bool {
	for _, v := range s {
		if v == str {
			return true
		}
	}

	return false
}





 
