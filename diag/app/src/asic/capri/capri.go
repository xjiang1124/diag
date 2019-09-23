package capri

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
    SnakeResult string `yaml:"SNAKE_RESULT"`
}

var prbsLogFn = "aapl.log"

func Prbs(mode string, poly string, duration int) (err int) {
    var sbus string
    var speed string
    var errCount string

    var targetSpeedList []string
    var sbusList []uint64
    var cmd string

    var sbusPcieListNaples100 = []uint64{2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32}
    var sbusEthListNaples100 = []uint64{34,35,36,37,38,39,40,41}

    var sbusPcieListNaples25 = []uint64{18,20,22,24,26,28,30,32}
    var sbusEthListNaples25 = []uint64{34,38}

    var sbusIdx = 0

    err = errType.SUCCESS
    cardType := os.Getenv("CARD_TYPE")

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

    // Check result
    if mode == "PCIE" {
        targetSpeedList = []string{"15", "16", "17"}
        if (cardType == "NAPLES100") ||
           (cardType == "FORIO")     ||
           (cardType == "VOMERO") {
            sbusList = make([]uint64, 16)
            sbusList = sbusPcieListNaples100[:]
        } else if (cardType == "NAPLES25") ||
                  (cardType == "NAPLES25SWM") {
            sbusList = make([]uint64, 16)
            sbusList = sbusPcieListNaples25[:]
        } else {
            sbusList = make([]uint64, 16)
            sbusList = sbusPcieListNaples100[:]
        }
    } else if mode == "ETH" {
        targetSpeedList = []string{"25", "26", "27"}
        if (cardType == "NAPLES100") ||
           (cardType == "FORIO")     ||
           (cardType == "VOMERO") {
            sbusList = make([]uint64, 16)
            sbusList = sbusEthListNaples100[:]
        } else if (cardType == "NAPLES25") ||
                  (cardType == "NAPLES25SWM") {
            sbusList = make([]uint64, 16)
            sbusList = sbusEthListNaples25[:]

            sbusList = make([]uint64, 16)
            sbusList = sbusEthListNaples25[:]
        } else {
            sbusList = make([]uint64, 16)
            sbusList = sbusEthListNaples100[:]
        }
    } else {
        dcli.Println("e", "Invalid mode:", mode)
        err = errType.INVALID_PARAM
        return
    }
    cmd = "/data/nic_arm/aapl/aapl_prbs_all.sh"

    // For Eth PRBS, need to re-init serdes
    dcli.Println("d", "Eth init")
    if mode == "ETH" {
        err = runCmd.Run("AAPL ETH SERDES INIT DONE", "AAPL ETH SERDES RESET FAILED", cmd, mode, "INIT")
        if err != errType.SUCCESS {
            dcli.Println("e", "Failed to init Eth serdes!")
            return
        }
    }

    passSign := "AAPL PRBS DONE"
    failSign := "AAPL PRBS FAIL"

    err = runCmd.Run(passSign, failSign, cmd, mode, "PRBS", poly, strconv.Itoa(duration))

    if err != errType.SUCCESS {
        dcli.Println("e", "PRBS Test Failed!")
        return
    }

    re := regexp.MustCompile(`^\s+:([0-9a-f]+)\s+@\s+(\d+)\.\d+\s+1\.\d+\s+(\d+).*`)

    // Analyze PRBS log to determine pass/fail
    logFn := "/data/nic_arm/aapl/" + prbsLogFn

    file, errCode := os.Open(logFn)
    if errCode != nil {
        dcli.Println("e", "Failed to open log file", logFn)
        err = errType.FAIL
        return
    }
    defer file.Close()
    dcli.Println("i", sbusList, targetSpeedList)

    scanner := bufio.NewScanner(file)
    for scanner.Scan() {

        if errCode := scanner.Err(); errCode != nil {
            err = errType.FAIL
            break
        }

        match := re.MatchString(scanner.Text())
        if match == true {
            //submatchall := re.FindAllString(scanner.Text(), -1)
            submatchall := re.FindAllStringSubmatch(scanner.Text(), -1)
            for _, element := range submatchall {
                //dcli.Println("i", element)
                sbus = element[1]
                speed = element[2]
                errCount = element[3]
            }
            dcli.Printf("i", "sbus: 0x%s; speed: %s; errCount: %s\n", sbus, speed, errCount)

            sbusUint64, _ := strconv.ParseUint(sbus, 16, 64)
            if sbusUint64 != sbusList[sbusIdx] {
                dcli.Println("e", "Sbus index mismatch! Expected", sbusList[sbusIdx], "read", sbusUint64)
                err = errType.FAIL
            }

            speedMatch := misc.StringInSlice(speed, targetSpeedList)
            if speedMatch == false {
                dcli.Println("e", "Sbus", sbusUint64, "Speed mismatch! Expected", targetSpeedList, "read", speed)
                err = errType.FAIL
            }

            if errCount != "0" {
                dcli.Println("e", "Sbus", sbusUint64, "PRBS error found!", errCount)
                err = errType.FAIL
            }

            sbusIdx = sbusIdx + 1

        }
    }

    if sbusIdx < len(sbusList) {
        dcli.Println("e", "Did not find all sbus! expect", len(sbusList), "; found", sbusIdx)
        err = errType.FAIL
    }

    if err == errType.SUCCESS {
        dcli.Println("i", "MODE", "PRBS PASSED")
    } else {
        dcli.Println("i", "MODE", "PRBS FAILED")
    }

    return err
}


func SnakeCheck() (err int) {
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
                    dcli.Println("i", "SNAKE FAILED")
                    err = errType.FAIL
                    return
                } else {
                    errGo = process.Signal(syscall.Signal(0))
                    if errGo != nil {
                        dcli.Printf("i", "process.Signal on pid %d returned: %v\n", pid, errGo)
                        dcli.Println("i", "SNAKE FAILED")
                        err = errType.FAIL
                        return
                    }
                }
                dcli.Println("i", "SNAKE RUNNING")
                return
            }
        }
    }

    dcli.Println("i", "Snake test has finished")

    yamlFile, errGo := ioutil.ReadFile("result.yaml")
    if errGo != nil {
        dcli.Printf("i", "%v \n", errGo)
        dcli.Println("i", "SNAKE RUNNING")
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
    dcli.Println("i", c.SnakeResult)
    return
}

func Snake(mode string, duration int, verbose bool) (err int) {
    var filename string
    var errGo error

    mode = strings.ToUpper(mode)

    if (mode != "PCIE_LB") && (mode != "HBM_LB") {
        dcli.Println("e", "Invalid snake mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

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
    cmd := exec.Command(cmdStr, "snake_all.tcl", mode, strconv.Itoa(duration))
    if verbose == false {
        errGo = cmd.Run()
        if errGo != nil {
            dcli.Println("e", "Snake failed", errGo)
            return
        }
    } else {
	    passSign := "Snake Done"
	    failSign := "Snake Failed"
	    err = runCmd.Run(passSign, failSign, cmdStr, "snake_all.tcl", mode, strconv.Itoa(duration))

	    if err != errType.SUCCESS {
	        dcli.Println("e", "Snake Test Failed!")
	    }
    }

    if err != errType.SUCCESS {
        dcli.Println("e", "Snake Test Failed!")
    }

    if err != errType.SUCCESS {
        updateYaml("FAIL")
        return
    }

    dcli.Println("i", "Snake Done")

    err = SnakePost(mode)
    return
}

func SnakePost(mode string) (err int) {
    var logFn string
    var resultStr string
    var errGo error

    testDone := false

    mode = strings.ToUpper(mode)
    //logFn = "snake.log"

    if (mode != "PCIE_LB") && (mode != "HBM_LB") {
        dcli.Println("e", "Invalid snake mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    if mode == "PCIE_LB" {
        logFn = "snake_pcie.log"
    } else {
        logFn = "snake_hbm.log"
    }

    errGo = os.Chdir("/data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
    if errGo != nil {
        dcli.Println("e", errGo)
        return
    }

    // Parse log file
    // Three erros are expected
    // ERROR :: cap0.ms.em.int_groups.intreg: axi_interrupt : 1 EN 1 hier_enabled 1
    // ERROR :: Unexpected int set: cap0.ms.em
    // ERROR :: NX:: EOS:: interrupt-non-zero for reg:MS_M_AM_STS: 0x80
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

    expErr1 := "cap0.ms.em.int_groups.intreg: axi_interrupt : 1 EN 1 hier_enabled 1"
    expErr2 := "Unexpected int set: cap0.ms.em"
    expErr3 := "interrupt-non-zero for reg:MS_M_AM_STS:"
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {

        if errCode := scanner.Err(); errCode != nil {
            err = errType.FAIL
            break
        }

        readLine := scanner.Text()
        if strings.Contains(readLine, "ERROR ::") {
            expErr := strings.SplitAfter(readLine, ":: ")
            if strings.Contains(readLine, expErr1) ||
               strings.Contains(readLine, expErr2) ||
               strings.Contains(readLine, expErr3) {
                dcli.Println("i", "Expected Error Found ::", expErr[1])
                continue
            } else {
                dcli.Println("e", "ERROR ::", expErr[1])
                err = errType.FAIL
            }
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
    defer f.Close()

    resultStr = fmt.Sprintf("SNAKE_RESULT: %s", resultStr)
    _, errGo = f.Write([]byte(resultStr))
    if errGo != nil {
        dcli.Println("e", "Failed to open yaml file", errGo)
        err = errType.FAIL
        return
    }
    f.Sync()

    dcli.Println("i", "Result in YAML file")
    return

}

