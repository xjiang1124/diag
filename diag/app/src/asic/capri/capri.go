package capri

import (
    "bufio"
    "os"
    "regexp"
    "strconv"
    "strings"

    "common/runCmd"
    "common/dcli"
    "common/errType"
)

var prbsLogFn = "aapl.log"

func PciePrbs(poly string, duration int) (err int) {
    var sbus string
    var speed string
    var errCount string

    var targetSpeed string
    var sbusList []uint64

    var sbusListNaples100 = []uint64{2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32}
    var sbusIdx = 0

    err = errType.SUCCESS
    cardType := os.Getenv("CARD_TYPE")

    poly = strings.ToUpper(poly)

    if (poly != "PRBS7"  ||
        poly != "PRBS9"  ||
        poly != "PRBS15" ||
        poly != "PRBS31") {
        dcli.Println("e", "Invalid POLY:", poly)
    }

    cmd := "/data/nic_arm/aapl/aapl_prbs.sh"
    passSign := "AAPL PRBS DONE"
    failSign := "AAPL PRBS FAIL"

    err = runCmd.Run(passSign, failSign, cmd, "")
    dcli.Println("d", cmd, "done")

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

    // Check result
    targetSpeed = "16"
    if cardType == "NAPLES100" {
        sbusList = make([]uint64, 16)
        sbusList = sbusListNaples100[:]
    } else if cardType == "NAPLES25" {
        sbusList = make([]uint64, 16)
        sbusList = sbusListNaples100[8:]
    } else {
        sbusList = make([]uint64, 16)
        sbusList = sbusListNaples100[:]
    }
    dcli.Println("i", sbusList, targetSpeed)

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

            if speed != targetSpeed {
                dcli.Println("e", "Sbus", sbusUint64, "Speed mismatch! Expected", targetSpeed, "read", speed)
                err = errType.FAIL
            }

            if errCount != "0" {
                dcli.Println("e", "Sbus", sbusUint64, "PRBS error found!", errCount)
                err = errType.FAIL
            }

            sbusIdx = sbusIdx + 1

        }
    }

    return err
}

func Prbs(mode string, poly string, duration int) (err int) {
    var sbus string
    var speed string
    var errCount string

    var targetSpeed string
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
        targetSpeed = "16"
        if cardType == "NAPLES100" {
            sbusList = make([]uint64, 16)
            sbusList = sbusPcieListNaples100[:]
        } else if cardType == "NAPLES25" {
            sbusList = make([]uint64, 16)
            sbusList = sbusPcieListNaples25[:]
        } else {
            sbusList = make([]uint64, 16)
            sbusList = sbusPcieListNaples100[:]
        }
        cmd = "/data/nic_arm/aapl/aapl_prbs.sh"
    } else if mode == "ETH" {
        targetSpeed = "26"
        if cardType == "NAPLES100" {
            sbusList = make([]uint64, 16)
            sbusList = sbusEthListNaples100[:]
        } else if cardType == "NAPLES25" {
            sbusList = make([]uint64, 16)
            sbusList = sbusEthListNaples25[:]
        } else {
            sbusList = make([]uint64, 16)
            sbusList = sbusEthListNaples100[:]
        }
        cmd = "/data/nic_arm/aapl/eth_aapl_prbs.sh"
    } else {
        dcli.Println("e", "Invalid mode:", mode)
        err = errType.INVALID_PARAM
        return
    }

    passSign := "AAPL PRBS DONE"
    failSign := "AAPL PRBS FAIL"

    err = runCmd.Run(passSign, failSign, cmd, poly, strconv.Itoa(duration))
    dcli.Println("d", cmd, "done")

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
    dcli.Println("i", sbusList, targetSpeed)

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

            if speed != targetSpeed {
                dcli.Println("e", "Sbus", sbusUint64, "Speed mismatch! Expected", targetSpeed, "read", speed)
                err = errType.FAIL
            }

            if errCount != "0" {
                dcli.Println("e", "Sbus", sbusUint64, "PRBS error found!", errCount)
                err = errType.FAIL
            }

            sbusIdx = sbusIdx + 1

        }
    }

    return err
}


func Eth_Prbs(poly string, duration int) (err int) {
    return Prbs("ETH", poly, duration)
}

