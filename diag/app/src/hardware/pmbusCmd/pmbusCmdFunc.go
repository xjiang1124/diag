package pmbusCmd

import (
    "math"

    "common/errType"
    "common/misc"

    "protocol/pmbus"
)

const (
    PAGE_0    = 0x00
    PAGE_1    = 0x01
	PAGE_NONE = 0xFF

    VOUT_MODE_LNR = 0x0
    VOUT_MODE_VID = 0x1
)

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

/*
    READ_VOUT in Linear16 format
 */
func ReadVoutLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
    var data uint16
    var vmode byte
    var exp uint64

    // Write page register
    if (page != PAGE_NONE) {
        err = pmbus.WriteByte(devName, PAGE, page)
        if err != errType.SUCCESS {
            return
        }
    }

    // Read VOUT_MODE
    vmode, err = pmbus.ReadByte(devName, VOUT_MODE)
    if err != errType.SUCCESS {
        return
    }
    if (vmode >> 5) != VOUT_MODE_LNR {
        err = errType.PMBUS_INV_MODE
        return
    }
    exp = uint64(vmode & 0x1F)

    data, err = pmbus.ReadWord(devName, READ_VOUT)
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
        err = pmbus.WriteByte(devName, PAGE, page)
        if err != errType.SUCCESS {
            return
        }
    }

    data, err = pmbus.ReadWord(devName, cmd)

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
    integer, dec, err = ReadLnr11(devName, page, READ_PIN)
    return
}

/*
    READ_POUT
 */
func ReadPoutLnr(devName string, page byte) (integer uint64, dec uint64, err int) {
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
        err = pmbus.WriteByte(devName, PAGE, page)
        if err != errType.SUCCESS {
            return
        }
    }

    data, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}

func ReadMfrId(devName string, numBytes int) (dataBuf []byte, err int) {
    dataBuf = make([]byte, numBytes)
    retLen, err := pmbus.ReadBlock(devName, MFR_ID, dataBuf)
    if err == errType.SUCCESS {
        if retLen != numBytes {
            err = errType.PMBUS_NUM_BYTE_MISMATCH
        }
    }
    return
}

func ReadMfrModel(devName string, numBytes int) (dataBuf []byte, err int) {
    dataBuf = make([]byte, numBytes)
    retLen, err := pmbus.ReadBlock(devName, MFR_MODEL, dataBuf)
    if err == errType.SUCCESS {
        if retLen != numBytes {
            err = errType.PMBUS_NUM_BYTE_MISMATCH
        }
    }
    return
}

