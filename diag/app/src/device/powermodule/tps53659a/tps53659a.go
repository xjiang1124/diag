package tps53659a

import (
    //"bufio"
    //"encoding/hex"
    //"fmt"
    //"math"
    //"os"
    //"reflect"
    //"sort"
    //"strings"

    "device/powermodule/tps53659"
    //"common/errType"
    //"common/misc"
    //"hardware/i2cinfo"
    //"hardware/pmbus"
    //"protocol/pmbus"
)

const (
    DEVICE_ID = 0x5a
    VERIFY_FLAG = "=== READ VERIFY ==="
)

func ReadStatus(devName string) (status uint16, err int) {

    status, err = tps53659.ReadStatus(devName)
    return
}


func ReadVout(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadVout(devName)
    return
}

func ReadVboot(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadVboot(devName) 
    return 
}

func ReadIout(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadIout(devName)
    return
}

func ReadIoutPhase(devName string, phase byte) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadIoutPhase(devName, phase)
    return
}

/*
    Read register with linear 11 format and calculate output
 */
func ReadRegLnr11(devName string, cmd uint64) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadRegLnr11(devName, cmd)
    return
}

func ReadVin(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadVin(devName)
    return
}

func ReadIin(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadIin(devName)
    return
}

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadTemp(devName)
    return
}

func ReadPout(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadPout(devName)
    return
}

func ReadPin(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadPin(devName)
    return
}

func ReadPinMax10(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadPinMax10(devName)
    return
}

func ReadVoutLn(devName string) (integer uint64, dec uint64, err int) {

    integer, dec, err = tps53659.ReadVoutLn(devName)
    return
}

func ReadDeviceID(devName string) (devID byte, err int) {

    devID, err = tps53659.ReadDeviceID(devName)
    return devID, err
}

func FindVid(devName string, voutMv uint64) (vid byte, err int) {

    vid, err = tps53659.FindVid(devName, voutMv)
    return
}

func UpdateVboot(devName string, tgtVoutMv uint64) (err int) {

    err = tps53659.UpdateVboot(devName, tgtVoutMv)
    return
}

func SetVMarginByValue(devName string, tgtVoutMv uint64) (err int) {

    err = tps53659.SetVMarginByValue(devName, tgtVoutMv)
    return
}

func SetVMargin(devName string, pct int) (err int) {

    err = tps53659.SetVMargin(devName, pct)
    return
}


func DispStatus(devName string) (err int) {

    err = tps53659.DispStatus(devName)
    return
}

func ProgramVerifyNvm(devName string, fileName string, mode string, verbose bool) (err int) {

    err = tps53659.ProgramVerifyNvm(devName, fileName, mode, verbose)
    return
}

func Info(devName string) (err int) {

    err = tps53659.Info(devName)
    return
}


