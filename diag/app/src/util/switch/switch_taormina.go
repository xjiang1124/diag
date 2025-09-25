package main

import (
    "os"
    "os/exec"
    "fmt"
    "strconv"
    "strings"
    "common/cli"
    "common/errType"
    "device/bcm/td3"
    "platform/taormina"
)


const errhelp = "\nswitch:\n" +
        //"switch fantest\n" +
        "switch test fan/i2c/qsfp/sfp/sfp_laser/dramsize/resistor/presence  (example -> 'switch test fan')\n" +
        "\n" +
        "switch td3 prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>  loopback:<gb/retimer>\n\n" +
        "switch td3 snake <elbPortMask> <time> <phy/ext>\n" +
        "                                ///////OPTIONAL ARGS//////////\n" +
        "                                pktsize:<size>    pktpattern:<pattern>\n" +
        //"                                pktpattern:<pattern>\n" +
        "                                dumptemps:<0/1>\n" +
        "                                fanspeed:<50/60/70/80/90/100>\n" +
        "                                maxelbatemp:value\n" +
        "                                maxtd3temp:value\n" +
        "                                gbloopback:<host/line>\n" +
        "                                retimerloopback:<host/line>\n" +
        "                                pollerroratend:<0/1>\n" +
        "                                EXAMPLE pktsize:1480 pktpattern:0xFFFFFFFF dumptemps:1 fanspeed:70 maxelbatemp:65 maxtd3temp:80\n" +
        "switch td3 snakecompliance <elbPortMask> <time> <phy/ext>\n" +
        "switch td3 vrmfix\n" +
        "\n" + 
        "switch elba memtest <elba mask 0x1/0x2/0x3> <time in seconds> \n" +
        "switch elba edmatest <elba mask 0x1/0x2/0x3> \n" +
        "switch elba rtctest <elba mask 0x1/0x2/0x3>\n" +
        "switch elba checkecc/checkpcilink/checklinkflap <elba#>\n" +
        "\n" +
        "switch cpu usbtest <file size in MB> <# of files to generate>\n" +
        "switch cpu memtest <# test threads> <percent of mem to test 1-100> <time>\n" +
        "switch cpu pciscan -noelba\n" +
        "switch cpu ecc\n" +
        "\n" +
        "switch show power/temp/link\n" +
        "switch voltage margin <+/-percent>\n" +
        "\n"
        
   
                
/* 
I2C -> I2C
QSFP -> I2C
SFP -> I2C
SFP -> LAS
CPU - DRAMSIZE
SWITCH -> RESISTOR (command not in switch help)
SWITCH -> PRESENT 
 
 
root@10000:/home/diag/diag# diag -stest
============ TOR1:TAORMINA ============
-------- SWITCH --------
ELBA_RTC            idle
VRM_FIX             idle
FPGA_STRAPPING      idle
ELBA_EDMA_TEST      idle
ELBA_ARM_MEMORY     idle
INVENTORY           idle
FANRPM              idle
PRESENT             idle
SNAKE               idle
-------- I2C --------
I2C                 idle
-------- BCM --------
PRBSEXT             idle
-------- SFP --------
I2C                 idle
LASER               idle
-------- CPU --------
DRAMSIZE            idle
PCISCAN             idle
USB                 idle
MEMORY              idle
-------- QSFP --------
I2C                 idle
-------- ASIC --------
L1                  idle
*/ 

func taormina_switch_cli() {
    argc := len(os.Args[0:])
    rc := 0

    if argc < 2 {
        fmt.Printf(" %s \n", errhelp)
        return
    }

    if os.Args[1] == "grep" {
        wc, _ := taormina.Grep_syslog_wc(os.Args[2])
        fmt.Printf(" WC=%d\n\n", wc)
    }
    if os.Args[1] == "tpmcheck" {
        taormina.TPM_CHECK(1)
    }
    if os.Args[1] == "getpca" {
        pcaRev, _ := taormina.GetFRU_PCA()
        fmt.Printf("PCA REV=%d\n", pcaRev)
        return
    }
    //"switch test fan/i2c/qsfp/sfp/sfp_laser/dramsize/resistor/presence  (example -> 'switch test fan')\n" +
    if os.Args[1] == "test" {
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        if os.Args[2] == "fan" {
            fmt.Printf(" FAN TEST\n")
            rc := taormina.Fan_RPM_test(25)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "i2c" {
            fmt.Printf(" I2C TEST\n")
            rc := taormina.TaorI2cTest()
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "qsfp" {
            argList := []string{}
            fmt.Printf(" QSFP TEST\n")
            rc := taormina.QsfpI2Ctest(argList)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "sfp" {
            argList := []string{}
            fmt.Printf(" SFP TEST\n")
            rc := taormina.Sfp_i2c_test(argList)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "sfp_laser" {
            argList := []string{}
            fmt.Printf(" SFP LASER TEST\n")
            rc := taormina.Sfp_signal_test(argList)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "dramsize" {
            rc := taormina.X86_DDR_Display_Info(1)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "resistor" {
            if argc < 4 {
                fmt.Printf("\n [WARN] Please provide another arg with the expected resistor value.  i.e. 1, 2, 3, etc\n\n")
                return
            }
            strapping, _ := strconv.ParseUint(os.Args[3], 0, 32)
            rc := taormina.FPGA_Strapping_Test(int(strapping))
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "presence" {
            rc := taormina.Presence_Test()
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        }
    } else if os.Args[1] == "fanstuck" {
         if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        pwm, _ := strconv.ParseUint(os.Args[2], 0, 32)
        rc := taormina.Fan_FIX_Stuck_Fan(0, int(pwm))
        if rc != errType.SUCCESS {
            os.Exit(-1) 
        } else {
            os.Exit(0)
        }
    } else if os.Args[1] == "fantest" {
        fmt.Printf(" FAN TEST\n")
        rc := taormina.Fan_RPM_test(25)
        if rc != errType.SUCCESS {
            os.Exit(-1) 
        } else {
            os.Exit(0)
        }
    } else if os.Args[1] == "resistor" {  
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        strapping, _ := strconv.ParseUint(os.Args[2], 0, 32)
        rc := taormina.FPGA_Strapping_Test(int(strapping))
        if rc != errType.SUCCESS {
            os.Exit(-1) 
        } else {
            os.Exit(0)
        }
        return
    } else if os.Args[1] == "td3" {  
        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            return
        }
        if os.Args[2] == "testinit" {
            rc := td3.BCMShell_Test_Init()
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        }
        if os.Args[2] == "PrintPortRmonStats" {
            portnumber, _ := strconv.ParseUint(os.Args[3], 0, 32)
            rc := td3.PrintPortRmonStats(int(portnumber))
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        }

        if os.Args[2] == "testrun" {
            testnumber, _ := strconv.ParseUint(os.Args[3], 0, 32)
            _,_,_,_,rc := td3.BCMshell_Test_Run(int(testnumber))
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        }
        if os.Args[2] == "testresult" {
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
            rc := taormina.TD3_Check_AVS_Programming("TDNT_PDVDD")
            fmt.Printf(" CHECK AVS FIX RC=%d\n", rc)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
            return
        } else if os.Args[2] == "regread" {
            data32, _ := td3.ReadReg("TD3", os.Args[3])
            fmt.Printf(" Reg Value = 0x%x\n", data32)
            return
        } else if os.Args[2] == "retimer_temperatures" {
            fmt.Printf("IN RETIMER TEMP\n")
            temps, _ := td3.RetimerGetTemperatures("RETIMER")
            for i:=0;i<len(temps);i++ {
                fmt.Printf("Retimer-%d  Temp=%fC\n", i, temps[i])
            }
        } else if os.Args[2] == "dis_unreliablelos" {
            fmt.Printf("IN RETIMER TEMP\n")
            rc := td3.TD3_Lane_Config_Disable_UNRELIABLELOS_and_LPDFE(1)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "retimer_si" {
            fmt.Printf("IN RETIMER TEMP\n")
            rc := td3.RetimerSetSI(1)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "retimer_dumpsi" {
            fmt.Printf("IN RETIMER TEMP\n")
            rc := td3.RetimerDumpSI()
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "gearbox_temperatures" {
            fmt.Printf("IN GEARBOX TEMP\n")
            temps, _ := td3.GearboxGetTemperatures("GEARBOX")
            for i:=0;i<len(temps);i++ {
                fmt.Printf("Gearbox-%d  Temp=%fC\n", i, temps[i])
            }
        } else if os.Args[2] == "vrmfix" {
            rc := taormina.TD3_VRM_FIX("TDNT_PDVDD")
            fmt.Printf(" VRM FIX RC=%d\n", rc)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "prbs" {
            var loopback = 0
            var extraArg bool
            if argc < 4 { fmt.Printf(" Not enough args... prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>"); return; }
            time, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            extraArg = contains_with_a_string(os.Args, "loopback", "gb")
            if extraArg == true { loopback |= taormina.PRBS_GB_LPBK } 
            extraArg = contains_with_a_string(os.Args, "loopback", "retimer")
            if extraArg == true { loopback |= taormina.PRBS_RETIMER_LPBK } 

            rc := taormina.Prbs(int(time), os.Args[4], loopback)
            if rc != errType.SUCCESS {
                cli.Printf("i", "PRBS FAILED\n\n")
                os.Exit(-1) 
            } else {
                cli.Printf("i", "PRBS PASSED\n\n")
                os.Exit(0)
            }
        } else if (os.Args[2] == "snake" || os.Args[2] == "snakecompliance" || os.Args[2] == "snakeforward") {
            var dumptemperature uint32 = 1
            var data32 uint32
            var pkt_length, pkt_pattern uint64 = 0, 0  
            var TD3MaxTemp, ElbaMaxTemp, Fanspeed int = td3.TD3_MAX_TEMP, taormina.ELBA_MAX_TEMP, 00 //00 fanspeed means dont set it.. just use what is running
            var extraArg bool
            var test_type uint32 = td3.SNAKE_TEST_LINE_RATE
            var gbloopback = 0
            var retimerloopback = 0;
            var PollErrorAtEnd = 0;

            if argc < 6 { fmt.Printf(" Not enough args..."); return; }

            if os.Args[2] == "snakecompliance" {
                test_type = td3.SNAKE_TEST_ENVIRONMENT
            }
            if os.Args[2] == "snakeforward" {
                test_type = td3.SNAKE_TEST_NEXT_PORT_FORWARDING
            }

            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            duration, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf(" argc=%d\n", argc)
/*
        "                                ///////OPTIONAL ARGS//////////\n" +
        "                                pktsize:<size>\n" +
        "                                pktpattern:<pattern>\n" +
        "                                dumptemps:<0/1>\n" +
        "                                fanspeed:<50/60/70/80/90/100>\n" +
        "                                maxelbatemp:value\n" +
        "                                maxtd3temp:value\n" +
        "                                EXAMPLE pktsize:1480 pktpattern:0xFFFFFFFF dumptemps:1 fanspeed:70 maxelbatemp:65 maxtd3temp:80\n" +
*/
            data32, extraArg = contains_with_a_value(os.Args, "pktsize") 
            if extraArg == true { pkt_length = uint64(data32) }

            data32, extraArg = contains_with_a_value(os.Args, "pktpattern") 
            if extraArg == true { pkt_pattern = uint64(data32) }

            data32, extraArg = contains_with_a_value(os.Args, "dumptemps") 
            if extraArg == true { dumptemperature = uint32(data32) }

            data32, extraArg = contains_with_a_value(os.Args, "fanspeed") 
            if extraArg == true { Fanspeed = int(data32) }

            data32, extraArg = contains_with_a_value(os.Args, "maxelbatemp") 
            if extraArg == true { ElbaMaxTemp = int(data32) }

            data32, extraArg = contains_with_a_value(os.Args, "maxtd3temp") 
            if extraArg == true { TD3MaxTemp = int(data32) }

            extraArg = contains_with_a_string(os.Args, "gbloopback", "host")
            if extraArg == true { gbloopback = taormina.SNAKE_GB_HOST_LPBK } 
            extraArg = contains_with_a_string(os.Args, "gbloopback", "line")
            if extraArg == true { gbloopback = taormina.SNAKE_GB_LINE_LPBK } 

            extraArg = contains_with_a_string(os.Args, "retimerloopback", "host")
            if extraArg == true { retimerloopback = taormina.SNAKE_RETIMER_HOST_LPBK } 
            extraArg = contains_with_a_string(os.Args, "retimerloopback", "line")
            if extraArg == true { retimerloopback = taormina.SNAKE_RETIMER_LINE_LPBK }

            data32, extraArg = contains_with_a_value(os.Args, "pollerroratend") 
            if extraArg == true { PollErrorAtEnd = int(data32) }


            cli.Printf("i", " pkt_length=%d\n", pkt_length)
            cli.Printf("i", " pkt_pattern=0x%x\n", pkt_pattern)
            cli.Printf("i", " dumptemperature=%x\n", dumptemperature)
            cli.Printf("i", " Fanspeed=%d\n", Fanspeed)
            cli.Printf("i", " ElbaMaxTemp=%d\n", ElbaMaxTemp)
            cli.Printf("i", " TD3MaxTemp=%d\n", TD3MaxTemp)
            cli.Printf("i", " gbloopback=%d\n", gbloopback)
            cli.Printf("i", " retimerloopback=%d\n", retimerloopback)
            cli.Printf("i", " PollErrorAtEnd=%d\n", PollErrorAtEnd)

            rc := taormina.System_Snake_Test(test_type, uint32(mask), uint32(duration), os.Args[5], pkt_length, pkt_pattern, dumptemperature, TD3MaxTemp, ElbaMaxTemp, Fanspeed, gbloopback, retimerloopback, PollErrorAtEnd)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }

        } else if os.Args[2] == "gbloopback" {
            if argc < 5 { 
                fmt.Printf(" Not enough args... gb_loopback <level (0/1)> <mode (1/2)> <enable (1/0)\n"); os.Exit(-1) 
            }
            level, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            mode, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            enable, err := strconv.ParseUint(os.Args[5], 0, 32)
            if err != nil {
                fmt.Printf(" Args[5] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }

            rc := taormina.BCM_GearBox_Set_Loopback(int(level), int(mode), int(enable))
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "gbcheckloopback" {
            if argc < 4 { 
                fmt.Printf(" Not enough args... gbcheckloopback <level (0/1)> <mode (1/2)> <enable (1/0)\n"); os.Exit(-1) 
            }
            level, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }
            enable, err := strconv.ParseUint(os.Args[4], 0, 32)
            if err != nil {
                fmt.Printf(" Args[4] ParseUint is showing ERR = %v.   Exiting Program\n", err); os.Exit(-1)
            }

            rc := taormina.BCM_GearBox_Check_Loopback(int(level), int(enable))
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "gbchecklink" {
            rc := taormina.BCM_GearBox_Check_Link(1, 1)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "checkgb" {
            rc := td3.CheckForRevA_Gearbox()
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "printvlan" {
            td3.PrintBCMShellVLANcmd()
        } else if os.Args[2] == "test" {
            rc := td3.TD3_Run_Diags()
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        }
    } else if os.Args[1] == "elba" {
        if os.Args[2] == "vrmfix" {
            taormina.ElbaVRMfix()
        } else if os.Args[2] == "checkeyeheight" {
            elba, _ := strconv.ParseUint(os.Args[3], 0, 32)
            lane, _ := strconv.ParseUint(os.Args[4], 0, 32)

            _, mv0, mv1, mv2 := taormina.Elba_Check_Eye_Height(int(elba), int(lane), 1)
            fmt.Printf("\b0=%dmv \n1=%dmv \n2=%dmv\n", mv0, mv1, mv2)

        } else if os.Args[2] == "checklinkflap" {

            e := taormina.Elba_Check_Link_Flap_Count(0, 1) 
            e |= taormina.Elba_Check_Link_Flap_Count(1, 1) 
            e |= taormina.TD3_Check_Link_Flap()

            if (e != errType.SUCCESS) {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "printmacstats" {
            elba, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            e := taormina.Elba_Get_Mac_Stats(int(elba)) 
            if e != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "printmacstats1" {
            elba, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            mibs, e := taormina.Elba_Get_Mac_Stats_Into_Struct(int(elba), 1) 
            for _, temp := range mibs  {
                fmt.Printf("fcs=%x\n", temp.RSFEC_CH_SYMBOL_ERR_CNT)
            }
            if e != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "checkpcilink" {
            elba, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf(" Checkking PCI LINK:\n"); 
            e := taormina.Elba_Check_Pci_Link(int(elba), 0, 0) 
            if e != errType.SUCCESS {
                cli.Printf("i", "Checking PCI Link FAILED\n")
                os.Exit(-1) 
            } else {
                cli.Printf("i", "Checking PCI Link PASSED\n")
                os.Exit(0)
            }
        } else if os.Args[2] == "checkecc_console" {
            elba, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            fmt.Printf(" Checkking for ECC Errors:\n"); 
            e := taormina.ElbaCheckECC_via_console(uint32(elba), 1, 0) 
            if e == 0 {
                fmt.Printf(" passed\n")
            } else {
                fmt.Printf(" failed\n")
            }
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
            rc := taormina.ElbaMemoryTest(uint32(mask), uint32(time), uint32(85), 1) 
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
            return
        } else if os.Args[2] == "edma1" || os.Args[2] == "EDMA1" {  
            if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rc := taormina.ElbaEDMA_Test(uint32(mask), 1, 200) 
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
            return
        } else if os.Args[2] == "edma2" || os.Args[2] == "EDMA2" {  
            if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rc := taormina.ElbaEDMA_Test_WRPAD(uint32(mask), 1, 200) 
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
            return
        } else if os.Args[2] == "edma3" || os.Args[2] == "EDMA3" {  
            if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rc := taormina.ElbaEDMA_Test(uint32(mask), 1, 100) 
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
            return
        } else if os.Args[2][0] == 'e' || os.Args[2][0] == 'E' {  //edmatest
            if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            mask, err := strconv.ParseUint(os.Args[3], 0, 32)
            if err != nil {
                fmt.Printf(" Args[3] ParseUint is showing ERR = %v.   Exiting Program\n", err); return
            }
            rc := taormina.ElbaEDMA_Test_Console_Only_CXOS_SCRIPT(uint32(mask), 1, 100) 
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } else {
                os.Exit(0)
            }
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
            rc := taormina.USBtest(int(mb), int(itterations)) 
            if rc != errType.SUCCESS {
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
            rc := taormina.X86_CPU_MemoryTest(uint32(threads), uint32(percent), uint32(time), 1) 
            if rc != errType.SUCCESS {
                os.Exit(-1)
            } else { 
                os.Exit(0)
            }
        } else if os.Args[2][0] == 'e' || os.Args[2][0] == 'E' {  //ecctest
            rc := taormina.X86_DDR_Check_ECC(1)
            if rc != errType.SUCCESS {
                fmt.Printf(" Errors Detected\n")
                os.Exit(-1)
            } else { 
                fmt.Printf(" No Errors Detected\n")
                os.Exit(0)
            }
        } else if os.Args[2] == "3v3fix" {
            rc := taormina.TaorminaP3V3trimFix()
            if rc != errType.SUCCESS {
                cli.Printf("e", "3v3fix FAILED\n")
                os.Exit(-1)
            } else { 
                cli.Printf("i", "3v3fix PASSED\n")
                os.Exit(0)
            }
        } else if os.Args[2][0] == 'p' || os.Args[2][0] == 'P' {  //pci scan
            var skipelba uint32 
            if contains(os.Args, "-noelba") {
                skipelba = 1
            }
            rc := taormina.Pci_scan(skipelba)
            if rc != errType.SUCCESS {
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
        if os.Args[2][0] == 'l' || os.Args[2][0] == 'L' {  //link

            rc := taormina.Enable_Trident3_Ports()
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } 

            ps_output, err := td3.ExecBCMshellCMD("ps", 5)
            if err != errType.SUCCESS {
                return
            }
            fmt.Printf("\n")
            for i , entry := range(td3.TaorPortMap) {
                rc := td3.LinkCheck(entry.Name, ps_output) 
                if rc == errType.LINK_UP {
                    cli.Printf("i", "Port-%.02d  %4s: LINK UP\n", i+1, entry.Name)
                } else if rc == errType.LINK_DOWN {
                    cli.Printf("i", "Port-%.02d  %4s: LINK DOWN\n", i+1, entry.Name)
                } else if rc == errType.LINK_DISABLED {
                    cli.Printf("i", "Port-%.02d  %4s: LINK DISABLED\n", i+1, entry.Name)
                } else {
                    cli.Printf("e", "Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, entry.Name)
                }
            }
            fmt.Printf("\n")
            rc = taormina.BCM_GearBox_Check_Link(1, 1)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } 

            rc = taormina.BCM_Retimer_Check_Link(1, 1)
            if rc != errType.SUCCESS {
                os.Exit(-1) 
            } 

            //Get Elba's memory info to see how much free memory is available to test with
            for i:=0; i < 2; i++ {
                var cmdStr string
                if  i == 0 {
                    cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.13.1 /nic/bin/pdsctl show port status"
                    fmt.Printf("\nELBA0 LINK STATUS\n")
                } else if i == 1 {
                    cmdStr = "ip netns exec ntb sshpass -p pen123 timeout 500 ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@169.254.7.1 /nic/bin/pdsctl show port status"
                    fmt.Printf("\nELBA1 LINK STATUS\n")
                } 
                output , errGo := exec.Command("sh", "-c", cmdStr).Output()
                if errGo != nil {
                    cli.Printf("e", "Cmd %s failed! %v", cmdStr, errGo)
                    err = errType.FAIL
                    return
                }
                
                fmt.Printf("%s\n", output)
            }
            
            os.Exit(0)

        } else if os.Args[2][0] == 'p' || os.Args[2][0] == 'P' {    //power
            rc = taormina.ShowPower()
        } else if os.Args[2][0] == 't' || os.Args[2][0] == 'T' {    //temperature
            rc = taormina.ShowTemperature()
        } else if os.Args[2][0] == 'f' || os.Args[2][0] == 'F' {    //fans
            rc = taormina.ShowFanSpeed() 
        } else {
            fmt.Printf(" Bad ARG--> ARGV[2]=%s\n", os.Args[2])
            return
        }
        if rc != errType.SUCCESS {
            os.Exit(-1)
        } else { 
            os.Exit(0)
        }

    }
    return
}


func contains(s []string, str string) bool {
    for _, v := range s {
            if len(v) < len(str) {
                continue
            }
            if v[:len(str)] == str {
                    return true
            }
    }

    return false
}


func contains_with_a_value(s []string, str string) (data32 uint32, found bool) {
    fmt.Printf(" str=%s\n", str);
    for _, v := range s {
            if len(v) < len(str) {
                continue
            }
            if v[:len(str)] == str {
                s1 := strings.Split(v, ":")
                tmp64, err := strconv.ParseUint(s1[1], 0, 32)
                if err != nil {
                    fmt.Printf(" Parse error. %s:%s  Err return says '%s'\n", err, s1[0], s1[1], err); os.Exit(-1)
                }
                data32 = uint32(tmp64)
                found=true
                return
            }
    }

    found = false
    return
}


func contains_with_a_string(s []string, str string, strarg string) (found bool) {
    fmt.Printf(" str=%s strarg=%s\n", str, strarg);
    for _, v := range s {
            if len(v) < len(str) {
                continue
            }
            if v[:len(str)] == str {
                s1 := strings.Split(v, ":")
                if s1[1] == strarg {
                    found = true
                    return
                }
            }
    }

    found = false
    return
}





 
