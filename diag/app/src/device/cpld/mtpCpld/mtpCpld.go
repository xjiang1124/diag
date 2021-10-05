package mtpCpld

//#cgo CFLAGS: -I. -I../../../../../include
//#cgo LDFLAGS: -ldl
//#include <acc.h>
//#include <ftd2xx.h>
//#include <dlfcn.h>
//#include <sys/types.h>
//#include <unistd.h>
//
//int
//com_jtag_init(void *f)
//{
//   int (*jtag_init)();
//
//   jtag_init = (int (*)())f;
//   return jtag_init();
//}
//
//int
//com_jtag_reset(void *f, uint slot)
//{
//   int (*jtag_reset)(uint);
//
//   jtag_reset = (int (*)(uint))f;
//   return jtag_reset(slot);
//}
//
//int
//com_jtag_enable(void *f, uint slot)
//{
//   int (*jtag_enable)(uint);
//
//   jtag_enable = (int (*)(uint))f;
//   return jtag_enable(slot);
//}
//
//int
//com_jtag_wr(void *f, uint slot, unsigned long long address, uint data, uint flag)
//{
//   int (*jtag_wr)(uint, unsigned long long, uint, uint);
//
//   jtag_wr = (int (*)(uint, unsigned long long, uint, uint))f;
//   return jtag_wr(slot, address, data, flag);
//}
//
//int
//com_jtag_rd(void *f, uint slot, unsigned long long address, uint *data, uint flag)
//{
//   int (*jtag_rd)(uint, unsigned long long, uint *, uint);
//
//   jtag_rd = (int (*)(uint, unsigned long long, uint *, uint))f;
//   return jtag_rd(slot, address, data, flag);
//}
//
//int
//com_spi_reg_init(void *f)
//{
//   int (*spi_reg_init)();
//
//   spi_reg_init = (int (*)())f;
//   return spi_reg_init();
//}
//
//int
//com_spi_wr(void *f, u_char address, u_char data)
//{
//   int (*spi_wr)(u_char, u_char);
//
//   spi_wr = (int (*)(u_char, u_char))f;
//   return spi_wr(address, data);
//}
//
//int
//com_spi_rd(void *f, u_char address, u_char *data)
//{
//   int (*spi_rd)(u_char, u_char *);
//
//   spi_rd = (int (*)(u_char, u_char *))f;
//   return spi_rd(address, data);
//}
//
//int
//com_spi_flash_init(void *f)
//{
//   int (*spi_flash_init)();
//
//   spi_flash_init = (int (*)())f;
//   return spi_flash_init();
//}
//
//int
//com_jtag_flash_init(void *f)
//{
//   int (*jtag_flash_init)();
//
//   jtag_flash_init = (int (*)())f;
//   return jtag_flash_init();
//}
//
//int
//com_cpld_program(void *f, char *filename)
//{
//   int (*cpld_program)(u_char *);
//
//   cpld_program = (int (*)(u_char *))f;
//   return cpld_program(filename);
//}
//
//int
//com_cpld_read(void *f, char *filename)
//{
//   int (*cpld_read)(u_char *);
//
//   cpld_read = (int (*)(u_char *))f;
//   return cpld_read(filename);
//}
//
//int
//com_spi_mdio_init(void *f)
//{
//   int (*spi_mdio_init)();
//
//   spi_mdio_init = (int (*)())f;
//   return spi_mdio_init();
//}
//
//int
//com_mdio_wr(void *f, uint inst, uint dev_address, uint address, uint data)
//{
//   int (*mdio_wr)(uint, uint, uint, uint);
//
//   mdio_wr = (int (*)(uint, uint, uint, uint))f;
//   return mdio_wr(inst, dev_address, address, data);
//}
//
//int
//com_mdio_rd(void *f, uint inst, uint dev_address, uint address, uint *data)
//{
//   int (*mdio_rd)(uint, uint, uint, uint *);
//
//   mdio_rd = (int (*)(uint, uint, uint, uint *))f;
//   return mdio_rd(inst, dev_address, address, data);
//}
import "C"

import (
    "common/cli"
    "common/errType"
    "unsafe"
)

func JtagRest(slot uint) (err int) {
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    jtag_init := C.dlsym(handle, C.CString("jtag_init"))
    if jtag_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    jtag_reset := C.dlsym(handle, C.CString("jtag_reset"))
    if jtag_reset == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_jtag_init(jtag_init)); err > 0 {
        err = errType.FAIL
	cli.Println("e", "JTAG init failed!")
	return
    }
    err = int(C.com_jtag_reset(jtag_reset, C.uint(slot)))
    if err > 0 {
        err = errType.FAIL
	cli.Println("e", "JTAG reset failed!")
    }
    return
}

func JtagEnable(slot uint) (err int) {
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    jtag_init := C.dlsym(handle, C.CString("jtag_init"))
    if jtag_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    jtag_enable := C.dlsym(handle, C.CString("jtag_enable"))
    if jtag_enable == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_jtag_init(jtag_init)); err > 0 {
        err = errType.FAIL
	cli.Println("e", "JTAG init failed!")
	return
    }
    err = int(C.com_jtag_enable(jtag_enable, C.uint(slot)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG enable failed!")
    }
    return
}

func JtagWrite(slot uint, addr uint64, data uint, sse uint) (err int) {
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    jtag_init := C.dlsym(handle, C.CString("jtag_init"))
    if jtag_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    jtag_wr := C.dlsym(handle, C.CString("jtag_wr"))
    if jtag_wr == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_jtag_init(jtag_init)); err > 0 {
        err = errType.FAIL
	cli.Println("e", "JTAG init failed!")
	return
    }
    err = int(C.com_jtag_wr(jtag_wr, C.uint(slot), C.ulonglong(addr), C.uint(data), C.uint(sse)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "JTAG write failed!")
    }
    return
}

func JtagRead(slot uint, addr uint64, sse uint) (data uint, err int) {
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    jtag_init := C.dlsym(handle, C.CString("jtag_init"))
    if jtag_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    jtag_rd := C.dlsym(handle, C.CString("jtag_rd"))
    if jtag_rd == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_jtag_init(jtag_init)); err > 0 {
        err = errType.FAIL
	cli.Println("e", "JTAG init failed!")
	return
    }
    var cData C.uint
    err = int(C.com_jtag_rd(jtag_rd, C.uint(slot), C.ulonglong(addr), &cData, C.uint(sse)))
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
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    spi_reg_init := C.dlsym(handle, C.CString("spi_reg_init"))
    if spi_reg_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    spi_wr := C.dlsym(handle, C.CString("spi_wr"))
    if spi_wr == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_spi_reg_init(spi_reg_init)); err > 0 {
        err = errType.FAIL
	cli.Println("e", "SPI init failed!")
	return
    }
    err = int(C.com_spi_wr(spi_wr, C.u_char(addr), C.u_char(data)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "CPLD write failed!")
    }
    return
}

func CpldRead(addr uint8) (data uint8, err int) {
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    spi_reg_init := C.dlsym(handle, C.CString("spi_reg_init"))
    if spi_reg_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    spi_rd := C.dlsym(handle, C.CString("spi_rd"))
    if spi_rd == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_spi_reg_init(spi_reg_init)); err > 0 {
        err = errType.FAIL
	cli.Println("e", "SPI init failed!")
	return
    }
    var cData C.u_char
    err = int(C.com_spi_rd(spi_rd, C.u_char(addr), &cData))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "CPLD read failed!")
    } else {
        data = uint8(cData)
        cli.Printf("i", "CPLD read at addr 0x%x with data 0x%x\n", addr, cData)
    }
    return
}

func CpldFlashProg(inst uint, inPutFile string) (err int) {
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    spi_flash_init := C.dlsym(handle, C.CString("spi_flash_init"))
    if spi_flash_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    jtag_flash_init := C.dlsym(handle, C.CString("jtag_flash_init"))
    if jtag_flash_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    cpld_program := C.dlsym(handle, C.CString("cpld_program"))
    if cpld_program == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if inst > 0 {
        err = int(C.com_spi_flash_init(spi_flash_init))
    } else {
        err = int(C.com_jtag_flash_init(jtag_flash_init))
    }
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "CpldFlashProg init failed!")
        return
    }
    err = int(C.com_cpld_program(cpld_program, C.CString(inPutFile)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("CPLD program failed!")
    }
    return
}

func CpldFlashRead(inst uint, outPutFile string) (err int) {
    libname :=C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    spi_flash_init := C.dlsym(handle, C.CString("spi_flash_init"))
    if spi_flash_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    jtag_flash_init := C.dlsym(handle, C.CString("jtag_flash_init"))
    if jtag_flash_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    cpld_read := C.dlsym(handle, C.CString("cpld_read"))
    if cpld_read == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if inst > 0 {
        err = int(C.com_spi_flash_init(spi_flash_init))
    } else {
        err = int(C.com_jtag_flash_init(jtag_flash_init))
    }
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "CpldFlashRead init failed!")
        return
    }
    err = int(C.com_cpld_read(cpld_read, C.CString(outPutFile)))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "CPLD read failed!")
    }
    return
}


func MvlWrite(inst uint, dev_addr uint, addr uint, data uint) (err int) {
    libname := C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    spi_mdio_init := C.dlsym(handle, C.CString("spi_mdio_init"))
    if spi_mdio_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    mdio_wr := C.dlsym(handle, C.CString("mdio_wr"))
    if mdio_wr == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_spi_mdio_init(spi_mdio_init)); err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO init failed!")
        return
    }
    if err = int(C.com_mdio_wr(mdio_wr, C.uint(inst), C.uint(dev_addr), C.uint(addr), C.uint(data))); err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO write failed!")
    }
    return
}

func MvlRead(inst uint, dev_addr uint, addr uint) (data uint, err int) {
    libname := C.CString("/home/diag/diag/tools/libacc.so")
    defer C.free(unsafe.Pointer(libname))
    handle := C.dlopen(libname, C.RTLD_LAZY)
    if handle == nil {
        err = errType.ERR_LIB_OPEN
        return;
    }
    defer func() {
        if r := C.dlclose(handle); r != 0 {
            err = errType.ERR_LIB_CLOSE
        }
    }()

    spi_mdio_init := C.dlsym(handle, C.CString("spi_mdio_init"))
    if spi_mdio_init == nil {
        err = errType.ERR_FIND_SYM
        return
    }
    mdio_rd := C.dlsym(handle, C.CString("mdio_rd"))
    if mdio_rd == nil {
        err = errType.ERR_FIND_SYM
        return
    }

    if err = int(C.com_spi_mdio_init(spi_mdio_init)); err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO init failed!")
        return
    }
    var cData C.uint
    err = int(C.com_mdio_rd(mdio_rd, C.uint(inst), C.uint(dev_addr), C.uint(addr), &cData))
    if err > 0 {
        err = errType.FAIL
        cli.Println("e", "MDIO read failed!")
    } else {
        data = uint(cData)
        cli.Printf("i", "MDIO read data 0x%x\n", cData)
    }
    return
}

