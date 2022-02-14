package main

import (
	"fmt"
    "flag"
    "log"
    "os"
    "syscall"
    "unsafe"
)

func ReadU32(addr int64) uint32 {
        var value uint32
        const bufferSize int = 4096

        pageSize := syscall.Getpagesize()
        pageSize64 := int64(pageSize)
        pageAddr := addr / pageSize64 * pageSize64
        pageOffset := addr - pageAddr

        file, err := os.Open("/dev/mem")
        if err != nil {
                log.Fatal(err)
        }

        defer file.Close()
        mmap, err := syscall.Mmap(int(file.Fd()), pageAddr, pageSize, syscall.PROT_READ, syscall.MAP_SHARED)

        if err != nil {
                log.Fatal(err)
        }
        value = *(*uint32)(unsafe.Pointer(&mmap[pageOffset]))
        err = syscall.Munmap(mmap)
        if err != nil {
                log.Fatal(err)
        }
        return value
}

func WriteU32(addr int64, data uint32) {
        const bufferSize int = 4096

        pageSize := syscall.Getpagesize()
        pageSize64 := int64(pageSize)
        pageAddr := addr / pageSize64 * pageSize64
        pageOffset := addr - pageAddr

        file, err := os.OpenFile("/dev/mem", os.O_RDWR, 0333)
        if err != nil {
            log.Fatal(err)
            return
        }

        defer file.Close()
        mmap, err := syscall.Mmap(int(file.Fd()), pageAddr, pageSize, syscall.PROT_WRITE, syscall.MAP_SHARED)

        if err != nil {
            log.Fatal(err)
            return
        }

        *(*uint32)(unsafe.Pointer(&mmap[pageOffset])) = data

        err = syscall.Munmap(mmap)
        if err != nil {
            log.Fatal(err)
        }
        return
}

func ReadU16(addr int64) uint16 {
        var value uint16
        const bufferSize int = 4096

        pageSize := syscall.Getpagesize()
        pageSize64 := int64(pageSize)
        pageAddr := addr / pageSize64 * pageSize64
        pageOffset := addr - pageAddr

        file, err := os.Open("/dev/mem")
        if err != nil {
                log.Fatal(err)
        }

        defer file.Close()
        mmap, err := syscall.Mmap(int(file.Fd()), pageAddr, pageSize, syscall.PROT_READ, syscall.MAP_SHARED)

        if err != nil {
                log.Fatal(err)
        }
        value = *(*uint16)(unsafe.Pointer(&mmap[pageOffset]))
        err = syscall.Munmap(mmap)
        if err != nil {
                log.Fatal(err)
        }
        return value
}

func WriteU16(addr int64, data uint16) {
        const bufferSize int = 4096

        pageSize := syscall.Getpagesize()
        pageSize64 := int64(pageSize)
        pageAddr := addr / pageSize64 * pageSize64
        pageOffset := addr - pageAddr

        file, err := os.OpenFile("/dev/mem", os.O_RDWR, 0333)
        if err != nil {
            log.Fatal(err)
            return
        }

        defer file.Close()
        mmap, err := syscall.Mmap(int(file.Fd()), pageAddr, pageSize, syscall.PROT_WRITE, syscall.MAP_SHARED)

        if err != nil {
            log.Fatal(err)
            return
        }

        *(*uint16)(unsafe.Pointer(&mmap[pageOffset])) = data

        err = syscall.Munmap(mmap)
        if err != nil {
            log.Fatal(err)
        }
        return
}

func ReadU8(addr int64) uint8 {
        var value uint8
        const bufferSize int = 4096

        pageSize := syscall.Getpagesize()
        pageSize64 := int64(pageSize)
        pageAddr := addr / pageSize64 * pageSize64
        pageOffset := addr - pageAddr

        file, err := os.Open("/dev/mem")
        if err != nil {
                log.Fatal(err)
        }

        defer file.Close()
        mmap, err := syscall.Mmap(int(file.Fd()), pageAddr, pageSize, syscall.PROT_READ, syscall.MAP_SHARED)

        if err != nil {
                log.Fatal(err)
        }
        value = *(*uint8)(unsafe.Pointer(&mmap[pageOffset]))
        err = syscall.Munmap(mmap)
        if err != nil {
                log.Fatal(err)
        }
        return value
}

func WriteU8(addr int64, data uint8) {
        const bufferSize int = 4096

        pageSize := syscall.Getpagesize()
        pageSize64 := int64(pageSize)
        pageAddr := addr / pageSize64 * pageSize64
        pageOffset := addr - pageAddr

        file, err := os.OpenFile("/dev/mem", os.O_RDWR, 0333)
        if err != nil {
            log.Fatal(err)
            return
        }

        defer file.Close()
        mmap, err := syscall.Mmap(int(file.Fd()), pageAddr, pageSize, syscall.PROT_WRITE, syscall.MAP_SHARED)

        if err != nil {
            log.Fatal(err)
            return
        }

        *(*uint8)(unsafe.Pointer(&mmap[pageOffset])) = data

        err = syscall.Munmap(mmap)
        if err != nil {
            log.Fatal(err)
        }
        return
}

func main() {
    rdPtr := flag.Bool("rd", false, "Read memory")
    wrPtr := flag.Bool("wr", false, "Write memory")
    rd1bPtr := flag.Bool("rd1b", false, "Read memory 1 Byte")
    wr1bPtr := flag.Bool("wr1b", false, "Write memory 1 Byte")
    rd2bPtr := flag.Bool("rd2b", false, "Read memory 2 Byte")
    wr2bPtr := flag.Bool("wr2b", false, "Write memory 2 Byte")

    addrPtr := flag.Uint64   ("addr",0,         "addr")
    dataPtr := flag.Uint64   ("data",0,         "data")
    flag.Parse()

    if *rdPtr == true {
        ret := ReadU32(int64(*addrPtr))
        fmt.Printf("read: 0x%x\n", ret)
    }

    if *wrPtr == true {
        data := uint32(*dataPtr)
        WriteU32(int64(*addrPtr), data)
        fmt.Printf("Done Write; addr=0x%x; data=0x%x\n", *addrPtr, data)
    }

    if *rd1bPtr == true {
        ret := ReadU8(int64(*addrPtr))
        fmt.Printf("read: 0x%x\n", ret)
    }

    if *wr1bPtr == true {
        data := uint8(*dataPtr)
        WriteU8(int64(*addrPtr), data)
        fmt.Printf("Done Write; addr=0x%x; data=0x%x\n", *addrPtr, data)
    }

    if *rd2bPtr == true {
        ret := ReadU16(int64(*addrPtr))
        fmt.Printf("read: 0x%x\n", ret)
    }

    if *wr2bPtr == true {
        data := uint16(*dataPtr)
        WriteU16(int64(*addrPtr), data)
        fmt.Printf("Done Write; addr=0x%x; data=0x%x\n", *addrPtr, data)
    }
}
