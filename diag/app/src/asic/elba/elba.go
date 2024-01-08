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
    "common/runCmd"
)

type TResult struct {
    TestResult string `yaml:"TEST_RESULT"`
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
    f.Close()
    runCmd.Run("", "", "sync")

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
