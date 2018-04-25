package vrmsim
import (
    "common/errType"
    "common/misc"
)

type I2cRegSim struct {
    offset uint32
    value uint32
    numByte uint32
}

var Tps53659RegSim = []I2cRegSim {
    I2cRegSim {0x00, 0x00, 2}, // Page
    I2cRegSim {0x01, 0x00, 2}, // Operation
    I2cRegSim {0x02, 0x00, 2}, // on_off_config
    I2cRegSim {0x20, 0x27, 2}, // VOUT_mode
    I2cRegSim {0x21, 0xBF, 2}, // VOUT_command
    I2cRegSim {0x25, 0x00, 2}, // VOUT_MARGIN_HIGH
    I2cRegSim {0x26, 0x00, 2}, // VOUT_MARGIN_LOW
    I2cRegSim {0x79, 0xA5, 2}, // STATUS_WORD
    I2cRegSim {0x88, 0xF029, 2}, // READ_VIN
    I2cRegSim {0x89, 0xD14F, 2}, // READ_IIN
    I2cRegSim {0x8B, 0x6F, 2}, // READ_VOUT
    I2cRegSim {0x8C, 0xD131, 2}, // READ_IOUT
    I2cRegSim {0x8D, 0xD14D, 2}, // READ_TEMP_1
    I2cRegSim {0x96, 0xD13C, 2}, // READ_POUT
    I2cRegSim {0x97, 0xD145, 2}, // READ_PIN
    I2cRegSim {0xAD, 0x59, 2}, // IC_DEVICE_ID
    I2cRegSim {0xD4, 0xD139, 2}, // MFR_SPECIFIC_04
    I2cRegSim {0xDB, 0xBF, 2}, // VOUT_command
}

var Tps549a20RegSim = []I2cRegSim {
    I2cRegSim {0x01, 0x00, 2}, // Operation
    I2cRegSim {0x02, 0x00, 2}, // on_off_config
    I2cRegSim {0x79, 0xA5, 2}, // STATUS_WORD
    I2cRegSim {0xD4, 0xD139, 2}, // MFR_SPECIFIC_04
}
func GetDefaultValue(regTbl []I2cRegSim, offset uint32, data []byte) int {
    for _, reg := range(regTbl) {
        if reg.offset == offset {
            misc.U32ToBytes(reg.value, data)
            return errType.SUCCESS
        }
    }
    return errType.FAIL
}

