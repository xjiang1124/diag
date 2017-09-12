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
    "common/powermodule/tpsAll"
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

func getVrmStatus() int {
    var tps tpsAll.TpsAll
    var tps53659 tps53659.TPS53659

    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "VRM")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", outStr)


    for _, vrm := range(hwvrm.VrmTbl) {
        if vrm.Comp == "TPS53659" {
            tps = &tps53659
        }
        outStr = fmt.Sprintf(fmtNameStr, vrm.Name)

        dig, frac, _ := tps.ReadPout(vrm.I2cIdx, vrm.DevAddr, vrm.Channel)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadVout(vrm.I2cIdx, vrm.DevAddr, vrm.Channel)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadIout(vrm.I2cIdx, vrm.DevAddr, vrm.Channel)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadPin(vrm.I2cIdx, vrm.DevAddr, vrm.Channel)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadVin(vrm.I2cIdx, vrm.DevAddr, vrm.Channel)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadIin(vrm.I2cIdx, vrm.DevAddr, vrm.Channel)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        dig, frac, _ = tps.ReadTemp(vrm.I2cIdx, vrm.DevAddr, vrm.Channel)
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        cli.Println("i", outStr)
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
        getVrmStatus()
        // Print CPU temp
        getCpuTemp(*compPtr)
    }

}

