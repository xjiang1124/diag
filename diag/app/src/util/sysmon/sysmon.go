package main

import (
    "bufio"
    "flag"
    //"fmt"
    "os"
    "os/exec"
    "regexp"
    "strings"

    "common/cli"
//    "common/diagEngine"
    "config"
    "common/errType"
    "common/misc"
    "hardware/hwinfo"

    //"device/tempsensor/tmp42123"
)

//var cardInfo diagEngine.CardInfo

var flagName string = config.DiagNicBinPath+"sysmon.flag"

func Init(procName string) {
    cli.Init("log_"+procName+".txt", config.OutputMode)
}

func exitContMode () {
    os.Remove(flagName)
}

func outputBuf(buf string) {
    scanner := bufio.NewScanner(strings.NewReader(buf))
    for scanner.Scan() {
        cli.Println("i", scanner.Text())
    }
}

func outputBufComp(buf string) {
    r, _ := regexp.Compile(".*(Package).*")
    scanner := bufio.NewScanner(strings.NewReader(buf))
    for scanner.Scan() {
        if r.MatchString(scanner.Text()) {
            cli.Println("i", scanner.Text())
        }
    }
}

func getCpuTemp(compFlag bool) int{

    // Check ARM/Intel CPU type
    out, err := exec.Command("/home/diag/diag/util/cpuinfo.sh").Output()

    cli.Println("i", "============================")
    cli.Println("i", "CPU Status")

    if string(out[0]) == "0" {
        out, err = exec.Command("/home/diag/diag/util/mvl_showtemp.sh").CombinedOutput()
        outputBuf(string(out))
    } else {
        out, err = exec.Command("sensors", "-A", "--no-adapter").Output()

        if err != nil {
            cli.Println("f", "failed to run sensor command")
            return errType.FAIL
        }
        if compFlag == true {
            outputBufComp(string(out))
        } else {
            outputBuf(string(out))
        }
        cli.Println("i", "")
    }
    return errType.SUCCESS
}

func getVrmStatus() int {
    cli.Println("i", "============================")
    cli.Println("i", "VRM Status")

    for dev, dispFunc := range(hwinfo.DispStaList) {
        dispFunc(dev)
    }

    cli.Println("i", "")
    return errType.SUCCESS
}

func dispTemp() (err int) {
    cli.Println("i", "============================")
    cli.Println("i", "Temp Sensor Readings")
    //tmp42123.DispTemp("TEMP_SENSOR")
    cli.Println("i", "To be implemented")
    return
}

func main () {
    // Initialization
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    Init(procName)

    // Define input arguement
    tPtr := flag.Bool("t", false, "Enable timebased system monitoring")
    qPtr := flag.Bool("q", false, "Quit continuous mode")
    intvPtr := flag.Int("intv", 30, "Time interval(in sec) to ready system status info")
    compPtr := flag.Bool("c", false, "Enable compact output")
    flag.Parse()

    if (*qPtr == true) {
        os.Remove(flagName)
        return
    }

    if (*tPtr == true) {
        //flagName := config.DiagNicBinPath+"sysmon.flag"
        f, err := os.OpenFile(flagName, os.O_RDWR|os.O_CREATE, 0755)
        if err != nil {
            cli.Println("e", err)
            return
        }
        if err := f.Close(); err != nil {
            cli.Println("e", err)
            return
        }
        for {
            _, err := os.Stat(flagName)
            if os.IsNotExist(err) {
                cli.Println("i", "Exit continuous mode")
                return
            }
            getVrmStatus()
            dispTemp()

            // Print CPU temp
            getCpuTemp(*compPtr)
            misc.SleepInSec(*intvPtr)
        }
    } else {
        getVrmStatus()
        dispTemp()
        // Print CPU temp
        getCpuTemp(*compPtr)
    }

}

