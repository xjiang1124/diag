package main

import (
    "common/cli"
    "common/misc"
    "common/errType"
    "device/cpld"
    "hardware/hwdev"
    "util/utillib"
    "hardware/i2cinfo"
//    "device/cpld"
//    "util/utillib"
)

func mvlIntTest() (err int) {
    var data uint8
    var i uint
    for i = 0; i < 2; i++ {
        //clear int
        _, err = cpld.MvlRead(i, 0x1b, 0x0);
        if err != errType.SUCCESS {
            cli.Println("e", "Mvl swtich ", i, "mdio read failed!")
            return
        }
        data, err = cpld.CpldRead(0x5)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        if data & (1 << i) != 0 {
            cli.Println("e", "Marvell switch ", i, "interrup is not cleaed!")
        }

        //test
        data, err = cpld.CpldRead(0x1)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        data |= 1 << (i+1)
        err = cpld.CpldWrite(0x1, data)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        misc.SleepInSec(1)
        data &= ^(1 << (i+1))
        err = cpld.CpldWrite(0x1, data)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        misc.SleepInSec(1)
        data, err = cpld.CpldRead(0x5)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        if data & (1 << i) == 0 {
            cli.Println("i", "##### Marvell switch", i, "TEST FAILED! #####")
        } else {
            cli.Println("i", "##### Marvell switch", i, "TEST PASSED! #####")
        }

        //clear on source again
        _, err = cpld.MvlRead(i, 0x1b, 0x0);
        if err != errType.SUCCESS {
            cli.Println("e", "Mvl swtich ", i, "mdio read failed!")
            return
        }
    }

    return
}

func wdtIntTest() (err int) {
    var data uint8
    data, err = cpld.CpldRead(0x5)
    if err != errType.SUCCESS {
        cli.Println("e", "CPLD read failed!")
        return
    }
    if data & (1 << 3) != 0 {
        cli.Println("e", "Watch dog interrup is not cleaed!")
        return
    }

    data, err = cpld.CpldRead(0xe)
    if err != errType.SUCCESS {
        cli.Println("e", "CPLD read failed!")
        return
    }
    data |= 0x8
    err = cpld.CpldWrite(0xe, data)
    if err != errType.SUCCESS {
        cli.Println("e", "CPLD write failed!")
        return
    }

    misc.SleepInSec(35)

    data, err = cpld.CpldRead(0x5)
    if err != errType.SUCCESS {
        cli.Println("e", "CPLD read failed!")
        return
    }
    if data & 0x8 == 0 {
        cli.Println("e", "##### Watch dog TEST FAILED! #####")
    } else {
        cli.Println("i", "##### Watch dog TEST PASSED! #####")
    }

    data, err = cpld.CpldRead(0xe)
    if err != errType.SUCCESS {
        cli.Println("e", "CPLD read failed!")
        return
    }
    data &= ^uint8(0x8)
    err = cpld.CpldWrite(0xe, data)
    if err != errType.SUCCESS {
        cli.Println("e", "CPLD write failed!")
        return
    }

    return
}

func uutPowTest(uutMask uint) (err int) {
    var p12vReg, p3v3Reg, pretReg, errMask uint8 = 0x10, 0x12, 0x14, 0
    var i, p12vData, p3v3Data, present uint8

    for i = 0; i < 10; i++ {
        if uutMask & (1 << i) == 0 {
            continue;
        }
        //enable P3V3 and P12V
        p12vData, err = cpld.CpldRead(p12vReg + i/8)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        p12vData |= 1 << (i % 8)
        err = cpld.CpldWrite(p12vReg + i/8, p12vData)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        p3v3Data, err = cpld.CpldRead(p3v3Reg + i/8)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        p3v3Data |= 1 << (i % 8)
        err = cpld.CpldWrite(p3v3Reg + i/8, p3v3Data)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        misc.SleepInUSec(500)
        //check present bit
        present, err = cpld.CpldRead(pretReg + i/8)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        if present & 1 << (i % 8) == 0 {
            errMask |= 1 << i
            cli.Println("e", "12V was off, 3V3 was on, no present bit, inst", i, "failed!")
        }

        //turn off 12V
        p12vData &= ^(1 << (i % 8))
        err = cpld.CpldWrite(p12vReg + i/8, p12vData)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        misc.SleepInUSec(500)
        //check present bit
        present, err = cpld.CpldRead(pretReg + i/8)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        if present & 1 << (i % 8) != 0 {
            errMask |= 1 << i
            cli.Println("e", "12V was off, 3V3 was on, still hold present bit, inst", i, "failed!")
        }

        //turn on 12V, turn off 3.3V
        p12vData |= 1 << (i % 8)
        err = cpld.CpldWrite(p12vReg + i/8, p12vData)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        p3v3Data &= ^(1 << (i % 8))
        err = cpld.CpldWrite(p3v3Reg + i/8, p3v3Data)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        misc.SleepInUSec(500)
        //check present bit
        present, err = cpld.CpldRead(pretReg + i/8)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        if present & 1 << (i % 8) != 0 {
            errMask |= 1 << i
            cli.Println("e", "12V was on, 3V3 was off, still hold present bit, inst", i, "failed!")
        }

        //turn off 12V, turn off 3.3V
        p12vData &= ^(1 << (i % 8))
        err = cpld.CpldWrite(p12vReg + i/8, p12vData)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        misc.SleepInUSec(500)
        //check present bit
        present, err = cpld.CpldRead(pretReg + i/8)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        if present & 1 << (i % 8) != 0 {
            errMask |= 1 << i
            cli.Println("e", "12V was off, 3V3 was off, still hold present bit, inst", i, "failed!")
        }
    }

    if errMask > 0 {
        cli.Println("e", "##### UUT Power TEST FAILED! #####")
        err = int(errMask)
        return
    }
    cli.Println("i", "#####", "UUT Power", "TEST PASSED! #####")
    return
}

func peRstTest(uutMask uint) (err int) {
    var peRstReg uint8 = 0x16
    var errMask	int = 0
    var peRstData, i uint8
    for i = 0; i < 10; i++ {
        if uutMask & (1 << i) == 0 {
            continue;
        }
        peRstData, err = cpld.CpldRead(peRstReg + i/8)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD read failed!")
            return
        }
        peRstData |= 1 << (i % 8)
        err = cpld.CpldWrite(peRstReg + i/8, peRstData)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
        err = hwdev.DispStatus("NAPLES_MTP", "UUT_NONE")
        if err == errType.SUCCESS {
            errMask |= 1 << i
            cli.Println("e", "I2C is accessible when PeRst is set, inst", i, "failed")
        }

        //unreset peRst
        peRstData &= ^(1 << (i % 8))
        err = cpld.CpldWrite(peRstReg + i/8, peRstData)
        if err != errType.SUCCESS {
            cli.Println("e", "CPLD write failed!")
            return
        }
    }
    if errMask > 0 {
        cli.Println("e", "##### PERST TEST FAILED! #####")
        err = errMask
        return
    }
    cli.Println("i", "#####", "PERST", "TEST PASSED! #####")
    return
}

func pcsTest(index uint) (err int) {
    var inst, phy, addr, data uint
    // nic -> MTP
    inst = index / 5
    phy = (index % 5) + 0x10
    addr = 0x1
    data, _ = cpld.MvlRead(inst, phy, uint(addr))
    if data >> 14 == 0x3 {
        cli.Println("i", "NIC to MTP PCS is sync'd!")
    } else {
        cli.Println("e", "NIC to MTP PCS is NOT sync'd! PCS control register is 0x", data)
        err = 1
    }
    // MTP -> nic
    i2cinfo.SwitchI2cTblByIndex(index)
    phy = 0xD
    addr = 0x11
    data, _ = utillib.ReadWriteSmi("READ", uint64(phy), uint64(addr), uint16(data), "b")
    if (data & 0x400 > 0) && (data != 0xffff) {
        cli.Println("i", "NIC to MTP PCS is sync'd!")
    } else {
        cli.Println("e", "MTP to MTP PCS is NOT sync'd! Status register is 0x", data)
        err = 1
    }
    if err > 0 {
        cli.Println("e", "##### PCS TEST FAILED! #####")
    } else {
        cli.Println("i", "##### PCS TEST PASSED! #####")
    }
    return
}

