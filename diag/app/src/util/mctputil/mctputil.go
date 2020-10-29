package main

import (
    "flag"
    "strings"
    "strconv"
    "common/cli"
    "common/errType"
    "protocol/smbusNew"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    "util/utillib"
    "device/cpld/nicCpldCommon"
)

func myUsage () {
    flag.PrintDefaults()
}

func gen_packet(mctpinfo nicCpldCommon.MctpCmd, addr byte) (data []byte){
    var pec byte

    dataBuf := make([]byte, 1)
    dataBuf[0] = (byte)(addr << 1 )
    dataBuf = append(dataBuf, (byte)(mctpinfo.Cmd))
    dataBuf = append(dataBuf, mctpinfo.Value...)
    if mctpinfo.Pec == true {
        pec = utillib.Calc_crc8(dataBuf, mctpinfo.Len + 2)
        dataBuf = append(dataBuf, pec)
    }
    dataBuf = append(dataBuf[:0], dataBuf[2:]...)

    return dataBuf
}

func main() {
    var byteCnt int
    var err int
    var devAddr byte 

    flag.Usage = myUsage

    udid_direct := flag.Bool("udid_direct", false, "Get UDID in direct mode")
    udid_gen    := flag.Bool("udid_gen", false, "Get UDID in general mode")
    reset       := flag.Bool("reset", false, "reset device")
    clearAP     := flag.Bool("clear_ap", false, "clear AP")
    setAddr     := flag.Bool("setAddr", false, "Set ARP address")
    slotPtr     := flag.Int("slot", 0, "UUT slot number")
    devAddrPtr  := flag.String("addr", "", "address to assign to the target")

    flag.Parse()

    slot := *slotPtr
    if slot <  1 || slot > 10 {
        cli.Println("e", "Invalid slot number or no slot number specified!")
        myUsage()
        return
    }
    uut := "UUT_"+strconv.Itoa(slot)

    lock, _ := hwinfo.PreUutSetup(uut)
    defer hwinfo.PostUutClean(lock)

    iInfo, err :=i2cinfo.GetI2cInfo("CPLD_MCTP")
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain I2C info of CPLD_MCTP")
        return
    }

    err = smbusNew.Open("CPLD_MCTP", iInfo.Bus, iInfo.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device CPLD_MCTP, err code=", err, " Bus=", iInfo.Bus, " devAddr=", iInfo.DevAddr)
        return
    }
    defer smbusNew.Close()

    if *udid_direct == true {
        dataBuf := make([]byte, nicCpldCommon.GetUDIDdirect.ResLen)
        byteCnt, err = smbusNew.ReadBlock("CPLD_MCTP", (uint64)(iInfo.DevAddr << 1), dataBuf)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to get udid in direct mode, err code=", err)
            return
        } else {
            for i:=0; i < byteCnt; i ++ {
                cli.Printf("i", "data[%d] = 0x%x\n", i, dataBuf[i])
            }
        }
        return
    }

    if *udid_gen == true {
        dataBuf := make([]byte, nicCpldCommon.GetUDIDgen.ResLen)
        byteCnt, err = smbusNew.ReadBlock("CPLD_MCTP", nicCpldCommon.GetUDIDgen.Cmd, dataBuf)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to get udid in general mode, err code=", err)
            return
        } else {
            for i:=0; i < byteCnt; i ++ {
                cli.Printf("i", "data[%d] = 0x%x\n", i, dataBuf[i])
            }
        }
        return
    }

    if ( *clearAP == true ) {
        dataBuf := make([]byte, nicCpldCommon.ClearAp.Len)
        dataBuf = gen_packet(nicCpldCommon.ClearAp, iInfo.DevAddr)
        err = smbusNew.WriteByte("CPLD_MCTP", nicCpldCommon.ClearAp.Cmd, dataBuf[0])
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to send clear ap command, err code=", err)
            return
        }
        return
    }

    if ( *reset == true ) {
        dataBuf := make([]byte, nicCpldCommon.Reset.Len)
        dataBuf = gen_packet(nicCpldCommon.Reset, iInfo.DevAddr)
        err = smbusNew.WriteByte("CPLD_MCTP", nicCpldCommon.Reset.Cmd, dataBuf[0])
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to send reset command, err code=", err)
            return
        } 
        return
    }

    if ( *setAddr == true ) {
        if *devAddrPtr == "" {
	    devAddr = iInfo.DevAddr << 1
        } else {
            devAddrStr := strings.ToLower(*devAddrPtr)
            devAddrStr = strings.Replace(devAddrStr, "0x", "", -1)
            value, hextrue := strconv.ParseUint(devAddrStr, 16, 8)
	    if hextrue != nil {
                cli.Println("e", "Please specify a hex number for device address ", *devAddrPtr)
                return
            }
            devAddr = (byte)(value)
        }
        dataBuf := make([]byte, nicCpldCommon.SetAddr.Len)
        byteCnt, err = smbusNew.ReadBlock("CPLD_MCTP", nicCpldCommon.GetUDIDgen.Cmd, dataBuf)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to get udid err code=", err)
            return
        }
        cli.Printf("i", "Changing MCTP device from address 0x%x to 0x%x\n",
                   dataBuf[nicCpldCommon.SetAddr.Len - 1], devAddr)
	dataBuf[nicCpldCommon.SetAddr.Len - 1] = (byte)(devAddr)
        dataBuf = gen_packet(nicCpldCommon.SetAddr, iInfo.DevAddr)
        dataBuf = append(dataBuf[:0], dataBuf[1:]...)
        byteCnt, err = smbusNew.WriteBlock("CPLD_MCTP", nicCpldCommon.SetAddr.Cmd, dataBuf)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to send set address command, err code=", err)
            return
        } 
        return
    }
   
    myUsage()   
}
