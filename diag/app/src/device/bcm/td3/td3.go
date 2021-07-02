package td3

import (
    "bufio"
    "fmt"
    "os"
    "regexp"
    "strconv"
    "time"
    "strings"
    "os/exec"
    //"cardinfo"
    "common/cli"
    "common/errType"
    "device/fpga/taorfpga"
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
"f = open('/tmp/bcm_cmd_output', 'w')\n"+
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
"os.system(\"cat /tmp/bcm_cmd_output\")\n"+
"\n"



const BCM_SCRIPT_FILE_NAME  =  "/bcm_shell_execute_cmd.py"


// EEPROM entry data structure
type PortMap struct {
    SwitchPort      int
    PhysicalPort    int
    Name            string
}

const (
    TAOR_EXTERNAL_25G_PORTS  = 48
    TAOR_EXTERNAL_100G_PORTS = 6
    TAOR_INTERNAL_PORTS = 8
)

var TaorPortMap = []PortMap {
    PortMap{0, 23, "xe8"},   //Front Panel Port 0
    PortMap{1, 24, "xe9"},   //Front Panel Port 1
    PortMap{2, 21, "xe6"},   //Front Panel Port 2
    PortMap{3, 22, "xe7"},   //Front Panel Port 3
    PortMap{4, 27, "xe12"},   //Front Panel Port 4
    PortMap{5, 28, "xe13"},   //Front Panel Port 5
    PortMap{6, 25, "xe10"},   //Front Panel Port 6
    PortMap{7, 26, "xe11"},   //Front Panel Port 7
    PortMap{8, 31, "xe16"},   //Front Panel Port 8
    PortMap{9, 32, "xe17"},   //Front Panel Port 9
    PortMap{10, 29, "xe14"},  //Front Panel Port 10
    PortMap{11, 30, "xe15"},  //Front Panel Port 11
    PortMap{12, 47, "xe26"},  //Front Panel Port 12
    PortMap{13, 48, "xe27"},  //Front Panel Port 13
    PortMap{14, 45, "xe24"},  //Front Panel Port 14
    PortMap{15, 46, "xe25"},  //Front Panel Port 15
    PortMap{16, 51, "xe30"},  //Front Panel Port 16
    PortMap{17, 52, "xe31"},  //Front Panel Port 17
    PortMap{18, 49, "xe28"},  //Front Panel Port 18
    PortMap{19, 50, "xe29"},  //Front Panel Port 19
    PortMap{20, 55, "xe34"},  //Front Panel Port 20
    PortMap{21, 56, "xe35"},  //Front Panel Port 21
    PortMap{22, 53, "xe32"},  //Front Panel Port 22
    PortMap{23, 54, "xe33"},  //Front Panel Port 23
    PortMap{24, 68, "xe37"},  //Front Panel Port 24
    PortMap{25, 67, "xe36"},  //Front Panel Port 25
    PortMap{26, 70, "xe39"},  //Front Panel Port 26
    PortMap{27, 69, "xe38"},  //Front Panel Port 27
    PortMap{28, 72, "xe41"},  //Front Panel Port 28
    PortMap{29, 71, "xe40"},  //Front Panel Port 29
    PortMap{30, 74, "xe43"},  //Front Panel Port 30
    PortMap{31, 73, "xe42"},  //Front Panel Port 31
    PortMap{32, 76, "xe45"},  //Front Panel Port 32
    PortMap{33, 75, "xe44"},  //Front Panel Port 33
    PortMap{34, 78, "xe47"},  //Front Panel Port 34
    PortMap{35, 77, "xe46"},  //Front Panel Port 35
    PortMap{36, 100, "xe55"}, //Front Panel Port 36
    PortMap{37, 99 , "xe54"}, //Front Panel Port 37
    PortMap{38, 102, "xe57"}, //Front Panel Port 38
    PortMap{39, 101, "xe56"}, //Front Panel Port 39
    PortMap{40, 104, "xe59"}, //Front Panel Port 40
    PortMap{41, 103, "xe58"}, //Front Panel Port 41
    PortMap{42, 106, "xe61"}, //Front Panel Port 42
    PortMap{43, 105, "xe60"}, //Front Panel Port 43
    PortMap{44, 108, "xe63"}, //Front Panel Port 44
    PortMap{45, 107, "xe62"}, //Front Panel Port 45
    PortMap{46, 110, "xe65"}, //Front Panel Port 46
    PortMap{47, 109, "xe64"}, //Front Panel Port 47

    PortMap{48, 57, "ce5"},   //Front Panel Port 48 100G
    PortMap{49, 61, "ce6"},   //Front Panel Port 49 100G
    PortMap{50, 83, "ce7"},   //Front Panel Port 50 100G
    PortMap{51, 87, "ce8"},   //Front Panel Port 51 100G
    PortMap{52, 115, "ce11"}, //Front Panel Port 52 100G
    PortMap{53, 1  , "ce0"},  //Front Panel Port 53 100G

    PortMap{54, 9  , "ce1"},  //Internal Port to ELBA0.3 100G
    PortMap{55, 91 , "ce9"},  //Internal Port to ELBA0.2 100G
    PortMap{56, 95 , "ce10"}, //Internal Port to ELBA1.3 100G
    PortMap{57, 13 , "ce2"},  //Internal Port to ELBA1.2 100G
    PortMap{58, 123, "ce12"}, //Internal Port to ELBA0.0 100G
    PortMap{59, 127, "ce13"}, //Internal Port to ELBA1.1 100G
    PortMap{60, 33,  "ce3"},  //Internal Port to ELBA0.1 100G
    PortMap{61, 37,  "ce4"},  //Internal Port to ELBA1.0 100G
}



/* 
PRBS 
port xe6-xe17,xe24-xe47,xe54-xe65 enable=true 
port ce0,ce5,ce6-ce8,ce11 enable=true 

BCM.0> ps
                 ena/        speed/ link auto    STP                  lrn  inter   max   cut   loop
           port  link  Lns   duplex scan neg?   state   pause  discrd ops   face frame  thru?  back
       ce0(  1)  down   4  100G  FD   SW  No   Forward  TX RX   None   FA  CAUI4  9412    No
       ce1(  9)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
       xe0( 10)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
       xe1( 11)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
       xe2( 12)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
       ce2( 13)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
       xe3( 14)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
       xe4( 15)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
       xe5( 16)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
       xe6( 21)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No  
       xe7( 22)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
       xe8( 23)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
       xe9( 24)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe10( 25)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe11( 26)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe12( 27)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe13( 28)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe14( 29)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe15( 30)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe16( 31)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe17( 32)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
       ce3( 33)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
      xe18( 34)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe19( 35)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe20( 36)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
       ce4( 37)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
      xe21( 38)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe22( 39)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe23( 40)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe24( 45)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe25( 46)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe26( 47)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe27( 48)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe28( 49)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe29( 50)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe30( 51)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe31( 52)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe32( 53)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe33( 54)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe34( 55)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe35( 56)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
       ce5( 57)  down   4  100G  FD   SW  No   Forward  TX RX   None   FA  CAUI4  9412    No
       ce6( 61)  down   4  100G  FD   SW  No   Forward  TX RX   None   FA  CAUI4  9412    No
      xe36( 67)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe37( 68)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe38( 69)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe39( 70)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe40( 71)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe41( 72)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe42( 73)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe43( 74)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe44( 75)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe45( 76)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe46( 77)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe47( 78)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
       ce7( 83)  down   4  100G  FD   SW  No   Forward  TX RX   None   FA  CAUI4  9412    No
       ce8( 87)  down   4  100G  FD   SW  No   Forward  TX RX   None   FA  CAUI4  9412    No
       ce9( 91)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
      xe48( 92)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe49( 93)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe50( 94)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      ce10( 95)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
      xe51( 96)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe52( 97)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe53( 98)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe54( 99)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe55(100)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe56(101)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe57(102)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe58(103)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe59(104)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe60(105)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe61(106)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe62(107)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe63(108)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe64(109)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      xe65(110)  down   1   25G  FD   SW  No   Forward          None   FA     CR  9412    No
      ce11(115)  down   4  100G  FD   SW  No   Forward  TX RX   None   FA  CAUI4  9412    No
      ce12(123)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
      xe66(124)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe67(125)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe68(126)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      ce13(127)  !ena   4  100G  FD   SW  No     Block          None    F  CAUI4  9412    No
      xe69(128)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe70(129)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
      xe71(130)  !ena   1     -     None  No   Forward          None   FA   Null 16356    No
BCM.0>
*/ 

func ExecBCMshellCMD(commands string) (command_output string, err int) {
    var cmdString string
    err = errType.SUCCESS
    path, errE := os.Getwd()
    if errE != nil {
        fmt.Println(errE)
        err = errType.FAIL
        return
    }
    path = path + BCM_SCRIPT_FILE_NAME//"/bcm_shell_execute_cmd.py"

    f, errEE := os.Open(path)
    if errEE != nil {
        fmt.Printf(" %s does not exist.. creating file\n", path)
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
    cmdString = path + " " + commands//" \"show temp\""
    output, errGo := exec.Command("bash", "-c", cmdString).Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }
    command_output = string(output)
    return
}



/********************************************************** 
  *    @param prbs_mode          User specified polynomial
 *                              0 - PRBS7
 *                              1 - PRBS9
 *                              2 - PRBS11
 *                              3 - PRBS15
 *                              4 - PRBS23
 *                              5 - PRBS31
 *                              6 - PRBS58
***********************************************************/
func Prbs(sleep int, prbs string) (err int) {
    var errGo error
    var data32 uint32
    var addr uint64 = taorfpga.D0_FP_SFP_CTRL_3_0_REG;
    var SFPnumber, QSFPnumber, bitcompare uint32
    var port25G_s string
    var port100G_s string
    var tmp_s string
    var prbsType string

    if prbs == "prbs7" {
        prbsType = "0"
    } else if prbs == "prbs9" {
        prbsType = "1"
    } else if prbs == "prbs11" {
        prbsType = "2"
    } else if prbs == "prbs15" {
        prbsType = "3"
    } else if prbs == "prbs23" {
        prbsType = "4"
    } else if prbs == "prbs31" {
        prbsType = "5"
    } else if prbs == "prbs58" {
        prbsType = "6"
    } else {
        cli.Printf("e", "PRBS Parameter passed is not valid. You passed '%s'\n", prbs)
        err = errType.FAIL
        return
    }

    /* Check SFP's are present */
    cli.Printf("i", "Checking for SFP Presence\n")
    addr = taorfpga.D0_FP_SFP_STAT_3_0_REG;
    for SFPnumber=0;SFPnumber<taorfpga.MAXSFP;SFPnumber++ {
        addr = addr + ((uint64(SFPnumber)/4) * 4)
        bitcompare = (1 << ((SFPnumber%4)*8))
        data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
        if errGo != nil {
            err = errType.FAIL
            return
        }

        //1 = NOT PRESENT
        if (data32 & bitcompare) == bitcompare {
            cli.Printf("e", "SFP-%d is not detecting presence.  Check SFP-%d is present\n", SFPnumber+1, SFPnumber+1)
            err = errType.FAIL
            return
        } 
    }


    /* Check QSFP's are present */
    cli.Printf("i", "Checking for QSFP Presence\n")
    addr = taorfpga.D0_FP_QSFP_STAT_51_48_REG;
    for QSFPnumber=0;QSFPnumber<taorfpga.MAXSFP;QSFPnumber++ {
        addr = addr + ((uint64(QSFPnumber)/4) * 4)
        bitcompare = (1 << ((QSFPnumber%4)*8))
        data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
        if errGo != nil {
            err = errType.FAIL
            return
        }

        //1 = NOT PRESENT
        if (data32 & bitcompare) == bitcompare {
            cli.Printf("e", "QSFP-%d is not detecting presence.  Check QSFP-%d is present\n", QSFPnumber+1, QSFPnumber+1)
            err = errType.FAIL
            return
        } 
    }

    /* Enable SFP's */
    cli.Printf("i", "Enabling SFP's\n")
    addr = taorfpga.D0_FP_SFP_CTRL_3_0_REG;
    for i:=0;i<taorfpga.MAXSFP;i++ {
        addr = addr + ((uint64(i)/4) * 4)
        errGo = taorfpga.TaorWriteU32( taorfpga.DEVREGION0, addr, 0x06060606)
        if errGo != nil {
            err = errType.FAIL
            return
        }
    }

    //No return output to check on this command
    cli.Printf("i", "Disabling BCM LinkScan\n")
    command := " \"LINKscan off\""
    output, err := ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }


    for i:=0; i<TAOR_EXTERNAL_25G_PORTS; i++ {
        if i == (TAOR_EXTERNAL_25G_PORTS - 1) {
            tmp_s = fmt.Sprintf("%s", TaorPortMap[i].Name)
        } else {
            tmp_s = fmt.Sprintf("%s,", TaorPortMap[i].Name)
        }
        port25G_s = port25G_s + tmp_s
    }
    for i:=TAOR_EXTERNAL_25G_PORTS; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
        if i == (TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS - 1) {
            tmp_s = fmt.Sprintf("%s", TaorPortMap[i].Name)
        } else {
            tmp_s = fmt.Sprintf("%s,", TaorPortMap[i].Name)
        }
        port100G_s = port100G_s + tmp_s
    }
    
    //No return output to check on this command
    cli.Printf("i", "Enabling all 25G Ports\n")
    command = " \"port " + port25G_s +" enable=true\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = " \"port " + port100G_s +" enable=true\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 25G Ports\n")
    command = " \"phy diag " + port25G_s +" prbs set unit=0 p="+prbsType+"\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 100G Ports\n")
    command = " \"phy diag " + port100G_s +" prbs set unit=0 p="+prbsType+"\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //First time you read status it will show an error, have to read it again later after sleep
    cli.Printf("i", "Read Status to clear errors\n")
    command = " \"phy diag " + port25G_s +" prbs get unit=0\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    command = " \"phy diag " + port100G_s +" prbs get unit=0\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //sleep
    time.Sleep(time.Duration(sleep) * time.Second)

    //Check output
    //xe6 (21):  PRBS OK!
    //xe6 (21):  PRBS has -2 errors!
    cli.Printf("i", "Check 25G Ports Status\n")
    command = " \"phy diag " + port25G_s +" prbs get unit=0\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    for i:=0; i<TAOR_EXTERNAL_25G_PORTS; i++ {
        scanner := bufio.NewScanner(strings.NewReader(output))
        for scanner.Scan() {
            if  strings.Contains(scanner.Text(), "phy diag")==true {
                continue
            }
            if strings.Contains(scanner.Text(), TaorPortMap[i].Name)==true {
                if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                    cli.Printf("i", "Port-%d PRBS Passed\n", i)
                } else {
                    cli.Printf("i", "Port-%d PRBS Failed --> %s \n", i, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        return
    }
    
    cli.Printf("i", "Check 100G Ports Status\n")
    command = " \"phy diag " + port100G_s +" prbs get unit=0\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    for i:=TAOR_EXTERNAL_25G_PORTS; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
        scanner := bufio.NewScanner(strings.NewReader(output))
        for scanner.Scan() {
            if  strings.Contains(scanner.Text(), "phy diag")==true {
                continue
            }
            if strings.Contains(scanner.Text(), TaorPortMap[i].Name)==true {
                if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                    cli.Printf("i", "Port-%d PRBS Passed\n", i)
                } else {
                    cli.Printf("i", "Port-%d PRBS Failed --> %s \n", i, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        return
    }


    cli.Printf("i", "Disable 25G PRBS\n")
    command = " \"phy diag " + port25G_s +" prbs clear\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    cli.Printf("i", "Disable 100G PRBS\n")
    command = " \"phy diag " + port100G_s +" prbs clear\""
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    return

/*

//LINKscan off

//FP 25G
port xe6-xe17,xe24-xe47,xe54-xe65 enable=true
phy diag xe6-xe17,xe24-xe47,xe54-xe65 prbs set unit=0 p=6
phy diag xe6-xe17,xe24-xe47,xe54-xe65 prbs get unit=0
phy diag xe6-xe17,xe24-xe47,xe54-xe65 prbsstat counters
phy diag xe6-xe17,xe24-xe47,xe54-xe65 prbs clear

//FP 100G
port ce0,ce5,ce6-ce8,ce11 enable=true
phy diag ce0,ce5,ce6-ce8,ce11 prbs set unit=0 p=6
phy diag ce0,ce5,ce6-ce8,ce11 prbs get unit=0
phy diag ce0,ce5,ce6-ce8,ce11 prbs clear
*/

}






func CheckForRevA_Gearbox() (err int) {
    var output string
    var RevA bool = false

    for i:=0; i<4; i++ {

        command := fmt.Sprintf("\"phy raw c45 0x%x 0x1e 0xb2ca\"", (i * 0x20))
        //BCM.0> phy raw c45 0x00 0x1e 0xb2ca
        //    0xb2ca: 0x00b0

        output, err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
        //fmt.Printf(" OUTPUT=%s\n", output)
        scanner := bufio.NewScanner(strings.NewReader(output))
        for scanner.Scan() {
            if strings.Contains(scanner.Text(), "0xb2ca:") {
                out := strings.TrimSpace(scanner.Text())
                data64, _ := strconv.ParseUint(out[8:], 0, 64)
                fmt.Printf(" Gearbox-%d Revision = 0x%.04x\n", i, data64)
                if data64 == 0x00A0 {
                    RevA = true
                }
            }
        }
    }
    if RevA == true {
        fmt.Printf(" ERROR: Taormina has at least one Rev A\n")
    } else {
        fmt.Printf(" PASS: Taormina has Rev B gearboxes\n")
    }
    return
}



func ReadTemp(devName string) (currTemp []float64, peakTemp []float64, err int) {
    var output string
    command := " \"show temp\""

    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
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


