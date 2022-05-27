package main

import (
    "fmt"
    "flag"
    "os"
    "os/exec"
    "regexp"
    "strconv"

    "cardinfo"
    "common/cli"
    "common/errType"
    "common/misc"
    "device/cpld/naples100Cpld"
    "device/cpld/nicCpldCommon"
    "device/cpld/ortanoCpld"
    "hardware/hwdev"
)

var powerStatName = []string{"capri vdd", "capri avdd", "capri vdd arm", "capri vdd hbm", "capri emmc",
                            "nic p1v8", "nic p2v5", "efuse p2v5", "nic p3v3", "nic p5v0", "p12v", "pwr ok"}

var powerStatNameSWM = []string{"capri vdd", "capri avdd", "capri vdd arm", "capri vdd hbm", "capri emmc",
                            "nic p1v8", "nic p2v5", "efuse p2v5", "nic p3v3", "nic p5v0", "p12v", "pwr ok",
                            "VRD Fault", "alom cbl prsn", "temp trip"}

var OrtanoPowerFail0 = []string{"p12v", "p5v0_nic", "vdd_core", "vdd_arm", "ddr_vddq", "vdd_ddr", "p3v3_nic", "p1v8_nic"}
var OrtanoPowerFail1 = []string{"avdd_pcie", "avddh_pcie", "pll_avdd_pcie", "p0v8_nw", "pod_pll", "p3v3_aod", "ddr_vtt", "ddr_vpp"}
var OrtanoPowerFail2 = []string{"vdd_mac", "avdd_d6", "avddh_d6", "rtvdd", "pvdd", "tvddh", "p1v8_aod_se", "p1v8_aod_pll"}

func init() {
}

func uutPresent(uutName string) (data byte, present bool) {
    devName := "CPLD"
    addr := uint64(naples100Cpld.REG_ID)

    present = false

    cli.DisableVerbose()
    data, err := hwdev.NaplesCpldRdBlind(devName, addr, uutName)

    if err == errType.SUCCESS {
        present = true
        cli.EnableVerbose()
        return
    }

    data, err = hwdev.NaplesCpldRdBlind("CPLD_ALT", addr, uutName)
    if err == errType.SUCCESS {
        present = true
        cli.EnableVerbose()
        return
    }

    data, err = hwdev.NaplesCpldRdBlind("CPLD_ADAP", addr, uutName)
    if err == errType.SUCCESS {
        // If adaptor present, turn on CPLD SMB and read ID
        data, err = hwdev.NaplesCpldRd("CPLD_ADAP", 0x1, uutName)
        if err == errType.SUCCESS {
            present = true
            cli.EnableVerbose()
            return
        }
        data &^=(0x02)
        data  |=(0x04)
        err = hwdev.NaplesCpldWr("CPLD_ADAP", 0x1, data, uutName)
        if err != errType.SUCCESS {
            present = false
            cli.EnableVerbose()
            return

        }

        data, err = hwdev.NaplesCpldRdBlind("CPLD_ALT", addr, uutName)
        if err == errType.SUCCESS {
            present = true
            cli.EnableVerbose()
            return
        }
    }

    cli.EnableVerbose()

    return
}

func InterposerID(uutName string) (data byte, err int) {
    devName := "CPLD"
    addr := uint64(naples100Cpld.REG_INTERPOSER_ID)

    data, err = hwdev.NaplesCpldRd(devName, addr, uutName)

    return
}

func present() (err int) {
    var presentStr string
    var out []byte
    var outStr string
    var errGo error
    var uutFieldStr string
    var PN string
    var SN string
    var submatchall [][]string
    var interpoID byte

    maxUut := 10
    prsntNoneStr := "UUT_NONE"
    regexPN := regexp.MustCompile(`.*Part Number\s+([\d\-]+).*`)
    regexAN := regexp.MustCompile(`.*Assembly Number\s+([\d\-]+).*`)
    regexSN := regexp.MustCompile(`.*Serial Number\s+([\dA-Za-z]+).*`)

    for i := 1; i <= maxUut; i++ {
        uutName := "UUT_"+strconv.Itoa(i)
        data, present := uutPresent(uutName)
        PN = "N/A"
        SN = "N/A"

        if present == true {
            switch data {
            case nicCpldCommon.ID_NAPLES100:
                presentStr = "NAPLES100"
            case nicCpldCommon.ID_NAPLES100IBM:
                presentStr = "NAPLES100IBM"
            case nicCpldCommon.ID_NAPLES100DELL:
                presentStr = "NAPLES100DELL"
            case nicCpldCommon.ID_NAPLES25:
                presentStr = "NAPLES25"
            case nicCpldCommon.ID_NAPLES25OCP:
                presentStr = "NAPLES25OCP"
            case nicCpldCommon.ID_NAPLES25SWM:
                presentStr = "NAPLES25SWM"
            case nicCpldCommon.ID_NAPLES25WFG:
                presentStr = "NAPLES25WFG"
            case nicCpldCommon.ID_NAPLES25SWM_DELL:
                presentStr = "NAPLES25SWMDELL"
            case nicCpldCommon.ID_NAPLES25SWM_833:
                presentStr = "NAPLES25SWM833"
            case nicCpldCommon.ID_FORIO:
                presentStr = "FORIO"
            case nicCpldCommon.ID_VOMERO:
                presentStr = "VOMERO"
            case nicCpldCommon.ID_VOMERO2:
                presentStr = "VOMERO2"
            case nicCpldCommon.ID_ORTANO:
                presentStr = "ORTANO"
            case nicCpldCommon.ID_ORTANO2:
                presentStr = "ORTANO2"
            case nicCpldCommon.ID_ORTANO2A:
                presentStr = "ORTANO2A"
            case nicCpldCommon.ID_ORTANO2I:
                presentStr = "ORTANO2I"
            case nicCpldCommon.ID_LACONA_DELL:
                presentStr = "LACONADELL"
            case nicCpldCommon.ID_LACONA32_DELL:
                presentStr = "LACONA32DELL"
            case nicCpldCommon.ID_LACONA:
                presentStr = "LACONA"
            case nicCpldCommon.ID_LACONA32:
                presentStr = "LACONA32"
            case nicCpldCommon.ID_POMONTE:
                presentStr = "POMONTE"
            case nicCpldCommon.ID_POMONTE_DELL:
                presentStr = "POMONTEDELL"
            case nicCpldCommon.ID_NAPLES100HPE:
                presentStr = "NAPLES100HPE"
            case nicCpldCommon.ID_BIODONA_D4:
                presentStr = "BIODONA_D4"
            case nicCpldCommon.ID_BIODONA_D5:
                presentStr = "BIODONA_D5"
            case nicCpldCommon.ID_NAPLES_MTP:
                presentStr = "NAPLES_MTP"
            default:
                presentStr = "Unknown"
            }
            interpoID, err = InterposerID(uutName)
            if  err  != errType.SUCCESS {
                interpoID = 0
            }
        } else {
            presentStr = prsntNoneStr
            interpoID = 0
        }

        // prepare PN and SN from fru eeprom
        if  presentStr != prsntNoneStr {
            if os.Getenv(uutName) != presentStr {
                os.Setenv(uutName, presentStr)
            }
            uutFieldStr = "-uut=" + uutName
            out, errGo = exec.Command("/home/diag/diag/util/eeutil", "-field=PN", "-disp", uutFieldStr).Output()
            if errGo != nil {
                cli.Println("e", errGo)
                err = errType.FAIL
            }
            outStr = string(out)
            //cli.Println("i", "Debugging: output of eeutil PN reading -", outStr)
            if regexPN.MatchString(outStr) {
                submatchall = regexPN.FindAllStringSubmatch(outStr, -1)
                for _, element := range submatchall {
                    PN  = element[1]
                }
            } else if regexAN.MatchString(outStr) { // using Assembly Number
                submatchall = regexAN.FindAllStringSubmatch(outStr, -1)
                for _, element := range submatchall {
                    PN  = element[1]
                }
            } else {
                PN = "NotProgrammed"
            }

            out, errGo = exec.Command("/home/diag/diag/util/eeutil", "-field=SN", "-disp", uutFieldStr).Output()
            if errGo != nil {
                cli.Println("e", errGo)
                err = errType.FAIL
            }
            outStr = string(out)
            //cli.Println("i", "Debugging: output of eeutil SN reading -", outStr)
            if regexSN.MatchString(outStr) {
                submatchall = regexSN.FindAllStringSubmatch(outStr, -1)
                for _, element := range submatchall {
                    SN  = element[1]
                }
            } else {
                SN = "NotProgrammed"   // not programmed, empty slot show "N/A"
            }
        }

        if interpoID != 0 {
            cli.Printf("i", "UUT_%-2d  %-12s  %-13s  %s  INTERPOSER=%d\n", i, presentStr, PN, SN, interpoID)
        } else {
            cli.Printf("i", "UUT_%-2d  %-12s  %-13s  %s\n", i, presentStr, PN, SN)
        }
    }
    return
}

func getPowerGoodOrtano(uutName string) (powerGood bool) {
    addr := uint64(ortanoCpld.REG_ASIC_PIN_STAT1)

    stat1, err := hwdev.NaplesCpldRd("CPLD", addr, uutName)
    if err != errType.SUCCESS {
        powerGood = false
    } else {
        if stat1 & 0x8 > 0 {
            powerGood = true
        } else {
            powerGood = false
        }
    }
    return
}

func getPowerGood(uutName string) (powerGood bool) {
    addr := uint64(naples100Cpld.REG_POWER_STAT1)

    stat1, err := hwdev.NaplesCpldRd("CPLD", addr, uutName)
    if err != errType.SUCCESS {
        powerGood = false
    } else {
        if (stat1 & 0x8) != 0 && (stat1 & 0x1) != 0 {
            powerGood = true
        } else {
            powerGood = false
        }
    }
    return
}

func powerStatusCheck(slot int) (err int) {
    uutName := "UUT_"+strconv.Itoa(slot)
    var powerGood bool

    cardType := os.Getenv(uutName)
    fmt.Printf(" CardType=%s\n", cardType)

    cli.DisableVerbose()

    err, asicType := cardinfo.GetAsicType(cardType)
    if asicType == "ELBA" {
        powerGood = getPowerGoodOrtano(uutName)
    } else {
        powerGood = getPowerGood(uutName)
    }
    cli.EnableVerbose()

    if powerGood {
        cli.Printf("i", "UUT_%-15d     power good\n", slot)
    } else {
        cli.Printf("i", "UUT_%-15d     power failure\n", slot)
    }

    return
}

func mtpIdentify() (err int) {
    var rev string
    var fmtStr string = "export MTP_REV=\"REV_%s\"\n"

    out, errGo := exec.Command("/home/diag/diag/util/eeutil", "-dev=fru", "-disp").Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
    }
    outStr := string(out)
    re :=regexp.MustCompile(`.*HW_MAJOR_REV\s+(\d+).*`)
    match :=re.MatchString(outStr)
    if match == true {
        submatchall := re.FindAllStringSubmatch(outStr, -1)
        for _, element := range submatchall {
            rev  = element[1]
        }
    } else {
        rev = "NONE"
    }
    cli.Println("i", "Rev:", rev)

    file, errGo := os.OpenFile("/home/diag/diag/log/board_env.txt", os.O_CREATE|os.O_WRONLY|os.O_SYNC|os.O_APPEND, 0666)
    if errGo != nil {
        cli.Println("e", "Cannot create file", err)
    }
    defer file.Close()

    fmt.Fprintf(file, fmtStr, rev)

    return
}

func sysDetect() (err int) {
    var presentStr string
    var fmtStr string = "export UUT_%d=\"%s\"\n"

    //file, err1 := os.Create("/home/diag/diag/log/board_env.txt")
    file, err1 := os.OpenFile("/home/diag/diag/log/board_env.txt", os.O_CREATE|os.O_WRONLY|os.O_SYNC|os.O_APPEND, 0666)
    if err1 != nil {
        cli.Println("e", "Cannot create file", err)
    }
    defer file.Close()

    maxUut := 10
    prsntNoneStr := "UUT_NONE"
    for i := 1; i <= maxUut; i++ {
        uutName := "UUT_"+strconv.Itoa(i)
        data, present := uutPresent(uutName)

        if present == true {
            switch data {
            case nicCpldCommon.ID_NAPLES100:
                presentStr = "NAPLES100"
            case nicCpldCommon.ID_NAPLES100IBM:
                presentStr = "NAPLES100IBM"
            case nicCpldCommon.ID_NAPLES100HPE:
                presentStr = "NAPLES100HPE"
            case nicCpldCommon.ID_NAPLES100DELL:
                presentStr = "NAPLES100DELL"
            case nicCpldCommon.ID_NAPLES25:
                presentStr = "NAPLES25"
            case nicCpldCommon.ID_NAPLES25OCP:
                presentStr = "NAPLES25OCP"
            case nicCpldCommon.ID_NAPLES25SWM:
                presentStr = "NAPLES25SWM"
            case nicCpldCommon.ID_NAPLES25WFG:
                presentStr = "NAPLES25WFG"
            case nicCpldCommon.ID_FORIO:
                presentStr = "FORIO"
            case nicCpldCommon.ID_VOMERO:
                presentStr = "VOMERO"
            case nicCpldCommon.ID_VOMERO2:
                presentStr = "VOMERO2"
            case nicCpldCommon.ID_ORTANO:
                presentStr = "ORTANO"
            case nicCpldCommon.ID_ORTANO2:
                presentStr = "ORTANO2"
            case nicCpldCommon.ID_ORTANO2A:
                presentStr = "ORTANO2A"
            case nicCpldCommon.ID_ORTANO2I:
                presentStr = "ORTANO2I"
            case nicCpldCommon.ID_NAPLES25SWM_DELL:
                presentStr = "NAPLES25SWMDELL"
            case nicCpldCommon.ID_NAPLES25SWM_833:
                presentStr = "NAPLES25SWM833"
            case nicCpldCommon.ID_BIODONA_D4:
                presentStr = "BIODONA_D4"
            case nicCpldCommon.ID_BIODONA_D5:
                presentStr = "BIODONA_D5"
            case nicCpldCommon.ID_NAPLES_MTP:
                presentStr = "NAPLES_MTP"
            case nicCpldCommon.ID_LACONA_DELL:
                presentStr = "LACONADELL"
            case nicCpldCommon.ID_LACONA:
                presentStr = "LACONA"
            case nicCpldCommon.ID_LACONA32_DELL:
                presentStr = "LACONA32DELL"
            case nicCpldCommon.ID_LACONA32:
                presentStr = "LACONA32"
            case nicCpldCommon.ID_POMONTE_DELL:
                presentStr = "POMONTEDELL"
            case nicCpldCommon.ID_POMONTE:
                presentStr = "POMONTE"
            default:
                presentStr = "Unknown"
            }
        } else {
            presentStr = prsntNoneStr
        }
        fmt.Fprintf(file, fmtStr, i, presentStr)
    }
    return
}

func statusDump(slot int)  {
    devName := "CPLD"
    uutName := "UUT_"+strconv.Itoa(slot)

    cpldRegList := []uint64{0, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1E, 0x20, 0x21, 0x26, 0x27, 0x28, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x30, 0x31, 0x32, 0x49, 0x50, 0x80}

    cli.Println("i", "Dumping CPLD registers for slot", slot)
    for _, cpldReg := range cpldRegList {
        val, _ := hwdev.NaplesCpldRd(devName, cpldReg, uutName)
        cli.Printf("i", "Addr: 0x%02x; Value: 0x%02x\n", cpldReg, val)
    }

    return
}

func dispPowerStatus(pwrStatName[] string, reg_value byte) {
    for i := 0; i < len(pwrStatName); i++ {
        cli.Printf("i","%-15s%d\n", pwrStatName[i], (reg_value >> uint(i)) & 1)
    }
}

func powerStatusDumpOrtano(uutName string)  {

    cli.DisableVerbose()
    stat0, _ := hwdev.NaplesCpldRd("CPLD", uint64(ortanoCpld.REG_POWER_STAT0), uutName)
    stat1, _ := hwdev.NaplesCpldRd("CPLD", uint64(ortanoCpld.REG_POWER_STAT1), uutName)
    stat2, _ := hwdev.NaplesCpldRd("CPLD", uint64(ortanoCpld.REG_POWER_STAT2), uutName)
    cli.EnableVerbose()

    dispPowerStatus(OrtanoPowerFail0, stat0) 
    dispPowerStatus(OrtanoPowerFail1, stat1) 
    dispPowerStatus(OrtanoPowerFail2, stat2) 

    return
}

func powerStatusDump(slot int)  {
    devName := "CPLD"
    uutName := "UUT_"+strconv.Itoa(slot)
    cardType := os.Getenv(uutName)
    pwrStatName := powerStatName
    fmt.Printf(" CardType=%s\n", cardType)

    if cardType == "NAPLES25SWM" {
        pwrStatName = powerStatNameSWM
    } else if cardType == "ORTANO" || cardType == "ORTANO2" || cardType == "ORTANO2A" || cardType == "ORTANO2I" {
        powerStatusDumpOrtano(uutName)
        return
    }

    cli.DisableVerbose()
    stat0, _ := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_POWER_STAT0), uutName)
    stat1, _ := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_POWER_STAT1), uutName)
    cli.EnableVerbose()

    for i := 0; i < len(pwrStatName); i++ {
        if(i < 8) {
            cli.Printf("i","%-15s%d\n", pwrStatName[i], (stat0 >> uint(i)) & 1)
        } else {
            cli.Printf("i","%-15s%d\n", pwrStatName[i], (stat1 >> uint(i - 8)) & 1)
        }
    }

    return
}

func esecureStatusDump(slot int)  {
    devName := "CPLD"
    uutName := "UUT_"+strconv.Itoa(slot)

    //cli.DisableVerbose()
    esecStat, _     := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_ASIC_PSST), uutName)
    esecLiveStat, _ := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_ASIC_PIN_STAT_0), uutName)
    //puffErrLmt, _   := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_PUFF_ERR_LMT), uutName)
    puffErrCnt, _   := hwdev.NaplesCpldRd(devName, uint64(naples100Cpld.REG_PUFF_ERR_CNT), uutName)
    cli.EnableVerbose()

    cli.Printf("i", "%-15s0x%x\n", "ESEC Setting:", esecStat)
    cli.Printf("i", "%-15s0x%x\n", "ESEC Live Status:", esecLiveStat)
    //cli.Printf("i", "%-15s0x%x\n", "Puff Err Limit:", puffErrLmt)
    cli.Printf("i", "%-15s0x%x\n", "Puff Err Cnt:", puffErrCnt)

    return
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage

    presentPtr := flag.Bool("present", false, "Show UUT present status")
    envPtr     := flag.Bool("env", false, "Detect/set environment")
    psPtr      := flag.Bool("ps", false, "Power Status")
    slotPtr    := flag.Int("slot", 0, "Slot Number")
    powDumpPtr := flag.Bool("pw", false, "Power state dump")
    esecPtr    := flag.Bool("esec", false, "Escure status dump")
    stsPtr     := flag.Bool("sts", false, "Entire status dump")
    mtpIdPtr   := flag.Bool("mtpid", false, "Identify MTP reversion")

    flag.Parse()

    slot := *slotPtr

    if *presentPtr == true {
        present()
        return
    }

    if *envPtr == true {
        sysDetect()
        misc.SleepInSec(1)
        mtpIdentify()
        return
    }

    if *psPtr == true {
        powerStatusCheck(slot)
        return
    }

    if *powDumpPtr == true {
        powerStatusDump(slot)
        return
    }

    if *esecPtr == true {
        esecureStatusDump(slot)
        return
    }

    if *stsPtr == true {
        statusDump(slot)
        return
    }

    if *mtpIdPtr == true {
        mtpIdentify()
        return
    }

    myUsage()
}

