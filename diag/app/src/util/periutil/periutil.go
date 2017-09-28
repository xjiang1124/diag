package main

import (
    "flag"
    "fmt"

    "common/cli"
    "common/errType"
    "common/i2c"
    "common/misc"

    "config"

    "hardware/hwdev"
)

const (
    OP_I2C = 0
    OP_SPI = 1
    OP_QSPI = 2
)

func init() {
    cli.Init("log_periutil.txt", config.OutputMode)
}

func main() {
    var opMode int

    devNamePtr := flag.String("n", "", `Device name; list as following 
        FRU
        QSFP_0_A0
        QSFP_0_A2
        QSFP_1_A0
        QSFP_1_A2
        RTC
        TEMP_SENSOR
        VRM_CAPRI_DVDD
        VRM_CAPRI_AVDD
        VRM_HBM
        VRM_ARM`)
    rPtr := flag.Bool("r", false, "Read operation")
    wPtr := flag.Bool("w", false, "Write operation")
    oPtr := flag.Uint64("o", 0, "Offset")
    dPtr := flag.Uint64("dt", 0, "Data to be written")
    nPtr := flag.Uint64("nb", 1, "Number of bytes")
    flag.Parse()

    if *devNamePtr == "" ||
       (*rPtr == true && *wPtr == true) ||
       (*rPtr == true && *nPtr == 0) {
        flag.Usage()
        return
    }
    cli.Println("i", "Devname:", *devNamePtr, "; R:", *rPtr, "; W:", *wPtr, "; Data:", *dPtr, "; Number of bytes:", *nPtr)

    if misc.HasElem(hwdev.I2cTbl, *devNamePtr) == true {
        opMode = OP_I2C
    } else {
        cli.Println("E", "Wrong device name")
        flag.Usage()
        return
    }
    if *rPtr == true {
        if opMode == OP_I2C {
            data, err := i2c.Read(*devNamePtr, *oPtr, *nPtr)
            if err != errType.SUCCESS {
                outPtr := fmt.Sprintf("Failed to read I2C dev: dev=%s; offset=0x%x; numBytes=%d", *devNamePtr, *oPtr, *nPtr)
                cli.Println("e", outPtr)
            } else {
                dataU64 := misc.BytesToU64(data, *nPtr)
                //cli.Println("e", "Read data", dataU64)
                outPtr := fmt.Sprintf("Read data: dev=%s; offset=0x%X; numBytes=%d; data=0x%X", *devNamePtr, *oPtr, *nPtr, dataU64)
                cli.Println("i", outPtr)
                return
            }
        }

    }
}

