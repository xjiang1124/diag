package main

import (
    "os"
    "os/exec"
    "strconv"
    "fmt"
    "flag"
    "strings"
    "common/errType"
    "common/cli"
    "device/bcm/td3"
)





func initBCMShell() (err int) {
    var output string
    var gb_init_flag bool
    var rt_init_flag bool
    err = errType.SUCCESS

    gb_init_flag = get_gb_init_state()
    rt_init_flag = get_rt_init_state()

    output, err = td3.ExecBCMshellCMD("init all", 20)
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to execute 'init all'")
        cli.Println("e", "OUTPUT =", string(output))
        return err
    }

    if gb_init_flag {
        cli.Println("i", "Gearboxes are already init'd. Re-running init...")
    }
    output, err = td3.ExecBCMshellCMD("gb_init", 10)

    
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to execute 'gb_init'")
        cli.Println("e", "OUTPUT =", string(output))
        return err
    }

    if rt_init_flag {
        cli.Println("i", "Retimers are already init'd. Re-running init...")
    }
    output, err = td3.ExecBCMshellCMD("rt_init", 10)
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to execute 'rt_init'")
        cli.Println("e", "OUTPUT =", string(output))
        return err
    }

    return errType.SUCCESS
}

func get_gb_init_state() (gb_init_flag bool) {
    gb_init_flag = false

    output, err := td3.ExecBCMshellCMD("gb_state", 5)
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to check gearbox init state")
        cli.Println("e", "OUTPUT =", string(output))
        return
    } else if strings.Contains(string(output), "Unknown command") {
        cli.Println("i", "HPE BCM Shell is running!")
        cli.Println("i", "Please execute 'start_diag_bcm_shell.sh' to switch to diag BCM shell for bcmutil.")
        return
    } else if strings.Contains(string(output), "True") {
        gb_init_flag = true
    } else {
        gb_init_flag = false
    }

    return gb_init_flag
}

func get_rt_init_state() (rt_init_flag bool) {
    rt_init_flag = false

    output, err := td3.ExecBCMshellCMD("rt_state", 5)
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to check retimer init state")
        cli.Println("e", "OUTPUT =", string(output))
        return
    } else if strings.Contains(string(output), "Unknown command") {
        cli.Println("i", "HPE BCM Shell is running!")
        cli.Println("i", "Please execute 'start_diag_bcm_shell.sh' to switch to diag BCM shell for bcmutil.")
        return
    } else if strings.Contains(string(output), "True") {
        rt_init_flag = true
    } else {
        rt_init_flag = false
    }

    return rt_init_flag
}


const errhelp = "\nbcmutil:\n" +
        "bcmutil td3 testinit\n" +
        "bcmutil td3 testrun <test#>\n" +
        "bcmutil td3 testresult <test#>\n" +
        "bcmutil td3 testall\n" +
        "\n" +
        "### TEST NUMBER AND DESCRIPTION ###\n" +
        "1   : Register reset defaults ...\n" +
        "2   : PCI Compliance ...\n" +
        "3   : Register read/write ...\n" +
        "4   : PCI S-Channel Buf ...\n" +
        "5   : BIST ...\n" +
        "21  : CPU Benchmarks ...\n" +
        "30  : Counter width verification test ...\n" +
        "31  : Counter read/write test ...\n" +
        "50  : Memory Fill/Verify ...\n" +
        "52  : Rand Mem Addr, write all\n" +
        "516 : TCAM BIST\n" +
        "\n"


func main() {
    infoPtr    := flag.Bool  (  "info", false, "Display Taormina brd rev and phy info")
    initPtr    := flag.Bool  (  "init", false, "Initialize all TD3/Gearbox/Retimer")
    dispPtr    := flag.Bool  (  "disp", false, "Display Gearbox and Retimer settings")
    diagPtr    := flag.Bool  (  "diag", false, "Display gearbox diagnostics (temperature and voltage)")
    prbsPtr    := flag.Bool  (  "prbs", false, "Display PRBS settings, status, or run PRBS test")
    lanePtr    := flag.Bool  (  "lane", false, "Display gearbox diagnostics lane status")
    sanityPtr  := flag.Bool  ("sanity", false, "Execute BCM TD3 sanity tests")

    // input parameters
    configPtr  := flag.Bool  ("config", false, "Display Gearbox and Retimer settings")
    enablePtr  := flag.Bool  ( "enable", false, "Enable PRBS test on Gearbox or Retimer, sys/line side")
    statusPtr  := flag.Bool  ( "status", false, "Display initialization status or PRBS test status")
    clearPtr   := flag.Bool  (  "clear", false, "Clear PRBS status, and disable PRBS")
    devNamePtr := flag.String(    "dev", "all", "Device name: gb (gearbox) or rt (retimer)")
    devidxPtr  := flag.Int   (    "idx", 0,     "Device index: gb [0 ~ 3] or rt [0 ~ 2]")
    sidePtr    := flag.String(   "side", "",    "if_side: [sys|line]")
    polyPtr    := flag.String(   "poly", "",    "PRBS polynomial (e.g. poly58, poly31, etc.")
    lanemapPtr := flag.Int   ("lanemap", 0,     "lane_map")
    dbglvlPtr  := flag.Int   ( "dbglvl", 0,     "debug level [0 ~ 3]")

    flag.Parse()
    dev     := strings.ToLower(*devNamePtr)
    devidx  := *devidxPtr
    side    := strings.ToLower(*sidePtr)
    poly    := strings.ToLower(*polyPtr)
    lanemap := *lanemapPtr
    dbglvl  := *dbglvlPtr

    var output string
    var outbyte []byte
    var err int
    var path string
    var errGo error
    //var f_handler *os.File
    var cmdString string

    var gb_init_flag bool
    var rt_init_flag bool

    err = errType.SUCCESS

    argc := len(os.Args[0:])

    if argc < 2 {
        fmt.Printf(" %s \n", errhelp)
        flag.Usage()
        fmt.Printf("\n")
        return
    }
    
    if os.Args[1] == "td3" {

        if argc < 3 {
            fmt.Printf(" %s \n", errhelp)
            flag.Usage()
            fmt.Printf("\n")
            return
        }
        if os.Args[2] == "testinit" {
            rc := td3.BCMShell_Test_Init()
            if rc != errType.SUCCESS {
                os.Exit(-1)
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "testall" {
            rc := td3.TD3_Run_Diags()
            if rc != errType.SUCCESS {
                os.Exit(-1)
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "testrun" {
             if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            testnumber, _ := strconv.ParseUint(os.Args[3], 0, 32)
            rc := td3.BCMshell_Test_Run(int(testnumber))
            if rc != errType.SUCCESS {
                os.Exit(-1)
            } else {
                os.Exit(0)
            }
        } else if os.Args[2] == "testresult" {
             if argc < 4 {
                fmt.Printf(" %s \n", errhelp)
                return
            }
            testnumber, _ := strconv.ParseUint(os.Args[3], 0, 32)
            loop, runcnt, passcnt, failcnt, _ := td3.BCMshell_Test_Results(int(testnumber))
            fmt.Printf(" LoopCnt=%d  ", loop)
            fmt.Printf(" Runcnt=%d  ", runcnt)
            fmt.Printf(" Passcnt=%d  ", passcnt)
            fmt.Printf(" Failcnt=%d  ", failcnt)
            return
        } else {
            fmt.Printf("\nERROR: argv[1] is invalid\n")
            fmt.Printf(" %s \n", errhelp)
            return
        }
        
    } else {  

        // check if diag BCM shell is running. If not exit
        cmdString = "ps aux"
        outbyte, errGo = exec.Command("bash", "-c", cmdString).Output()
        if errGo != nil {
            cli.Println("e", "Failed to check if diag BCM shell is running!")
            return
        } else if !strings.Contains(string(outbyte), "bcm.user") {
            cli.Println("i", "Diag BCM shell is NOT running!")
            cli.Println("i", "Please run script start_diag_bcm_shell to launch and try again.")
            cli.Println("i", "Note: quit the Diag BCM shell session with Telnet escape sequence '<Ctrl> + ] + quit'.")
            return
        }


        if *infoPtr {
            // good to run even gb/rt not yet init'd
            output, err = td3.ExecBCMshellCMD("gbrt_info", 5)
            if err != errType.SUCCESS {
                cli.Println("e", "BCM shell failed to execute 'gbrt_info'")
                cli.Println("e", "OUTPUT =", string(output))
                return
            } else {
                cli.Println("i", string(output))
            }
            return
        }


        if *initPtr {
            if *statusPtr {
                // read and display gb/rt init status
                if get_gb_init_state() {
                    cli.Println("i", "Gearbox Initialization State: True")
                } else {
                    cli.Println("i", "Gearbox Initialization State: False")
                }
                if get_rt_init_state() {
                    cli.Println("i", "Retimer Initialization State: True")
                } else {
                    cli.Println("i", "Retimer Initialization State: False")
                }
                return
            }

            /*
            // check file FPGABARS not exist, run script to create it
            // if script not exist, create script
            // Note: BCM Shell cannot handle Linux shell script
            _, errGo = os.Stat(FPGABARS)
            if errGo != nil {
                cli.Println("e", "Failed to open", FPGABARS)
                _, errGo = os.Stat(FPGA_GET_DEV_BAR_SCRIPT_NAME)
                if errGo != nil {
                    cli.Println("e", "Failed to open", FPGA_GET_DEV_BAR_SCRIPT_NAME)
                    f_handler, errGo = os.OpenFile(FPGA_GET_DEV_BAR_SCRIPT_NAME, os.O_CREATE|os.O_WRONLY, 0644)
                    if errGo != nil {
                        cli.Printf("e", " Failed to open filename=%s.   ERR=%s\n", FPGA_GET_DEV_BAR_SCRIPT_NAME, errGo)
                        err = errType.FAIL
                        return
                    }
                    f_handler.WriteString(string(fpga_get_dev_bar[:]))
                    f_handler.Close()
                    cli.Printf("i", " Created file %s\n", FPGA_GET_DEV_BAR_SCRIPT_NAME)
                }
                os.Chmod(FPGA_GET_DEV_BAR_SCRIPT_NAME, 0777)
                _, errGo = exec.Command("bash", "-c", FPGA_GET_DEV_BAR_SCRIPT_NAME).Output()
                if errGo != nil {
                    cli.Printf("e", " Failed to execute %s. ERR=%s\n", FPGA_GET_DEV_BAR_SCRIPT_NAME, errGo)
                    return
                }
                cli.Printf("i", " Executed %s to create file %s\n", FPGA_GET_DEV_BAR_SCRIPT_NAME, FPGABARS)
            }
            */
            

            err = initBCMShell()
            if err != errType.SUCCESS {
                cli.Println("e", "BCM Shell failed to initialize TD3/Gearbox/Retimer")
            } else {
                cli.Println("i", "BCM Shell successfully initialized TD3/Gearbox/Retimer")
            }
            return
        }


        if dev != "all" && dev != "gb" && dev != "rt" {
            cli.Println("e", "Unsupported device name:", dev)
            return
        }

        gb_init_flag = get_gb_init_state()
        rt_init_flag = get_rt_init_state()
        if !gb_init_flag && !rt_init_flag {
            cli.Println("e", "Gearboxes and restimers are not yet initialized!")
            return
        } else if !gb_init_flag {
            cli.Println("e", "Gearboxes are not initialized!")
        } else if !rt_init_flag {
            cli.Println("e", "Retimers are not initialized!")
        }


        if *dispPtr {
            if gb_init_flag && (dev == "all" || dev == "gb") {
                output, err = td3.ExecBCMshellCMD("gb_info", 5)
                if err != errType.SUCCESS {
                    cli.Println("e", "BCM shell failed to execute 'gb_info'")
                    cli.Println("e", "OUTPUT =", string(output))
                    return
                } else {
                    cli.Println("i", string(output))
                }
            }

            if rt_init_flag && (dev == "all" || dev == "rt") {
                output, err = td3.ExecBCMshellCMD("rt_info", 5)
                if err != errType.SUCCESS {
                    cli.Println("e", "BCM shell failed to execute 'rt_info'")
                    cli.Println("e", "OUTPUT =", string(output))
                    return
                } else {
                    cli.Println("i", string(output))
                }
            }

            return
        }


        if *diagPtr {
            output, err = td3.ExecBCMshellCMD("gb_diag all", 20)
            if err != errType.SUCCESS {
                cli.Println("e", "BCM shell failed to execute 'gb_diag all'")
                cli.Println("e", "OUTPUT =", string(output))
                return
            } else {
                cli.Println("i", string(output))
            }
            return
        }


        if *sanityPtr {
            // only sanity check on TD3, nothing for GB/RT
            cli.Println("i", "==== BCM TD3 sanity tests ====")
            path, errGo = os.Getwd()
            if errGo != nil {
                cli.Println("i", errGo)
                return
            }
            path = path + "/td3_sanity.soc"
            _, errGo = os.Stat(path)
            if errGo != nil {
                cli.Println("e", "Failed to open", path)
                return
            }
        }

        if *prbsPtr {
            //bcmutil only work with Diag BCM shell
            if dev != "gb" && dev != "rt" {
                cli.Println("e", "device", dev, "not supported! Please use gb (gearbox) or rt (retimer)")
                return
            }

            if *configPtr {
                // display PRBS configurations
                cmdString = dev + "_prbs config"
                output, err = td3.ExecBCMshellCMD(cmdString, 5)
                if err != errType.SUCCESS {
                    cli.Println("e", "BCM shell failed to execute", cmdString)
                    cli.Println("e", "OUTPUT =", string(output))
                    return
                } else {
                    cli.Println("i", string(output))
                }

                return
            }

            if side != "sys" && side != "line" {
                cli.Println("e", "Invalid if_side", side, "please use -side=<sys|line>")
                return
            }

            if *statusPtr {
                cmdString = dev + "_prbs status " + side
                output, err = td3.ExecBCMshellCMD(cmdString, 5)
                if err != errType.SUCCESS {
                    cli.Println("e", "BCM shell failed to execute", cmdString)
                    cli.Println("e", "OUTPUT =", string(output))
                    return
                } else {
                    cli.Println("i", string(output))
                }

                return
            }

            if *clearPtr {
                // Clear PRBS status, and disable PRBS
                cmdString = dev + "_prbs clear " + side
                output, err = td3.ExecBCMshellCMD(cmdString, 5)
                if err != errType.SUCCESS {
                    cli.Println("e", "BCM shell failed to execute", cmdString)
                    cli.Println("e", "OUTPUT =", string(output))
                    return
                } else {
                    cli.Println("i", string(output))
                }

                return
            }

            if poly != "poly7" && poly != "poly9" && poly != "poly11" &&
               poly != "poly15" && poly != "poly23" && poly != "poly31" &&
               poly != "poly58" && poly != "poly49" && poly != "poly10" &&
               poly != "poly20" && poly != "poly13" {
                cli.Println("e", dev, side, "invalid poly string:", poly)
                return
            }

            if *enablePtr {
                // <dev>_prbs enable <side> gen <poly>
                cmdString = dev + "_prbs enable " + side + " gen " + poly
                output, err = td3.ExecBCMshellCMD(cmdString, 5)
                if err != errType.SUCCESS {
                    cli.Println("e", "BCM shell failed to execute", cmdString)
                    cli.Println("e", "OUTPUT =", string(output))
                    return
                } else {
                    cli.Println("i", string(output))
                }

                // <dev>_prbs enable <side> chk <poly>
                cmdString = dev + "_prbs enable " + side + " chk " + poly
                output, err = td3.ExecBCMshellCMD(cmdString, 5)
                if err != errType.SUCCESS {
                    cli.Println("e", "BCM shell failed to execute", cmdString)
                    cli.Println("e", "OUTPUT =", string(output))
                    return
                } else {
                    cli.Println("i", string(output))
                }

                return
            }

            cli.Println("i", "Usage: bcmutil -prbs -config|enable|status|clear -dev=gb|rt -side=sys|line -poly=poly")
            return
        }

        if *lanePtr {
            if dev != "gb" && dev != "rt" {
                cli.Println("e", "device", dev, "not supported! Please use gb (gearbox) or rt (retimer)")
                return
            }

            if dev == "gb" {
                if devidx < 0 || devidx > 3 {
                   cli.Println("e", "Gearbox index is out of range [0 ~ 3]:", devidx)
                   return
                }
                if lanemap != 0xf && lanemap != 0xf0 {
                    cli.Println("e", "Invalid gearbox lane_map [0x0F | 0xF0]:", lanemap)
                   return
                }
            }

            if dev == "rt" {
                if devidx < 0 || devidx > 2 {
                   cli.Println("e", "Retimer index is out of range [0 ~ 2]:", devidx)
                   return
                }
                if lanemap <= 0x0 && lanemap > 0xff {
                    cli.Println("e", "Invalid retimer lane_map [0x01 ~ 0xFF]:", lanemap)
                   return
                }
            }

            if dbglvl < 0 || dbglvl > 3 {
                dbglvl = 0
            }
            if dbglvl == 3 {
                cli.Println("i", "Be patient! Debug level 3 takes longer time to dump eye diagram...")
            }

            // gb_lane status <gb_idx> <lane_map [0x0f|0xf0]> [dbg_lvl [0-3]]
            // rt_lane status <rt_idx> <lane_map [0x01~0xff]> [dbg_lvl [0-3]]
            cmdString = fmt.Sprintf("%s_lane status %d lane_map %d dbglvl %d", dev, devidx, lanemap, dbglvl)
            output, err = td3.ExecBCMshellCMD(cmdString, 5)
            if err != errType.SUCCESS {
                cli.Println("e", "BCM shell failed to execute", cmdString)
                cli.Println("e", "OUTPUT =", string(output))
                return
            } else {
                cli.Println("i", string(output))
            }

            return
        }
    }

    fmt.Printf(" %s \n", errhelp)
    flag.Usage()
    fmt.Printf("\n")
}

