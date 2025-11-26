package sucuart

import (
    "fmt"
    "time"
    "bufio"
    "bytes"
    "strings"
    "strconv"
    "regexp"
    "math"
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
    port.SetReadTimeout(10 * time.Second)
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
    retry_count := 0
    for {
        read_count++
        // limit the number of read attempts
        if read_count > 65536 || retry_count > 10 {
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
            //right after power cycle, we might get prompt from UART before sending any commands
            if idx := bytes.Index(result, []byte(cmd)); idx != -1 {
                break
            } else {
                //discard if the buffer does not contain the command we sent
                result = result[:0]
                read_count = 0
                retry_count++
            }
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

func suc_single_cmd(slot int, cmd string, print_output bool) (output []byte) {
    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return
    }
    defer u.close_suc_uart()

    output, err = u.send_cmd_suc_uart(cmd + "\r\n")
    if err != errType.SUCCESS {
        return
    }

    if print_output {
        lines := strings.Split(string(output), "\r\n")
        for _, line := range lines {
            // Skip empty last element if string ends with \r\n
            if line == "" {
                continue
            }
            cli.Println("i", line)
        }
    }

    return
}

func suc_cmd_list(slot int, cmd_list []string) () {
    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return
    }
    defer u.close_suc_uart()

    for i, cmd := range cmd_list {
        buf, err := u.send_cmd_suc_uart(cmd + "\r\n")
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
    cmd_list := []string{"device list"}
    suc_cmd_list(slot, cmd_list)
}

func Suc_dev_status(slot int) () {
    cmd_list := []string{"tmp451 temperature", "voltage mp2861_sensor", "voltage ina3221_sensor"}
    suc_cmd_list(slot, cmd_list)
    cli.Println("i")
    //print the voltages for those not monitored by ina3221
    ds4424_output := suc_single_cmd(slot, "voltage ds4424_info", false)
    rails := []string{"VDDIO_P1V2", "VDDAN_P1V8_PX", "VDDAN_P1V8_ETH", "VDDPL_P1V2", "VDDPL_P1V1_PX", "VDDPL_P1V1_ETH", "VDDPL_0P75"}
    results := make(map[string]string)
    lines := strings.Split(string(ds4424_output), "\r\n")
    for _, line := range lines {
        for _, rail := range rails {
            if strings.Contains(line, rail) {
                parts := strings.Split(line, "Volt=")
                if len(parts) > 1 {
                    vout := strings.TrimSuffix(parts[1], "V")
                    results[rail] = vout
                }
            }
        }
    }
    if len(results) != 0 {
        cli.Println("i", "NAME            | VOUT")
        cli.Println("i", "------------------------")
        for _, rail := range rails {
            if vout, exists := results[rail]; exists {
                cli.Printf("i", "%-15s | %s\n", rail, vout)
            }
        }
    }
}

func Suc_dev_margin(slot int, voltage_name string, pct int) () {
    var cmd_vmarg string
    if voltage_name != "VDD_CORE" {
        cmd_vmarg = "voltage ds4424_margin " + voltage_name + " " + strconv.Itoa(pct)
    } else {
        cmd_vmarg = "voltage mp2861_margin " + strconv.Itoa(pct)
    }
    cmd_list := []string{cmd_vmarg}
    suc_cmd_list(slot, cmd_list)
    time.Sleep(time.Duration(100) * time.Millisecond)
    return
}

func Suc_dev_vset(slot int, voltage_name string, vboot int, vout int, vmin int, vmax int) () {
    var cmd_list []string
    if voltage_name == "VDD_CORE" {
        if vboot != -1 {
            cmd_vboot := "voltage mp2861_set vboot " + strconv.Itoa(vboot)
            cmd_list = append(cmd_list, cmd_vboot)
        }
        if vout != -1 {
            vdd_core_output := suc_single_cmd(slot, "voltage mp2861_sensor", false)
            re := regexp.MustCompile(`VDD_CORE\s+\|\s+([\d.]+)`)
            match := re.FindStringSubmatch(string(vdd_core_output))
            if len(match) > 1 {
                vboot_str := match[1]
                vboot_val, err := strconv.ParseFloat(vboot_str, 64)
                if err != nil {
                    cli.Println("e", "Error converting VBOOT to float:", err)
                    return
                }
                vboot_mv := int(vboot_val * 1000)
                pct := int(math.Round((float64(vout - vboot_mv) / float64(vboot_mv)) * 100))
                cli.Printf("i", "vmarg pct is %d\n", pct)
                cmd_vmarg := "voltage mp2861_margin " + strconv.Itoa(pct)
                cmd_list = append(cmd_list, cmd_vmarg)
            } else {
                cli.Println("e", "VBOOT value not found")
                return
            }
        }
        if vmin != -1 {
            cmd_vmin := "voltage mp2861_set vmin " + strconv.Itoa(vmin)
            cmd_list = append(cmd_list, cmd_vmin)
        }
        if vmax != -1 {
            cmd_vmax := "voltage mp2861_set vmax " + strconv.Itoa(vmax)
            cmd_list = append(cmd_list, cmd_vmax)
        }
    } else {
        if vout != -1 {
            //first set margin=0 to read the base value
            cmd_vmarg := "voltage ds4424_margin " + voltage_name + " 0"
            suc_single_cmd(slot, cmd_vmarg, true)
            time.Sleep(time.Duration(100) * time.Millisecond)
            ds4424_output := suc_single_cmd(slot, "voltage ds4424_info", false)
            re := regexp.MustCompile(fmt.Sprintf(`%s\s+\|.*?Volt=([\d.]+)V`, voltage_name))
            match := re.FindStringSubmatch(string(ds4424_output))
            if len(match) > 1 {
                volt_str := match[1]
                volt_val, err := strconv.ParseFloat(volt_str, 64)
                if err != nil {
                    cli.Println("e", "Error converting Volt to float:", err)
                    return
                }
                volt_mv := int(volt_val * 1000)
                pct := int(math.Round((float64(vout - volt_mv) / float64(volt_mv)) * 100))
                cli.Printf("i", "vmarg pct is %d\n", pct)
                cmd_vmarg = "voltage ds4424_margin " + voltage_name + " " + strconv.Itoa(pct)
                cmd_list = append(cmd_list, cmd_vmarg)
            } else {
                cli.Println("e", "Volt value not found")
                return
            }
        }
    }
    if cmd_list != nil {
        suc_cmd_list(slot, cmd_list)
        time.Sleep(time.Duration(100) * time.Millisecond)
    }
    return
}

func Suc_dev_margin_info(slot int) () {
    cmd_list := []string{"voltage ds4424_info"}
    suc_cmd_list(slot, cmd_list)
}

func Suc_cpld_read(slot int, offset byte) (data byte, err int) {
    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return 0, err
    }
    defer u.close_suc_uart()
    cmd := "cpld_reg read " + fmt.Sprintf("0x%02x", offset)
    buf, err := u.send_cmd_suc_uart(cmd + "\r\n")
    if err != errType.SUCCESS {
        return 0, err
    }
    //cli.Println("%s", string(buf))
    parts := strings.Split(string(buf), "= ") // Split on "= "
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
    cmd := "cpld_reg write " + fmt.Sprintf("0x%02x ", offset) + fmt.Sprintf("0x%02x", value)
    buf, err := u.send_cmd_suc_uart(cmd + "\r\n")
    if err != errType.SUCCESS {
        return
    }
    //cli.Println("%s", string(buf))
    parts := strings.Split(string(buf), "= ") // Split on "="
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
            command_list = append(command_list, trimmed_cmd)
        }
    }
    suc_cmd_list(slot, command_list)
}