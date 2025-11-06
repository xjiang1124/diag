package sucuart

import (
    "fmt"
    "time"
    "bufio"
    "bytes"
    "strings"
    "strconv"
    "common/cli"
    "common/errType"
    "go.bug.st/serial"
    "github.com/gofrs/flock"
    "os/exec"
)

type SUCUARTHandle struct {
    slot int
    port serial.Port
    lock *flock.Flock
}

func open_suc_uart(slot int, baud int) (handle *SUCUARTHandle , err int) {
    var i int
    lock_path := fmt.Sprintf("/var/lock/sucuart%d.lock", slot)
    uut_uart := fmt.Sprintf("/dev/SUCUART%d", slot)

    //check that the /dev/sucuart device is not already opened.
    //Strange things can happen otherwise including the code getting stuck.
    cmdStr := fmt.Sprintf("lsof %s\n", uut_uart)
    output , _ := exec.Command("sh", "-c", cmdStr).Output()
    if len(output) != 0 {
        cli.Printf("e","Another process has console device %s open.  This process cannot open it", uut_uart)
        err = errType.FAIL
        return
    }

    fileLock := flock.New(lock_path)
    for i = 0; i < 1000; i++ {
        locked, err_l := fileLock.TryLock()
        if err_l != nil {
            cli.Printf("e", "failed to acquire SUCUART lock for slot %d: %v", slot, err_l)
        }
        if locked {
            break
        }
        time.Sleep(time.Duration(10) * time.Millisecond)
    }
    if i == 1000 {
        return nil, errType.FAIL
    }

    mode := &serial.Mode{
                BaudRate: baud,
                Parity:   serial.NoParity,
                StopBits: serial.OneStopBit,
            }
    port, err_o := serial.Open(uut_uart, mode)
    if err_o != nil {
        fileLock.Unlock()
        cli.Printf("e", "failed to open SUCUART for slot %d: %v", slot, err_o)
        return nil, errType.FAIL
    }
    port.SetReadTimeout(1 * time.Second)
    return &SUCUARTHandle{slot, port, fileLock}, errType.SUCCESS
}

func (u *SUCUARTHandle) send_cmd_suc_uart(cmd string) (output []byte, err int) {
    if u == nil || u.port == nil {
        cli.Println("e", "SUCUART handle not initialized")
        return nil, errType.FAIL
    }

    _, err_w := u.port.Write([]byte(cmd))
    if err_w != nil {
        cli.Println("e", "SUCUART write failed:", err_w)
        return nil, errType.FAIL
    }

    reader := bufio.NewReader(u.port)
    prompt := []byte("uart:~$")
    var result []byte
    read_count := 0
    for {
        read_count++
        // limit the number of read attempts
        if read_count > 65536 {
            break
        }
        b, err_r := reader.ReadByte()
        if err_r != nil {
            // Read timeout or error
            if err_r.Error() == "EOF" {
                break
            }
            cli.Println("e", "SUCUART Read error:", err_r)
            break
        }
        result = append(result, b)
        if bytes.HasSuffix(result, prompt) {
            break
        }
    }
    //fmt.Printf("Received: %s\n", result)
    //remove the echoed command
    if idx := bytes.Index(result, []byte(cmd)); idx != -1 {
        result = result[idx+len(cmd):]
    }
    //remove the prompt
    last_line := bytes.LastIndex(result, []byte("\r\n"))
    if last_line != -1 {
        result = result[:last_line]
    }
    //time.Sleep(200 * time.Millisecond)
    return result, errType.SUCCESS
}

func (u *SUCUARTHandle) close_suc_uart() {
    if u == nil {
        return
    }
    if u.port != nil {
        u.port.Close()
    }
    if u.lock != nil {
        u.lock.Unlock()
    }
}

func suc_cmd_list(slot int, cmd_list []string) () {
    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return
    }
    defer u.close_suc_uart()

    for i, cmd := range cmd_list {
        buf, err := u.send_cmd_suc_uart(cmd)
        if err != errType.SUCCESS {
            return
        }
        lines := strings.Split(string(buf), "\r\n")
        for _, line := range lines {
            // Skip empty last element if string ends with \r\n
            if line == "" {
                continue
            }
            cli.Println("i", line)
        }
        if i != len(cmd_list) - 1 {
            cli.Println("i")
        }
    }
    return
}

func Suc_dev_list(slot int) () {
    cmd_list := []string{"device list\r\n"}
    suc_cmd_list(slot, cmd_list)
}

func Suc_dev_status(slot int) () {
    cmd_list := []string{"voltage ina3221_sensor\r\n", "voltage mp2861_sensor\r\n", "tmp451 temperature\r\n"}
    suc_cmd_list(slot, cmd_list)
}

func Suc_dev_margin(slot int) () {
    return
}

func Suc_cpld_read(slot int, offset byte) (data byte, err int) {
    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return 0, err
    }
    defer u.close_suc_uart()
    cmd := "diag_cpld read " + fmt.Sprintf("0x%02x\r\n", offset)
    buf, err := u.send_cmd_suc_uart(cmd)
    if err != errType.SUCCESS {
        return 0, err
    }
    //cli.Println("%s", string(buf))
    parts := strings.Split(string(buf), "value ") // Split on "value "
    if len(parts) > 1 {
        hexValue := strings.TrimSpace(parts[1])
        if strings.HasPrefix(hexValue, "0x") {
            value, err_p := strconv.ParseUint(hexValue[2:], 16, 8) // Remove "0x", parse as base 16
            if err_p != nil {
                cli.Println("e", "Error converting hex to integer:", err_p)
                return 0, errType.FAIL
            }
            return byte(value), errType.SUCCESS
        }
    } else {
        return 0, errType.FAIL
    }
    return
}

func Suc_cpld_write(slot int, offset byte, value byte) (err int) {
    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return
    }
    defer u.close_suc_uart()
    cmd := "diag_cpld write " + fmt.Sprintf("0x%02x ", offset) + fmt.Sprintf("0x%02x\r\n", value)
    buf, err := u.send_cmd_suc_uart(cmd)
    if err != errType.SUCCESS {
        return
    }
    //cli.Println("%s", string(buf))
    parts := strings.Split(string(buf), "value ") // Split on "value "
    if len(parts) > 1 {
        return errType.SUCCESS
    } else {
        return errType.FAIL
    }
    return
}

func Suc_exec_cmds(slot int, cmds string) () {
    raw_commands := strings.Split(cmds, ";")
    var command_list []string
    for _, command := range raw_commands {
        trimmed_cmd := strings.TrimSpace(command)
        if trimmed_cmd != "" {
            command_list = append(command_list, trimmed_cmd + "\r\n")
        }
    }
    suc_cmd_list(slot, command_list)
}