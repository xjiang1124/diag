package i2cPtcl

import (
    "golang.org/x/exp/io/i2c"
    "strconv"

    "common/cli"
    "common/errType"
)

var i2cDev *i2c.Device

func init() {
}

//func Open(devName string) (err int) {
func Open(devName string, bus uint32, devAddr byte) (err int) {
    var errgo error
    i2cDev, errgo = i2c.Open(&i2c.Devfs{Dev: "/dev/i2c-"+strconv.Itoa(int(bus))}, int(devAddr))
    if errgo != nil {
        cli.Println("e", "Can not open I3C interface:", errgo)
        err = errType.FAIL
    }
    return
}

func Close() {
    i2cDev.Close()
}

func Read(numBytes uint64) (data []byte, err int) {
    data = make ([]byte, numBytes)
    errgo := i2cDev.Read(data)
    if errgo != nil {
        cli.Println("e", "I2C read failed!e:", errgo)
        err = errType.FAIL
    }
    return
}

func Write(data []byte) (err int) {
    errgo := i2cDev.Write(data)
    if errgo != nil {
        cli.Println("e", "I2C read failed!e:", errgo)
        err = errType.FAIL
    }
    return
}
