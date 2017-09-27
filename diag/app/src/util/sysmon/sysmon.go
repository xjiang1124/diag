package main

import (
    "bufio"
    "flag"
    "fmt"
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

    vrmTitle := []string {"VBOOT", "POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", outStr)

    for _, vrm := range(vrmTbl) {
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        } else if vrm.Comp == "TPS549A20" {
            tps = &tps549a20
        } else {
            continue
        }

        outStr = fmt.Sprintf(fmtNameStr, vrm.Name)

        dig, frac, _ := tps.ReadVboot(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadPout(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadVout(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadIout(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadPin(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadVin(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadIin(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadTemp(vrm.Name, vrm.Channel)
        if dig == 0 && frac == 0 {
            outStrTemp = "-.-"
        } else {
            outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        }
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        status, _ := tps.ReadStatus(vrm.Name, vrm.Channel)
        outStrTemp = fmt.Sprintf("0x%X", status)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        cli.Println("i", outStr)
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

