package main

import (
    "fmt"
    "flag"
    "os"
    "os/exec"
    "regexp"
    "strconv"
    "strings"
    "cardinfo"
    "common/cli"
    "common/errType"
    "common/misc"
    "device/cpld/naples100Cpld"
    "device/cpld/nicCpldCommon"
    "device/cpld/ortanoCpld"
    "device/cpld/salinaCpld"
    "device/fpga/panareafpga"
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
var FpgaPowerFail3   = []string{"fpga_mgtavcc_pg", "fpga_mgtavtt_pg"}
var GinestraPowerFail0 = []string{"p12v", "p5v0_nic", "vdd_core", "vdd_arm", "pmic_pwr/ddr_vddq", "vdd_ddr", "p3v3_nic", "p1v8_nic"}
var GinestraPowerFail1 = []string{"avdd", "avddh", "rtvdd", "tvddh", "gilo_efuse"}
var GinestraPowerFail2 = []string{"qsfp1_pwr", "qsfp2_pwr", "p12v_hotswap", "gilo_vrd_hot", "gilo_ddr_pmic_gsi", "clock_buf_los"}
var SalinaPowerFail = []string{"vrd_hot", "vrd_fault", "dram0_pwr_fail", "dram1_pwr_fail"}
var SalinaPowerFailCode = []string{"PWR OK", "P12V Fail", "P5V Fail", "P3v3_NIC Fail", "P1V8_NIC Fail", "VDD_12 Fail", 
                                   "VDD_075 Fail", "VDD_CORE Fail", "VDDQ Fail", "VDD_DDR Fail", "VDD_ARM Fail", "GPIO8", 
                                   "CORE_PLL lock Fail", "CPU_PLL lock Fail", "FLASH_PLL lock Fail", "QSPI_RST _L timeout", "DPU warm boot", "ROT warm boot", 
                                   "MTP warm boot", "GPIO3 PC", "ROT PC", "MTP PC", "WDT timeout", "CSR PW Not OK"}

func init() {
}

func uutPresent(uutName string) (data byte, present bool) {
    devName := "CPLD"
    addr := uint64(naples100Cpld.REG_ID)

    present = false

    if os.Getenv("CARD_TYPE") == "MTP_PANAREA" {
        present, _ = panareafpga.SLOTpresentUUT(uutName)
        //Currently there is no way to read the CPLD ID on GelsoP.  We need to get USB working in order to do that.
        //For now on Panarea, just hard code the CPLD ID since GelsoP is our only card right now.
        if present == true {
            data = 0x83
        } else {
            data = 0x00
        }
        return
    }

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

    cli.DisableVerbose()
    data, err = hwdev.NaplesCpldRd(devName, addr, uutName)
    cli.EnableVerbose()

    return
}

func CapabilityID(uutName string) (data byte, err int) {
    devName := "CPLD"
    addr := uint64(naples100Cpld.REG_CAPABILITY_ID)

    cli.DisableVerbose()
    data, err = hwdev.NaplesCpldRd(devName, addr, uutName)
    cli.EnableVerbose()

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
    var capabilityID byte

    maxUut := 10
    prsntNoneStr := "UUT_NONE"
    regexPN := regexp.MustCompile(`.*Part Number\s+([\dA-Za-z\-]+).*`)
    regexAN := regexp.MustCompile(`.*Assembly Number\s+([\dA-Za-z\-]+).*`)
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
            case nicCpldCommon.ID_ORTANO2AC:
                presentStr = "ORTANO2AC"
            case nicCpldCommon.ID_ORTANO2I:
                presentStr = "ORTANO2I"
            case nicCpldCommon.ID_ORTANO2S:
                presentStr = "ORTANO2S"
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
            case nicCpldCommon.ID_GINESTRA_D4:
                presentStr = "GINESTRA_D4"
            case nicCpldCommon.ID_GINESTRA_D5:
                presentStr = "GINESTRA_D5"
            case nicCpldCommon.ID_MALFA:
                presentStr = "MALFA"
            case nicCpldCommon.ID_POLLARA:
                presentStr = "POLLARA"
            case nicCpldCommon.ID_LENI:
                presentStr = "LENI"
            case nicCpldCommon.ID_LENI48G:
                presentStr = "LENI48G"
            case nicCpldCommon.ID_LINGUA:
                presentStr = "LINGUA"
            case nicCpldCommon.ID_NAPLES_MTP:
                presentStr = "NAPLES_MTP"
            case nicCpldCommon.ID_GELSOP:
                presentStr = "GELSOP"
            default:
                presentStr = "Unknown"
            }
            if presentStr == "ORTANO2I" {
                interpoID, err = InterposerID(uutName)
                if  err  != errType.SUCCESS {
                    interpoID = 0
                }
            } else if presentStr == "ORTANO2S" {
                capabilityID, err = CapabilityID(uutName)
                if  err  != errType.SUCCESS {
                    capabilityID = 0
                }
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

            //Temporary work around for Gelsop.   Due to Microcontroller h/w bug, we cannot have an eeprom to program right now
            //As a work around to get scripting efforts moving, we will just hard code the part number and serial number 
            if(presentStr == "GELSOP") {
                PN = "101-P00001-00A"
                SN = "serialnumber"+strconv.Itoa(i)
            } else {
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
        }

        if presentStr == "ORTANO2I" {
            cli.Printf("i", "UUT_%-2d  %-12s  %-13s  %s  INTERPOSER=%d\n", i, presentStr, PN, SN, interpoID)
        } else if presentStr == "ORTANO2S" {
            cli.Printf("i", "UUT_%-2d  %-12s  %-13s  %s  CAPABILITY=%d\n", i, presentStr, PN, SN, capabilityID)
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

func getPowerGoodSalina(uutName string) (powerGood bool) {
    addr := uint64(salinaCpld.REG_RESET_CODE)

    stat1, err := hwdev.NaplesCpldRd("CPLD", addr, uutName)
    if err != errType.SUCCESS {
        powerGood = false
    } else {
        if stat1 == 0 {
            powerGood = true
        } else if 0x1 <= stat1 && stat1 <= 0xa {
            // power shutoff due to power rail failure
            powerGood = false
        } else if stat1 == 0x16 || stat1 == 0x18 {
            // power shutoff due to functional failure
            powerGood = false
        } else {
            // resets are not power failure in diag test
            powerGood = true
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
    if asicType == "ELBA" || asicType == "GIGLIO" {
        powerGood = getPowerGoodOrtano(uutName)
    } else if asicType == "SALINA" {
        powerGood = getPowerGoodSalina(uutName)
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
            case nicCpldCommon.ID_ORTANO2AC:
                presentStr = "ORTANO2AC"
            case nicCpldCommon.ID_ORTANO2I:
                presentStr = "ORTANO2I"
            case nicCpldCommon.ID_ORTANO2S:
                presentStr = "ORTANO2S"
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
            case nicCpldCommon.ID_GINESTRA_D4:
                presentStr = "GINESTRA_D4"
            case nicCpldCommon.ID_GINESTRA_D5:
                presentStr = "GINESTRA_D5"
            case nicCpldCommon.ID_MALFA:
                presentStr = "MALFA"
            case nicCpldCommon.ID_POLLARA:
                presentStr = "POLLARA"
            case nicCpldCommon.ID_LENI:
                presentStr = "LENI"
            case nicCpldCommon.ID_LENI48G:
                presentStr = "LENI48G"
            case nicCpldCommon.ID_LINGUA:
                presentStr = "LINGUA"
            case nicCpldCommon.ID_GELSOP:
                presentStr = "GELSOP"
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
    if slot < 1 || slot > 10 {
        cli.Println("e", "Invalid slot number. Expected: [1,10]. Entered:", slot)
        return
    }

    uutName := "UUT_"+strconv.Itoa(slot)
    _, present := uutPresent(uutName)
    if present != true {
        cli.Printf("e", "Slot %d: card not present/power-on.\n", slot)
        return
    }

    asic_type := os.Getenv("ASIC_TYPE")
    var cpldRegList []uint64
    if asic_type == "SALINA" {
        cpldRegList = []uint64{0, 0x01, 0x02, 0x10, 0x11, 0x12, 0x14, 0x16, 0x18, 0x19, 0x1A, 0x1E, 0x20, 0x21, 0x22, 0x26, 0x27, 0x28, 0x2B, 0x2C, 0x2D, 0x30, 0x31, 0x32, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x80}
    } else {
        cpldRegList = []uint64{0, 0x01, 0x02, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1E, 0x20, 0x21, 0x26, 0x27, 0x28, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x30, 0x31, 0x32, 0x49, 0x50, 0x80, 0x99, 0x9A}
    }

    cli.Println("i", "Dumping CPLD registers for slot", slot)
    for _, cpldReg := range cpldRegList {
        val, _ := hwdev.NaplesCpldRd(devName, cpldReg, uutName)
        cli.Printf("i", "Addr: 0x%02x; Value: 0x%02x\n", cpldReg, val)
    }

    return
}

func dispPowerStatus(pwrStatName[] string, reg_value byte) {
    for i := 0; i < len(pwrStatName); i++ {
        cli.Printf("i","%-18s%d\n", pwrStatName[i], (reg_value >> uint(i)) & 1)
    }
}

func dispPowerStatusCode(pwrStatName[] string, reg_value byte) {
    if reg_value >= 0 && reg_value < 0x18 {
        cli.Printf("i","Reset code:%-7s%d\n", pwrStatName[reg_value], reg_value)
    } else {
        cli.Printf("i","Invalid power reset code\n")
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

func powerStatusDumpSalina(uutName string)  {

    cli.DisableVerbose()
    stat0, _ := hwdev.NaplesCpldRd("CPLD", uint64(salinaCpld.REG_RESET_CODE), uutName)
    stat1, _ := hwdev.NaplesCpldRd("CPLD", uint64(salinaCpld.REG_POWER_FAULT), uutName)
    cli.EnableVerbose()

    dispPowerStatusCode(SalinaPowerFailCode, stat0) 
    stat1 = stat1 & 0x3c
    stat1 = stat1 >> 2 
    dispPowerStatus(SalinaPowerFail, stat1) 

    return
}

func powerStatusDumpFpga(uutName string)  {

    cli.DisableVerbose()
    stat3, _ := hwdev.NaplesCpldRd("CPLD", 0x33, uutName)
    cli.EnableVerbose()

    dispPowerStatus(FpgaPowerFail3, stat3)

    return
}

func powerStatusDumpGinestra(uutName string)  {

    cli.DisableVerbose()
    stat0, _ := hwdev.NaplesCpldRd("CPLD", uint64(ortanoCpld.REG_POWER_STAT0), uutName)
    stat1, _ := hwdev.NaplesCpldRd("CPLD", uint64(ortanoCpld.REG_POWER_STAT1), uutName)
    stat2, _ := hwdev.NaplesCpldRd("CPLD", uint64(ortanoCpld.REG_POWER_STAT2), uutName)
    cli.EnableVerbose()

    dispPowerStatus(GinestraPowerFail0, stat0)
    dispPowerStatus(GinestraPowerFail1, stat1)
    dispPowerStatus(GinestraPowerFail2, stat2)

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
    } else if cardType == "ORTANO" || cardType == "ORTANO2" || cardType == "ORTANO2A" || cardType == "ORTANO2AC" || cardType == "ORTANO2I" || cardType == "ORTANO2S" {
        powerStatusDumpOrtano(uutName)
        return
    } else if cardType == "LACONA32DELL" || cardType == "LACONA32" || cardType == "POMONTEDELL" || cardType == "POMONTE" {
        powerStatusDumpOrtano(uutName)
        powerStatusDumpFpga(uutName)
        return
    } else if cardType == "GINESTRA_D4" || cardType == "GINESTRA_D5" {
        powerStatusDumpGinestra(uutName)
        return
    } else if cardType == "MALFA" || cardType == "POLLARA" || cardType == "LENI" || cardType == "LENI48G" || cardType == "LINGUA" {
        powerStatusDumpSalina(uutName)
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
    cpuPtr     := flag.Bool("cpu", false, "Show CPU information")
    ddrPtr     := flag.Bool("ddr", false, "Show DDR information")
    hdparmPtr  := flag.Bool("hdparm", false, "Show Harddisk basic information")

    flag.Parse()

    slot := *slotPtr
    var out []byte
    var errGo error

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

    if *cpuPtr == true {
        out, errGo = exec.Command("bash", "-c", "sudo -SE <<< \"lab123\" dmidecode -t processor | grep Version:").Output()
        if errGo != nil {
            cli.Println("e", errGo)
        } else {
            strArray := strings.Split(string(out[:]), ":")
            outStr := strings.TrimSpace(strArray[1])
            cli.Println("i", "CPU Model:", outStr)
        }

        // CPU temperature
        out, errGo = exec.Command("bash", "-c", "sensors").Output()
        if errGo != nil {
            cli.Println("e", errGo)
        } else {
            strArray := strings.Split(string(out[:]), "\n")
            cli.Println("i", "")
            cli.Println("i", "Temperature Sensors:")
            for i := 0; i < len(strArray); i++ {
                if !strings.Contains(strArray[i], "ERROR") {
                    cli.Println("i", strings.TrimSpace(strArray[i]))
                }
            }
        }

        return
    }

    if *ddrPtr == true {
        out, errGo = exec.Command("bash", "-c", "sudo -SE <<< \"lab123\" dmidecode -t memory | grep \"Number Of Devices\"").Output()
        if errGo != nil {
            cli.Println("e", errGo)
        } else {
            cli.Println("i", strings.TrimSpace(string(out[:])))
        }

        //cmdStr := string("dmidecode -t memory | grep -A32 \"Memory Device\" | grep -e \"Memory Device\" -e \"Size:\" -e \"Bank Locator:\" -e \"Type:\" -e \"Speed:\" -e \"Manufacturer:\" | grep -v \"Config\" | grep -v \"Volatile\" | grep -v \"Cache\" | grep -v \"Logical\"")
        cmdStr := string("sudo -SE <<< \"lab123\" dmidecode -t memory | grep -A32 \"Memory Device\" | grep -e \"Memory Device\" -e \"Size:\" -e \"Bank Locator:\" -e \"Type:\" -e \"Speed:\" -e \"Manufacturer:\" | grep -v \"Volatile\" | grep -v \"Cache\" | grep -v \"Logical\"")
        out, errGo = exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Println("e", errGo)
        } else {
            strArray := strings.Split(string(out[:]), "\n")
            for i := 0; i < len(strArray); i++ {
                //cli.Println("i", "\n", string(out[:]))
                cli.Println("i", strArray[i])
            }
        }

        return
    }

    if *hdparmPtr == true {
        cmdStr := string("sudo -SE <<< \"lab123\" fdisk -l | grep -e Disk | grep -e sectors | grep -iv loop | grep -iv usb | grep -iv nvme")
        out, errGo = exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil || len(out) == 0 {
            cmdStr = string("sudo -SE <<< \"lab123\" fdisk -l | grep -e Disk | grep -e sectors | grep -e nvme")
            out, errGo = exec.Command("bash", "-c", cmdStr).Output()
            if errGo != nil {
                cli.Println("e", errGo)
                return
            }
        }
        cli.Println("i", strings.TrimSpace(string(out[:])))

        strArray := strings.Split(string(out[:]), ":")
        hdName := strings.Split(strArray[0], " ")

        if !strings.Contains(hdName[1], "nvme") {
            cmdStr = string("sudo -SE <<< \"lab123\" hdparm -I " + strings.TrimSpace(hdName[1]) + " | grep -A4 \"ATA device\"")
        } else {
            cmdStr = string("sudo -SE <<< \"lab123\" nvme list -o json " + strings.TrimSpace(hdName[1]) + " | grep -e \"ModelNumber\x5c\x7cSerialNumber\x5c\x7cProductName\x5c\x7cFirmware\"")
        }
        out, errGo = exec.Command("bash", "-c", cmdStr).Output()
        if errGo != nil {
            cli.Println("e", errGo)
        } else {
            strArray = strings.Split(string(out[:]), "\n")
            for i := 0; i < len(strArray); i++ {
                cli.Println("i", strings.Trim(strArray[i], ","))
            }
        }

        return
    }

    myUsage()
}

