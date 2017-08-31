package main

import (
    "bufio"
    "flag"
    "os"
    "os/exec"
    "regexp"
    "strings"

    "common/cli"
    "common/diagEngine"
    "config"
    "common/errType"
    "common/misc"
)

var cardInfo diagEngine.CardInfo

func Init(procName string) {
    cli.Init("log_"+procName+".txt", config.OutputMode)
    // Do not card DSP name here
    diagEngine.CardInfoInit(procName)
    cardInfo = diagEngine.GetCardInfo()
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
    cmdPath := config.DiagHostBinPath
    out, err := exec.Command(cmdPath+"sensors", "-A", "--no-adapter").Output()

    if err != nil {
        cli.Println("f", "failed to run sensor command")
        return errType.Fail
    }
    if compFlag == true {
        outputBufComp(string(out))
    } else {
        outputBuf(string(out))
    }

    return errType.Success
}


func main () {
    // Initialization
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    Init(procName)

    // Define input arguement
    tPtr := flag.Bool("t", false, "Enable timebased system monitoring")
    intvPtr := flag.Int("intv", 30, "Time interval(in sec) to ready system status info")
    compPtr := flag.Bool("c", false, "Enable compact output")
    flag.Parse()

    if (*tPtr == true) {
        for {
            // Print CPU temp
            getCpuTemp(*compPtr)
            misc.SleepInSec(*intvPtr)
        }
    } else {
        // Print CPU temp
        getCpuTemp(*compPtr)
    }

}

