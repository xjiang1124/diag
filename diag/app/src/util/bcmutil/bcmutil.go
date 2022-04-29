package main

import (
    "flag"
    "os"
    "os/exec"
    "strconv"
    "strings"
    "bufio"
    "fmt"
    "time"

    "common/cli"
    "common/dcli"
    "common/errType"
)


const bcm_shell_execute_cmd =
"#!/usr/bin/env python\n\n"+
"from pyroute2 import netns\n"+
"from telnetlib import Telnet\n"+
"import signal\n"+
"import datetime\n"+
"import sys\n"+
"import os\n"+
"\n"+
"timeout = 1200\n"+
"netns.setns('swns')\n"+
"\n"+
"# create a script-wide timeout event\n"+
"\n"+
"\n"+
"def script_timeout_event(signum, frame):\n"+
"    raise Exception('Script exceeded timeout.')\n"+
"\n"+
"\n"+
"signal.signal(signal.SIGALRM, script_timeout_event)\n"+
"signal.alarm(timeout)\n"+
"\n"+
"# create the telnet connection\n"+
"tn = Telnet('127.0.0.1', '1943', timeout)\n"+
"\n"+
"# Add commands in the list.\n"+
"# Format : 'command  \n\n"+
"commandList = []\n"+
"\n"+
"# For taking command line arguments\n"+
"# Format : sudo python collect_bcm_l1_port_info.py command\n"+
"sys.argv = [i+' \\n' for i in sys.argv]\n"+
"if len(sys.argv) > 1:\n"+
"    commandList = commandList + sys.argv[1:]\n"+
"\n"+
"# Output File Location\n"+
"f = open('/tmp/bcm_cmd_output', 'w')\n"+
"\n"+
"# HPE BCM Shell has prompt BCM.0> immediately once login\n"+
"# no need to write a '\\n'. Instead, need to read to consume the first 'BCM.0>'\n"+
"# but diag bcm shell need to write \\n to reach prompt\n"+
"output = os.popen('ps -x | grep bcm.user | grep -v grep').read()\n"+
"if output.find('bcm.user') != -1:\n"+
"    tn.write('\\n')\n"+
"\n"+
"data = tn.read_until('BCM.0>')\n"+
"if data:\n"+
"    f.write(data)\n"+
"    # Loop over the commandList\n"+
"    # Collecting data till the next BCM.0 prompt\n"+
"for i in commandList:\n"+
"    tn.write(i)\n"+
"    data = tn.read_until('BCM.0>')\n"+
"    if data:\n"+
"        f.write(data)\n"+
"#else:\n"+
"#    tn.close()\n"+
"\n"+
"#tn.write('exit \\n')\n"+
"tn.write('\\n')\n"+
"tn.close\n"+
"f.write('\\n')\n"+
"timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())\n"+
"f.write(timestamp)\n"+
"f.write('\\n')\n"+
"f.close()\n"+
"os.system(\"cat /tmp/bcm_cmd_output\")\n"+
"\n"


const bcm_shell_execute_cmd_w_exit =
"#!/usr/bin/env python\n\n"+
"from pyroute2 import netns\n"+
"from telnetlib import Telnet\n"+
"import signal\n"+
"import datetime\n"+
"import sys\n"+
"import os\n"+
"import socket\n"+
"\n"+
"timeout = 1200\n"+
"netns.setns('swns')\n"+
"\n"+
"# create a script-wide timeout event\n"+
"\n"+
"\n"+
"def script_timeout_event(signum, frame):\n"+
"    raise Exception('Script exceeded timeout.')\n"+
"\n"+
"\n"+
"signal.signal(signal.SIGALRM, script_timeout_event)\n"+
"signal.alarm(timeout)\n"+
"\n"+
"# create the telnet connection\n"+
"tn = Telnet('127.0.0.1', '1943', timeout)\n"+
"\n"+
"# Add commands in the list.\n"+
"# Format : 'command  \n\n"+
"commandList = []\n"+
"\n"+
"# For taking command line arguments\n"+
"# Format : sudo python collect_bcm_l1_port_info.py command\n"+
"sys.argv = [i+' \\n' for i in sys.argv]\n"+
"if len(sys.argv) > 1:\n"+
"    commandList = commandList + sys.argv[1:]\n"+
"#commandList.append('exit \\n')\n"+
"\n"+
"# Output File Location\n"+
"f = open('/tmp/bcm_cmd_output', 'w')\n"+
"\n"+
"output = os.popen('ps -x | grep bcm.user | grep -v grep').read()\n"+
"if output.find('bcm.user') != -1:\n"+
"    tn.write('\\n')\n"+
"\n"+
"data = tn.read_until('BCM.0>')\n"+
"if data:\n"+
"    f.write(data)\n"+
"    # Loop over the commandList\n"+
"    # Collecting data till the next BCM.0 prompt\n"+
"    for i in commandList:\n"+
"        tn.write(i)\n"+
"        data = tn.read_until('BCM.0>')\n"+
"        f.write(data)\n"+
"#else:\n"+
"#    tn.close()\n"+
"#\n"+
"#tn.write('exit \\n')\n"+
"#tn.get_socket().shutdown(socket.SHUT_WR)\n"+
"tn.write('\\n')\n"+
"tn.close\n"+
"f.write('\\n')\n"+
"timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())\n"+
"f.write(timestamp)\n"+
"f.write('\\n')\n"+
"f.close()\n"+
"os.system(\"cat /tmp/bcm_cmd_output\")\n"+
"\n"


const fpga_get_dev_bar =
"#!/bin/bash\n\n"+
"echo -n \"0x\" > /tmp/fpgabars\n"+
"lspci -s 12:00.0 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars\n"+
"echo -n \"0x\" >> /tmp/fpgabars\n"+
"lspci -s 12:00.1 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars\n"+
"echo -n \"0x\" >> /tmp/fpgabars\n"+
"lspci -s 12:00.2 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars\n"+
"echo -n \"0x\" >> /tmp/fpgabars\n"+
"lspci -s 12:00.3 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars\n"+
"\n"


const BCM_SCRIPT_FILE_NAME  =  "/bcm_shell_execute_cmd.py"
const BCM_SCRIPT_FILE_NAME_W_EXIT  =  "/bcm_shell_execute_cmd_w_exit.py"
const FPGA_GET_DEV_BAR_SCRIPT_NAME = "./fpga_get_dev_bar.sh"
const FPGABARS = "/tmp/fpgabars"


func ExecBCMshellCMD(commands string) (command_output string, err int) {
    var cmdString string
    var retry int = 2
    var bcm_cmd_cnt uint64 = 0
    var bcm_w_exit_limit uint64 = 890
    var path string

    err = errType.SUCCESS
    original_path, errE := os.Getwd()
    if errE != nil {
        fmt.Println(errE)
        err = errType.FAIL
        return
    }

    _, errE = os.Stat("/tmp/bcm_cnt.txt")
    //TRY TO STORE THE BAR VALUES IN A FILE.  WE DONT WANT TO SCAN THE PCI AND GET THE BARS EVERYTIME WE USE ONE OF THE DIAG UTILITIES THAT CALLS THIS INIT
    if errE == nil {
        file, errGo := os.Open("/tmp/bcm_cnt.txt")
        if errGo != nil {
            cli.Println("e", "ERROR: Failed to Open /tmp/bcm_cnt.txt.   GO ERROR=%v", errGo)
            return
        }
        scanner := bufio.NewScanner(file)
        for scanner.Scan() {
            bcm_cmd_cnt, _ = strconv.ParseUint(strings.TrimSuffix(scanner.Text(), "\n"), 0, 64)
        }
        file.Close()
    }

    file, errGo := os.OpenFile("/tmp/bcm_cnt.txt", os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
    if errGo != nil {
        cli.Println("e", "ERROR: Failed to Open /tmp/bcm_cnt.txt.   GO ERROR=%v", errGo)
        return
    }
    bcm_cmd_cnt = bcm_cmd_cnt+1
    datawriter := bufio.NewWriter(file)
    _, _ = datawriter.WriteString(fmt.Sprintf("0x%x\n", bcm_cmd_cnt))
    datawriter.Flush()
    file.Close()

    for i:=0; i<retry; i++ {

        if bcm_cmd_cnt < bcm_w_exit_limit {
            path = original_path + BCM_SCRIPT_FILE_NAME_W_EXIT
        } else if bcm_cmd_cnt == bcm_w_exit_limit {
            dcli.Printf("i","[INFO/WARN] SWITCHING BCM SCRIPT\n")
            path = original_path + BCM_SCRIPT_FILE_NAME//"/bcm_shell_execute_cmd.py"
        } else {
            path = original_path + BCM_SCRIPT_FILE_NAME//"/bcm_shell_execute_cmd.py"
        }
        f, errEE := os.Open(path)
        if errEE != nil {
            cli.Printf("i"," %s does not exist.. creating file\n", path)
            f, errEEE := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0644)
            if errEEE != nil {
                cli.Printf("e", " Failed to open filename=%s.   ERR=%s\n", path, errEEE)
                err = errType.FAIL
                return
            }
            if bcm_cmd_cnt < bcm_w_exit_limit {
                f.WriteString(string(bcm_shell_execute_cmd_w_exit[:]))
            } else {
                f.WriteString(string(bcm_shell_execute_cmd[:]))
            }
            f.Close()
            os.Chmod(path, 0777)
            cli.Printf("i"," %s created\n", path)
        } else {
            f.Close()
        }

        cmdString = path + " " + "\"" + commands + "\""           //" \"show temp\""
        //cli.Printf("i"," running '%s' ...\n", cmdString)
        output, errGo := exec.Command("bash", "-c", cmdString).Output()
        if errGo != nil {
            if i == 0 {
                cli.Println("i", "[WARN] Failed to exec bcm shell command:",cmdString," GoERR=",errGo)
                cli.Printf("i", "[WARN] Script output returned = %s\n", string(output))
                cli.Printf("i", "[WARN] RETRYING COMMAND\n")
                time.Sleep(time.Duration(3) * time.Second)
            } else {
                cli.Println("e", "Failed to exec bcm shell command:",cmdString," GoERR=",errGo)
                cli.Printf("e", "Script output returned = %s\n",string(output))
                err = errType.FAIL
                return
            }
        } else {
            command_output = string(output)
            return
        }
    }
    return
}

func initBCMShell() (err int) {
    var output string
    var gb_init_flag bool
    var rt_init_flag bool
    err = errType.SUCCESS

    gb_init_flag = get_gb_init_state()
    rt_init_flag = get_rt_init_state()

    output, err = ExecBCMshellCMD("init all")
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to execute 'init all'")
        cli.Println("e", "OUTPUT =", string(output))
        return err
    }

    if gb_init_flag {
        cli.Println("i", "Gearboxes are already init'd. Re-running init...")
    }
    output, err = ExecBCMshellCMD("gb_init")
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to execute 'gb_init'")
        cli.Println("e", "OUTPUT =", string(output))
        return err
    }

    if rt_init_flag {
        cli.Println("i", "Retimers are already init'd. Re-running init...")
    }
    output, err = ExecBCMshellCMD("rt_init")
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell failed to execute 'rt_init'")
        cli.Println("e", "OUTPUT =", string(output))
        return err
    }

    return errType.SUCCESS
}

func get_gb_init_state() (gb_init_flag bool) {
    gb_init_flag = false

    output, err := ExecBCMshellCMD("gb_state")
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

    output, err := ExecBCMshellCMD("rt_state")
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

func main() {
    initPtr      := flag.Bool(  "init", false, "Initialize all TD3/Gearbox/Retimer")
    infoPtr      := flag.Bool(  "info", false, "Display Taormina brd rev and phy info")
    statePtr     := flag.Bool( "state", false, "Display Gearbox and Retimer initialization state")
    configPtr    := flag.Bool("config", false, "Display Gearbox and Retimer settings")
    diagPtr      := flag.Bool(  "diag", false, "Display gearbox diagnostics (temperature and voltage)")
    sanityPtr    := flag.Bool("sanity", false, "Execute BCM TD3 sanity tests")
    prbsPtr      := flag.Bool(  "prbs", false, "Display PRBS settings, status, or run PRBS test")
    flag.Parse()

    var output string
    var outbyte []byte
    var err int
    var path string
    var errGo error
    var f_handler *os.File
    var cmdString string

    var gb_init_flag bool
    var rt_init_flag bool

    err = errType.SUCCESS

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

    if *initPtr == true {
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

        err = initBCMShell()
        if err != errType.SUCCESS {
            cli.Println("e", "BCM Shell failed to initialize TD3/Gearbox/Retimer")
        } else {
            cli.Println("i", "BCM Shell successfully initialized TD3/Gearbox/Retimer")
        }
        return
    }


    if *infoPtr == true {
        // good to run even gb/rt not yet init'd
        output, err = ExecBCMshellCMD("gbrt_info")
        if err != errType.SUCCESS {
            cli.Println("e", "BCM shell failed to execute 'gbrt_info'")
            cli.Println("e", "OUTPUT =", string(output))
            return
        } else {
            cli.Println("i", string(output))
        }
        return
    }


    if *statePtr == true {
        // read and display gb/rt init state
        gb_init_flag = get_gb_init_state()
        if gb_init_flag {
            cli.Println("i", "Gearbox Initialization State: True")
        } else {
            cli.Println("i", "Gearbox Initialization State: False")
        }

        rt_init_flag = get_rt_init_state()
        if rt_init_flag {
            cli.Println("i", "Retimer Initialization State: True")
        } else {
            cli.Println("i", "Retimer Initialization State: False")
        }

        return
    }


    if *configPtr == true {
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

        if gb_init_flag {
            output, err = ExecBCMshellCMD("gb_info")
            if err != errType.SUCCESS {
                cli.Println("e", "BCM shell failed to execute 'gb_info'")
                cli.Println("e", "OUTPUT =", string(output))
                return
            } else {
                cli.Println("i", string(output))
            }
        }

        if rt_init_flag {
            output, err = ExecBCMshellCMD("rt_info")
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


    if *diagPtr == true {
        gb_init_flag = get_gb_init_state()
        if !gb_init_flag {
            cli.Println("e", "Gearboxes are not yet initialized!")
            return
        }

        output, err = ExecBCMshellCMD("gb_diag all")
        if err != errType.SUCCESS {
            cli.Println("e", "BCM shell failed to execute 'gb_diag all'")
            cli.Println("e", "OUTPUT =", string(output))
            return
        } else {
            cli.Println("i", string(output))
        }
        return
    }


    if *sanityPtr == true {
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

        cli.Println("i", "BCM.0> rcload", path)
        cli.Println("i", "Estimated running time might be 15 minutes or more ...")
        output, err = ExecBCMshellCMD("rcload " + path)
        if err != errType.SUCCESS {
            cli.Println("e", "BCM shell failed to execute 'rcload", path, "'")
            cli.Println("e", "OUTPUT =", string(output))
            return
        }

        cli.Println("i", "==== test log file /tmp/bcm_cmd_output ====")
        cli.Println("i", "==== BCM TD3 sanity tests complete ====")

        return
    }


    if *prbsPtr == true {
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

        cli.Println("i", "to be implemented: execute PRBS test on Gearbox/Retimer system/line side")
        return
    }


    flag.Usage()
}

