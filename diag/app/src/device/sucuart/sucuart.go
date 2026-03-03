package sucuart

import (
    "fmt"
    "time"
    "os"
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
    "device/fpga/panareafpga"
)

type SUCUARTHandle struct {
    slot int
    port serial.Port
    lock *flock.Flock
}

func open_suc_uart(slot int, baud int) (handle *SUCUARTHandle , err int) {
    var i int
    lock_path := fmt.Sprintf("/var/lock/sucuart%d.lock", slot)
    uut_uart_acm := fmt.Sprintf("/dev/SUCUART%d", slot)
    uut_uart_fpga := fmt.Sprintf("/dev/ttySuC%d", slot - 1)
    uut_uart := ""

    cardType := os.Getenv("CARD_TYPE")
    var present bool
    var SlotPoweredOn bool

    if cardType == "MTP_PONZA" {
        present, _ = ponza_slot_present(slot)
        SlotPoweredOn, _ = ponza_slot_powered_on(slot)
    } else {
        uutName := "UUT_"+strconv.Itoa(slot)
        present, _ = panareafpga.SLOTpresentUUT(uutName)
        SlotPoweredOn, _ = panareafpga.SLOTpoweredOn(uutName)
    }

    if present != true || SlotPoweredOn != true {
        cli.Printf("i", "slot %d is not present. Present: %v, PowerOn: %v\n", slot, present, SlotPoweredOn)
        return nil, errType.FAIL
    }

    _, err_o := os.Stat(uut_uart_acm)
    if err_o == nil {
        uut_uart = uut_uart_acm
    } else {
        _, err_p := os.Stat(uut_uart_fpga)
        if err_p == nil {
            uut_uart = uut_uart_fpga
        }
    }
    if uut_uart == "" {
        cli.Printf("e", "SUCUART not exist for slot %d\n", slot)
        return nil, errType.FAIL
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

    //check that the /dev/sucuart device is not already opened (for example, by con_connect.sh).
    //Strange things can happen otherwise including the code getting stuck.
    cmdStr := fmt.Sprintf("lsof %s\n", uut_uart)
    output , _ := exec.Command("sh", "-c", cmdStr).Output()
    if len(output) != 0 {
        fileLock.Unlock()
        cli.Printf("e","Another process has console device %s open.  This process cannot open it", uut_uart)
        err = errType.FAIL
        return
    }

    mode := &serial.Mode{
                BaudRate: baud,
                Parity:   serial.NoParity,
                StopBits: serial.OneStopBit,
            }
    port, err_o := serial.Open(uut_uart, mode)
    if err_o != nil {
        fileLock.Unlock()
        cli.Printf("e", "failed to open %s for slot %d: %v", uut_uart, slot, err_o)
        return nil, errType.FAIL
    }
    port.SetReadTimeout(1 * time.Second)
    return &SUCUARTHandle{slot, port, fileLock}, errType.SUCCESS
}

func (u *SUCUARTHandle) send_cmd_suc_uart_single_attempt(cmd string) (output []byte, err int) {
    if u == nil || u.port == nil {
        cli.Println("e", "SUCUART handle not initialized")
        return nil, errType.FAIL
    }
    wdata := []byte(cmd)
    total := 0
    retry_count := 0
    for total < len(wdata) {
        n, err_w := u.port.Write(wdata[total:])
        if err_w != nil {
            if err_w.Error() == "resource temporarily unavailable" {
                if retry_count < 10 {
                    time.Sleep(10 * time.Millisecond)
                    retry_count++
                    continue
                } else {
                    cli.Println("e", "SUCUART write failed after 10 retries: ", err_w)
                    return nil, errType.FAIL
                }
            } else {
                cli.Println("e", "SUCUART write failed:", err_w)
                return nil, errType.FAIL
            }
        } else {
            total += n
        }
    }

    prompt1 := []byte("uart:~$")
    prompt2 := []byte("suc:~$")
    var result []byte
    read_count := 0
    retry_count = 0
    b := make([]byte, 1)
    for {
        read_count++
        // limit the number of read attempts
        if read_count > 65536 || retry_count > 10 {
            return nil, errType.FAIL
        }
        n, err_r := u.port.Read(b)
        if err_r != nil {
            cli.Println("e", "SUCUART Read error:", err_r)
            return nil, errType.FAIL
        }
        // nothing available after timeout
        if n == 0 {
            cli.Println("e", "SUCUART Read timeout")
            return nil, errType.FAIL
        }
        result = append(result, b...)
        if bytes.HasSuffix(result, prompt1) || bytes.HasSuffix(result, prompt2) {
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
    if bytes.HasSuffix(result, prompt1) {
        result = result[:len(result)-len(prompt1)]
    } else if bytes.HasSuffix(result, prompt2) {
        result = result[:len(result)-len(prompt2)]
    }
    //time.Sleep(200 * time.Millisecond)
    return result, errType.SUCCESS
}

func (u *SUCUARTHandle) send_cmd_suc_uart(cmd string) (output []byte, err int) {
    maxRetries := 15
    for attempt := 1; attempt <= maxRetries; attempt++ {
        output, err = u.send_cmd_suc_uart_single_attempt(cmd)
        if err == errType.SUCCESS {
            return output, err
        }
        cli.Printf("e", "Error on uart command attempt %d\n", attempt)
        if attempt < maxRetries {
            time.Sleep(1 * time.Second)
        }
    }
    return nil, errType.FAIL
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

func suc_cmd_list(slot int, cmd_list []string, print_output bool) () {
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

        if print_output {
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
    }
    return
}

func Suc_dev_list(slot int) () {
    cmd_list := []string{"device list"}
    suc_cmd_list(slot, cmd_list, true)
}

func Suc_dev_status(slot int) () {
    var cmd_list []string
    var ds4424_output []byte
    var rails []string
    uutName := "UUT_"+strconv.Itoa(slot)
    cardType := os.Getenv(uutName)

    if cardType == "GELSOP" || cardType == "GELSOX" || cardType == "GELSOB" || cardType == "GELSOU" {
        cmd_list = []string{"i2c write sercom2 0x4c 0x23 0x94", "tmp451 temperature", "voltage mp2861_sensor", "voltage ina3221_sensor"}
        ds4424_output = suc_single_cmd(slot, "voltage ds4424_info", false)
        rails = []string{"VDDIO_P1V2", "VDDAN_P1V8_PX", "VDDAN_P1V8_ETH", "VDDPL_P1V2", "VDDPL_P1V1_PX", "VDDPL_P1V1_ETH", "VDDPL_0P75"}
    } else if cardType == "MORTARO" || cardType == "SARACENO" {
        cmd_list = []string{"i2c write sercom2 0x4c 0x23 0x94", "tmp451 temperature", "voltage mp2861_sensor"}
        ds4424_output = suc_single_cmd(slot, "voltage ds4424_info", false)
        rails = []string{"VDDCR_0P75"}
    } else {
        cli.Println("e", "Environment UUT_<slot> not set for this card or unsupported CARDT_TYPE.  Please run ./start_diag.sh + source ~/.bash_profile to set the UUT_<slot>")
    }
    suc_cmd_list(slot, cmd_list, true)
    cli.Println("i")
    //print the voltages for those not monitored by ina3221
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
    if voltage_name != "VDDCR_0P65" {
        cmd_vmarg = "voltage ds4424_margin " + voltage_name + " " + strconv.Itoa(pct)
    } else {
        cmd_vmarg = "voltage mp2861_margin " + strconv.Itoa(pct)
    }
    cmd_list := []string{cmd_vmarg}
    suc_cmd_list(slot, cmd_list, true)
    time.Sleep(time.Duration(100) * time.Millisecond)
    return
}

func Suc_dev_vset(slot int, voltage_name string, vboot int, vout int, vmin int, vmax int) () {
    var cmd_list []string
    if voltage_name == "VDDCR_0P65" {
        if vboot != -1 {
            cmd_vboot := "voltage mp2861_set vboot " + strconv.Itoa(vboot)
            cmd_list = append(cmd_list, cmd_vboot)
        }
        if vout != -1 {
            vddcr_0p65_output := suc_single_cmd(slot, "voltage mp2861_sensor", false)
            re := regexp.MustCompile(`VDDCR_0P65\s+\|\s+([\d.]+)`)
            match := re.FindStringSubmatch(string(vddcr_0p65_output))
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
        suc_cmd_list(slot, cmd_list, true)
        time.Sleep(time.Duration(100) * time.Millisecond)
    }
    return
}

func Suc_dev_margin_info(slot int) () {
    cmd_list := []string{"voltage ds4424_info"}
    suc_cmd_list(slot, cmd_list, true)
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
    }
    return 0, errType.FAIL
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
        return err
    }
    //cli.Println("%s", string(buf))
    parts := strings.Split(string(buf), "= ") // Split on "="
    if len(parts) > 1 {
        return errType.SUCCESS
    }
    return errType.FAIL
}

func Suc_cpld_read_ponza(vul_index int, offset byte) (data byte, err int) {
    // Calculate slot (1-6), fpga_index (0-2), and vul_on_fpga (0-1)
    slot := ((vul_index - 1) / 6) + 1
    fpga_index := ((vul_index - 1) % 6) / 2
    vul_on_fpga := (vul_index - 1) % 2

    //cli.Printf("i", "Selecting Vulcano %d: Slot %d (1-based), FPGA %d (0-based), Vul %d (0-based)\n",
    //    vul_index, slot, fpga_index, vul_on_fpga)

    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return
    }
    defer u.close_suc_uart()

    cmd := "diag_sqi init"
    _, err = u.send_cmd_suc_uart(cmd + "\r\n")
    if err != errType.SUCCESS {
        return 0, err
    }

    var cmd1 string
    var cmd2 string
    switch fpga_index {
    case 0: // FPGA 0
        cmd1 = "gpio conf pb 6 o0"
        cmd2 = "gpio conf pb 7 o0"
    case 1: // FPGA 1
        cmd1 = "gpio conf pb 6 o1"
        cmd2 = "gpio conf pb 7 o0"
    case 2: // FPGA 2
        cmd1 = "gpio conf pb 6 o0"
        cmd2 = "gpio conf pb 7 o1"
    }
    _, err = u.send_cmd_suc_uart(cmd1 + "\r\n")
    if err != errType.SUCCESS {
        return 0, err
    }
    _, err = u.send_cmd_suc_uart(cmd2 + "\r\n")
    if err != errType.SUCCESS {
        return 0, err
    }

    if vul_on_fpga == 0 {
        cmd = "diag_sqi reg_rd 0 " + fmt.Sprintf("0x%02x", offset)
    } else {
        cmd = "diag_sqi reg_rd 1 " + fmt.Sprintf("0x%02x", offset)
    }

    buf, err := u.send_cmd_suc_uart(cmd + "\r\n")
    if err != errType.SUCCESS {
        return 0, err
    }

    // buf is now in the format of a one-byte hex value, e.g., "0x72"
    hexValue := strings.TrimSpace(string(buf))

    // Check if buf is in "0x<hex>" format
    if !strings.HasPrefix(hexValue, "0x") {
        cli.Println("e", "Error: buf is not in 0x<hex> format. Got: %s", hexValue)
        return 0, errType.FAIL
    }

    // Remove "0x" prefix and parse as base-16
    value, err_p := strconv.ParseUint(hexValue[2:], 16, 8)
    if err_p != nil {
        cli.Println("e", "Error converting hex to integer:", err_p)
        return 0, errType.FAIL
    }

    return byte(value), errType.SUCCESS
}

func Suc_cpld_write_ponza(vul_index int, offset byte, value byte) (err int) {
    // Calculate slot (1-6), fpga_index (0-2), and vul_on_fpga (0-1)
    slot := ((vul_index - 1) / 6) + 1
    fpga_index := ((vul_index - 1) % 6) / 2
    vul_on_fpga := (vul_index - 1) % 2

    //cli.Printf("i", "Selecting Vulcano %d: Slot %d (1-based), FPGA %d (0-based), Vul %d (0-based)\n",
    //    vul_index, slot, fpga_index, vul_on_fpga)

    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return
    }
    defer u.close_suc_uart()

    cmd := "diag_sqi init"
    _, err = u.send_cmd_suc_uart(cmd + "\r\n")
    if err != errType.SUCCESS {
        return err
    }

    var cmd1 string
    var cmd2 string
    switch fpga_index {
    case 0: // FPGA 0
        cmd1 = "gpio conf pb 6 o0"
        cmd2 = "gpio conf pb 7 o0"
    case 1: // FPGA 1
        cmd1 = "gpio conf pb 6 o1"
        cmd2 = "gpio conf pb 7 o0"
    case 2: // FPGA 2
        cmd1 = "gpio conf pb 6 o0"
        cmd2 = "gpio conf pb 7 o1"
    }
    _, err = u.send_cmd_suc_uart(cmd1 + "\r\n")
    if err != errType.SUCCESS {
        return err
    }
    _, err = u.send_cmd_suc_uart(cmd2 + "\r\n")
    if err != errType.SUCCESS {
        return err
    }

    if vul_on_fpga == 0 {
        cmd = "diag_sqi reg_wr 0 " + fmt.Sprintf("0x%02x", offset) + fmt.Sprintf(" 0x%02x", value)
    } else {
        cmd = "diag_sqi reg_wr 1 " + fmt.Sprintf("0x%02x", offset) + fmt.Sprintf(" 0x%02x", value)
    }
    _, err = u.send_cmd_suc_uart(cmd + "\r\n")
    return err
}

/**************************************************************
*
* Read the raw frudata using "frudump raw" command
* 
* Data will come back in a hexdump format like below
* 
* uart:~$ frudump raw
* 00000000: 01 00 00 01 17 2c 00 bb  01 16 19 40 2d dd c8 41 |.....,.. ...@-..A|
* 00000010: 4d 44 20 20 20 20 20 f2  56 55 4c 43 41 4e 4f 2d |MD     . VULCANO-|
* ...
* ...
* 000001F0: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00 |........ ........|
*
**************************************************************/
func Suc_fru_read(slot int) (data []byte, err int) {
    u, err := open_suc_uart(slot, 115200)
    if err != errType.SUCCESS {
        return 
    }
    defer u.close_suc_uart()
    cmd := "frudump raw"
    buf, err := u.send_cmd_suc_uart(cmd + "\r\n")
    if err != errType.SUCCESS {
        return
    }
    fmt.Printf("%s\n", string(buf))
    splitOutput := strings.Split(string(buf), "\n");
    for _, splitLine := range(splitOutput) {
        re := regexp.MustCompile(`\b[0-9a-fA-F]{2}\b`)
	bytes := re.FindAllString(splitLine, -1)
        if len(bytes) < 16 {
            cli.Println("e", "Error: Not getting 16 bytes of data per line from 'frudump raw'.  Check that the Suc FRU is programmed")
            err = errType.FAIL;
            return;
        }
        for i:=0; i<16; i++ {
            u64, _ := strconv.ParseUint(bytes[i], 16, 8)   //base 16, 8-bits
            data = append(data, uint8(u64))
        }
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
    suc_cmd_list(slot, command_list, true)
}

func Suc_vul_sel_and_power_on(vul_index int, power_on bool) (err int) {
    // Validate vul_index (1-36)
    if vul_index < 1 || vul_index > 36 {
        cli.Printf("e", "Invalid vul_index %d. Must be between 1 and 36\n", vul_index)
        return errType.FAIL
    }

    // Calculate slot (1-6), fpga_index (0-2), and vul_on_fpga (0-1)
    slot := ((vul_index - 1) / 6) + 1
    fpga_index := ((vul_index - 1) % 6) / 2
    vul_on_fpga := (vul_index - 1) % 2

    //cli.Printf("i", "Selecting Vulcano %d: Slot %d (1-based), FPGA %d (0-based), Vul %d (0-based)\n",
    //    vul_index, slot, fpga_index, vul_on_fpga)

    var cmd_list []string

    cmd_list = append(cmd_list, "diag_sqi init")

    switch fpga_index {
    case 0: // FPGA 0
        cmd_list = append(cmd_list, "gpio conf pb 6 o0", "gpio conf pb 7 o0")
    case 1: // FPGA 1
        cmd_list = append(cmd_list, "gpio conf pb 6 o1", "gpio conf pb 7 o0")
    case 2: // FPGA 2
        cmd_list = append(cmd_list, "gpio conf pb 6 o0", "gpio conf pb 7 o1")
    }

    if vul_on_fpga == 0 {
        cmd_list = append(cmd_list, "diag_sqi reg_wr 0 0x1a 2")
    } else {
        cmd_list = append(cmd_list, "diag_sqi reg_wr 0 0x1a 4")
    }

    // Power on the selected Vulcano
    if power_on == true {
        if vul_on_fpga == 0 {
            cmd_list = append(cmd_list, "diag_sqi reg_wr 0 0x2 0x80", "diag_sqi reg_wr 0 0x2 0x90")
        } else {
            cmd_list = append(cmd_list, "diag_sqi reg_wr 1 0x2 0x80", "diag_sqi reg_wr 1 0x2 0x90")
        }
    }

    suc_cmd_list(slot, cmd_list, false)
    /*if power_on == true {
        cli.Printf("i", "Selected and powered on Vulcano %d\n", vul_index)
    } else {
        cli.Printf("i", "Selected Vulcano %d\n", vul_index)
    }*/
    return errType.SUCCESS
}

func ponza_slot_present(slot_num int) (present bool, err error) {
    if slot_num < 1 || slot_num > 6 {
        err = fmt.Errorf("ERROR: ponza_slot_present - slot_num must be in range 1 to 6")
        return
    }

    slot_zero_based := slot_num - 1
    reg_addr := uint64(0x180 + (slot_zero_based * 4))

    rValue, err := panareafpga.ReadU32(reg_addr)
    if err != nil {
        return
    }

    // Check bit 9 (0x200): if 0, card is present
    nic_present := rValue & 0x200
    if nic_present == 0 {
        present = true
    } else {
        present = false
    }

    return
}

func ponza_slot_powered_on(slot_num int) (isOn bool, err error) {
    if slot_num < 1 || slot_num > 6 {
        err = fmt.Errorf("ERROR: ponza_slot_powered_on - slot_num must be in range 1 to 6")
        return
    }

    slot_zero_based := slot_num - 1
    reg_addr := uint64(0x180 + (slot_zero_based * 4))

    rValue, err := panareafpga.ReadU32(reg_addr)
    if err != nil {
        return
    }

    // Check power bits (bits 1 and 3)
    // Bit 1: 12V power rail (0x2)
    // Bit 3: 54V power rail (0x8)
    power_12v := rValue & 0x2
    power_54v := rValue & 0x8

    // Card is considered powered on if both power bits are set
    if power_12v != 0 && power_54v != 0 {
        isOn = true
    } else {
        isOn = false
    }

    return
}
