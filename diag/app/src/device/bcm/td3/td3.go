package td3

import (
    "bufio"
    "fmt"
    "os"
    "regexp"
    "strconv"
    "strings"
    "time"
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
    ElbaNumber      int
}

const (
    TAOR_EXTERNAL_25G_PORTS  = 48
    TAOR_EXTERNAL_100G_PORTS = 6
    TAOR_NUMB_EXT_PORT       = (TAOR_EXTERNAL_25G_PORTS + TAOR_EXTERNAL_100G_PORTS) 
    TAOR_INTERNAL_PORT_START = (TAOR_EXTERNAL_25G_PORTS + TAOR_EXTERNAL_100G_PORTS) 
    TAOR_INTERNAL_PORTS = 8
    TAOR_TOTAL_PORTS = (TAOR_EXTERNAL_25G_PORTS + TAOR_EXTERNAL_100G_PORTS + TAOR_INTERNAL_PORTS)
)
//GB + RETIEMR PHY ADDRESS FOR MDIO ACCESS
var mdio_phy_addr_rev0 = []uint32{0x00, 0x20, 0x40, 0x60, 0x100, 0x120, 0x140}
var mdio_phy_addr_rev1 = []uint32{0x00, 0x02, 0x04, 0x06, 0x100, 0x102, 0x104}

var TaorPortMap = []PortMap {
    PortMap{0, 23, "xe8", 0},   //Front Panel Port 0
    PortMap{1, 24, "xe9", 0},   //Front Panel Port 1
    PortMap{2, 21, "xe6", 0},   //Front Panel Port 2
    PortMap{3, 22, "xe7", 0},   //Front Panel Port 3
    PortMap{4, 27, "xe12", 0},   //Front Panel Port 4
    PortMap{5, 28, "xe13", 0},   //Front Panel Port 5
    PortMap{6, 25, "xe10", 0},   //Front Panel Port 6
    PortMap{7, 26, "xe11", 0},   //Front Panel Port 7
    PortMap{8, 31, "xe16", 0},   //Front Panel Port 8
    PortMap{9, 32, "xe17", 0},   //Front Panel Port 9
    PortMap{10, 29, "xe14", 0},  //Front Panel Port 10
    PortMap{11, 30, "xe15", 0},  //Front Panel Port 11
    PortMap{12, 47, "xe26", 0},  //Front Panel Port 12
    PortMap{13, 48, "xe27", 0},  //Front Panel Port 13
    PortMap{14, 45, "xe24", 0},  //Front Panel Port 14
    PortMap{15, 46, "xe25", 0},  //Front Panel Port 15
    PortMap{16, 51, "xe30", 0},  //Front Panel Port 16
    PortMap{17, 52, "xe31", 0},  //Front Panel Port 17
    PortMap{18, 49, "xe28", 0},  //Front Panel Port 18
    PortMap{19, 50, "xe29", 0},  //Front Panel Port 19
    PortMap{20, 55, "xe34", 0},  //Front Panel Port 20
    PortMap{21, 56, "xe35", 0},  //Front Panel Port 21
    PortMap{22, 53, "xe32", 0},  //Front Panel Port 22
    PortMap{23, 54, "xe33", 0},  //Front Panel Port 23
    PortMap{24, 68, "xe37", 0},  //Front Panel Port 24
    PortMap{25, 67, "xe36", 0},  //Front Panel Port 25
    PortMap{26, 70, "xe39", 0},  //Front Panel Port 26
    PortMap{27, 69, "xe38", 0},  //Front Panel Port 27
    PortMap{28, 72, "xe41", 0},  //Front Panel Port 28
    PortMap{29, 71, "xe40", 0},  //Front Panel Port 29
    PortMap{30, 74, "xe43", 0},  //Front Panel Port 30
    PortMap{31, 73, "xe42", 0},  //Front Panel Port 31
    PortMap{32, 76, "xe45", 0},  //Front Panel Port 32
    PortMap{33, 75, "xe44", 0},  //Front Panel Port 33
    PortMap{34, 78, "xe47", 0},  //Front Panel Port 34
    PortMap{35, 77, "xe46", 0},  //Front Panel Port 35
    PortMap{36, 100, "xe55", 0}, //Front Panel Port 36
    PortMap{37, 99 , "xe54", 0}, //Front Panel Port 37
    PortMap{38, 102, "xe57", 0}, //Front Panel Port 38
    PortMap{39, 101, "xe56", 0}, //Front Panel Port 39
    PortMap{40, 104, "xe59", 0}, //Front Panel Port 40
    PortMap{41, 103, "xe58", 0}, //Front Panel Port 41
    PortMap{42, 106, "xe61", 0}, //Front Panel Port 42
    PortMap{43, 105, "xe60", 0}, //Front Panel Port 43
    PortMap{44, 108, "xe63", 0}, //Front Panel Port 44
    PortMap{45, 107, "xe62", 0}, //Front Panel Port 45
    PortMap{46, 110, "xe65", 0}, //Front Panel Port 46
    PortMap{47, 109, "xe64", 0}, //Front Panel Port 47

    PortMap{48, 57, "ce5", 0},   //Front Panel Port 48 100G
    PortMap{49, 61, "ce6", 0},   //Front Panel Port 49 100G
    PortMap{50, 83, "ce7", 0},   //Front Panel Port 50 100G
    PortMap{51, 87, "ce8", 0},   //Front Panel Port 51 100G
    PortMap{52, 115, "ce11", 0}, //Front Panel Port 52 100G
    PortMap{53, 1  , "ce0", 0},  //Front Panel Port 53 100G
 
    PortMap{54, 9  , "ce1",  0},  //Internal Port to ELBA0.3 100G   PHY U1_G0
    PortMap{55, 91 , "ce9",  0},  //Internal Port to ELBA0.2 100G   PHY U1_G0
    PortMap{56, 95 , "ce10", 1}, //Internal Port to ELBA1.3 100G   PHY U1_G2 
    PortMap{57, 13 , "ce2",  1},  //Internal Port to ELBA1.2 100G   PHY U1_G2 
    PortMap{58, 123, "ce12", 0}, //Internal Port to ELBA0.0 100G   PHY U1_G1 
    PortMap{59, 127, "ce13", 1}, //Internal Port to ELBA1.1 100G   PHY U1_G3
    PortMap{60, 33,  "ce3",  0},  //Internal Port to ELBA0.1 100G   PHY U1_G1 
    PortMap{61, 37,  "ce4",  1},  //Internal Port to ELBA1.0 100G   PHY U1_G3
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

func PrintBCMShellVLANcmd() (err int){
    for i:=0;i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS);i++ {
        //vlan add 40 pbm=xe37,xe33 ubm=xe37,xe33
        fmt.Printf("vlan add %d pbm=%s,%s ubm=%s,%s\n", i+10, TaorPortMap[i].Name, TaorPortMap[i+1].Name, TaorPortMap[i].Name, TaorPortMap[i+1].Name)
    }
    for i:=0;i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS);i++ {
        fmt.Printf("pvlan set %s %d\n",  TaorPortMap[i].Name, i+10)
    }
    return


/*
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
    */
}

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
    cmdString = path + " " + "\"" + commands + "\""           //" \"show temp\""
    output, errGo := exec.Command("bash", "-c", cmdString).Output()
    if errGo != nil {
        cli.Println("e", "Failed to exec command:",cmdString," GoERR=",errGo)
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
    command := "LINKscan off"
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
    command = "port " + port25G_s +" enable=true"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=true"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 25G Ports\n")
    command = "phy diag " + port25G_s +" prbs set unit=0 p="+prbsType
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 100G Ports\n")
    command = "phy diag " + port100G_s +" prbs set unit=0 p="+prbsType
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //First time you read status it will show an error, have to read it again later after sleep
    cli.Printf("i", "Read Status to clear errors\n")
    command = "phy diag " + port25G_s +" prbs get unit=0"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    command = "phy diag " + port100G_s +" prbs get unit=0"
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
    command = "phy diag " + port25G_s +" prbs get unit=0"
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
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        return
    }
    
    cli.Printf("i", "Check 100G Ports Status\n")
    command = "phy diag " + port100G_s +" prbs get unit=0"
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
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        return
    }


    cli.Printf("i", "Disable 25G PRBS\n")
    command = "phy diag " + port25G_s +" prbs clear"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    cli.Printf("i", "Disable 100G PRBS\n")
    command = "phy diag " + port100G_s +" prbs clear"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling BCM LinkScan\n")
    command = "LINKscan on"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    return
}


func MacStatRxByteSecond(port int) (stat uint64, err int) {
    var i int = 0
    var output string

    command := fmt.Sprintf("show c CLMIB_RBYT.%s", TaorPortMap[port].Name)
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //fmt.Printf(" CMD=%s  OUTPUT=%s\n", command, output)

    //OUTPUT=BCM.0> show c CLMIB_RBYT.xe13
    //CLMIB_RBYT.xe13             :       125,839,126,000    +116,801,588,000     474,771,761/s

    re := regexp.MustCompile(`[-]?\d[\d,]*[\.]?[\d{2}]*`)
    submatchall := re.FindAllString(output, -1)
    stat = 0
    for _, element := range submatchall {
        i++
        number := strings.Replace(element, ",", "", -1)
        if i == 6 {
            stat, _ = strconv.ParseUint(number, 0, 64)
            return
        }
    }
    return
}

func MacStatFCSerror(port int) (stat uint64, err int) {
    var i int = 0
    var output string

    command := fmt.Sprintf("show c all CLMIB_RFCS.%s", TaorPortMap[port].Name)
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //fmt.Printf(" CMD=%s  OUTPUT=%s\n", command, output)

    //BCM.0> show c all CLMIB_RFCS.ce1
    //CLMIB_RFCS.ce1              :                    59                  +0


    re := regexp.MustCompile(`[-]?\d[\d,]*[\.]?[\d{2}]*`)
    submatchall := re.FindAllString(output, -1)
    stat = 0
    for _, element := range submatchall {
        i++
        number := strings.Replace(element, ",", "", -1)
        if i == 4 {
            stat, _ = strconv.ParseUint(number, 0, 64)
            return
        }
    }
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
func Snake_All_Ports(elba_port_mask uint32, duration uint32, loopback_level string) (err int) {
    var errGo error
    var data32 uint32
    var addr uint64 = taorfpga.D0_FP_SFP_CTRL_3_0_REG;
    var SFPnumber, QSFPnumber, bitcompare uint32
    var port25G_s string
    var port100G_s string
    var tmp_s string
    var command string
    var output string
    var loopbackPhy uint32 = 0
    var VlanStart int = 10
    var ElbaVLANcreatScript = "/fs/nos/home_diag/dssman/run.sh"

    cli.Printf("i", "Starting Snake Test.  Elba Link Mask=%x,  Duration=%d", elba_port_mask, duration)

    if loopback_level == "phy" {
        loopbackPhy = 1
        cli.Printf("i", "Phy Loopback Selected\n")
    } else {
        cli.Printf("i", "External Loopback Selected\n")
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
    
    if loopbackPhy > 0 {
        cli.Printf("i", "Setting Phy Loopback on 25G Ports\n")
        command = "port " + port25G_s +" lb=phy"
        output, err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }

        //No return output to check on this command
        cli.Printf("i", "Setting Phy Loopback on 100G Ports\n")
        command = "port " + port100G_s +" lb=phy"
        output, err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
    }

    //quick sanity check to make sure the file exists

    currDir, _ := os.Getwd()
    os.Chdir("/fs/nos/home_diag/dssman")
    
    cli.Printf("i", "Executing dssman setup\n")
    exists, _ := taorfpga.Path_exists(ElbaVLANcreatScript)
    if exists == false {
        cli.Printf("e", "Script is missing --> \n", ElbaVLANcreatScript)
        err = errType.FAIL
        return
    }
    {
        execOutput, errGo := exec.Command("/bin/sh", ElbaVLANcreatScript).Output()
        if errGo != nil {
            cli.Println(string(execOutput))
            cli.Println("e", errGo)
            err = errType.FAIL
            //return
        }
        cli.Println("i", string(execOutput))
    }
    os.Chdir(currDir)
    
    //set pvlan
    for i:=0; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
        //pvlan set xe8 10
        command = fmt.Sprintf("pvlan set %s %d", TaorPortMap[i].Name, (VlanStart + i))
        cli.Printf("i", command)
        output, err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
        cli.Printf("i", "%s\n", command)
    }

    //set vlans 10-63 for the elba front panel ports
    //vlan 10-37 will go to lag521 (Elba0)
    //vlan 38-63 will go to lag522 (Elba1)
    //All front panel ingress packets get forwarded to an Elba
    for i:=0; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
        //vlan add 10 pbm=xe8,xe9 ubm=xe8,xe9
        if i == (((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)/2)-1) {  //port 27 needs to vlan with port 0 to create the vlan snake for lag521 (elba0)
            command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), TaorPortMap[i].Name, TaorPortMap[0].Name, TaorPortMap[i].Name, TaorPortMap[0].Name )
        } else if i == ((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)-1) { //Last entry needs to map back to port 28 to creat the vlan snake for lag522 (elba1)
            entry := ((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)/2)
            command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), TaorPortMap[i].Name, TaorPortMap[entry].Name, TaorPortMap[i].Name, TaorPortMap[entry].Name )
        } else {  
            command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), TaorPortMap[i].Name, TaorPortMap[i+1].Name, TaorPortMap[i].Name, TaorPortMap[i+1].Name )
        }
        cli.Printf("i", "%s\n", command)
        output, err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
    }





    //No return output to check on this command
    cli.Printf("i", "Enabling Vlan Translate\n")
    command = "vlan translate on"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling Forwarding on 25G ports\n")
    command = "stg stp 1 " + port25G_s +" forward"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling Forwarding on 100G ports\n")
    command = "stg stp 1 " + port100G_s +" forward"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=true"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=true"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //Clear stat counters
    cli.Printf("i", "clear c\n")
    command = "clear c\n"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    time.Sleep(time.Duration(5) * time.Second)

    for j:=0;j<1;j++ {
        var internal_port uint32 = 0
        for i:=TAOR_INTERNAL_PORT_START; i<(TAOR_INTERNAL_PORT_START+TAOR_INTERNAL_PORTS); i++ {
            if (elba_port_mask & (1<<internal_port)) == 0 {
                //fmt.Printf("[ERROR] Elba Port Mask = 0x%x...  mask=%x\n", elba_port_mask, (1<<internal_port))
                internal_port++
                continue;
            }
            internal_port++

            //First half of VLANS go to Elba 0 (lag521).    Elba 1 (lag 522) VLANS need t start on port27 which starts the 2nd half of the vlans   
            if TaorPortMap[i].ElbaNumber == 0 {
                command = fmt.Sprintf("tx 60 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.%s", TaorPortMap[0].Name, TaorPortMap[i].Name)
            } else {
                entry := ((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)/2)
                command = fmt.Sprintf("tx 60 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.%s", TaorPortMap[entry].Name, TaorPortMap[i].Name)
            }
            cli.Printf("i", "%s\n", command)
            output, err = ExecBCMshellCMD(command)
            if err != errType.SUCCESS {
                return
            }
            time.Sleep(time.Duration(5) * time.Second)
        }
    }
    



    {
        t1 := time.Now()
        var ElbaPortminBandwidth uint64 = 12000000000
        var Elba0bw, Elba1bw uint64
        var Lag521ExtPortminBandWidth uint64 = 0
        var Lag522ExtPortminBandWidth uint64 = 0
        var rc int = 0

        for i:=0; i<TAOR_INTERNAL_PORTS; i++ {
            var port uint32 = uint32(i)
            if (elba_port_mask & (1<<port)) ==  (1<<port) {
                if TaorPortMap[(i + TAOR_INTERNAL_PORT_START)].ElbaNumber == 0 {
                    Elba0bw = Elba0bw + ElbaPortminBandwidth
                } else {
                    Elba1bw = Elba1bw + ElbaPortminBandwidth
                }
            }
        }
        Lag521ExtPortminBandWidth = Elba0bw / (TAOR_NUMB_EXT_PORT / 2)
        Lag522ExtPortminBandWidth = Elba1bw / (TAOR_NUMB_EXT_PORT / 2)
        fmt.Printf(" Elba0bw bandwidth = %d\n", Elba0bw)
        fmt.Printf(" Elba1bw bandwidth = %d\n", Elba1bw)
        fmt.Printf(" Lag521 min bandwidth = %d\n", Lag521ExtPortminBandWidth)
        fmt.Printf(" Lag522 min bandwidth = %d\n", Lag522ExtPortminBandWidth)
        /*
         Elba0bw bandwidth = 24000000000
         Elba1bw bandwidth = 24000000000
         Lag521 min bandwidth = 222222222
         Lag522 min bandwidth = 222222222
         */
        for {
            for i:=0; i < TAOR_TOTAL_PORTS; i++ {
                var RxBytes uint64
                var FCSerror uint64
                RxBytes, err = MacStatRxByteSecond(i)
                if err != errType.SUCCESS {
                    return
                }
                fmt.Printf("Port-%d %d/s\n", i, RxBytes)
                //lag521
                if (i < (TAOR_NUMB_EXT_PORT/2)) &&  (RxBytes < Lag521ExtPortminBandWidth) { 
                    cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , TaorPortMap[i].Name, RxBytes, Lag521ExtPortminBandWidth)
                    rc = errType.FAIL
                }
                //lag522
                if (i >= (TAOR_NUMB_EXT_PORT/2)) && (i < TAOR_NUMB_EXT_PORT) {
                    if RxBytes < Lag522ExtPortminBandWidth { 
                        cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , TaorPortMap[i].Name, RxBytes, Lag522ExtPortminBandWidth)
                        rc = errType.FAIL
                    }
                }
                //Internal Port going to Elba
                if i >= TAOR_INTERNAL_PORT_START {
                    var port uint32 = uint32(i - TAOR_INTERNAL_PORT_START)
                    if (elba_port_mask & (1<<port)) > 0 {
                        if RxBytes < ElbaPortminBandwidth { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , TaorPortMap[i].Name, RxBytes, ElbaPortminBandwidth)
                            rc = errType.FAIL
                        }
                    }
                }

                FCSerror, err = MacStatFCSerror(i)
                if err != errType.SUCCESS {
                    return
                }
                if FCSerror > 0 {
                    cli.Printf("e", "Port-%d (%s) has %d FCS Errors\n", i , TaorPortMap[i].Name, FCSerror)
                    rc = errType.FAIL
                }
            }

            t2 := time.Now()
            diff := t2.Sub(t1)
            fmt.Println(" Elapsed Time=",diff," Duration=",duration)
            if uint32(diff.Seconds()) > duration {
                fmt.Printf(" DUATION BREAK\n")
                break
            }
            if rc == errType.FAIL {
                fmt.Printf(" ERR BREAK\n")
                err = errType.FAIL
                break
            }
        }
    }

    //No return output to check on this command
    cli.Printf("i", "Disabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=false"
    ExecBCMshellCMD(command)

    //No return output to check on this command
    cli.Printf("i", "Disabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=false"
    ExecBCMshellCMD(command)

    /* For compile error that var is not used */
    if TaorPortMap[0].ElbaNumber > 100000 {
            fmt.Printf("%s\n", output)
    }

    if err == errType.SUCCESS {
        cli.Printf("i", "Snake Test PASSED")
    } else {
        cli.Printf("e", "Snake Test FAILED")
    }

    return


}






func CheckForRevA_Gearbox() (err int) {
    var output, command string
    var strapping uint32
    err = errType.SUCCESS

    strapping, _ = taorfpga.GetResistorStrapping() 

    for i:=0; i<4; i++ {

        if strapping == 0 {
            command = fmt.Sprintf("phy raw c45 0x%x 0x1e 0xb2ca", mdio_phy_addr_rev0[i])
        } else {
            command = fmt.Sprintf("phy raw c45 0x%x 0x1e 0xb2ca", mdio_phy_addr_rev1[i])
        }
        
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
                if data64 != 0x00B0 {
                    err = errType.FAIL
                }
            }
        }
    }

    if err == errType.SUCCESS {
        fmt.Printf(" PASS: Taormina has Rev B gearboxes\n")
    } else {
        fmt.Printf(" ERROR: Taormina has at least one gearbox that is not rev B\n")
    }

    return
}



func ReadTemp(devName string) (currTemp []float64, peakTemp []float64, err int) {
    var output string
    command := "show temp"

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


