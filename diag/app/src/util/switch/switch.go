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
        "switch td3 snake <elbPortMask> <time> <phy/ext> [pktsize] [32-bit pattern]\n" +
        "switch td3 snakeforward <elbPortMask> <time> <phy/ext>\n" +
        "switch td3 vrmfix\n" +
        "\n" + 
        "switch elba memtest <elba mask 0x1/0x2/0x3> <time in seconds> \n" +
        "\n" +
        "switch show power/temp/link\n" +
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
        if os.Args[2] == "vrmfix" {

            rc := taormina.TD3_VRM_FIX("TDNT_PDVDD")
            fmt.Printf(" VRM FIX RC=%d\n", rc);
        }
        if os.Args[2] == "prbs" {
            if argc < 4 { fmt.Printf(" Not enough args... prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>"); return; }
            time, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            td3.Prbs(int(time), os.Args[4])
        }
        if os.Args[2] == "snakeforward" {
            if argc < 6 { fmt.Printf(" Not enough args..."); return; }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            duration, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            td3.Snake_All_Ports_Forward_Next_Port(uint32(mask), uint32(duration), os.Args[5])
        }
        if os.Args[2] == "snake" {
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
            td3.Snake_Line_Rate(uint32(mask), uint32(duration), os.Args[5], pkt_length, pkt_pattern)
        }
        if os.Args[2] == "checkgb" {
            td3.CheckForRevA_Gearbox()
        }
        if os.Args[2] == "printvlan" {
            td3.PrintBCMShellVLANcmd()
        }
    } else if os.Args[1] == "elba" {
        if os.Args[2] == "vrmfix" {
            taormina.ElbaVRMfix()
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
        } else {
            fmt.Printf(" Bad ARG--> ARGV[2]=%s\n", os.Args[2])
            return
        }
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


 
