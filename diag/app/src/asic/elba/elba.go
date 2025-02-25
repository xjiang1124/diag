package elba

import (
    "bufio"
    "fmt"
    "io/ioutil"
    "os"
    "os/exec"
    "regexp"
    "strconv"
    "strings"
    "syscall"

    "gopkg.in/yaml.v2"

    "common/dcli"
    "common/errType"
    "common/misc"
    "common/runCmd"
)

type TResult struct {
    TestResult string `yaml:"TEST_RESULT"`
}


/********************************************************************************
 Check Elba for ECC Errors. 
 
 Need to read the 12 registers below which are the IRQ and ECC data registers
 
   read 0x30520020     //CHECK MC0 CORRECTABLE IRQ (See below for bit defines).  
   read 0x305a0020     //CHECK MC1 CORRECTABLE IRQ (see below for bit defines). 
   read 0x30530464     //BITS[31:0]
   read 0x30530468     //BITS[63:32] --> MC0-SYNCD_ADDR[47:40] / MC0-ADDR[39:0]
   read 0x3053046C     //BITS[31:0]
   read 0x30530470     //BITS[63:32] --> MC0-DATA[63:0]
   read 0x30530474     //[BITS31:0]  --> MC0-ECC C ID[16]
   read 0x305B0464     //BITS[31:0]
   read 0x305B0468     //BITS[63:32] --> MC1-SYNCD_ADDR[47:40] / MC0-ADDR[39:0]
   read 0x305B046C     //BITS[31:0]
   read 0x305B0470     //BITS[63:32] --> MC1-DATA[63:0]
   read 0x305B0474     //[BITS31:0]  --> MC1-ECC C ID[16]
 
   read 0x305305e4     --> MC0 INT STATUS ECC
   read 0x305b05e4     --> MC1 INT STATUS ECC
 
 
   FOR IRQ JUST CHECK TWO CORRECTED BITS BELOW
        [   1   ] ecc_dataout_corrected_1_interrupt:   0x0
        [   0   ] ecc_dataout_corrected_0_interrupt:   0x0 
**********************************************************************************/
func CheckECC() (err int) {
    var errGo error
    var ecc_check uint32
    ReadData := make([]uint32, 14)
    addresses := []uint32{  0x30520020,
                            0x305a0020,
                            0x30530464,
                            0x30530468,
                            0x3053046C,
                            0x30530470,
                            0x30530474,
                            0x305B0464,
                            0x305B0468,
                            0x305B046C,
                            0x305B0470,
                            0x305B0474,
                            0x305305e4,
                            0x305b05e4,
                        }

//var gbLoopbackLevel_map = map[int]string{
//    GB_LOOPBACK_LINE_SIDE : "Line",
//    GB_LOOPBACK_HOST_SIDE : "Host",
//}

    var syndrome_map = map[int]string{
           0x00 : "No Error",
           0x01 : "slice8.Check-0",
           0x02 : "slice8.Check-1",
           0x04 : "slice8.Check-2",       
           0x08 : "slice8.Check-3",
           0x0b : "slice7.Data-63",
           0x0e : "slice7.Data-62",
           0x10 : "slice8.Check-4",
           0x13 : "slice7.Data-61",
           0x15 : "slice7.Data-60",       
           0x16 : "slice7.Data-59",
           0x19 : "slice7.Data-58",
           0x1a : "slice7.Data-57",
           0x1c : "slice7.Data-56",
           0x20 : "slice8.Check-5",       
           0x23 : "slice6.Data-55",
           0x25 : "slice6.Data-54",
           0x26 : "slice6.Data-53",
           0x29 : "slice6.Data-52",       
           0x2a : "slice6.Data-51",
           0x2c : "slice6.Data-50",
           0x31 : "slice6.Data-49",       
           0x34 : "slice6.Data-48",       
           0x40 : "slice8.Check-6",
           0x4a : "slice5.Data-47",       
           0x4f : "slice5.Data-46",
           0x52 : "slice5.Data-45",
           0x54 : "slice5.Data-44",
           0x57 : "slice5.Data-43",
           0x58 : "slice5.Data-42",
           0x5b : "slice5.Data-41",
           0x5e : "slice5.Data-40",
           0x62 : "slice4.Data-39",
           0x64 : "slice4.Data-38",
           0x67 : "slice4.Data-37",
           0x68 : "slice4.Data-36",
           0x6b : "slice4.Data-35",
           0x6d : "slice4.Data-34",
           0x70 : "slice4.Data-33",
           0x75 : "slice4.Data-32",
           0x80 : "slice8.Check-7",
           0x8a : "slice3.Data-31",
           0x8f : "slice3.Data-30",
           0x92 : "slice3.Data-29",
           0x94 : "slice3.Data-28",
           0x97 : "slice3.Data-27",
           0x98 : "slice3.Data-26",
           0x9b : "slice3.Data-25",
           0x9d : "slice3.Data-24",       
           0xa2 : "slice2.Data-23",
           0xa4 : "slice2.Data-22",
           0xa7 : "slice2.Data-21",
           0xa8 : "slice2.Data-20",
           0xab : "slice2.Data-19",
           0xad : "slice2.Data-18",
           0xb0 : "slice2.Data-17",
           0xb5 : "slice2.Data-16",
           0xcb : "slice1.Data-15",
           0xce : "slice1.Data-14",
           0xd3 : "slice1.Data-13",
           0xd5 : "slice1.Data-12",
           0xd6 : "slice1.Data-11",
           0xd9 : "slice1.Data-10",
           0xda : "slice1.Data-9 ",
           0xdc : "slice1.Data-8 ",
           0xe3 : "slice0.Data-7 ",
           0xe5 : "slice0.Data-6 ",
           0xe6 : "slice0.Data-5 ",
           0xe9 : "slice0.Data-4 ",
           0xea : "slice0.Data-3 ",
           0xec : "slice0.Data-2 ",
           0xf1 : "slice0.Data-1 ",
           0xf4 : "slice0.Data-0 ",
    }

    for cnt , addr := range(addresses) {
        ReadData[cnt], errGo = misc.ReadU32(uint64(addr))
        if errGo != nil {
            fmt.Printf("ERROR: Failed to read the ecc registers from Elba at address 0x%x\n", addr)
            err = errType.FAIL
            return
        }
    }

    //Mask out the IRQ BITs we don't care about
    ReadData[0] = ReadData[0] & 0x3
    ReadData[1] = ReadData[1] & 0x3
    
    //All registers associated with the ECC need to be zero, or we hit an ecc correctable error
    //MC0
    ecc_check = ReadData[0] | ReadData[2] | ReadData[3] | ReadData[4] | ReadData[5] | ReadData[6]
    if ecc_check > 0 {
        fmt.Printf("ERROR: Elba MC0 Correctable Error Data Set\n")
        err = errType.FAIL
    }
    fmt.Printf("MC0 ecc_dataout_corrected_1_interrupt  = 0x%x\n", ReadData[0] & 0x2) 
    fmt.Printf("MC0 ecc_dataout_corrected_0_interrupt  = 0x%x\n", ReadData[0] & 0x1)
    fmt.Printf("MC0-SYNCD_ADDR[47:40] / MC0-ADDR[39:0] = 0x%x%.08x\n", ReadData[3], ReadData[2])
    fmt.Printf("MC0-DATA[63:0]                         = 0x%x%.08x\n", ReadData[5], ReadData[4])
    fmt.Printf("MC0-ECC C ID[16]                       = 0x%x\n", ReadData[6])
    if ( ((ReadData[12] & 0xA)>0) || 
          (ReadData[12] & 0x5)>0) {
        var syndrome int = int((ReadData[3] >> 8) & 0xFF)   //get 8-bit syndrome
        if syndrome != 0 {
            syndrome_string, ok := syndrome_map[int(syndrome)]
            if ok {
                fmt.Println("MC0 ECC Syndrome=", syndrome_string)
            }
        }
    }


    //MC1
    ecc_check = ReadData[1] | ReadData[7] | ReadData[8] | ReadData[9] | ReadData[10] | ReadData[11]
    if ecc_check > 0 {
        fmt.Printf("ERROR: Elba MC1 Correctable Error Data Set\n")
        err = errType.FAIL
    }
    fmt.Printf("MC1 ecc_dataout_corrected_1_interrupt  = 0x%x\n", ReadData[1] & 0x2) 
    fmt.Printf("MC1 ecc_dataout_corrected_0_interrupt  = 0x%x\n", ReadData[1] & 0x1)
    fmt.Printf("MC1-SYNCD_ADDR[47:40] / MC0-ADDR[39:0] = 0x%x%.08x\n", ReadData[8], ReadData[7])
    fmt.Printf("MC1-DATA[63:0]                         = 0x%x%.08x\n", ReadData[10], ReadData[9])
    fmt.Printf("MC1-ECC C ID[16]                       = 0x%x\n", ReadData[11])
    if ( ((ReadData[13] & 0xA)>0) || 
        (ReadData[13] & 0x5)>0) {
        var syndrome int = int((ReadData[8] >> 8) & 0xFF)   //get 8-bit syndrome
        if syndrome != 0 {
            syndrome_string, ok := syndrome_map[syndrome]
            if ok {
                fmt.Println("MC1 ECC Syndrome=", syndrome_string)
            }
        }
    }
    
    if err == errType.FAIL {
        fmt.Printf("ECC Check FAILED\n\n");
    } else {
        fmt.Printf("ECC Check PASSED\n\n");
    }
    return
}

func Prbs(mode string, poly string, duration int, intLpbk int, asicType string) (err int) {
    var cmd string
    var filename string
    var errGo error
    var resultStr string

    err = errType.SUCCESS

    mode = strings.ToUpper(mode)
    poly = strings.ToUpper(poly)

    if (poly != "PRBS7"  &&
        poly != "PRBS9"  &&
        poly != "PRBS15" &&
        poly != "PRBS31") {
        dcli.Println("e", "Invalid POLY:", poly)
        err = errType.INVALID_PARAM
        return
    }

    dcli.Println("i", mode, strconv.Itoa(duration), intLpbk, asicType)

    errGo = os.Chdir("/data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
    if errGo != nil {
        dcli.Println("e", errGo)
        return
    }

    filename = "result.yaml"
    errGo = os.Remove(filename)
    if errGo != nil {
        dcli.Println("i", errGo)
    } else {
        dcli.Println("i", "Yaml file deleted")
    }

    if asicType == "ELBA" {
        cmd = "/data/nic_arm/elba/asic_src/ip/cosim/tclsh/nic_prbs.sh"
    } else {
        cmd = "/data/nic_arm/giglio/asic_src/ip/cosim/tclsh/nic_prbs.sh"
    }
    if mode == "PCIE" {
        passSign := "PCIE PRBS PASSED"
        failSign := "PCIE PRBS FAILED"
        err = runCmd.Run(passSign, failSign, cmd, "PCIE", strconv.Itoa(duration), strconv.Itoa(intLpbk))
    } else if mode == "ETH" {
        passSign := "MX PRBS PASSED"
        failSign := "MX PRBS FAILED"
        err = runCmd.Run(passSign, failSign, cmd, "ETH", strconv.Itoa(duration), strconv.Itoa(intLpbk))
    } else {
        dcli.Println("e", "Invalid mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    if err != errType.SUCCESS {
        dcli.Println("e", mode, "PRBS Test Failed!")
        resultStr = "FAIL"
    } else {
        dcli.Println("i", mode, "PRBS PASSED")
        resultStr = "SUCCESS"
    }

    err = updateYaml(resultStr)
    dcli.Println("i", "YAML file updated")

    return err
}

func SnakeAndPrbsCheck(testType string) (err int) {
    var c TResult
    var pid string

    errGo := os.Chdir("/data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
    if errGo != nil {
        dcli.Println("e", "Failed to change dir!")
        err = errType.FAIL
        return
    }

	//cmdStr := "ps | grep asicutil"
	cmdStr := "ps | grep asicutil"
    out, errGo := exec.Command("bash", "-c", cmdStr).Output()
    if errGo != nil {
        dcli.Println("e", errGo)
    }
    outStr := string(out)

    // Get PID
    re := regexp.MustCompile(`^\s*(\d+)\sroot.*`)
    scanner := bufio.NewScanner(strings.NewReader(outStr))
    for scanner.Scan() {
        if strings.Contains(scanner.Text(), "_lb") {
            match := re.MatchString(scanner.Text())
            if match == true {
                submatchall := re.FindAllStringSubmatch(scanner.Text(), -1)
                for _, element := range submatchall {
                    pid = element[1]
                    dcli.Println("i", "PID:", pid)
                }
                pidInt, _ := strconv.Atoi(string(pid))
                process, errGo := os.FindProcess(pidInt)
                if errGo != nil {
                    dcli.Printf("e", "Failed to find process: %s\n", errGo)
                    dcli.Println("i", testType, "FAILED")
                    err = errType.FAIL
                    return
                } else {
                    errGo = process.Signal(syscall.Signal(0))
                    if errGo != nil {
                        dcli.Printf("i", "process.Signal on pid %d returned: %v\n", pid, errGo)
                        dcli.Println("i", testType, "FAILED", )
                        err = errType.FAIL
                        return
                    }
                }
                dcli.Println("i", testType, "RUNNING")
                return
            }
        }
    }

    dcli.Println("i", testType, "test has finished")

    yamlFile, errGo := ioutil.ReadFile("result.yaml")
    if errGo != nil {
        dcli.Printf("i", "%v \n", errGo)
        dcli.Println("i", "No yaml file,", testType, "RUNNING")
        err = errType.FAIL
        return
    }

    errGo = yaml.Unmarshal(yamlFile, &c)
    if errGo != nil {
        dcli.Printf("e", "Unmarshal: %v", errGo)
        err = errType.FAIL
        return
    }

    //c.getConf()
    dcli.Println("i", c.TestResult)

    return
}

func Snake(mode string, duration int, intLpbk int, verbose bool, snakeNum int, asicType string) (err int) {
    var filename string
    var errGo error

    mode = strings.ToUpper(mode)

    errGo = os.Chdir("/data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
    if errGo != nil {
        dcli.Println("e", errGo)
        return
    }

    filename = "result.yaml"
    errGo = os.Remove(filename)
    if errGo != nil {
        dcli.Println("i", errGo)
    } else {
        dcli.Println("i", "Yaml file deleted")
    }

    cmdStr := "./diag.exe"
    dcli.Println("d", "verbose")
    passSign := "Snake Done"
    failSign := "Snake Failed"
    verboseStr := "0"
    if verbose == true {
        verboseStr = "1"
    }

    if asicType == "ELBA" {
        err = runCmd.Run(passSign, failSign, cmdStr, "../elba/elb_arm_snake.tcl", mode, strconv.Itoa(duration), strconv.Itoa(intLpbk), verboseStr, strconv.Itoa(snakeNum))
    } else {
        err = runCmd.Run(passSign, failSign, cmdStr, "../giglio/gig_arm_snake.tcl", mode, strconv.Itoa(duration), strconv.Itoa(intLpbk), verboseStr, strconv.Itoa(snakeNum))
    }

    if err != errType.SUCCESS {
        dcli.Println("e", "Snake Test Failed!")
    }

    //if err != errType.SUCCESS {
    //    updateYaml("FAIL")
    //    return
    //}

    dcli.Println("i", "Snake Done")

    err = SnakePost(asicType)
    return
}

func SnakePost(asicType string) (err int) {
    var logFn string
    var resultStr string
    var errGo error
    //var expFound bool

    testDone := false

    if asicType == "ELBA" {
        logFn = "snake_elba.log"
    } else {
        logFn = "snake_giglio.log"
    }

    errGo = os.Chdir("/data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
    if errGo != nil {
        dcli.Println("e", errGo)
        return
    }

    // Parse log file
    dcli.Println("i", "Aanlyzing snake result")
    logFn = "/data/nic_arm/nic/asic_src/ip/cosim/tclsh/" + logFn

    file, errGo := os.Open(logFn)
    if errGo != nil {
        dcli.Println("e", "Failed to open log file", logFn, errGo)
        err = errType.FAIL
        updateYaml("FAIL")
        return
    }
    defer file.Close()

    // Three erros are expected
    //expErrList := make([]string, 5)
    //expErrList[0] = "elb0.ms.ms.int_groups.intreg: int_prp3_interrupt : 1 EN 1 hier_enabled 1"
    //expErrList[1] = "Unexpected int set: elb0.ms.ms"
    //expErrList[2] = "elb0.ms.ms.int_prp3.intreg: byte_read_interrupt"
    //expErrList[3] = "elb_ms_eos_int : MS ms_csr.int_prp3.intreg is non zero"
    //expErrList[4] = "elb_ms_eos_int : MS ms_csr.int_prp3.intreg.byte_read_interrupt is non zero"

    scanner := bufio.NewScanner(file)
    for scanner.Scan() {

        if errCode := scanner.Err(); errCode != nil {
            err = errType.FAIL
            break
        }

        readLine := scanner.Text()
        if strings.Contains(readLine, "ERROR ::") {
            //expErr := strings.SplitAfter(readLine, ":: ")
            //expErr := readLine

            //expFound = false
            //for i:=0; i<len(expErrList); i++ {
            //    if  strings.Contains(readLine, expErrList[i]) {
            //        expFound = true
            //    }
            //}

            //if expFound == true {
            //    dcli.Println("i", "Expected Error Found ::", expErr)
            //    continue
            //} else {
            //    dcli.Println("e", readLine)
            //    err = errType.FAIL
            //}
            dcli.Println("e", readLine)
            err = errType.FAIL

        }

        if strings.Contains(readLine, "Snake Done") {
            testDone = true
        }
    }

    if testDone == false {
        dcli.Println("e", "Snake test did not finish: no ending signature found")
        resultStr = "FAIL"
    } else {
        if err == errType.SUCCESS {
            dcli.Println("i", "SNAKE TEST PASSED")
            resultStr = "SUCCESS"
        } else {
            dcli.Println("i", "SNAKE TEST FAILED")
            resultStr = "FAIL"
        }
    }

    err = updateYaml(resultStr)
    dcli.Println("i", "YAML file updated")
    return
}

func updateYaml (resultStr string) (err int) {

    errGo := os.Chdir("/data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
    if errGo != nil {
        dcli.Println("e", "Failed to change dir!")
        err = errType.FAIL
        return
    }

    f, errGo := os.Create("result.yaml")
    if errGo != nil {
        dcli.Println("e", "Failed to open yaml file!")
        err = errType.FAIL
        return
    }

    resultStr = fmt.Sprintf("TEST_RESULT: %s", resultStr)
    _, errGo = f.Write([]byte(resultStr))
    if errGo != nil {
        dcli.Println("e", "Failed to open yaml file", errGo)
        err = errType.FAIL
        return
    }
    f.Sync() 
    f.Close()

    dcli.Println("i", "Result in YAML file")
    return

}

func L1(mode string, sn string) (err int) {
    var cmd string
    err = errType.SUCCESS

    errGo := os.Chdir("/data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
    if errGo != nil {
        dcli.Println("e", "Failed to change dir!")
        err = errType.FAIL
        return
    }

    dcli.Println("i", "Running L1 Test ...")
    cmd = "./diag.exe"
    passSign := "ARM L1 TESTS PASSED"
    failSign := "ARM L1 TESTS FAILED"
    err = runCmd.Run(passSign, failSign, cmd, "../elba/elb_arm_l1.tcl", sn, mode)

    if err != errType.SUCCESS {
        dcli.Println("e",  "L1 TEST FAILED!")
    } else {
        dcli.Println("i", "L1 TEST PASSED")
    }
    return 
}
