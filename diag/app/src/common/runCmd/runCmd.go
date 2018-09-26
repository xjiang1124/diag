package runCmd

import (
    "os/exec"
    "io"
    "strings"
    "sync"

    "common/dcli"
    "common/errType"
    "common/misc"
)

const (
    IDLE    = 0
    RUNNING = 1
    PASS    = 2
    FAIL    = 3
)

var cmdStatus int = IDLE

func copyLogs(r io.Reader, passSign string, failSign string) {
    buf := make([]byte, 2048)
    for {
        misc.SleepInUSec(500000)
        n, err := r.Read(buf)
        if n > 0 {
            dcli.Printf("NO_INFO", "%s", string(buf[0:n]))
            if strings.Contains(string(buf[0:n]), passSign) {
                cmdStatus = PASS
            }
            if strings.Contains(string(buf[0:n]), failSign) {
                cmdStatus = FAIL
            }
        }
        if err != nil {
            break
        }
    }
}

func Run(passSign string, failSign string, name string, arg ... string) (err int) {
    cmdStatus = RUNNING

    cmd := exec.Command(name, arg...)
    stdout, _ := cmd.StdoutPipe()
    stderr, _ := cmd.StderrPipe()
    var wg sync.WaitGroup

    cmd.Start()
    wg.Add(2)
    go func() {
        defer wg.Done()
        copyLogs(stdout, passSign, failSign)
    }()

    go func() {
        defer wg.Done()
        copyLogs(stderr, passSign, failSign)
    }()

    wg.Wait()
    cmd.Wait()

    if cmdStatus == RUNNING {
        cmdStatus = FAIL
    }

    if cmdStatus == PASS {
        err = errType.SUCCESS
    } else {
        err = errType.FAIL
    }

    cmdStatus = IDLE
    return
}


