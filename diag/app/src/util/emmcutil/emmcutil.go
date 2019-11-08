package main

import (
//    "crypto/md5"
//    "os/exec"
//    "io"
//    "log"
//    "os"
    "flag"
//    "fmt"
//    "bytes"
//    "strconv"
//    "path/filepath"
    "common/cli"
    "common/errType"
    "device/emmc"
)

const APP_VERSION = "0.1"

// The flag package provides a default help printer via -h switch
var versionFlag *bool = flag.Bool("v", false, "Print the version number.")
var fileSize     *string = flag.String("s", "1m", "Test file size.")
var countPtr     *int = flag.Int("c", 0, "Test file size.")

func main() {
    flag.Parse() // Scan the arguments list 

    if *versionFlag {
        cli.Println("i", "Version:", APP_VERSION)
    }

    err := emmc.EmmcTest(*fileSize, *countPtr)
    if err != errType.SUCCESS {
        cli.Println("i", "eMMC test failed!")
    } else {
        cli.Println("i", "eMMC test passed")
    }

//    count := *countPtr
//    fileName := "emmctest"
//    cmd := exec.Command("dd", "if=/dev/urandom", "of=emmctest", "bs="+*fileSize+"M", "count=1")
//    var out bytes.Buffer
//    cmd.Stdout = &out
//    _ = cmd.Run()
////    if e != nil {
////        fmt.Println(cmd.Args)
////        log.Fatal(e)
////    }
////    fmt.Printf("in all caps: %q\n", out.String())
//    cmd = exec.Command("sync")
//    f, err := os.Open(fileName)
//    _ = cmd.Run()
//    if err != nil {
//        log.Fatal(err)
//    }
//    defer f.Close()
//
//    origMd5 := md5.New()
//    if _, err := io.Copy(origMd5, f); err != nil {
//        log.Fatal(err)
//    }
//    fmt.Printf("Origin %x\n", origMd5.Sum(nil))
//
//    for i := 0; i < count; i++ {
//        cmd = exec.Command("cp", fileName, fileName+strconv.Itoa(i))
//        _ = cmd.Run()
//        cmd = exec.Command("sync")
//        _ = cmd.Run()
//        fd, err := os.Open(fileName+strconv.Itoa(i))
//        if err != nil {
//            log.Fatal(err)
//        }
//        defer fd.Close()
//
//        newMd5 := md5.New()
//        if _, err := io.Copy(newMd5, fd); err != nil {
//            log.Fatal(err)
//        }
////        fmt.Printf("new%d %x\n", i, newMd5.Sum(nil))
//        if !bytes.Equal(origMd5.Sum(nil), newMd5.Sum(nil)) {
//            fmt.Printf("md5sum error at iter%d", i)
//            os.Exit(-1)
//        }
//    }
//    fmt.Printf("All %d files md5sum are matched\n", count)
//
//    matches, err := filepath.Glob("emmctest*")
//
//    for _, str := range matches {
//        _, err := exec.Command("rm", "-rf", str).CombinedOutput()
//        if err != nil {
//            fmt.Printf("rm emmctest got error: %s\n", err)
//        }
//    }
//    cmd = exec.Command("sync")
//    _ = cmd.Run()
}

