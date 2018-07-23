package pex8716

import (
    "common/cli"
    "common/errType"
    "common/misc"
)

//func pexLpbkConfig1() (err int) {
//    var data uint32
//    var port byte
//
//    // Everything is configured based on base port 0
//    port = 0
//
//    // Configuration release
//    WriteReg(REG_CONF_RLS, 1, ACC_MODE_TP, port, BYTE_EN_ALL)
//    misc.SleepInSec(1)
//
//    //dataBuf := make([]byte, REG_WIDTH)
//    pattern0 := uint32(0x11223344)
//    pattern1 := uint32(0x11223344)
//    pattern2 := uint32(0x11223344)
//    pattern3 := uint32(0x11223344)
//    //pattern1 := uint32(0x55667788)
//    //pattern2 := uint32(0x11223344)
//    //pattern3 := uint32(0x55667788)
//
//    //clear 0x224 bit10 => Digital loopback slave mode
//    WriteReg(PHYSICALTEST0, 0, ACC_MODE_TP, port, BYTE_EN_ALL)
//
//    //write pattern to register
//    WriteReg(TESTPATTERN0, pattern0, ACC_MODE_TP, port, BYTE_EN_ALL)
//    WriteReg(TESTPATTERN1, pattern1, ACC_MODE_TP, port, BYTE_EN_ALL)
//    WriteReg(TESTPATTERN2, pattern2, ACC_MODE_TP, port, BYTE_EN_ALL)
//    WriteReg(TESTPATTERN3, pattern3, ACC_MODE_TP, port, BYTE_EN_ALL)
//
//    // write reg 0x208 
//    // set bit[24, 25] 
//    //    00b => Gen1
//    //    01b => Gen2
//    //    10b => Gen3
//    // clear [28, 29] => select port0
//    WriteReg(PORTCONTROL, 0x02000000, ACC_MODE_TP, port, BYTE_EN_ALL)
//    // Port 1 the same speed as port 0
//    WriteReg(PORTCONTROL, 0x12000000, ACC_MODE_TP, port, BYTE_EN_ALL)
//
//    //set reg 0x230 port 0 master lpbk
//    WriteReg(PORTCOMMAND, 0x10, ACC_MODE_TP, port, BYTE_EN_ALL)
//    misc.SleepInSec(1)
//
//    //read back to make sure lpbk is ready
//    var i uint = 0
//    for ; i < 100; i++ {
//        misc.SleepInUSec(1)
//        data, _ = ReadReg(PORTCOMMAND, ACC_MODE_TP, port, BYTE_EN_ALL)
//        if data & 0x80 != 0 {
//            break
//        }
//    }
//    if i == 10 {
//        cli.Println("e", "Port lpbk master state is not ready")
//        cli.Println("e", "##### PCIe TEST FAILED! #####")
//        err = errType.FAIL
//    }
//    cli.Println("i", "Configuration Done")
//    return
//}

/**
 * Mode: 0 - master loopback on port 0
 *       1 - master loopback on port 1
 */
func pexLpbkConfig(mode int) (err int) {
    var data uint32
    var port byte

    // Everything is configured based on base port 0
    port = 0

    // Configuration release
    WriteReg(REG_CONF_RLS, 1, ACC_MODE_TP, port, BYTE_EN_ALL)
    misc.SleepInSec(1)

    //dataBuf := make([]byte, REG_WIDTH)
    pattern0 := uint32(0x11223344)
    pattern1 := uint32(0x11223344)
    pattern2 := uint32(0x11223344)
    pattern3 := uint32(0x11223344)

    //clear 0x224 bit10 => Digital loopback slave mode
    WriteReg(PHYSICALTEST0, 0, ACC_MODE_TP, port, BYTE_EN_ALL)

    //write pattern to register
    WriteReg(TESTPATTERN0, pattern0, ACC_MODE_TP, port, BYTE_EN_ALL)
    WriteReg(TESTPATTERN1, pattern1, ACC_MODE_TP, port, BYTE_EN_ALL)
    WriteReg(TESTPATTERN2, pattern2, ACC_MODE_TP, port, BYTE_EN_ALL)
    WriteReg(TESTPATTERN3, pattern3, ACC_MODE_TP, port, BYTE_EN_ALL)

    // write reg 0x208 
    // set bit[24, 25] 
    //    00b => Gen1
    //    01b => Gen2
    //    10b => Gen3
    // clear [28, 29] => select port0
    WriteReg(PORTCONTROL, 0x02000000, ACC_MODE_TP, port, BYTE_EN_ALL)
    // Port 1 the same speed as port 0
    WriteReg(PORTCONTROL, 0x12000000, ACC_MODE_TP, port, BYTE_EN_ALL)

    //set reg 0x230 port 0 master lpbk
    if mode == 0 {
        WriteReg(PORTCOMMAND, 1, ACC_MODE_TP, port, BYTE_EN_ALL)
    } else {
        WriteReg(PORTCOMMAND, 0x10, ACC_MODE_TP, port, BYTE_EN_ALL)
    }
    misc.SleepInSec(1)

    //read back to make sure lpbk is ready
    var i uint = 0
    for ; i < 100; i++ {
        var rdyFlag uint32
        if mode == 0 {
            rdyFlag = 0x8
        } else {
            rdyFlag = 0x80
        }

        misc.SleepInUSec(500000)
        data, _ = ReadReg(PORTCOMMAND, ACC_MODE_TP, port, BYTE_EN_ALL)
        if data & rdyFlag != 0 {
            break
        }
    }
    if i == 100 {
        cli.Println("e", "Port lpbk master state is not ready")
        cli.Println("e", "##### PCIe TEST FAILED! #####")
        err = errType.FAIL
    }
    cli.Println("i", "Configuration Done")
    return
}

//func pexTestStart1() (err int) {
//    var port byte
//    //write reg 0x228 to set parallel lpbk, enable generator
//    //dataBuf[2] = 0x2
//    //dataBuf[3] = 0xFF
//    //err = WriteReg(PHYSICALTEST1, dataBuf)
//    //data := uint32(0xFF020000)
//    data := uint32(0xF0010000)
//    WriteReg(PHYSICALTEST1, data, ACC_MODE_TP, port, BYTE_EN_ALL)
//    cli.Println("i", "Test started")
//    return
//}

func pexTestStart(mode int) (err int) {
    var port byte
    //write reg 0x228 to set parallel lpbk, enable generator
    //dataBuf[2] = 0x2
    //dataBuf[3] = 0xFF
    //err = WriteReg(PHYSICALTEST1, dataBuf)
    //data := uint32(0xFF020000)
    var data uint32
    if mode == 0 {
        data = uint32(0xF020000)
    } else {
        data = uint32(0xF0010000)
    }
    WriteReg(PHYSICALTEST1, data, ACC_MODE_TP, port, BYTE_EN_ALL)
    cli.Println("i", "Test started")
    return
}

func pexTestStop() (err int) {
    var port byte
    var data uint32
    data = 0
    err = WriteReg(PHYSICALTEST1, data, ACC_MODE_TP, port, BYTE_EN_ALL)
    return
}

//func pexTestCheck1() (err int) {
//    var data uint32
//    var port byte
//    dataBuf := make([]byte, REG_WIDTH)
//
//    cli.Println("i", "Checking result")
//    for i:=8; i< 16; i++ {
//        // Lane select
//        dataBuf[3] = (byte)(i % 4)
//        data = misc.BytesToU32(dataBuf, 4)
//        reg := DIAGDATAQUAD0 + (uint32)((i/4)*4)
//
//        WriteReg(reg, data, ACC_MODE_TP, port, BYTE_EN_ALL)
//        data, _ = ReadReg(reg, ACC_MODE_TP, port, BYTE_EN_ALL)
//        dataBuf = misc.U32ToBytes(data)
//
//        if dataBuf[3] & 0x80 == 0 {
//            cli.Println("Serdes", i, "UTP is not sync")
//            err = errType.FAIL
//            continue
//        }
//        if dataBuf[2] != 0 {
//            cli.Println("i", "Serdes", i, "error count:", dataBuf[2], "error, expected", dataBuf[0], "actual", dataBuf[1])
//            cli.Printf("d", ", reg=0x%x, data=0x%x, databuf3=0x%x\n", reg, data, dataBuf[2])
//            err = errType.FAIL
//        } else {
//            cli.Println("i", "Serdes", i, "UTP passed!")
//        }
//    }
//    return
//}


func pexTestCheck(mode int) (err int) {
    var data uint32
    var port byte
    dataBuf := make([]byte, REG_WIDTH)

    var start int
    var end int
    var syncFlag byte
    if mode == 0 {
        start = 0
        end = 8
        syncFlag = 0x8
    } else {
        start = 8
        end = 16
        syncFlag = 0x80
    }

    cli.Println("i", "Checking result")
    for i:=start; i< end; i++ {
        // Lane select
        dataBuf[3] = (byte)(i % 4)
        data = misc.BytesToU32(dataBuf, 4)
        reg := DIAGDATAQUAD0 + (uint32)((i/4)*4)

        WriteReg(reg, data, ACC_MODE_TP, port, BYTE_EN_ALL)
        data, _ = ReadReg(reg, ACC_MODE_TP, port, BYTE_EN_ALL)
        dataBuf = misc.U32ToBytes(data)

        if dataBuf[3] & syncFlag == 0 {
            cli.Println("Serdes", i, "UTPnot synced")
            err = errType.FAIL
            continue
        }
        if dataBuf[2] != 0 {
            cli.Println("i", "Serdes", i, "error count:", dataBuf[2], "error, expected", dataBuf[0], "actual", dataBuf[1])
            cli.Printf("d", ", reg=0x%x, data=0x%x, databuf3=0x%x\n", reg, data, dataBuf[2])
            err = errType.FAIL
        } else {
            cli.Println("i", "Serdes", i, "UTP passed!")
        }
    }
    return
}

func pexTestCleanup(port byte) (err int) {
    WriteReg(PHYSICALTEST1, 0, ACC_MODE_TP, port, BYTE_EN_ALL)
    cli.Println("i", "Test done!")
    return
}

func UTPTest(devName string, duration int, mode int) (err int) {
    err = Open(devName)
    //curDura := 30
    if err != errType.SUCCESS {
        return
    }
    defer Close()

    err = pexLpbkConfig(mode)
    if err != errType.SUCCESS {
        return
    }

    pexTestStart(mode)

    cli.Println("i", "Precheck UTP")
    misc.SleepInSec(1)
    err = pexTestCheck(mode)
    if err != errType.SUCCESS {
        cli.Println("i", "UTP precheck failed, restart UTP test")
        pexTestStop()
        misc.SleepInSec(1)
        pexTestStart(mode)
    } else {
        cli.Println("i", "UTP precheck passed")
    }

    cli.Println("i", "Wait for", duration, "seconds")
    misc.SleepInSec(duration)

    err = pexTestCheck(mode)

    if err == errType.SUCCESS {
        cli.Println("i", "#### PCIe TEST PASSED! #####")
    } else {
        cli.Println("e", "#### PCIe TEST FAILED! #####")
    }

    pexTestStop()
    //pexTestCleanup()
    return
}


