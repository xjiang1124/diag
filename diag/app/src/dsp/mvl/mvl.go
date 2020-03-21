package main

import (
//    "flag"
    "common/spi"
    "common/diagEngine"
    "common/cli"
    "common/dcli"
    "common/errType"
    "common/misc"
    "config"
    "os"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "MVL"
)

const MVL_ID = 0x115
const MVL_ID_REG = 0x3

func Mvl_Init() {
    //in case no EEPROM
}

func Mvl_AccHdl(argList []string) {
    var data uint32

//    spi.MvlSmiRegRead(0x2, &data, 0x3)
    spi.MvlRegRead(MVL_ID_REG, &data, 0x10)
    cli.Printf("d", "cpld 0x%x", data)
    if (data >> 4) != MVL_ID {
        //retry: read one more time to avoid hal conflict
        spi.MvlRegRead(MVL_ID_REG, &data, 0x10)
        cli.Printf("d", "cpld the 2nd 0x%x", data)
        if (data >> 4) != MVL_ID {
            dcli.Println("e", "MVL acc test failed!")
            diagEngine.FuncMsgChan <- errType.FAIL
        } else {
            diagEngine.FuncMsgChan <- errType.SUCCESS
            dcli.Println("i", "MVL acc test passed!")
        }
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS
        dcli.Println("i", "MVL acc test passed!")
    }
    return
}

func Mvl_StubHdl(argList []string) {

    var data0, data1 uint32
    err := 0

    spi.MvlSmiRegWrite(0x16, 0x6, 0x3)
    misc.SleepInSec(1)
    spi.MvlSmiRegWrite(0x12, 0x18, 0x3)
    misc.SleepInSec(1)
    spi.MvlSmiRegWrite(0x10, 0x18, 0x3)
//    misc.SleepInSec(1)
//    spi.MvlSmiRegWrite(0x12, 0x18, 0x3)

    misc.SleepInSec(1)

    //check error counter
    spi.MvlSmiRegRead(0x11, &data0, 0x3)
    if (data0 & 0xFF) != 0 {
       dcli.Printf("e", "Port 3 stub test has error, counter reg 0x%x\n", data0)
       err = 1
    } else if data0 == 0 {
        dcli.Println("e", "Port 3 stub test has no packet")
        err = 1
    } else {
        dcli.Printf("i", "Port 3 stub test passed! 0x%x\n", data0)
    }
    spi.MvlSmiRegWrite(0x10, 0x0, 0x3)
    spi.MvlSmiRegWrite(0x12, 0x0, 0x3)
    spi.MvlSmiRegWrite(0x16, 0x0, 0x3)

    misc.SleepInSec(1)

    if os.Getenv("CARD_TYPE") == "NAPLES100" {
        spi.MvlSmiRegWrite(0x16, 0x6, 0x4)
        misc.SleepInSec(1)
        spi.MvlSmiRegWrite(0x12, 0x18, 0x4)
        misc.SleepInSec(1)
        spi.MvlSmiRegWrite(0x10, 0x18, 0x4)
    //    spi.MvlSmiRegWrite(0x12, 0x18, 0x4)

        misc.SleepInSec(1)

        spi.MvlSmiRegRead(0x11, &data1, 0x4)
        if (data1 & 0xFF) != 0 {
           dcli.Printf("e", "Port 4 stub test has error, counter reg 0x%x\n", data1)
           err = 1
        } else if data1 == 0 {
            dcli.Println("e", "Port 4 stub test has no packet")
            err = 1
        } else {
            dcli.Printf("i", "Port 4 stub test passed! 0x%x\n", data1)
        }

        spi.MvlSmiRegWrite(0x10, 0x0, 0x4)
        spi.MvlSmiRegWrite(0x12, 0x0, 0x4)
        spi.MvlSmiRegWrite(0x16, 0x0, 0x4)
        misc.SleepInSec(5)
    }

    dcli.Println("i", "MVL stub test cleanup")
    if err == 1 {
        dcli.Println("e", "MVL stub test failed!")
        diagEngine.FuncMsgChan <- errType.FAIL
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    }
    return
}

func Mvl_TrfHdl(argList []string) {
    var data uint32

    //get packet number, port mask
    //start traffic

    //check error counter
    if data != MVL_ID {
        dcli.Println("e", "MVL acc test failed!")
        diagEngine.FuncMsgChan <- errType.FAIL
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    }
    return
}

func Mvl_LedHdl(argList []string) {
    var data uint32

    //duration, port mask?

    spi.MvlRegRead(MVL_ID_REG, &data, 0x3)
    if data != MVL_ID {
        dcli.Println("e", "MVL acc test failed!")
        diagEngine.FuncMsgChan <- errType.FAIL
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    }
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["ACC"]    = Mvl_AccHdl
    diagEngine.FuncMap["STUB"]    = Mvl_StubHdl
    diagEngine.FuncMap["TRF"]    = Mvl_TrfHdl
    diagEngine.FuncMap["LED"]    = Mvl_LedHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
