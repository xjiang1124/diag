package capri

import (
    "bufio"
    "os"
    "regexp"
    "strings"

    //"common/runCmd"
    "common/cli"
    "common/dcli"
    "common/errType"
)

//var aaplPath = "/data/aapl"
//var prbsLogFn = "aapl.a.log"
var prbsLogFn = "aapl.log"

func PciePrbs(poly string, duration int) (err int) {
    var sbus string
    var speed string
    var errCount string

    err = errType.SUCCESS

    poly = strings.ToUpper(poly)

    if (poly != "PRBS7"  ||
        poly != "PRBS9"  ||
        poly != "PRBS15" ||
        poly != "PRBS31") {
        dcli.Println("e", "Invalid POLY:", poly)
    }

    re := regexp.MustCompile(`^\s+:([0-9a-f]+)\s+@\s+(\d+)\.\d+\s+1\.\d+\s+(\d+).*`)

    // Analyze PRBS log to determine pass/fail
    logFn := "./" + prbsLogFn

    file, errCode := os.Open(logFn)
    if errCode != nil {
        err = errType.FAIL
        return
    }
    defer file.Close()

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
        }
    }

    return err
}

