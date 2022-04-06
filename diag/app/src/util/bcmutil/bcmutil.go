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
"timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())\n"+
"f.write('\\n')\n"+
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
"timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())\n"+
"f.write('\\n')\n"+
"f.write(timestamp)\n"+
"f.close()\n"+
"os.system(\"cat /tmp/bcm_cmd_output\")\n"+
"\n"


const BCM_SCRIPT_FILE_NAME  =  "/bcm_shell_execute_cmd.py"
const BCM_SCRIPT_FILE_NAME_W_EXIT  =  "/bcm_shell_execute_cmd_w_exit.py"


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
        cli.Printf("i"," running '%s' ...\n", cmdString)
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


func main() {
    initPtr      := flag.Bool(  "init", false, "Init TD3/Gearbox/Retimer")
    sanityPtr    := flag.Bool("sanity", false, "Execute BCM TD3 sanity tests")
    flag.Parse()

    var output string
    err := errType.SUCCESS

    if *initPtr == true {
        cli.Println("i", "Initializing TD3/Gearbox/Retimer ...")
        return
    }

    if *sanityPtr == true {
        cli.Println("i", "==== BCM TD3 sanity tests ====")

        path, errPath := os.Getwd()
        if errPath != nil {
            cli.Println("i", errPath)
            return
        }
        path = path + "/td3_sanity.soc"
        _, errPath = os.Stat(path)
        if errPath != nil {
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

    flag.Usage()
}

