package rc19013

import (
    "fmt"
    "strconv"
    "common/errType"

    "common/cli"
    "protocol/smbusNew"
    "hardware/i2cinfo"
)

/*
 * Applicable to Renesas RC19016/013/008/004
 * Matera with RC19013A100 (DevID = 0x8D)
 * Reg data in byte
 */

const (
    //SMBus Registers
    OUTPUT_ENABLE_0      uint = 0x00 + 0x80
    OUTPUT_ENABLE_1      uint = 0x01 + 0x80
    OEb_PIN_READBACK_0   uint = 0x02 + 0x80
    OEb_PIN_READBACK_1   uint = 0x03 + 0x80
    SBEN_RDBK_LOS_CONFIG uint = 0x04 + 0x80
    VENDOR_REVISION_ID   uint = 0x05 + 0x80
    DEVICE_ID      uint = 0x06 + 0x80    //RC19013A100=0x8D
    BYTE_COUNT     uint = 0x07 + 0x80
    SBI_MASK_0     uint = 0x08 + 0x80
    SBI_MASK_1     uint = 0x09 + 0x80

    //RESERVED: 0x0A

    SBI_READBACK_0 uint = 0x0B + 0x80
    SBI_READBACK_1 uint = 0x0C + 0x80

    //RESERVED: 0x0D ~ 0x10

    LPHCSL_AMP_CTRL        uint = 0x11 + 0x80
    PD_RESTORE_LOSb_ENABLE uint = 0x12 + 0x80

    //RESERVED: 0x13

    OUTPUT_SLEW_RATE_0 uint = 0x14 + 0x80
    OUTPUT_SLEW_RATE_1 uint = 0x15 + 0x80

    //RESERVED: 0x16 ~ 0x25

    WRITE_LOCK_NOCLEAR         uint = 0x26 + 0x80
    WRITE_LOCK_CLEAR_LOS_EVENT uint = 0x27 + 0x80
)

var RegList = []uint {
    OUTPUT_ENABLE_0,
    OUTPUT_ENABLE_1,
    OEb_PIN_READBACK_0,
    OEb_PIN_READBACK_1,
    SBEN_RDBK_LOS_CONFIG,
    VENDOR_REVISION_ID,
    DEVICE_ID,
    BYTE_COUNT,
    SBI_MASK_0,
    SBI_MASK_1,
    SBI_READBACK_0,
    SBI_READBACK_1,
    LPHCSL_AMP_CTRL,
    PD_RESTORE_LOSb_ENABLE,
    OUTPUT_SLEW_RATE_0,
    OUTPUT_SLEW_RATE_1,
    WRITE_LOCK_NOCLEAR,
    WRITE_LOCK_CLEAR_LOS_EVENT,
}

var RegNames = map[uint]string {
    OUTPUT_ENABLE_0:        "OUTPUT_ENABLE_0",
    OUTPUT_ENABLE_1:        "OUTPUT_ENABLE_1",
    OEb_PIN_READBACK_0:     "OEb_PIN_READBACK_0",
    OEb_PIN_READBACK_1:     "OEb_PIN_READBACK_1",
    SBEN_RDBK_LOS_CONFIG:   "SBEN_RDBK_LOS_CONFIG",
    VENDOR_REVISION_ID:     "VENDOR_REVISION_ID",
    DEVICE_ID:      "DEVICE_ID",
    BYTE_COUNT:     "BYTE_COUNT",
    SBI_MASK_0:     "SBI_MASK_0",
    SBI_MASK_1:     "SBI_MASK_1",
    SBI_READBACK_0:         "SBI_READBACK_0",
    SBI_READBACK_1:         "SBI_READBACK_1",
    LPHCSL_AMP_CTRL:        "LPHCSL_AMP_CTRL",
    PD_RESTORE_LOSb_ENABLE: "PD_RESTORE_LOSb_ENABLE",
    OUTPUT_SLEW_RATE_0:     "OUTPUT_SLEW_RATE_0",
    OUTPUT_SLEW_RATE_1:     "OUTPUT_SLEW_RATE_1",
    WRITE_LOCK_NOCLEAR:     "WRITE_LOCK_NOCLEAR",
    WRITE_LOCK_CLEAR_LOS_EVENT: "WRITE_LOCK_CLEAR_LOS_EVENT",
}

func readByteSmbus(devName string, offset uint) (Data byte, err int) {
    err = errType.SUCCESS

    //Opens smbus connection
    i2cSmbus, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain smbus info for dev", devName)
        return
    }
    err = smbusNew.Open(devName, i2cSmbus.Bus, i2cSmbus.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open smbus: dev", devName,
                    "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
        return
    }
    defer smbusNew.Close()

    Data, err = smbusNew.ReadByte(devName, uint64(offset))
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read from %s at offset 0x%02x", devName, offset))
        return
    }

    return
}

func writeByteSmbus(devName string, offset uint, val byte) (err int) {
    err = errType.SUCCESS

    //Opens smbus connection
    i2cSmbus, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain smbus info for dev", devName)
        return
    }
    err = smbusNew.Open(devName, i2cSmbus.Bus, i2cSmbus.DevAddr)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open smbus: dev", devName,
                    "Bus", i2cSmbus.Bus, "DevAddr", i2cSmbus.DevAddr)
        return
    }
    defer smbusNew.Close()

    err = smbusNew.WriteByte(devName, uint64(offset), val)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write FRU at offset", offset, "with value", val)
    }
    return
}


func ReadDevID(devName string) (dev_id byte, err int) {
    err = errType.SUCCESS
    dev_id, err = readByteSmbus(devName, DEVICE_ID)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read device ID @ 0x%x for dev %s", DEVICE_ID, devName))
    }
    return
}

func ReadVendorRev(devName string) (vendor_rev byte, err int) {
    err = errType.SUCCESS
    vendor_rev, err = readByteSmbus(devName, VENDOR_REVISION_ID)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read vendor revision @ 0x%x for dev %s", VENDOR_REVISION_ID, devName))
    }
    return
}

func GetOutEn(devName string) (out_en_sts uint16, err int) {
    err = errType.SUCCESS
    var data0 byte
    var data1 byte

    //CLK0_EN ~ CLK7_EN
    data0, err = readByteSmbus(devName, OUTPUT_ENABLE_0)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read clk output enable sts @ 0x%x for dev %s", OUTPUT_ENABLE_0, devName))
        return
    }

    // CLK8_EN ~ CLK15_EN
    data1, err = readByteSmbus(devName, OUTPUT_ENABLE_1)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read clk output enable sts @ 0x%x for dev %s", OUTPUT_ENABLE_1, devName))
        return
    }

    out_en_sts = uint16(data1)
    out_en_sts = out_en_sts << 8
    out_en_sts = out_en_sts | uint16(data0)
    //cli.Println("d", fmt.Sprintf("dev %s CLK_EN sts: 0x%04x", devName, out_en_sts))

    return
}

func SetOutEn(devName string, clk_idx uint, setting bool) (err int) {
    err = errType.SUCCESS

    var regOffset uint
    if clk_idx <= 7 {
        regOffset = OUTPUT_ENABLE_0
    } else if clk_idx <=15 {
        regOffset = OUTPUT_ENABLE_1
    } else {
        err = errType.INVALID_PARAM
        cli.Println("e", fmt.Sprintf("Invalid CLK Index (0 ~ 15): %d", clk_idx))
        return
    }

    var data byte
    var old_setting bool
    data, err = readByteSmbus(devName, regOffset)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to read clk output enable sts @ 0x%x for dev %s", OUTPUT_ENABLE_1, devName))
        return
    }
    if (data & (1 << clk_idx)) == 0 {
        old_setting = false
    } else {
        old_setting = true
    }
    if setting == old_setting {
        cli.Println("i", fmt.Sprint("Setting CLK%d OUTPUT_EN to '%s': It was already '%s'", clk_idx, strconv.FormatBool(setting), strconv.FormatBool(old_setting)))
        return
    }
    if setting {
        data += byte(1<<clk_idx)
    } else {
        data -= byte(1<<clk_idx)
    }

    err = writeByteSmbus(devName, regOffset, data)
    if err != errType.SUCCESS {
        cli.Println("e", fmt.Sprintf("Failed to write clk output enable @ 0x%x for dev %s", regOffset, devName))
    }
    return
}

func DumpRegs(devName string, dumpRegList []uint) (err int) {
    err = errType.SUCCESS

    for _, idx := range dumpRegList {
        data, errSmbus := readByteSmbus(devName, idx)
        if errSmbus != errType.SUCCESS {
            cli.Println("e", fmt.Sprintf("Failed to read @ 0x%x", idx))
            err = errSmbus
            return
        }
        cli.Println("i", fmt.Sprintf("Reg[%s] = 0x%02x", RegNames[idx], data))
    }

    return
}

func DispStatus(devName string) (err int) {
    err = errType.SUCCESS

    var dispRegList = []uint {
        DEVICE_ID,
        VENDOR_REVISION_ID,
        OUTPUT_ENABLE_0,
        OUTPUT_ENABLE_1,
    }

    err = DumpRegs(devName, dispRegList)
    return
}


/*
 * Read Renesas RC Register
 * --------------------------------
 * Controller (host) send a start bit
 * Controller (host) send the write address
 * Renesas clock acknowledge
 * Controller (host) send the beginning byte Location = N
 * Renesas clock acknowledge
 * Controller (host) send a separate start bit
 * Controller (host) send the read address
 * Renesas clock acknowledge
 * Renesas clock send the data byte count = X
 * Renesas clock send Byte N+X-1
 * Renesas clock send Byte L through Byte X (if X(H) was written to Byte 7)
 * Controller (host) need to acknowledge each byte
 * Controller (host) send a not acknowledge bit
 * Controller (host) send a stop bit
 */


/*
 * Write Renesas RC Register
 * --------------------------------
 * Controller (host) send a start bit
 * Controller (host) send the write address
 * Renesas clock acknowledge
 * Controller (host) send the beginning byte Location = N
 * Renesas clock acknowledge
 * Controller (host) send the byte count = X
 * Renesas clock acknowledge
 * Controller (host) start sending Byte N through Byte N+X-1
 * Renesas clock acknowledge each byte one at a time
 * Controller (host) send a stop bit
 */

