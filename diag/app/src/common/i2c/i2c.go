// i2c.go specifies I2C wrapper for I2C library
package i2c

import (
    //"fmt"

    "config"
    "common/errType"
    "hardware/vrmsim"
)

func Read(i2cIdx uint32, devAddr uint32, offset uint32, data []byte, numBytes uint32) int {
    if config.SimMode == 1 {
        return ReadSim(i2cIdx, devAddr, offset, data, numBytes)
    }
    return errType.Success
}

func Write(i2cIdx uint32, devAddr uint32, offset uint32, data []byte, numBytes uint32) int {
    return errType.Success
}

func ReadSim(i2cIdx uint32, devAddr uint32, offset uint32, data []byte, numBytes uint32) int {
    retVal := errType.Success

    // vrm_capri
    if i2cIdx == 2 && devAddr == 0xc4  {
        retVal = vrmsim.GetDefaultValue(vrmsim.Tps53659RegSim, offset, data)
    }

    // vrm_capri
    if i2cIdx == 2 && (devAddr == 0x36 || devAddr == 0x38) {
        retVal = vrmsim.GetDefaultValue(vrmsim.Tps549a20RegSim, offset, data)
    }

    return retVal
}

