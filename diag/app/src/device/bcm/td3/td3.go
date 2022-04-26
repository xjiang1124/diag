package td3

import (
    "bufio"
    "bytes"
    "fmt"
    "io/ioutil"
    "os"
    "regexp"
    "strconv"
    "strings"
    "time"
    "os/exec"
    //"cardinfo"
    "common/cli"
    "common/dcli"
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
"import socket\n"+
"\n"+
"timeout = 2\n"+
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
"#tn.write('exit \\n')\n"+
"tn.get_socket().shutdown(socket.SHUT_WR)\n"+
"tn.close\n"+
"timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())\n"+
"f.write('\\n')\n"+
"f.write(timestamp)\n"+
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
"timeout = 5\n"+
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
"commandList.append('exit \\n')\n"+
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
"#else:\n"+
"#    tn.close()\n"+
"#\n"+
"#tn.write('exit \\n')\n"+
"#tn.get_socket().shutdown(socket.SHUT_WR)\n"+
"#tn.close\n"+
"timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())\n"+
"f.write('\\n')\n"+
"f.write(timestamp)\n"+
"f.close()\n"+
"os.system(\"cat /tmp/bcm_cmd_output\")\n"+
"\n"

const BCM_SCRIPT_FILE_NAME  =  "/bcm_shell_execute_cmd.py"
const BCM_SCRIPT_FILE_NAME_W_EXIT  =  "/bcm_shell_execute_cmd_w_exit.py"


const TD3_MAX_TEMP = 100

// Port Map Data Structure
type PortMap struct {
    SwitchPort      int
    PhysicalPort    int
    Name            string
    ElbaNumber      int
    Pre             int
    Main            int
    Post            int

}

const (
    TAOR_EXTERNAL_25G_PORTS  = 48
    TAOR_EXTERNAL_100G_PORTS = 6
    TAOR_NUMB_EXT_PORT       = (TAOR_EXTERNAL_25G_PORTS + TAOR_EXTERNAL_100G_PORTS) 
    TAOR_INTERNAL_PORT_START = (TAOR_EXTERNAL_25G_PORTS + TAOR_EXTERNAL_100G_PORTS) 
    TAOR_INTERNAL_PORTS = 8
    TAOR_TOTAL_PORTS = (TAOR_EXTERNAL_25G_PORTS + TAOR_EXTERNAL_100G_PORTS + TAOR_INTERNAL_PORTS)
)

const (
    SNAKE_TEST_NEXT_PORT_FORWARDING = 1
    SNAKE_TEST_LINE_RATE = 2
    SNAKE_TEST_ENVIRONMENT = 3
)


//GB + RETIEMR PHY ADDRESS FOR MDIO ACCESS
const GEARBOX_START = 0
const RETIMER_START = 4
var mdio_phy_addr_rev0 = []uint32{0x00, 0x20, 0x40, 0x60, 0x100, 0x120, 0x140}
var mdio_phy_addr_rev1 = []uint32{0x00, 0x02, 0x04, 0x06, 0x100, 0x102, 0x104}

var TaorPortMap = []PortMap {
    PortMap{0, 23, "xe8", 0, 6, 60, 0},   //Front Panel Port 0
    PortMap{1, 24, "xe9", 0, 6, 60, 0},   //Front Panel Port 1
    PortMap{2, 21, "xe6", 0, 6, 60, 0},   //Front Panel Port 2
    PortMap{3, 22, "xe7", 0, 6, 60, 0},   //Front Panel Port 3
    PortMap{4, 27, "xe12", 0, 6, 60, 0},   //Front Panel Port 4
    PortMap{5, 28, "xe13", 0, 6, 60, 0},   //Front Panel Port 5
    PortMap{6, 25, "xe10", 0, 6, 60, 0},   //Front Panel Port 6
    PortMap{7, 26, "xe11", 0, 6, 60, 0},   //Front Panel Port 7
    PortMap{8, 31, "xe16", 0, 6, 60, 0},   //Front Panel Port 8
    PortMap{9, 32, "xe17", 0, 6, 60, 0},   //Front Panel Port 9
    PortMap{10, 29, "xe14", 0, 6, 60, 0},  //Front Panel Port 10
    PortMap{11, 30, "xe15", 0, 6, 60, 0},  //Front Panel Port 11
    PortMap{12, 47, "xe26", 0, 6, 60, 0},  //Front Panel Port 12
    PortMap{13, 48, "xe27", 0, 6, 60, 0},  //Front Panel Port 13
    PortMap{14, 45, "xe24", 0, 6, 60, 0},  //Front Panel Port 14
    PortMap{15, 46, "xe25", 0, 6, 60, 0},  //Front Panel Port 15
    PortMap{16, 51, "xe30", 0, 6, 60, 0},  //Front Panel Port 16
    PortMap{17, 52, "xe31", 0, 6, 60, 0},  //Front Panel Port 17
    PortMap{18, 49, "xe28", 0, 6, 60, 0},  //Front Panel Port 18
    PortMap{19, 50, "xe29", 0, 6, 60, 0},  //Front Panel Port 19
    PortMap{20, 55, "xe34", 0, 6, 60, 0},  //Front Panel Port 20
    PortMap{21, 56, "xe35", 0, 6, 60, 0},  //Front Panel Port 21
    PortMap{22, 53, "xe32", 0, 6, 60, 0},  //Front Panel Port 22
    PortMap{23, 54, "xe33", 0, 6, 60, 0},  //Front Panel Port 23
    PortMap{24, 68, "xe37", 0, 6, 60, 0},  //Front Panel Port 24
    PortMap{25, 67, "xe36", 0, 6, 60, 0},  //Front Panel Port 25
    PortMap{26, 70, "xe39", 0, 6, 60, 0},  //Front Panel Port 26
    PortMap{27, 69, "xe38", 0, 6, 60, 0},  //Front Panel Port 27
    PortMap{28, 72, "xe41", 0, 6, 60, 0},  //Front Panel Port 28
    PortMap{29, 71, "xe40", 0, 6, 60, 0},  //Front Panel Port 29
    PortMap{30, 74, "xe43", 0, 6, 60, 0},  //Front Panel Port 30
    PortMap{31, 73, "xe42", 0, 6, 60, 0},  //Front Panel Port 31
    PortMap{32, 76, "xe45", 0, 6, 60, 0},  //Front Panel Port 32
    PortMap{33, 75, "xe44", 0, 6, 60, 0},  //Front Panel Port 33
    PortMap{34, 78, "xe47", 0, 6, 60, 0},  //Front Panel Port 34
    PortMap{35, 77, "xe46", 0, 6, 60, 0},  //Front Panel Port 35
    PortMap{36, 100, "xe55", 0, 6, 60, 0}, //Front Panel Port 36
    PortMap{37, 99 , "xe54", 0, 6, 60, 0}, //Front Panel Port 37
    PortMap{38, 102, "xe57", 0, 6, 60, 0}, //Front Panel Port 38
    PortMap{39, 101, "xe56", 0, 6, 60, 0}, //Front Panel Port 39
    PortMap{40, 104, "xe59", 0, 6, 60, 0}, //Front Panel Port 40
    PortMap{41, 103, "xe58", 0, 6, 60, 0}, //Front Panel Port 41
    PortMap{42, 106, "xe61", 0, 6, 60, 0}, //Front Panel Port 42
    PortMap{43, 105, "xe60", 0, 6, 60, 0}, //Front Panel Port 43
    PortMap{44, 108, "xe63", 0, 6, 60, 0}, //Front Panel Port 44
    PortMap{45, 107, "xe62", 0, 6, 60, 0}, //Front Panel Port 45
    PortMap{46, 110, "xe65", 0, 6, 60, 0}, //Front Panel Port 46
    PortMap{47, 109, "xe64", 0, 6, 60, 0}, //Front Panel Port 47

    PortMap{48, 57, "ce5", 0, -6, 73, 0},   //Front Panel Port 48 100G
    PortMap{49, 61, "ce6", 0, -6, 73, 0},   //Front Panel Port 49 100G
    PortMap{50, 83, "ce7", 0, -6, 73, 0},   //Front Panel Port 50 100G
    PortMap{51, 87, "ce8", 0, -6, 73, 0},   //Front Panel Port 51 100G
    PortMap{52, 115, "ce11", 0, -6, 73, 0}, //Front Panel Port 52 100G
    PortMap{53, 1  , "ce0", 0, -6, 73, 0},  //Front Panel Port 53 100G
 
    PortMap{54, 9  , "ce1",  0, 0, 60, 0},  //Internal Port to ELBA0.3 100G   PHY U1_G0
    PortMap{55, 91 , "ce9",  0, 0, 60, 0},  //Internal Port to ELBA0.2 100G   PHY U1_G0
    PortMap{56, 95 , "ce10", 1, 0, 60, 0}, //Internal Port to ELBA1.3 100G   PHY U1_G2 
    PortMap{57, 13 , "ce2",  1, 0, 60, 0},  //Internal Port to ELBA1.2 100G   PHY U1_G2 
    PortMap{58, 123, "ce12", 0, 0, 60, 0}, //Internal Port to ELBA0.0 100G   PHY U1_G1 
    PortMap{59, 127, "ce13", 1, 0, 60, 0}, //Internal Port to ELBA1.1 100G   PHY U1_G3
    PortMap{60, 33,  "ce3",  0, 0, 60, 0},  //Internal Port to ELBA0.1 100G   PHY U1_G1 
    PortMap{61, 37,  "ce4",  1, 0, 60, 0},  //Internal Port to ELBA1.0 100G   PHY U1_G3
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

    exists, _ := taorfpga.Path_exists("/tmp/bcm_cnt.txt")
    //TRY TO STORE THE BAR VALUES IN A FILE.  WE DONT WANT TO SCAN THE PCI AND GET THE BARS EVERYTIME WE USE ONE OF THE DIAG UTILITIES THAT CALLS THIS INIT
    if exists == true {
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
        } else {
            f.Close()
        }
        
        cmdString = path + " " + "\"" + commands + "\""           //" \"show temp\""
        output, errGo := exec.Command("bash", "-c", cmdString).Output()
        if errGo != nil {
            if i == 0 {
                cli.Println("i", "[WARN] Failed to exec bcm shell command:",cmdString," GoERR=",errGo)
                cli.Printf("i", "[WARN] Script output returned =%s\n",string(output))
                cli.Printf("i", "[WARN] RETRYING COMMAND\n")
                time.Sleep(time.Duration(3) * time.Second)
            } else {
                cli.Println("e", "Failed to exec bcm shell command:",cmdString," GoERR=",errGo)
                cli.Printf("e", "Script output returned =%s\n",string(output))
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



/******************************************************************************** 
* 
* Execute a command in the bcm shell.
* Search the output for the string results.  Pass/Fail on match to the results
*                                                                                 
*  
*********************************************************************************/ 
func BCMShellExecuteCmdCheckResults(command string, results string) (output string, err int) {
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    scanner := bufio.NewScanner(strings.NewReader(output))
    for scanner.Scan() {
        if strings.Contains(scanner.Text(), results) {
            return
        }
    }
    err = errType.FAIL
    return
}


/*************************************************************************************************** 
 This function needs the output of ps passed to it.   The idea is to run "ps" once and take that output
 and check the link on whatever ports are under test and avoid calling into the bcm shell
 multiple times to run "ps" per port as the bcm shell call is time consuming
 
  BCM.0> ps
                 ena/        speed/ link auto    STP                  lrn  inter   max   cut   loop
           port  link  Lns   duplex scan neg?   state   pause  discrd ops   face frame  thru?  back
       ce0(  1)  !ena   4  100G  FD   SW  No   Forward  TX RX   None   FA  CAUI4  9412    No
       ce1(  9)  up     4  100G  FD   SW  No   Forward          None    F  CAUI4  9408    No
 
 RETURN CODES
FAIL
LINK_DOWN
LINK_UP  
LINK_DISABLED      
*****************************************************************************************************/
func LinkCheck(portname string, bcm_shell_ps_output string) (err int) {

    err = errType.FAIL
    split_ps_command := strings.Split(bcm_shell_ps_output,"\n")

    for _, ps_line := range(split_ps_command) {
        match := fmt.Sprintf("\\b%s\\b", portname)
        matched, errGo := regexp.MatchString(match, ps_line)
        if errGo != nil {
            cli.Printf("e", "LinkCheck(): Parsing 'ps' output from bcm shell.  Either 'ps' data is bad, or port name is invalid\n")
            err = errType.FAIL
        } else if matched {
            if strings.Contains(ps_line, "!ena")==true {
                err = errType.LINK_DISABLED
            } else if strings.Contains(ps_line, "up")==true {
                err = errType.LINK_UP
            } else  {
                err = errType.LINK_DOWN
            }
        }
    }

    return
}
/*************************************************************************************************** 
  BCM.0> g TOP_AVS_SEL_REG
  TOP_AVS_SEL_REG.top0[7][0x2009800]=0x7e: <RESERVED_0=0,AVS_SEL=0x7e>
***************************************************************************************************/
func ReadReg(devName string, regName string) (data32 uint32, err int) {
    var output string
    command := "g " + regName

    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    /* Match substring between = and :  */
    re := regexp.MustCompile(`=(.*):`)
    match := re.FindStringSubmatch(string(output))
    if len(match) > 1 {
            data64, errGo := strconv.ParseUint(match[1], 0, 32)
            if errGo != nil {
                cli.Println("e", "TD3 Readreg failed.")
                cli.Printf("e", "OUTPUT ='%s'", string(output))
                err = errType.FAIL
            }
            data32 = uint32(data64)
    } else {
            cli.Println("e", "TD3 Readreg failed.  Output Length is too small.  Output length=%d", len(match))
            cli.Printf("e", "OUTPUT ='%s'", string(output))
            err = errType.FAIL
    }
    return
}


func ReadTemp(devName string) (currTemp []float64, peakTemp []float64, err int) {
    var output string
    command := "show temp"

    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        cli.Println("e", "BCM shell 'show temp' failed to execute properly")
        cli.Printf("e", "OUTPUT ='%s'", string(output))
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

func CheckTemperatures(devName string, maxTemp int) (currTemp []float64, peakTemp []float64, err int) {
    //currTemp := []float64{}
    //peakTemp := []float64{}

    currTemp, peakTemp, err = ReadTemp(devName)
    if err != errType.SUCCESS {
        return
    }
    for i:=0; i<len(currTemp); i++ {
        if int(currTemp[i]) > maxTemp {
            cli.Printf("e", "BCM TD3:  Temperature sensor-%d.  Current Reading %d is exceeding threshold of %d\n", i, int(currTemp[i]), maxTemp)
            err = errType.FAIL
        }
    }
    for i:=0; i<len(peakTemp); i++ {
        if int(peakTemp[i]) > maxTemp {
            cli.Printf("e", "BCM TD3:  Temperature sensor-%d.  Peak Reading %d is exceeding threshold of %d\n", i, int(peakTemp[i]), maxTemp)
            err = errType.FAIL
        }
    }

    return
}


func GetTemperature(devName string) (temperatures []float64, err int) {
    temperatures, _, err = ReadTemp(devName)
    return
}


func GetPeakTemperature(devName string) (temperatures []float64, err int) {
    _, temperatures, err = ReadTemp(devName)
    return
}


func DispStatus(devName string) (err int) {
    cTemp := []float64{}
    pTemp := []float64{}
    gbTemp := []float64{}
    retTemp := []float64{}
    err = errType.SUCCESS
    



    cTemp, pTemp, err = ReadTemp(devName)
    if err != errType.SUCCESS {
        return err
    }

    degSym := fmt.Sprintf("(%cC)",0xB0)
    tmpStr := fmt.Sprintf("%-10s TD3 Current Temp %s", devName, degSym)
    for _, temp := range cTemp {
        tmpStr = fmt.Sprintf("%s %0.1f", tmpStr, temp)
    }
    cli.Println("i", tmpStr)
    degSym = fmt.Sprintf("(%cC)",0xB0)
    tmpStr = fmt.Sprintf("%-10s TD3 Peak Temp    %s", devName, degSym)
    for _, temp := range pTemp {
        tmpStr = fmt.Sprintf("%s %0.1f", tmpStr, temp)
    }
    cli.Println("i", tmpStr)
   
    gbTemp, err = GearboxGetTemperatures()
    if err != errType.SUCCESS {
        return err
    }
    degSym = fmt.Sprintf("(%cC)",0xB0)
    tmpStr = fmt.Sprintf("%-10s GearBox Temp     %s", devName, degSym)
    for _, temp := range gbTemp {
        tmpStr = fmt.Sprintf("%s %0.1f", tmpStr, temp)
    }
    cli.Println("i", tmpStr)

    retTemp, err = RetimerGetTemperatures()
    if err != errType.SUCCESS {
        return err
    }
    degSym = fmt.Sprintf("(%cC)",0xB0)
    tmpStr = fmt.Sprintf("%-10s Retimer Temp     %s", devName, degSym)
    for _, temp := range retTemp {
        tmpStr = fmt.Sprintf("%s %0.1f", tmpStr, temp)
    }
    cli.Println("i", tmpStr)

    return
}



/****************************************************************************
* Get the RX Byte Count Statistics for all ports 
* Saves a lot of time by not reading them one port at a time due 
* to telneting into bcm shell to run command
* 
*****************************************************************************/ 
func GetRmonStat_AllPorts(stat string) (stats string, err int) {
    shellcmd := fmt.Sprintf("show c all %s", stat)
    stats, err = ExecBCMshellCMD(shellcmd)
    if err != errType.SUCCESS {
        return
    }
    return
}

/****************************************************************************
* Need to pass the data from GetAllPortBytesSecond() into this function
* 
*****************************************************************************/  
func MacStatRxByteSecond(bcm_shell_stats_output string, port int) (stat uint64, err int) {
    var i int = 0
    stat = 0
    split_stat_command := strings.Split(bcm_shell_stats_output,"\n")

    for _, stat_line := range(split_stat_command) {
        match := fmt.Sprintf("\\bCLMIB_RBYT.%s\\b", TaorPortMap[port].Name)
        matched, errGo := regexp.MatchString(match, stat_line)
        if errGo != nil {
            cli.Printf("e", "MacStatRxByteSecond(): Parsing 'ps' output from bcm shell.  Either 'ps' data is bad, or port name is invalid\n")
            err = errType.FAIL
        } else if matched {
            //CLMIB_RBYT.ce12             :        40,479,386,976     +40,479,386,976  12,256,893,179/s
            re := regexp.MustCompile(`[-]?\d[\d,]*[\.]?[\d{2}]*`)
            submatchall := re.FindAllString(stat_line, -1)
            stat = 0
            for _, element := range submatchall {
                i++
                if i == 4 {
                    number := strings.Replace(element, ",", "", -1)
                    stat, _ = strconv.ParseUint(number, 0, 64)
                    return
                }
            }

        }
    }

    return
}

func MacStatFCSerror(bcm_shell_stats_output string, port int) (stat uint64, err int) {
    var i int = 0
    stat = 0
    split_stat_command := strings.Split(bcm_shell_stats_output,"\n")

    for _, stat_line := range(split_stat_command) {
        match := fmt.Sprintf("\\bCLMIB_RFCS.%s\\b", TaorPortMap[port].Name)
        matched, errGo := regexp.MatchString(match, stat_line)
        if errGo != nil {
            cli.Printf("e", "MacStatFCSerror(): Parsing 'ps' output from bcm shell.  Either 'ps' data is bad, or port name is invalid\n")
            err = errType.FAIL
        } else if matched {
            //CLMIB_RFCS.ce1              :                    59                  +0
            re := regexp.MustCompile(`[-]?\d[\d,]*[\.]?[\d{2}]*`)
            submatchall := re.FindAllString(stat_line, -1)
            stat = 0
            for _, element := range submatchall {
                i++
                //fmt.Printf("(%d)%s  ", i, element)
                if i == 2 {
                    number := strings.Replace(element, ",", "", -1)
                    stat, _ = strconv.ParseUint(number, 0, 64)
                    return
                }
            }
        }
    }

    return
}


func DecodeMacStat(bcm_shell_stats_output string, stat_name string, port int, stat_position int) (stat uint64, err int) {
    var i int = 0
    stat = 0
    split_stat_command := strings.Split(bcm_shell_stats_output,"\n")

    for _, stat_line := range(split_stat_command) {
        match := fmt.Sprintf("\\b%s.%s\\b", stat_name, TaorPortMap[port].Name)
        matched, errGo := regexp.MatchString(match, stat_line)
        if errGo != nil {
            cli.Printf("e", "MacStatFCSerror(): Parsing 'ps' output from bcm shell.  Either 'ps' data is bad, or port name is invalid\n")
            err = errType.FAIL
        } else if matched {
            re := regexp.MustCompile(`[-]?\d[\d,]*[\.]?[\d{2}]*`)
            submatchall := re.FindAllString(stat_line, -1)
            stat = 0
            for _, element := range submatchall {
                i++
                if i == stat_position {
                    number := strings.Replace(element, ",", "", -1)
                    stat, _ = strconv.ParseUint(number, 0, 64)
                    return
                }
            }
        }
    }

    return
}

/* 
            CLMIB_TPOK.xe69             :                     0                  +0
            CLMIB_TPKT.xe69             :                     0                  +0
            CLMIB_TPOK.xe69             :                     0                  +0
            CLMIB_TPKT.xe69             :                     0                  +0
*/
func DumpRxTxCounters() (err int) {
    var RPOK, RPKT, TPOK, TPKT string
    var RxPOK, RxPKT, TxPOK, TxPKT uint64
    
    RPOK, err = GetRmonStat_AllPorts("CLMIB_RPOK") 
    if err != errType.SUCCESS { return }
    RPKT, err = GetRmonStat_AllPorts("CLMIB_RPKT") 
    if err != errType.SUCCESS { return }
    TPOK, err = GetRmonStat_AllPorts("CLMIB_TPOK") 
    if err != errType.SUCCESS { return }
    TPKT, err = GetRmonStat_AllPorts("CLMIB_TPKT") 
    if err != errType.SUCCESS { return }

    fmt.Printf("Port      -  RPOK         RPKT         TPOK         TPKT\n")
    for i:=0; i < TAOR_TOTAL_PORTS; i++ {
        RxPOK, err = DecodeMacStat(RPOK, "CLMIB_RPOK", i, 2)
        if err != errType.SUCCESS { return}
        RxPKT, err = DecodeMacStat(RPKT, "CLMIB_RPKT", i, 2)
        if err != errType.SUCCESS { return }
        TxPOK, err = DecodeMacStat(TPOK, "CLMIB_TPOK", i, 2)
        if err != errType.SUCCESS { return }
        TxPKT, err = DecodeMacStat(TPKT, "CLMIB_TPKT", i, 2)
        if err != errType.SUCCESS { return }
        fmt.Printf("%02d (%-4s)  - %-12d %-12d %-12d %-12d \n", i+1, TaorPortMap[i].Name, RxPOK, RxPKT, TxPOK, TxPKT)
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
func Prbs(sleep int, prbs string) (err int) {
    var rc int
    var errGo error
    var data32 uint32
    var addr uint64
    var SFPnumber, QSFPnumber, bitcompare uint32
    var port25G_s string
    var port100G_s string
    var tmp_s string
    var prbsType string
    var command, output string

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

    cli.Printf("i", "Disabling Ports in VTYSH\n")
    cmdString := "echo \"conf\nint 1/1/1-1/1/54\nshutdown\nend\n\" | vtysh"
    output1, errGo1 := exec.Command("bash", "-c", cmdString).Output()
    if errGo1 != nil {
        cli.Println("e", "Failed to exec command:",cmdString," GoERR=",errGo1)
        cli.Printf("e", "OUTPUT='%s'\n", output1)
        err = errType.FAIL
        return
    }
    time.Sleep(time.Duration(2) * time.Second)
    
    err = Set_Pre_Main_Post_25G_EXT(1)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on TD3 25G Ports\n")
        return
    }

    err = RetimerSetSI(1)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on Retimer 100G Ports\n")
        return
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

    /* Enable QSFP's */
    cli.Printf("i", "Enabling QSFP's\n")
    addr = taorfpga.D0_FP_QSFP_CTRL_51_48_REG;
    for i:=0;i<taorfpga.MAXQSFP;i++ {
        addr = addr + ((uint64(i)/4) * 4)
        data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
        data32 = (data32 & 0xFEFEFEFE)  //mask out reset bit
        taorfpga.TaorWriteU32( taorfpga.DEVREGION0, addr, data32)
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

    //Check Link
    {
        var link_rc, link_retry int
        var ps_output string
prbslinkcheckretry:
        cli.Printf("i", "Checking Link\n")
        time.Sleep(time.Duration(2) * time.Second)
        ps_output, err = ExecBCMshellCMD("ps")
        if err != errType.SUCCESS {
            return
        }
        for i:=0; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
            link_rc = LinkCheck(TaorPortMap[i].Name, ps_output) 
            if link_rc == errType.LINK_UP {
                dcli.Printf("i", "Port-%.02d  %4s: LINK UP\n", i+1, TaorPortMap[i].Name)
            } else if link_rc == errType.LINK_DOWN {
                dcli.Printf("e", "Port-%.02d  %4s: LINK DOWN\n", i+1, TaorPortMap[i].Name)
                rc = -1
            } else if link_rc == errType.LINK_DISABLED {
                dcli.Printf("e", "Port-%.02d  %4s: LINK DISABLED\n", i+1, TaorPortMap[i].Name)
                rc = -1
            } else {
                dcli.Printf("e", "Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, TaorPortMap[i].Name)
                rc = -1
            }
        }
        fmt.Printf("\n")
        if rc != 0 {
            if link_retry < 2 {
                link_retry = link_retry + 1
                rc = 0
                goto prbslinkcheckretry
            }
            err = errType.FAIL
            return
        }
    }

    //No return output to check on this command
    cli.Printf("i", "Disabling BCM LinkScan\n")
    command = "LINKscan off"
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
    time.Sleep(time.Duration(2) * (time.Second))
    

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
    time.Sleep(time.Duration(1) * (time.Second))
    command = "phy diag " + port100G_s +" prbs get unit=0"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }


    //cli.Printf("i", "Check 25G Ports Status\n")
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
                    //cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        rc = -1
    }

    //cli.Printf("i", "Check 100G Ports Status\n")
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
                    //cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }

    //sleep
    cli.Printf("i", "Sleeping for %d seconds to let the test run\n", sleep)
    time.Sleep(time.Duration(sleep/2) * (time.Second))
    _, _, err = CheckTemperatures("TD3", TD3_MAX_TEMP)
    if err != errType.SUCCESS {
        rc = -1
    }
    time.Sleep(time.Duration(sleep/2) * (time.Second))

    /*
    t1 := time.Now()
    for
    {
        t2 := time.Now()
        diff := t2.Sub(t1)
        data32, rc = ReadReg("TD3", "TOP_AVS_SEL_REG")
        //fmt.Printf("AVS REG=%x\n", data32)
        if rc != errType.SUCCESS {
            cli.Printf("e", "ERROR FAILED TO READ TOP_AVS_SEL_REG")
            break
        }
        //fmt.Println(" Elapsed Time=",diff," Duration=",duration," High Temp=", TD3highTemp )
        if uint32(diff.Seconds()) > uint32(sleep) {
            break
        }
    } 
    */ 


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
                    cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        rc = -1
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
                if strings.Contains(scanner.Text(), "PRBS has -2 errors!")==true {
                    cli.Printf("i", "[WARN] Port-%d seeing 2 errors\n", i+1)
                } else if strings.Contains(scanner.Text(), "PRBS OK!")==true {
                    cli.Printf("i", "Port-%d PRBS Passed\n", i+1)
                } else {
                    cli.Printf("e", "Port-%d PRBS Failed --> %s \n", i+1, scanner.Text())
                    err = errType.FAIL
                }
            }
        }
    }
    if err == errType.FAIL {
        rc = -1
    }

    cli.Printf("i", "Disable 25G PRBS\n")
    command = "phy diag " + port25G_s +" prbs clear"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    time.Sleep(time.Duration(2) * (time.Second))
    cli.Printf("i", "Disable 100G PRBS\n")
    command = "phy diag " + port100G_s +" prbs clear"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }


    time.Sleep(time.Duration(3) * (time.Second))
    //No return output to check on this command
    cli.Printf("i", "Enabling BCM LinkScan\n")
    command = "LINKscan on"
    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    if rc != 0 {
        err = errType.FAIL
    }
    return
}


func LinkFlap() (err int) {
    var rc int
    var errGo error
    var data32 uint32
    var addr uint64
    var port25G_s string
    var port100G_s string
    var tmp_s string
    var prbsType string
    var command string

    prbsType = "6"

    cli.Printf("i", "Disabling Ports in VTYSH\n")
    cmdString := "echo \"conf\nint 1/1/1-1/1/54\nshutdown\nend\n\" | vtysh"
    output1, errGo1 := exec.Command("bash", "-c", cmdString).Output()
    if errGo1 != nil {
        cli.Println("e", "Failed to exec command:",cmdString," GoERR=",errGo1)
        cli.Printf("e", "OUTPUT='%s'\n", output1)
        err = errType.FAIL
        return
    }
    time.Sleep(time.Duration(2) * time.Second)
    
    err = Set_Pre_Main_Post_25G_EXT(0)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on TD3 25G Ports\n")
        return
    }

    err = RetimerSetSI(0)
    if err != errType.SUCCESS {
        cli.Printf("e", "ERROR, Failed to set Pre Post Main on Retimer 100G Ports\n")
        return
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

    /* Enable QSFP's */
    cli.Printf("i", "Enabling QSFP's\n")
    addr = taorfpga.D0_FP_QSFP_CTRL_51_48_REG;
    for i:=0;i<taorfpga.MAXQSFP;i++ {
        addr = addr + ((uint64(i)/4) * 4)
        data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
        data32 = (data32 & 0xFEFEFEFE)  //mask out reset bit
        taorfpga.TaorWriteU32( taorfpga.DEVREGION0, addr, data32)
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
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Enabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=true"
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //Check Link
    time.Sleep(time.Duration(2) * time.Second)
    time.Sleep(time.Duration(2) * time.Second)

    //No return output to check on this command
    cli.Printf("i", "Disabling BCM LinkScan\n")
    command = "LINKscan off"
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }



    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 25G Ports\n")
    command = "phy diag " + port25G_s +" prbs set unit=0 p="+prbsType
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    //No return output to check on this command
    cli.Printf("i", "Starting PRBS on all 100G Ports\n")
    command = "phy diag " + port100G_s +" prbs set unit=0 p="+prbsType
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    time.Sleep(time.Duration(2) * (time.Second))
    

    //First time you read status it will show an error, have to read it again later after sleep
    cli.Printf("i", "Read Status to clear errors\n")
    command = "phy diag " + port25G_s +" prbs get unit=0"
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    command = "phy diag " + port100G_s +" prbs get unit=0"
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }



    //sleep
    time.Sleep(time.Duration(5) * (time.Second))


    cli.Printf("i", "Disable 25G PRBS\n")
    command = "phy diag " + port25G_s +" prbs clear"
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    time.Sleep(time.Duration(2) * (time.Second))
    cli.Printf("i", "Disable 100G PRBS\n")
    command = "phy diag " + port100G_s +" prbs clear"
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }


    time.Sleep(time.Duration(3) * (time.Second))
    //No return output to check on this command
    cli.Printf("i", "Enabling BCM LinkScan\n")
    command = "LINKscan on"
    _, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }

    if rc != 0 {
        err = errType.FAIL
    }
    return
}



/* Only set the external ports.   Production software will set the internal ports,
   but don't know what to set for the sfp and qsfp loopbacks.
   FOR QSFP Loopbacks we need to set it on the RETIMER.  NEED CODE FOR THAT
 
   --> POST1=0x17(23), MAIN=0x3d(61), PRE=0x10(16) 
   phy control xe11 Preemphasis=0x173D10
*/
func Set_Pre_Main_Post_25G_EXT(PrintOutput int) (err int) {

    var command string

    //for i:=0; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
    for i:=0; i<(TAOR_EXTERNAL_25G_PORTS); i++ {
        //pvlan set xe8 10
        preemphasis:= TaorPortMap[i].Pre | (TaorPortMap[i].Main << 8) | (TaorPortMap[i].Post << 16)
        command = fmt.Sprintf("phy control %s Preemphasis=0x%x", TaorPortMap[i].Name, preemphasis)
        _ , err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
        if PrintOutput > 0 {
            cli.Printf("i", "%s\n", command)
        }
    }
    return
}


/*********************************************************************************************************** 
*  
* LINE RATE: 
*     CURRENTLY WITH DSC MANAGER IT ALLOCATES VLAN[36:10] TO LAG521/ELBA0, AND VLAN[56:37] TO LAG521/ELBA1
* 
*     In This test there are 4 vlan loops. 
*     1) ELBA0 on ports 0-15 
*     2) ELBA1 on ports 16-31 
*     3) TD3 25G ports 32-47 
*     4) TD3 100G ports 48-53 
*  
*     The VLAN setup is a bit messy since the vlans are not contiguous due to how the VLANS are 
*     allocated in DSC MANAGER. 
*  
* FORWARDING SNAKE TEST: 
*     FORWARD TO THE NEXT PORT. SPLIT INTO TWO PORT SEGMENTS.
*     1) VLAN 10-36 GO TO ELBA0 (LAG521)
*     2) VLAN 37-64 GO TO ELBA1 (LAG522)
*  
*  
*  
***********************************************************************************************************/ 
/*
func Snake_Test(test_type uint32, elba_port_mask uint32, duration uint32, loopback_level string, pkt_size uint64, pkt_pattern uint64) (err int) {
    var rc int = errType.SUCCESS
    var errGo error
    var data32 uint32
    var addr uint64
    var SFPnumber, QSFPnumber, bitcompare uint32
    var port25G_s string
    var port100G_s string
    var tmp_s string
    var command string
    var output string
    var loopbackPhy uint32 = 0
    var ElbaVLANcreatScript = "/fs/nos/home_diag/dssman/run.sh"

    var VlanStart int = 10
    var vlanMap = []int{10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85}

    if test_type == SNAKE_TEST_LINE_RATE {
        cli.Printf("i", "Starting Snake Test.  Line Rate.   Elba Link Mask=%x,  Duration=%d", elba_port_mask, duration)
    } else if test_type == SNAKE_TEST_NEXT_PORT_FORWARDING  {
        cli.Printf("i", "Starting Snake Test.. Forward to the Next Port.  Elba Link Mask=%x,  Duration=%d", elba_port_mask, duration)
    } else if test_type == SNAKE_TEST_ENVIRONMENT  {
        cli.Printf("i", "Starting Snake Test for Environmental Testing. Line Rate/512 Byte Packets.  Elba Link Mask=%x,  Duration=%d", elba_port_mask, duration)
    } else {
        cli.Printf("e", "ERROR: INVALID TEST TYPE PASSED TO SNAKE TEST.  TEST TYPE PASSSED=%d", test_type)
        err = errType.FAIL
        return
    }

    if loopback_level == "phy" {
        loopbackPhy = 1
        cli.Printf("i", "Phy Loopback Selected\n")
    } else {
        cli.Printf("i", "External Loopback Selected\n")
        // Check SFP's are present 
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


        // Check QSFP's are present 
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

        // Enable SFP's 
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

        // Enable QSFP's 
        cli.Printf("i", "Enabling QSFP's\n")
        addr = taorfpga.D0_FP_QSFP_CTRL_51_48_REG;
        for i:=0;i<taorfpga.MAXQSFP;i++ {
            addr = addr + ((uint64(i)/4) * 4)
            data32, errGo = taorfpga.TaorReadU32(taorfpga.DEVREGION0, addr)
            data32 = (data32 & 0xFEFEFEFE)  //mask out reset bit
            taorfpga.TaorWriteU32( taorfpga.DEVREGION0, addr, data32)
        }
    }


    //Temperature Check.. return if failed.  Had some issue's with heatsinks.. return if temp to high 
    if err = CheckTemperatures("TD3", TD3_MAX_TEMP); err != errType.SUCCESS {
        err = errType.FAIL
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
        if test_type == SNAKE_TEST_NEXT_PORT_FORWARDING  {
            command = fmt.Sprintf("pvlan set %s %d", TaorPortMap[i].Name, (VlanStart + i))
        } else {
            command = fmt.Sprintf("pvlan set %s %d", TaorPortMap[i].Name, vlanMap[i])
        }
        cli.Printf("i", command)
        output, err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
        cli.Printf("i", "%s\n", command)
    }

    //
    //  VLAN SETUP
    //  FORWARDING TEST:
    //    set vlans 10-63 for the elba front panel ports
    //    vlan 10-36 will go to lag521 (Elba0)
    //    vlan 37-63 will go to lag522 (Elba1)
    //    All front panel ingress packets get forwarded to an Elba
    //  LINE_RATE_TEST:
    //    vlan 10-25 will go to lag521 (Elba0)  FP Port 0-15
    //    vlan 37-52 will go to lag522 (Elba1)  FP port 16 - 31
    //    vlan 64-79 to front panel ports 32-47 (ones based, bypasses ELBA)
    //   vlan 80-85 to 100G ports 48-53 (bypasses ELBA)
    //  
    for i:=0; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {

        if test_type == SNAKE_TEST_NEXT_PORT_FORWARDING  {
            //vlan add 10 pbm=xe8,xe9 ubm=xe8,xe9
            if i == (((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)/2)-1) {  //port 27 needs to vlan with port 0 to create the vlan snake for lag521 (elba0)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), TaorPortMap[i].Name, TaorPortMap[0].Name, TaorPortMap[i].Name, TaorPortMap[0].Name )
            } else if i == ((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)-1) { //Last entry needs to map back to port 28 to creat the vlan snake for lag522 (elba1)
                entry := ((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)/2)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), TaorPortMap[i].Name, TaorPortMap[entry].Name, TaorPortMap[i].Name, TaorPortMap[entry].Name )
            } else {  
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", (VlanStart + i), TaorPortMap[i].Name, TaorPortMap[i+1].Name, TaorPortMap[i].Name, TaorPortMap[i+1].Name )
            }
        } else {
        //vlan add 10 pbm=xe8,xe9 ubm=xe8,xe9
            if i == 15 {  //port 15 needs to vlan with port 0 to create the vlan snake for lag521 (elba0)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], TaorPortMap[i].Name, TaorPortMap[0].Name, TaorPortMap[i].Name, TaorPortMap[0].Name )
            } else if i == 31 { //31 back to 16 for lag522 (elba1)
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], TaorPortMap[i].Name, TaorPortMap[16].Name, TaorPortMap[i].Name, TaorPortMap[16].Name )
            } else if i == 47 { //47 back to 32
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], TaorPortMap[i].Name, TaorPortMap[32].Name, TaorPortMap[i].Name, TaorPortMap[32].Name )
            } else if i == 53 { //53 back to 48
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], TaorPortMap[i].Name, TaorPortMap[48].Name, TaorPortMap[i].Name, TaorPortMap[48].Name )
            } else {  
                command = fmt.Sprintf("vlan add %d pbm=%s,%s ubm=%s,%s", vlanMap[i], TaorPortMap[i].Name, TaorPortMap[i+1].Name, TaorPortMap[i].Name, TaorPortMap[i+1].Name )
            }
        }
        cli.Printf("i", "%s\n", command)
        output, err = ExecBCMshellCMD(command)
        if err != errType.SUCCESS {
            return
        }
    }

    if test_type == SNAKE_TEST_LINE_RATE || test_type == SNAKE_TEST_ENVIRONMENT{
        //VLAN SETUP
        //NEED TO REMOVE ELBA PORTS FROM FRONT PANEL PORTS 32-53.   THESE PORTS WILL NOT FORWARD TO ELBA, AND WILL VLAN SNAKE JUST ON TD3
        //vlan remove 64 pbm=ce1-ce4,ce9-ce10,ce12-ce13
        for i:=32; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
            command = fmt.Sprintf("vlan remove %d pbm=ce1-ce4,ce9-ce10,ce12-ce13", vlanMap[i])
            cli.Printf("i", "%s\n", command)
            output, err = ExecBCMshellCMD(command)
            if err != errType.SUCCESS {
                return
            }
        }
    }


    err = Set_Pre_Main_Post_25G_EXT()
    if err != errType.SUCCESS {
        return
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

    //Check Link
    cli.Printf("i", "Checking Link\n")
    time.Sleep(time.Duration(1) * time.Second)
    ps_output, err := ExecBCMshellCMD("ps")
    if err != errType.SUCCESS {
        return
    }
    for i:=0; i<(TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS); i++ {
        link_rc := LinkCheck(TaorPortMap[i].Name, ps_output) 
        if link_rc == errType.LINK_UP {
            cli.Printf("i", "Port-%.02d  %4s: LINK UP\n", i+1, TaorPortMap[i].Name)
        } else if link_rc == errType.LINK_DOWN {
            cli.Printf("e", "Port-%.02d  %4s: LINK DOWN\n", i+1, TaorPortMap[i].Name)
            rc = -1
        } else if link_rc == errType.LINK_DISABLED {
            cli.Printf("e", "Port-%.02d  %4s: LINK DISABLED\n", i+1, TaorPortMap[i].Name)
            rc = -1
        } else {
            cli.Printf("e", "Port-%.02d  %4s: ERROR READING LINK STATUS\n", i+1, TaorPortMap[i].Name)
            rc = -1
        }
    }
    fmt.Printf("\n")
    if rc != 0 {
        err = errType.FAIL
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

    //Inject Packets
    {
        var internal_port uint32 = 0
        for i:=TAOR_INTERNAL_PORT_START; i<(TAOR_INTERNAL_PORT_START+TAOR_INTERNAL_PORTS); i++ {
            fileData := []byte{}
            WRdata := []byte{}
            filename := fmt.Sprintf("/fs/nos/home_diag/dssman/packet.hex.%s", TaorPortMap[i].Name)
            f, errGo := os.Open(filename)
            if errGo != nil {
                fmt.Printf("[ERROR] Failed to open filename=%s.   ERR=%s\n", filename, errGo)
                err = errType.FAIL
                return
            }
            scanner := bufio.NewScanner(f)
            scanner.Split(bufio.ScanBytes)

            // Use For-loop.
            for scanner.Scan() {
                b := scanner.Bytes()
                fileData = append(fileData, b[0])
            }
            f.Close()
            //fmt.Printf(" Length File Data = %d\n", len(fileData))

            filename = fmt.Sprintf("/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[i].Name)
            outF, errGo1 := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
            if errGo1 != nil {
                fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, errGo1)
                return
            }
            if (int(pkt_size) > 0) && (int(pkt_pattern) > 0) {
                WRdata = append(fileData[0:96])
                outF.WriteString(string(WRdata[:]))
                for z:=(96/2);z<int(pkt_size);z+=4 {
                    fmt.Fprintf(outF, "%02x", uint8((pkt_pattern & 0xFF000000) >> 24))
                    fmt.Fprintf(outF, "%02x", uint8((pkt_pattern & 0xFF0000) >> 16))
                    fmt.Fprintf(outF, "%02x", uint8((pkt_pattern & 0xFF00) >> 8))
                    fmt.Fprintf(outF, "%02x", uint8(pkt_pattern & 0xFF))
                }            
                outF.Close()
            } else {
                outF.WriteString(string(fileData[:]))
                outF.Close()
            }
        }

        if test_type == SNAKE_TEST_LINE_RATE {
            for i:=TAOR_INTERNAL_PORT_START; i<(TAOR_INTERNAL_PORT_START+TAOR_INTERNAL_PORTS); i++ {
                if (elba_port_mask & (1<<internal_port)) == 0 {
                    internal_port++
                    continue;
                }
                internal_port++

                if TaorPortMap[i].ElbaNumber == 0 {
                    command = fmt.Sprintf("tx 100 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[0].Name, TaorPortMap[i].Name)
                } else {
                    command = fmt.Sprintf("tx 100 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[16].Name, TaorPortMap[i].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(4) * time.Second)
            }
            for i:=0; i<2; i++ {
                if i == 0 {
                    command = fmt.Sprintf("tx 300 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[32].Name, TaorPortMap[55].Name)
                } else {
                    command = fmt.Sprintf("tx 300 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[48].Name, TaorPortMap[55].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(5) * time.Second)
            }
        } else if test_type == SNAKE_TEST_ENVIRONMENT {
            for i:=TAOR_INTERNAL_PORT_START; i<(TAOR_INTERNAL_PORT_START+TAOR_INTERNAL_PORTS); i++ {
                if (elba_port_mask & (1<<internal_port)) == 0 {
                    internal_port++
                    continue;
                }
                internal_port++

                if TaorPortMap[i].ElbaNumber == 0 {
                    command = fmt.Sprintf("tx 16 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[0].Name, TaorPortMap[i].Name)
                } else {
                    command = fmt.Sprintf("tx 16 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[16].Name, TaorPortMap[i].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(4) * time.Second)
            }
            for i:=0; i<2; i++ {
                if i == 0 {
                    command = fmt.Sprintf("tx 14 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[32].Name, TaorPortMap[55].Name)
                } else {
                    command = fmt.Sprintf("tx 26 pbm=%s file=/fs/nos/home_diag/dssman/packet.hex.custom.%s", TaorPortMap[48].Name, TaorPortMap[55].Name)
                }
                cli.Printf("i", "%s\n", command)
                output, err = ExecBCMshellCMD(command)
                if err != errType.SUCCESS {
                    return
                }
                time.Sleep(time.Duration(5) * time.Second)
            }

        } else {
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
                time.Sleep(time.Duration(4) * time.Second)
            }
        }
    }


    //CHECK STATS & TEMPERATURE
    {
        t1 := time.Now()
        var ElbaPortminBandwidth uint64 = 11250000000//12000000000
        var Elba0bw, Elba1bw uint64
        var Lag521ExtPortminBandWidth uint64 = 0
        var Lag522ExtPortminBandWidth uint64 = 0
        var rc int = 0
        var printRxBandwidth = 1
        printRxBwTime := time.Now()

        if test_type == SNAKE_TEST_ENVIRONMENT {
            ElbaPortminBandwidth = 3000000000
        }

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

        
        if test_type == SNAKE_TEST_LINE_RATE  {
            Lag521ExtPortminBandWidth = Elba0bw / (16)
            Lag522ExtPortminBandWidth = Elba1bw / (16)
        } else if test_type == SNAKE_TEST_ENVIRONMENT {
            Lag521ExtPortminBandWidth = Elba0bw / (16)
            Lag522ExtPortminBandWidth = Elba1bw / (16)
        } else {
            Lag521ExtPortminBandWidth = Elba0bw / (TAOR_NUMB_EXT_PORT / 2)
            Lag522ExtPortminBandWidth = Elba1bw / (TAOR_NUMB_EXT_PORT / 2)
        }
        fmt.Printf(" Elba0bw bandwidth = %d\n", Elba0bw)
        fmt.Printf(" Elba1bw bandwidth = %d\n", Elba1bw)
        fmt.Printf(" Lag521 min bandwidth = %d\n", Lag521ExtPortminBandWidth)
        fmt.Printf(" Lag522 min bandwidth = %d\n", Lag522ExtPortminBandWidth)

        for {
            var StatRxBytes string
            var StatFCS string

            // Get rx bytes for all ports and check them below 
            StatRxBytes, err = GetRmonStat_AllPorts("CLMIB_RBYT") 
            if err != errType.SUCCESS {
                return
            }
            // Get FCS error for all ports 
            StatFCS, err = GetRmonStat_AllPorts("CLMIB_RFCS") 
            if err != errType.SUCCESS {
                return
            }

            

            for i:=0; i < TAOR_TOTAL_PORTS; i++ {
                var RxBytes uint64
                var FCSerror uint64
                var MinBandWidth25G uint64  =  2900000000
                var MinBandWidth100G uint64 = 11500000000

                if test_type == SNAKE_TEST_ENVIRONMENT {
                    MinBandWidth25G  =  900000000
                    MinBandWidth100G = 3400000000
                }
                
                RxBytes, err = MacStatRxByteSecond(StatRxBytes, i)
                if err != errType.SUCCESS {
                    return
                }
                if printRxBandwidth == 1 {
                    fmt.Printf("Port-%d %d/s\n", i, RxBytes)
                    
                }


                if test_type == SNAKE_TEST_LINE_RATE || test_type == SNAKE_TEST_ENVIRONMENT {
                    //lag521
                    if (i < 16) &&  (RxBytes < Lag521ExtPortminBandWidth) { 
                        cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , TaorPortMap[i].Name, RxBytes, Lag521ExtPortminBandWidth)
                        rc = errType.FAIL
                    }
                    //lag522
                    if (i >= 16) && (i < 31) {
                        if RxBytes < Lag522ExtPortminBandWidth { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , TaorPortMap[i].Name, RxBytes, Lag522ExtPortminBandWidth)
                            rc = errType.FAIL
                        }
                    }
                    //TD3 25G Snake ports
                    if (i >= 32) && (i < 48) {
                        if RxBytes < MinBandWidth25G { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , TaorPortMap[i].Name, RxBytes, MinBandWidth25G)
                            rc = errType.FAIL
                        }
                    }

                    //TD3 25G Snake ports
                    if (i >= 48) && (i < 54) {
                        if RxBytes < MinBandWidth100G { 
                            cli.Printf("e", "Bandwidth on Port-%d (%s) is low.  Read=%d  Expected Minimum=%d\n", i , TaorPortMap[i].Name, RxBytes, MinBandWidth100G)
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
                } else {
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
                }

                FCSerror, err = MacStatFCSerror(StatFCS, i)
                if err != errType.SUCCESS {
                    return
                }
                if FCSerror > 0 {
                    cli.Printf("e", "Port-%d (%s) has %d FCS Errors\n", i , TaorPortMap[i].Name, FCSerror)
                    rc = errType.FAIL
                }
            }
            printRxBandwidth = 0

            //Temperature Check
            if err = CheckTemperatures("TD3", TD3_MAX_TEMP); err != errType.SUCCESS {
                rc = errType.FAIL
            }

            if rc == errType.FAIL {
                fmt.Printf(" ERR BREAK\n")
                err = errType.FAIL
                break
            }
            {
                var highTemp float64 = 0
                current_temperatures, _ := GetTemperature("TD3")
                for i:=0;i<len(current_temperatures);i++ {
                    if current_temperatures[i] > highTemp { highTemp = current_temperatures[i] }
                }
                t2 := time.Now()
                diff := t2.Sub(t1)
                fmt.Println(" Elapsed Time=",diff," Duration=",duration," High Temp=", highTemp )
                if uint32(diff.Seconds()) > duration {
                    fmt.Printf(" DUATION BREAK\n")
                    break
                }
                diff = t2.Sub(printRxBwTime)
                if uint32(diff.Seconds()) > 10 {
                    printRxBandwidth = 1
                    printRxBwTime = time.Now()
                }
            }

        }
    }

    if test_type == SNAKE_TEST_LINE_RATE || test_type == SNAKE_TEST_ENVIRONMENT{
        command = "port " + TaorPortMap[0].Name +" enable=false"
        command = command + ";port " + TaorPortMap[16].Name +" enable=false"
        command = command + ";port " + TaorPortMap[32].Name +" enable=false"
        command = command + ";port " + TaorPortMap[48].Name +" enable=false"
        ExecBCMshellCMD(command)
    } else {
        command = "port " + TaorPortMap[0].Name +" enable=false"
        command = command + ";port " + TaorPortMap[((TAOR_EXTERNAL_25G_PORTS+TAOR_EXTERNAL_100G_PORTS)/2)].Name +" enable=false"
        ExecBCMshellCMD(command)
    }

    //No return output to check on this command
    cli.Printf("i", "Disabling all 25G Ports\n")
    command = "port " + port25G_s +" enable=false"
    ExecBCMshellCMD(command)

    //No return output to check on this command
    cli.Printf("i", "Disabling all 100G Ports\n")
    command = "port " + port100G_s +" enable=false"
    ExecBCMshellCMD(command)

    fmt.Printf("\n")
    DumpRxTxCounters()
    fmt.Printf("\n")

    // For compile error that var is not used 
    if TaorPortMap[0].ElbaNumber > 100000 {
            fmt.Printf("%s\n", output)
    }
    
    if err == errType.SUCCESS && rc == errType.SUCCESS {
        cli.Printf("i", "Snake Test PASSED\n\n")
    } else {
        cli.Printf("e", "Snake Test FAILED\n\n")
    }

    return
}
*/


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

//Return the temperature of all 3 retimers at once
func GearboxGetTemperatures() (temperature []float64, err int) {
    var output, command string
    var strapping uint32
    err = errType.SUCCESS

    strapping, _ = taorfpga.GetResistorStrapping() 

    if strapping == 0 {
        command = fmt.Sprintf("phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210", mdio_phy_addr_rev0[GEARBOX_START + 0], mdio_phy_addr_rev0[GEARBOX_START + 1], mdio_phy_addr_rev0[GEARBOX_START + 2], mdio_phy_addr_rev0[GEARBOX_START + 3])
    } else {
        command = fmt.Sprintf("phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210", mdio_phy_addr_rev1[GEARBOX_START + 0], mdio_phy_addr_rev1[GEARBOX_START + 1], mdio_phy_addr_rev1[GEARBOX_START + 2], mdio_phy_addr_rev1[GEARBOX_START + 3])
    }
    
    //BCM.0> phy raw c45 0x100 0x1 0xd210
    //      0xd210: 0x02d8


    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    scanner := bufio.NewScanner(strings.NewReader(output))
    for scanner.Scan() {
        if strings.Contains(scanner.Text(), "0xd210:") {
            out := strings.TrimSpace(scanner.Text())
            data64, _ := strconv.ParseUint(out[8:], 0, 64)
            tFloat := float64(data64)
            tFloat = 434.10000 - 0.53504 * tFloat
            temperature = append(temperature, tFloat)
        }
    }
    return
}


//Return the temperature of all 3 retimers at once
func RetimerGetTemperatures() (temperature []float64, err int) {
    var output, command string
    var strapping uint32
    err = errType.SUCCESS

    strapping, _ = taorfpga.GetResistorStrapping() 

    if strapping == 0 {
        command = fmt.Sprintf("phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210", mdio_phy_addr_rev0[RETIMER_START + 0], mdio_phy_addr_rev0[RETIMER_START + 1], mdio_phy_addr_rev0[RETIMER_START + 2])
    } else {
        command = fmt.Sprintf("phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210; phy raw c45 0x%x 0x1 0xd210", mdio_phy_addr_rev1[RETIMER_START + 0], mdio_phy_addr_rev1[RETIMER_START + 1], mdio_phy_addr_rev1[RETIMER_START + 2])
    }
    
    //BCM.0> phy raw c45 0x100 0x1 0xd210
    //      0xd210: 0x02d8


    output, err = ExecBCMshellCMD(command)
    if err != errType.SUCCESS {
        return
    }
    scanner := bufio.NewScanner(strings.NewReader(output))
    for scanner.Scan() {
        if strings.Contains(scanner.Text(), "0xd210:") {
            out := strings.TrimSpace(scanner.Text())
            data64, _ := strconv.ParseUint(out[8:], 0, 64)
            tFloat := float64(data64)
            tFloat = 434.10000 - 0.53504 * tFloat
            temperature = append(temperature, tFloat)
        }
    }
    return
}


/********************************************************************************************************* 
   phy raw c45 0x100 0x1 0x8000 (0x9000 | (1<<lane))
   phy raw c45 0x100 0x1 0x8001 0x0
   phy raw c45 0x100 0x1 0xd1ad
   phy raw c45 0x100 0x1 0xd1ad 0x8004
 
***********************************************************************************************************/ 
func TD3_Lane_Config_Disable_UNRELIABLELOS_and_LPDFE(PrintOutput int) (err int) {
    var output, command string
    var strapping uint32
    err = errType.SUCCESS
    var retimer_address uint32 = 0

    strapping, _ = taorfpga.GetResistorStrapping() 

    for i:=0; i<3; i++ {
        if strapping == 0 {
            retimer_address = mdio_phy_addr_rev0[RETIMER_START + i]
        } else {
            retimer_address = mdio_phy_addr_rev1[RETIMER_START + i]
        }
        for lane:=0; lane<8; lane++ {
            command = fmt.Sprintf("phy raw c45 0x%x 0x1 0x8000 0x90%.02x; phy raw c45 0x%x 0x1 0x8001 0x0;phy raw c45 0x%x 0x1 0xd1ad 0x8004;phy raw c45 0x%x 0x1 0xd1ad", retimer_address, (1<<uint32(lane)), retimer_address,retimer_address, retimer_address)
            if PrintOutput > 0 {
                fmt.Printf("Setting QSFP LANE CONFIG --> %s\n", command)
            }
            output, err = ExecBCMshellCMD(command)
            if err != errType.SUCCESS {
                cli.Printf("e", "BCM SHELL ACCESS FAILED!  OUTPUT ='%s'", string(output))
                err = errType.FAIL
                return
            }
            fmt.Printf("%s\n", string(output))
        }
    }
    return
}



/******************************************************************************** 
* Set Pre/Post/Main 
* 
 
How to Read/Set TX FIR on Retimer (BCM81381) of Taormina:
================================================================

1) Configuration:
  Each Retimer has two ports. The system and line side lane mapping for every port are as below:
    System side:
      port #1 - 0x0f
      port #2 - 0xf0
    Line side:
      port #1 - 0x0f
      port #2 - 0xf0
  There are 3 retimers connected to TD3. The phy address for each retimer on P1 and later cards is as below:
    Retimer #1: 0x100
    Retimer #2: 0x102
    Retimer #3: 0x104

2) Retimer TX FIR Reg addresses:
  0x1d133: pre
  0x1d134: main
  0x1d135: post
  0x1d136: pre2
  0x1d137: post2
  0x1d138: post3

  0x1800: lane reg
    Value for line side: 0x90__ (__ represents the lane)
    Value for system side: 0xa0__ (__ represents the lane)

3) Set TX FIR (pre/main/post):
  The following is the example to set pre/main/post for both line and system side of port #1 on retimer #1.
  For different retimer and/or port, please replace the phy address and lane mapping respectively.
    pre = 10 (0xa)
    main = 65 (0x41)
    post = 20 (0x14)

  Setting sequence for line side, all 4 lanes of port 1 (lane 0x10/20/40/80)
  Lane 0x10:
    phy raw c45 0x100 0x1 0x8000 0x9010
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41   <-- MAIN
    phy raw c45 0x100 0x1 0xd135 0x14   <-- POST
    phy raw c45 0x100 0x1 0xd133 0xa    <-- PRE
    phy raw c45 0x100 0x1 0xd133 0x80a
  Lane 0x20:
    phy raw c45 0x100 0x1 0x8000 0x9020
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41
    phy raw c45 0x100 0x1 0xd135 0x14
    phy raw c45 0x100 0x1 0xd133 0xa
    phy raw c45 0x100 0x1 0xd133 0x80a
  Lane 0x40:
    phy raw c45 0x100 0x1 0x8000 0x9040
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41
    phy raw c45 0x100 0x1 0xd135 0x14
    phy raw c45 0x100 0x1 0xd133 0xa
    phy raw c45 0x100 0x1 0xd133 0x80a
  Lane 0x80:
    phy raw c45 0x100 0x1 0x8000 0x9080
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41
    phy raw c45 0x100 0x1 0xd135 0x14
    phy raw c45 0x100 0x1 0xd133 0xa
    phy raw c45 0x100 0x1 0xd133 0x80a

  Setting sequence for system side, all 4 lanes of port 1 (lane 0x10/20/40/80)
  Lane 0x10:
    phy raw c45 0x100 0x1 0x8000 0xa010
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41
    phy raw c45 0x100 0x1 0xd135 0x14
    phy raw c45 0x100 0x1 0xd133 0xa
    phy raw c45 0x100 0x1 0xd133 0x80a
  Lane 0x20:
    phy raw c45 0x100 0x1 0x8000 0xa020
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41
    phy raw c45 0x100 0x1 0xd135 0x14
    phy raw c45 0x100 0x1 0xd133 0xa
    phy raw c45 0x100 0x1 0xd133 0x80a
  Lane 0x40:
    phy raw c45 0x100 0x1 0x8000 0xa040
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41
    phy raw c45 0x100 0x1 0xd135 0x14
    phy raw c45 0x100 0x1 0xd133 0xa
    phy raw c45 0x100 0x1 0xd133 0x80a
  Lane 0x80:
    phy raw c45 0x100 0x1 0x8000 0xa080
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd134 0x41
    phy raw c45 0x100 0x1 0xd135 0x14
    phy raw c45 0x100 0x1 0xd133 0xa
    phy raw c45 0x100 0x1 0xd133 0x80a

4) Read TX FIR settings:
  The following is the example to read pre/main/post settings for line/system side of port #1 on retimer #1.
  For different retimer and/or port, please replace the phy address and lane mapping respectively.

  Reading sequence for line side, all 4 lanes of port 1 (lane 0x10/20/40/80)
  Lane 0x10:
    phy raw c45 0x100 0x1 0x8000 0x9010
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138
  Lane 0x20:
    phy raw c45 0x100 0x1 0x8000 0x9020
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138
  Lane 0x40:
    phy raw c45 0x100 0x1 0x8000 0x9040
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138
  Lane 0x80:
    phy raw c45 0x100 0x1 0x8000 0x9080
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138

  Reading sequence for system side, all 4 lanes of port 1 (lane 0x10/20/40/80)
  Lane 0x10:
    phy raw c45 0x100 0x1 0x8000 0xa010
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138
  Lane 0x20:
    phy raw c45 0x100 0x1 0x8000 0xa020
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138
  Lane 0x40:
    phy raw c45 0x100 0x1 0x8000 0xa040
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138
  Lane 0x80:
    phy raw c45 0x100 0x1 0x8000 0xa080
    phy raw c45 0x100 0x1 0x8001 0x0
    phy raw c45 0x100 0x1 0xd133
    phy raw c45 0x100 0x1 0xd134
    phy raw c45 0x100 0x1 0xd135
    phy raw c45 0x100 0x1 0xd136
    phy raw c45 0x100 0x1 0xd137
    phy raw c45 0x100 0x1 0xd138
 
 
    -6 is 0xfa
 
Pre (decimal): -6   (0xFA)
Main (decimal): 73  (0x49)
Post (decimal): 0 
 
 
Enter Command Code (0=Help): 21
Set TX FIR on Line/Sys side ? (0:Line, 1:Sys, 9=Exit)0
if_side = 0
Pre: -12~0, Main: 0~100, Post: -34~0
Set [Pre] [Main] [Post]: -6 83 0
tx_fir.pre = -6
tx_fir.main = 83
tx_fir.post = 0
Lane: 0x1, setting Pre/Main/Post=-6/83/0
READ  [0x18500] ==> [0x1381] @ MDIO_Addr [0x10] 
READ  [0x18501] ==> [0x80a1] @ MDIO_Addr [0x10] 
READ  [0x18596] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x18594] ==> [0xffff] @ MDIO_Addr [0x10] 
WRITE [0x18000] <== [0x9001] @ MDIO_Addr [0x10] 
READ  [0x18001] ==> [0x0] @ MDIO_Addr [0x10] 
WRITE [0x18001] <== [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x3000] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0x3400] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x3400] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0x35fa] @ MDIO_Addr [0x10] 
READ  [0x1d134] ==> [0x0] @ MDIO_Addr [0x10] 
WRITE [0x1d134] <== [0x53] @ MDIO_Addr [0x10] 
READ  [0x1d135] ==> [0xa8] @ MDIO_Addr [0x10] 
WRITE [0x1d135] <== [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d136] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d137] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d138] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d139] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13a] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13b] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13c] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13d] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13e] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x35fa] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0x5fa] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x5fa] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0xdfa] @ MDIO_Addr [0x10] 
Lane: 0x2, setting Pre/Main/Post=-6/83/0
READ  [0x18500] ==> [0x1381] @ MDIO_Addr [0x10] 
READ  [0x18501] ==> [0x80a1] @ MDIO_Addr [0x10] 
READ  [0x18596] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x18594] ==> [0xffff] @ MDIO_Addr [0x10] 
WRITE [0x18000] <== [0x9002] @ MDIO_Addr [0x10] 
READ  [0x18001] ==> [0x0] @ MDIO_Addr [0x10] 
WRITE [0x18001] <== [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x3000] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0x3400] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x3400] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0x35fa] @ MDIO_Addr [0x10] 
READ  [0x1d134] ==> [0x0] @ MDIO_Addr [0x10] 
WRITE [0x1d134] <== [0x53] @ MDIO_Addr [0x10] 
READ  [0x1d135] ==> [0xa8] @ MDIO_Addr [0x10] 
WRITE [0x1d135] <== [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d136] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d137] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d138] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d139] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13a] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13b] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13c] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13d] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d13e] ==> [0x0] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x35fa] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0x5fa] @ MDIO_Addr [0x10] 
READ  [0x1d133] ==> [0x5fa] @ MDIO_Addr [0x10] 
WRITE [0x1d133] <== [0xdfa] @ MDIO_Addr [0x10]  
 
********************************************************************************/ 
func RetimerSetSI(PrintOutput int) (err int) {
    var output, command string
    var strapping uint32
    err = errType.SUCCESS
    var retimer_address uint32 = 0

    strapping, _ = taorfpga.GetResistorStrapping() 

    for i:=0; i<3; i++ {
        if strapping == 0 {
            retimer_address = mdio_phy_addr_rev0[RETIMER_START + i]
        } else {
            retimer_address = mdio_phy_addr_rev1[RETIMER_START + i]
        }
        for lane:=0; lane<8; lane++ {
            command = fmt.Sprintf("phy raw c45 0x%x 0x1 0x8000 0x90%.02x; phy raw c45 0x%x 0x1 0x8001 0x0;", retimer_address, (1<<uint32(lane)), retimer_address)
            command1 := fmt.Sprintf("phy raw c45 0x%x 0x1 0xd133 0x3400; phy raw c45 0x%x 0x1 0xd133 0x35FA;", retimer_address, retimer_address)
            command2 := fmt.Sprintf("phy raw c45 0x%x 0x1 0xd134 0x49; phy raw c45 0x%x 0x1 0xd135 0x00;", retimer_address, retimer_address)
            command3 := fmt.Sprintf("phy raw c45 0x%x 0x1 0xd133 0x5FA; phy raw c45 0x%x 0x1 0xd133 0xDFA;", retimer_address, retimer_address)
            
            command = command + command1 + command2 + command3
            if PrintOutput > 0 {
                fmt.Printf("Setting QSFP SI --> %s\n", command)
            }
            output, err = ExecBCMshellCMD(command)
            if err != errType.SUCCESS {
                cli.Printf("e", "BCM SHELL ACCESS FAILED!  OUTPUT ='%s'", string(output))
                err = errType.FAIL
                return
            }
        }
    }
    return
}

func RetimerDumpSI() (err int) {
    var output, command string
    var strapping uint32
    err = errType.SUCCESS
    var retimer_address uint32 = 0

    strapping, _ = taorfpga.GetResistorStrapping() 

    for i:=0; i<3; i++ {


        if strapping == 0 {
            retimer_address = mdio_phy_addr_rev0[RETIMER_START + i]
        } else {
            retimer_address = mdio_phy_addr_rev1[RETIMER_START + i]
        }
        for lane:=0; lane<8; lane++ {
            command = fmt.Sprintf("phy raw c45 0x%x 0x1 0x8000 0x90%.02x; phy raw c45 0x%x 0x1 0x8001 0x0;", retimer_address, (1<<uint32(lane)), retimer_address)
            command1 := fmt.Sprintf("phy raw c45 0x%x 0x1 0xd133; phy raw c45 0x%x 0x1 0xd134;", retimer_address, retimer_address)
            command2 := fmt.Sprintf("phy raw c45 0x%x 0x1 0xd135; phy raw c45 0x%x 0x1 0xd136;", retimer_address, retimer_address)
            command3 := fmt.Sprintf("phy raw c45 0x%x 0x1 0xd137; phy raw c45 0x%x 0x1 0xd138;", retimer_address, retimer_address)
            
            command = command + command1 + command2 + command3
            
            fmt.Printf("Setting QSFP SI --> %s\n", command)
            output, err = ExecBCMshellCMD(command)
            if err != errType.SUCCESS {
                cli.Printf("e", "BCM SHELL ACCESS FAILED!  OUTPUT ='%s'", string(output))
                err = errType.FAIL
                return
            }
            cli.Printf("i", "'%s'\n", output)
        }
    }
    return
}


//Return the temperature of all 3 retimers at once
func TD3FlashTest(cycles int) (err int) {
    var output, command, results string
    err = errType.SUCCESS

    var s string

    fmt.Printf("DO NOT POWER OFF THE SYSTEM.  IT WILL BRICK TD3's PCI FIRMWARE.   DO YOU WANT TO CONTINUE? (y/N): ")
    _, errGo := fmt.Scan(&s)
    if errGo != nil {
            panic(errGo)
    }

    s = strings.TrimSpace(s)
    s = strings.ToLower(s)

    if s == "y" || s == "yes" {
    } else {
        return errType.FAIL
    }

    cli.Printf("i", "Backing up existing firmware to /tmp/td3pciefw.bin\n")
    command = "pciephy fw extract /tmp/td3pciefw.bin"
    results = "PCIE firmware extracted successfully"
    output, err = BCMShellExecuteCmdCheckResults(command, results)
    if err != errType.SUCCESS {
        cli.Printf("e", "Executed bcm shell cmd='%s'.   Did not get expected results='%s'\n", command, results)
        cli.Printf("e", "Output='%s'\n", output)
        return
    }    

    for i:=0; i<cycles; i++ {
        cli.Printf("i", "Loop-%d    Generating Random 1MB file /tmp/td3flash.bin\n", i)
        cmd := exec.Command("dd", "if=/dev/urandom", "of=/tmp/td3flash.bin", "bs=1M", "count=1")
        errGo = cmd.Run()
        if errGo != nil {
            cli.Printf("e", "dd failed.  err=%s\n", errGo)
            err = errType.FAIL
            return
        }

        //Have bcm shell program random generated image to flash
        cli.Printf("i", "Programming TD3 Flash\n")
        command = "pciephy fw load /tmp/td3flash.bin"
        results = "PCIE firmware updated successfully"
        output, err = BCMShellExecuteCmdCheckResults(command, results)
        if err != errType.SUCCESS {
            cli.Printf("e", "Executed bcm shell cmd='%s'.   Did not get expected results='%s'\n", command, results)
            cli.Printf("e", "Output='%s'\n", output)
            return
        }  

        //Read Back Firmware to new file
        cli.Printf("i", "Reading back random file from TD3 flash\n")
        command = "pciephy fw extract /tmp/td3flash_readback.bin"
        results = "PCIE firmware extracted successfully"
        output, err = BCMShellExecuteCmdCheckResults(command, results)
        if err != errType.SUCCESS {
            cli.Printf("e", "Executed bcm shell cmd='%s'.   Did not get expected results='%s'\n", command, results)
            cli.Printf("e", "Output='%s'\n", output)
            return
        } 

        //Compare data
        // per comment, better to not read an entire file into memory
        // this is simply a trivial example.
        f1, err1 := ioutil.ReadFile("/tmp/td3flash.bin")
        if err1 != nil {
            cli.Printf("e", "Opening /tmp/td3flash.bin failed  err=%s\n", errGo)
            err = errType.FAIL
            return
        }

        f2, err2 := ioutil.ReadFile("/tmp/td3flash_readback.bin")
        if err2 != nil {
            cli.Printf("e", "Opening /tmp/td3flash_readback.bin failed  err=%s\n", errGo)
            err = errType.FAIL
            return
        }

        if bytes.Equal(f1, f2) == false { // Per comment, this is significantly more performant.
            cli.Printf("e", "/tmp/td3flash.bin & /tmp/td3flash_readback.bin are not equal.  TD3 flash test failed\n")
            err = errType.FAIL
            return

        }
    }


    //Have bcm shell program random generated image to flash
    cli.Printf("i", "Programming original PCIe firmware to TD3 flash\n")
    command = "pciephy fw load /tmp/td3pciefw.bin"
    results = "PCIE firmware updated successfully"
    output, err = BCMShellExecuteCmdCheckResults(command, results)
    if err != errType.SUCCESS {
        cli.Printf("e", "Executed bcm shell cmd='%s'.   Did not get expected results='%s'\n", command, results)
        cli.Printf("e", "Output='%s'\n", output)
        return
    }  

    return
}



/***************************************************************************************
BCM.0> tl 50
U/A/S|Test|            Test           |Loop | Run |Pass |Fail |  Arguments
     | #  |            Name           |Count|Count|Count|Count|
-----+----+---------------------------+-----+-----+-----+-----+-----------
   S |  50| Memory Fill/Verify        |    1| 2469| 2469|    0| (none)
BCM.0>
****************************************************************************************/
func BCMshell_Test_Results(testnumber int)(loop int, runcnt int, passcnt int, failcnt int, err int) {




    return
}


