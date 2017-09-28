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
    "common/diagEngine"
    "config"
    "common/errType"
    "common/misc"

    "hardware/hwvrm"
    "common/powermodule/tps53659"
    "common/powermodule/tps549a20"
    "common/powermodule/tpsAll"

    "common/tempsensor/tmp422"
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
    cli.Println("i", "============================")
    cli.Println("i", "CPU Status")

    cmdPath := config.DiagHostBinPath
    out, err := exec.Command(cmdPath+"sensors", "-A", "--no-adapter").Output()

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

    return errType.SUCCESS
}

func getVrmStatus() int {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659
    var tps549a20 tps549a20.TPS549A20

    var vrmTbl []hwvrm.VrmInfo
    cardName := os.Getenv("CARD_NAME")
    if cardName == "NAPLES" {
        vrmTbl = hwvrm.VrmTblNaples
    } else {
        cli.Println("f", "Unsupported card:", cardName)
        return errType.FAIL
    }

    cli.Println("i", "============================")
    cli.Println("i", "VRM Status")

    for _, vrm := range(vrmTbl) {
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }
        tps.DispStatus(vrm.Name)
    }

    cli.Println("i", "")
    return errType.SUCCESS
}

func dispTemp() (err int) {
    cli.Println("i", "============================")
    cli.Println("i", "Temp Sensor Readings")
    tmp422.DispTemp("TEMP_SENSOR")
    cli.Println("i", "")
    return
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

