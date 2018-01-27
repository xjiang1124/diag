package dmutex

import (
    "strconv"

    "github.com/alexflint/go-filemutex"

    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
)

type mutexInfo struct {
    mHdl *filemutex.FileMutex
    mName string
}

var mutexMap map[string]*filemutex.FileMutex

func init() {
    mutexMap = make(map[string]*filemutex.FileMutex)
    for _, i2cInfo := range(i2cinfo.I2cTbl) {
        lockName := "/tmp/"+"i2c-"+strconv.Itoa(int(i2cInfo.Bus))+".lock"
        m, err := filemutex.New(lockName)
        if err != nil {
            cli.Println("e", "Failed to initialize lock:", lockName)
            continue
        }
        mutexMap[i2cInfo.Name] = m
    }

}

func Lock(mName string) (err int){
    mHdl, ok := mutexMap[mName]
    if ok == false {
        err = errType.INVALID_LOCK
        return
    }
    mHdl.Lock()
    return
}

func Unlock(mName string) (err int) {
    mHdl, ok := mutexMap[mName]
    if ok == false {
        err = errType.INVALID_LOCK
        return
    }
    mHdl.Unlock()
    return

}


