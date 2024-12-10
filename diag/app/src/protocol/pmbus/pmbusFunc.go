package pmbus

import (
    "math"

    "config"
    "common/cli"
    "common/errType"
    "common/misc"
    "protocol/smbus"
)

const (
    PAGE_0    = 0x00
    PAGE_1    = 0x01
	PAGE_NONE = 0xFF

    VOUT_MODE_LNR = 0x0
    VOUT_MODE_VID = 0x1
)

func Open(devName string) (err int) {
    if (config.SmbusMode == config.DISABLE) {
        return
    }
    err = smbus.Open(devName)
    return
}

func Close() (err int) {
    if (config.SmbusMode == config.DISABLE) {
        return
    }
    err = smbus.Close()
    return

}

/**********************************************************************
*  I2C PEC CODE --> Code to generate i2c pec byte
* 
* 
***********************************************************************/ 
const POLY    uint32 = (0x1070 << 3)

func I2C_generate_pec(crc uint8, data []uint8) (pec uint8, err int) {
    var i int

    for i=0; i<len(data);i++ {
       crc = crc8(uint16(crc ^ data[i]) << 8)
    }
    pec = crc
    return
}


func crc8(data uint16) (data8 uint8) {
    for i:=0; i<8; i++ {
        if (data & 0x8000) == 0x8000 {
            data = (data ^ uint16(POLY))
        }
        data = (data << 1)
    }
    data8 = uint8(data >> 8)
    return
}


func Convert_vr13_5mvVID(data uint16) (integer uint64, dec uint64, err int) {
    var vr13 float64
    vr13 = .25 + (float64(data-1) * .005)

    intpart, div := math.Modf(vr13)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return
}


func Convert_vr13_10mvVID(data uint16) (integer uint64, dec uint64, err int) {
    var vr13 float64
    vr13 = .50 + (float64(data-1) * .01)

    intpart, div := math.Modf(vr13)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return
}


/*
	Linear11 format
    16-bit value,
    upper 5 bits: Linear two's complement format exponent.
    lower 11 bits: Linear two's complement format mantissa.
 */
func Linear11(input uint16) (integer uint64, dec uint64, err int) {
    var expUint uint64
    var expInt int64
    var expFloat float64
    var manFloat float64
    var expOutFloat float64

    expUint = uint64(input >> 11)
    manFloat = float64(input & 0x7FF)

    expInt, err = misc.TwoCmplBits64(expUint, 5)
    if err != errType.SUCCESS {
        return 0, 0, err
    }

    expFloat = float64(expInt)
    expOutFloat = math.Pow(2, expFloat) * manFloat
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    //cli.Printf("d", "input=0x%x, integer=%d, dec=%d\n", input, integer, dec)

    return integer, dec, errType.SUCCESS
}

/*
    Linear16 calculation: Use by VOUT_MODE, VOUT_COMMAND. and READ_VOUT
    exp: 5 bit two’s complement binary integer
    man: 16 bit unsigned binary integer
 */
func Linear16(exp uint64, man uint16) (integer uint64, dec uint64, err int) {
    var expUint uint64
    var expInt int64
    var expFloat float64
    var manFloat float64
    var expOutFloat float64

    expUint = exp & 0x1F
    manFloat = float64(man)

    expInt, err = misc.TwoCmplBits64(expUint, 5)
    if err != errType.SUCCESS {
        return
    }

    expFloat = float64(expInt)
    expOutFloat = math.Pow(2, expFloat) * manFloat
    intpart, div := math.Modf(expOutFloat)

    integer = uint64(intpart)
    dec = uint64(div*1000)

    return
}

 //mantissa = trgtVolt / exponent 
func GetMantissa(exp uint16, targetVoltage float64) (mantissa uint16, err int) {
    var expInt int64
    var expOutFloat float64

    expInt, err = misc.TwoCmplBits64(uint64(exp & 0x1F), 5)
    if err != errType.SUCCESS {
        return
    }

    expOutFloat = math.Pow(2, float64(expInt))

    mantissa = uint16(targetVoltage / expOutFloat)


    return
}

/*
    READ_VOUT in Linear16 format
 */
func ReadVoutLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    var data uint16
    var vmode byte
    var exp uint64

    // Write page register
    if (page != PAGE_NONE) {
        err = smbus.WriteByte(devName, PAGE, page)
        if err != errType.SUCCESS {
            return
        }
    }

    // Read VOUT_MODE
    vmode, err = smbus.ReadByte(devName, VOUT_MODE)
    if err != errType.SUCCESS {
        return
    }
    if (vmode >> 5) != VOUT_MODE_LNR {
        err = errType.PMBUS_INV_MODE
        return
    }
    exp = uint64(vmode & 0x1F)
    // Sometimes can not read vmode
    if vmode == 0 {
        integer = 0
        dec = 0
        return
    }
    //cli.Println("d", "exp:", exp)

    data, err = smbus.ReadWord(devName, READ_VOUT)
    //cli.Printf("d", "vmode=0x%x, exp=0x%x, data=0x%x\n", vmode, exp, data)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err = Linear16(exp, data)

    return
}

/*
    Read in Linear11 format
 */
func ReadLnr11(devName string, page byte, cmd uint64) (integer uint64, dec uint64, err int) {
    var data uint16

    // Write page register
    if (page != PAGE_NONE) {
        err = smbus.WriteByte(devName, PAGE, page)
        if err != errType.SUCCESS {
            return
        }
    }

    data, err = smbus.ReadWord(devName, cmd)

    integer, dec, _ = Linear11(data)

    return integer, dec, errType.SUCCESS
}

func ReadVinLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_VIN)
    return
}

/*
    READ_IIN
 */
func ReadIinLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_IIN)
    return
}

/*
    READ_IOUT
 */
func ReadIoutLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_IOUT)
    return
}

/*
    READ_PIN
 */
func ReadPinLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    //cli.Println("d", "ReadPinLnr")
    integer, dec, err = ReadLnr11(devName, page, READ_PIN)
    return
}

/*
    READ_POUT
 */
func ReadPoutLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    //cli.Println("d", "ReadPoutLnr")
    integer, dec, err = ReadLnr11(devName, page, READ_POUT)
    return
}

/*
    READ_TEMP_1
 */
func ReadTemp1Lnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_TEMPERATURE_1)
    return
}

/*
    READ_TEMP_2
 */
func ReadTemp2Lnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_TEMPERATURE_2)
    return
}

/*
    READ_TEMP_3
 */
func ReadTemp3Lnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_TEMPERATURE_3)
    return
}

/*
    READ_FAN_SPEED_1
 */
func ReadFanSpd1Lnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_FAN_SPEED_1)
    return
}

/*
    READ_FAN_SPEED_2
 */
func ReadFanSpd2Lnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    integer, dec, err = ReadLnr11(devName, page, READ_FAN_SPEED_2)
    return
}

/*
    READ_STATUS
 */
func ReadStatusWord(devName string, page byte) (data uint16, err int) {
    // Write page register
    if (page != PAGE_NONE) {
        err = smbus.WriteByte(devName, PAGE, page)
        if err != errType.SUCCESS {
            return
        }
    }

    data, err = smbus.ReadWord(devName, STATUS_WORD)
    return
}

func ReadMfrId(devName string, numBytes int) (dataBuf []byte, err int) {
    dataBuf = make([]byte, numBytes)
    _, err = smbus.ReadBlock(devName, MFR_ID, dataBuf)
    if err == errType.SUCCESS {
//        if retLen != numBytes {
//            err = errType.PMBUS_NUM_BYTE_MISMATCH
//        }
    }
    return
}

func ReadMfrModel(devName string, numBytes int) (dataBuf []byte, err int) {
    dataBuf = make([]byte, numBytes)
    retLen, err := smbus.ReadBlock(devName, MFR_MODEL, dataBuf)
    if err == errType.SUCCESS {
        if retLen != numBytes {
            err = errType.PMBUS_NUM_BYTE_MISMATCH
        }
    }
    return
}

/*
    READ_BYTE
 */
func ReadByte(devName string, regAddr uint64) (data byte, err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        data, err = smbus.ReadByte(devName, regAddr)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus ReadByte failed! cmd=0x%x\n", regAddr)
    }
    return
}

func WriteByte(devName string, regAddr uint64, data byte) (err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        err = smbus.WriteByte(devName, regAddr, data)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus WriteByte failed! cmd=0x%x\n", regAddr)
    }

    return
}

func ReadWord(devName string, regAddr uint64) (data uint16, err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        data, err = smbus.ReadWord(devName, regAddr)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus ReadWord failed! cmd=0x%x\n", regAddr)
    }

    return
}

func WriteWord(devName string, regAddr uint64, data uint16) (err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        err = smbus.WriteWord(devName, regAddr, data)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus WriteWord failed! cmd=0x%x\n", regAddr)
    }

    return
}

func SendByte(devName string, cmd byte) (err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        err = smbus.SendByte(devName, cmd)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus SendByte failed! cmd=0x%x\n", cmd)
    }

    return

}

func ReadBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        byteCnt, err = smbus.ReadBlock(devName, regAddr, dataBuf)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus ReadBlock failed! cmd=0x%x\n", regAddr)
    }

    return
}

func Readi2cBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        byteCnt, err = smbus.Readi2cBlock(devName, regAddr, dataBuf)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus ReadBlock failed! cmd=0x%x\n", regAddr)
    }

    return
}

func WriteBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int) {
    if config.SmbusMode == config.DISABLE {
    } else {
        byteCnt, err = smbus.WriteBlock(devName, regAddr, dataBuf)
    }
    if err != errType.SUCCESS {
        cli.Printf("e", "PMBus WriteBlock failed! cmd=0x%x\n", regAddr)
    }

    return
}
