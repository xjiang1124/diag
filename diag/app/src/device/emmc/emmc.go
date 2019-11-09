package emmc

import (
    "bytes"
    "crypto/md5"
    "fmt"
    "hash"
    "io"
    "os"
    "os/exec"
    "path/filepath"
    "strconv"

    "common/cli"
    "common/errType"
)

func EmmcTest(fileSizeInMB string, count int) (err int) {

    fileName := "/data/nic_util/emmctest.bin"
    cmd := exec.Command("dd", "if=/dev/urandom", "of="+fileName, "bs="+fileSizeInMB+"M", "count=1")
    _, errGo := cmd.Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    cmd = exec.Command("sync")
    errGo = cmd.Run()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    f, errGo := os.Open(fileName)
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }
    defer f.Close()

    origMd5 := md5.New()
    _, errGo = io.Copy(origMd5, f)
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }
    cli.Printf("i", "Origin %x\n", origMd5.Sum(nil))

    var newMd5 hash.Hash
    for i := 0; i < count; i++ {
        cmd = exec.Command("cp", fileName, fileName+strconv.Itoa(i))
        _ = cmd.Run()
        cmd = exec.Command("sync")
        _ = cmd.Run()
        fd, errGo := os.Open(fileName+strconv.Itoa(i))
        if errGo != nil {
            cli.Println("e", errGo)
            err = errType.FAIL
            return
        }
        defer fd.Close()

        newMd5 = md5.New()
        _, errGo = io.Copy(newMd5, fd)
        if errGo != nil {
            cli.Println("e", errGo)
            err = errType.FAIL
            return
        }

        if !bytes.Equal(origMd5.Sum(nil), newMd5.Sum(nil)) {
            cli.Printf("i", "md5sum error at iter%d", i)
            err = errType.FAIL
            return
        }
    }
    cli.Printf("i", "All %d files md5sum are matched\n", count)

    // Clean up - deleted all files generated
    matches, errGo := filepath.Glob("/data/nic_util/"+"emmctest*")
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }

    for _, str := range matches {
        _, err := exec.Command("rm", "-rf", str).CombinedOutput()
        if err != nil {
            fmt.Printf("rm emmctest got error: %s\n", err)
        }
    }
    cmd = exec.Command("sync")
    _ = cmd.Run()

    return
}

