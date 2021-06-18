package td3

import (
    "fmt"
    "os"
    "regexp"
    "strconv"
    //"strings"
    "os/exec"
    //"cardinfo"
    "common/cli"
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
"timeout = 1\n"+
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
"f = open('/tmp/show_temp', 'w')\n"+
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
"else:\n"+
"    tn.close()\n"+
"\n"+
"tn.write('exit \\n')\n"+
"tn.close\n"+
"timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())\n"+
"f.write('\\n')\n"+
"f.write(timestamp)\n"+
"f.close()\n"+
"os.system(\"cat /tmp/show_temp\")\n"+
"\n"



func ReadTemp(devName string) (currTemp []float64, peakTemp []float64, err int) {
    var cmdString string
    path, errE := os.Getwd()
    if errE != nil {
        fmt.Println(errE)
        err = errType.FAIL
        return
    }
    path = path + "/bcm_shell_execute_cmd.py"

    f, errEE := os.Open(path)
    if errEE != nil {
        fmt.Printf(" show_temp.py does not exist.. creating file\n")
        f, errEEE := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0644)
        if errEEE != nil {
            fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", path, errEEE)
            err = errType.FAIL
            return
        }
        f.WriteString(string(bcm_shell_execute_cmd[:]))
        f.Close()
	os.Chmod(path, 0777)
    } else {
        f.Close()
    }
    cmdString = path + " \"show temp\""
    output, errGo := exec.Command("bash", "-c", cmdString).Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    re := regexp.MustCompile(`= [-]?\d[\d,]*[\.]?[\d{2}]*`)
    matches := re.FindAllString(string(output), -1)

    for i, match := range matches {
        if i % 2 == 0 {
            tFloat, _ := strconv.ParseFloat(match[2:], 64)
            currTemp = append(currTemp, tFloat)
        } else {
            tFloat, _ := strconv.ParseFloat(match[2:], 64)
            peakTemp = append(peakTemp, tFloat)
        }
        
    }
    return
}





func DispStatus(devName string) (err int) {
    cTemp := []float64{}
    pTemp := []float64{}
    err = errType.SUCCESS
    



    cTemp, pTemp, err = ReadTemp(devName)
    if err != errType.SUCCESS {
        return err
    }

    degSym := fmt.Sprintf("(%cC)",0xB0)
    tmpStr := fmt.Sprintf("%-10s Current Temp %s", devName, degSym)
    for _, temp := range cTemp {
        tmpStr = fmt.Sprintf("%s %0.1f", tmpStr, temp)
    }
    cli.Println("i", tmpStr)
    degSym = fmt.Sprintf("(%cC)",0xB0)
    tmpStr = fmt.Sprintf("%-10s Peak Temp    %s", devName, degSym)
    for _, temp := range pTemp {
        tmpStr = fmt.Sprintf("%s %0.1f", tmpStr, temp)
    }
    cli.Println("i", tmpStr)
    return
}


