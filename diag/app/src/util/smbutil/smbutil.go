package main

import (
    //"fmt"
    "flag"
    "strings"
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "common/errType"
    "util/utillib"
    "common/cli"
    "common/misc"
    "protocol/smbusNew"
    "unicode"
    "os"
)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage

    infoPtr     := flag.Bool(  "info", false, "Show I2C info table")
    devNamePtr  := flag.String("dev",  "",    "Device name")
    readPtr     := flag.Bool(  "rd",   false, "Read register value")
    readBlkPtr  := flag.Bool(  "rdb",  false, "Read register block value")
    writePtr    := flag.Bool(  "wr",   false, "Write register value")
    writeBlkPtr := flag.Bool(  "wrb",  false, "Write register block value")
    sendPtr     := flag.Bool(  "sd",   false, "Send byte")
    recvPtr     := flag.Bool(  "rb",   false, "Receive byte")
    modePtr     := flag.String("mode", "b",   "r/w mode: byte(b) or word(w)")
    addrPtr     := flag.Uint64("addr", 0,    "Register addr")
    dataPtr     := flag.Uint64("data", 0,    "Data value")
    numBytePtr  := flag.Uint64("nb",   0,    "Number of bytes")
    uutPtr      := flag.String("uut",  "UUT_NONE", "Target UUT")
    phyPtr      := flag.Uint64("phy", 0,    "Phy addr")
    smiPtr      := flag.Bool(  "smi", false, "Switch smi access")
    i2c16Ptr    := flag.Bool(  "i2c16", false, "16-bit addressing I2C mode")
    smbusPtr    := flag.String("smbus", "",    "Swap smbus to NIC or MTP on MALFA card")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    addr := *addrPtr
    data := *dataPtr
    mode := strings.ToUpper(*modePtr)
    numByte := *numBytePtr
    phyAddr := *phyPtr
    uut := strings.ToUpper(*uutPtr)
    swapName := strings.ToUpper(*smbusPtr)

    if len(uut) < 5 ||
       (unicode.IsDigit(rune(uut[4])) == false &&  uut != "UUT_NONE") {
        cli.Println("e", "Invalid UUT. UUT Needs to be UUT_NONE or UUT_#.",
                    "Entered UUT is", uut)
        return
    }

    if uut != "UUT_NONE" {
        lockName, err := hwinfo.PreUutSetup(uut)
        if err != errType.SUCCESS {
            return
        }
        defer hwinfo.PostUutClean(lockName)
    }

    // 16-bit internal addressing I2C
    if *i2c16Ptr == true {
        if *readPtr == true {
            utillib.I2c16_ReadWrite("READ", devName, addr, uint16(data), mode)
        }
        if *writePtr == true {
            utillib.I2c16_ReadWrite("WRITE", devName, addr, uint16(data), mode)
        }

        if *readBlkPtr == true {
            utillib.I2c16_ReadWriteBlk("READ_BLK", devName, addr, data, numByte)
            return
        }

        if *writeBlkPtr == true {
            utillib.I2c16_ReadWriteBlk("WRITE_BLK", devName, addr, data, numByte)
            return
        }

        return
    }

    if *readPtr == true {
        if devName == "SWITCH" {
            if *smiPtr == true {
                utillib.ReadWriteSmi("READ", phyAddr, addr, uint16(data), mode)
            } else {
                utillib.ReadWriteMdio("READ", phyAddr, addr, uint16(data), mode)
            }
        } else {
            utillib.ReadWriteSend("READ", devName, addr, uint16(data), mode)
        }
        return
    }

    if *writePtr == true {
        if devName == "SWITCH" {
            if *smiPtr == true {
                utillib.ReadWriteSmi("WRITE", phyAddr, addr, uint16(data), mode)
            } else {
                utillib.ReadWriteMdio("WRITE", phyAddr, addr, uint16(data), mode)
            }
        } else {
            utillib.ReadWriteSend("WRITE", devName, addr, uint16(data), mode)
        }
        return
    }

    if *sendPtr == true {
        utillib.ReadWriteSend("SEND", devName, addr, uint16(data), mode)
        return
    }

    if *recvPtr == true {
        utillib.ReadWriteSend("RECEIVE", devName, addr, uint16(data), mode)
        return
    }

    if *readBlkPtr == true {
        utillib.ReadWriteBlk("READ_BLK", devName, addr, data, numByte)
        return
    }

    if *writeBlkPtr == true {
        utillib.ReadWriteBlk("WRITE_BLK", devName, addr, data, numByte)
        return
    }

    if *infoPtr == true {
        i2cinfo.DispI2cInfoAll()
        return
    }

    if swapName != "" {
        // Only applicable to MALFA
        if uut == "UUT_NONE" || os.Getenv(uut) != "MALFA" {
            cli.Println("e", "Swap smbus to mtp/nic: only applicable to MALFA.",
                             "Entered UUT:", uut)
            return
        }

        if swapName == "NIC" {
            //Open smbus connection
            i2cSmbus, errSmbus := i2cinfo.GetI2cInfo("CPLD")
            if errSmbus != errType.SUCCESS {
                cli.Println("e", "Failed to obtain smbus info for CPLD")
                return
            }
            errSmbus = smbusNew.Open("CPLD", i2cSmbus.Bus, i2cSmbus.DevAddr)
            if errSmbus != errType.SUCCESS {
                cli.Println("e", "Failed to open smbus to CPLD:",
                            "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
                return
            }
            curVal, smbusRdErr := smbusNew.ReadByte("CPLD", uint64(0x1F))
            if smbusRdErr != errType.SUCCESS {
                cli.Println("e", "Failed to read smbus:",
                            "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
                return
            }
            // swap the smbus from mtp to nic: set cpld reg 0x1F bit#3
            curVal |= 0x4
            misc.SleepInUSec(10000) // delay for writing
            cli.DisableVerbose()
            _ = smbusNew.WriteByte("CPLD", uint64(0x1F), curVal)
            // don't check smbus error here because it's gone.
            cli.EnableVerbose()
            cli.Println("i", "smbus has been swapped to NIC")
        } else if swapName == "MTP" {
            // swap smbus from nic to mtp: power cycle the slot
            cli.Println("i", "Swap smbus from nic to mtp need to power cycle the slot.",
                             "Please carefully check and manually proceed.")
        } else {
            cli.Println("e", "Swap smbus=[NIC|MTP]. Entered smbus =", swapName)
        }
        return
    }

    myUsage()
}

