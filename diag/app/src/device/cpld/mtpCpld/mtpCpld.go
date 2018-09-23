package mtpCpld

//#cgo CFLAGS: -I. -I../../../../../include
//#cgo LDFLAGS: -lacc -lftd2xx
//#include <acc.h>
import "C"

import (
    "common/cli"
    "common/errType"
)

func JtagRest(slot uint) (err int) {
    if err = int(C.jtag_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG init failed!")
        return
    }
    err = int(C.jtag_reset(C.uint(slot)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG reset failed!")
    }
    return
}

func JtagEnable(slot uint) (err int) {
    if err = int(C.jtag_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG init failed!")
        return
    }
    err = int(C.jtag_enable(C.uint(slot)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG enable failed!")
    }
    return
}

func JtagWrite(slot uint, addr uint64, data uint, sse uint) (err int) {
    if err = int(C.jtag_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG init failed!")
        return
    }
    err = int(C.jtag_wr(C.uint(slot), C.ulonglong(addr), C.uint(data), C.uint(sse)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG write failed!")
    }
    return
}

func JtagRead(slot uint, addr uint64, sse uint) (data uint, err int) {
    if err = int(C.jtag_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG init failed!")
        return
    }
    var cData C.uint
    err = int(C.jtag_rd(C.uint(slot), C.ulonglong(addr), &cData, C.uint(sse)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG read failed!")
    } else {
        data = uint(cData)
        cli.Printf("i", "JTAG read data 0x%x\n", cData)
    }
    return
}

func CpldWrite(addr uint8, data uint8) (err int) {
    if err = int(C.spi_reg_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "SPI init failed!")
        return
    }
    if err = int(C.spi_wr(C.uchar(addr), C.uchar(data))); err > 0 {
        err = errType.FAIL
        cli.Println("e", "CPLD write failed!")
    }
    return
}

func CpldRead(addr uint8) (data uint8, err int) {
    if err = int(C.spi_reg_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "SPI init failed!")
        return
    }
    var cData C.uchar
    if err = int(C.spi_rd(C.uchar(addr), &cData)); err > 0 {
        err = errType.FAIL
        cli.Println("e", "CPLD read failed!")
    } else {
        data = uint8(cData)
        cli.Printf("i", "CPLD read at addr 0x%x with data 0x%x\n", addr, cData)
    }
    return
}

func CpldFlashProg(inst uint, inPutFile string) (err int) {
    if inst > 0 {
        err = int(C.spi_flash_init())
    } else {
        err = int(C.jtag_flash_init())
    }
    if err > 0 {
        err = errType.FAIL
        cli.Println("CpldFlashProg init failed!")
        return
    }
    err = int(C.cpld_program(C.CString(inPutFile)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("CPLD program failed!")
    }
    return
}

func CpldFlashRead(inst uint, outPutFile string) (err int) {
    if inst > 0 {
        err = int(C.spi_flash_init())
    } else {
        err = int(C.jtag_flash_init())
    }
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "CpldFlashRead init failed!")
        return
    }
    err = int(C.cpld_read(C.CString(outPutFile)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "CPLD read failed!")
    }
    return
}


func MvlWrite(inst uint, dev_addr uint, addr uint, data uint) (err int) {
    if err = int(C.spi_mdio_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO init failed!")
        return
    }
    if err = int(C.mdio_wr(C.uint(inst), C.uint(dev_addr), C.uint(addr), C.uint(data))); err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO write failed!")
    }
    return
}

func MvlRead(inst uint, dev_addr uint, addr uint) (data uint, err int) {
    if err = int(C.spi_mdio_init()); err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO init failed!")
        return
    }

    var cData C.uint
    if err = int(C.mdio_rd(C.uint(inst), C.uint(dev_addr), C.uint(addr), &cData)); err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO read failed!")
    } else {
        data = uint(cData)
        cli.Printf("i", "MDIO read data 0x%x\n", cData)
    }
    return
}

