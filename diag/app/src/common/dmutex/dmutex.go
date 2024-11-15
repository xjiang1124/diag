package dmutex

import (
    "github.com/alexflint/go-filemutex"

    "common/cli"
    "common/errType"
)

type mutexInfo struct {
    mHdl *filemutex.FileMutex
    mName string
}

var mutexMap map[string]*filemutex.FileMutex
var lockList = []string{"i2c-0", "i2c-1", "i2c-2", "i2c-3", "i2c-4", "i2c-5", "i2c-6", "i2c-7", "i2c-8", "i2c-9", "i2c-10", "i2c-11", "i2c-12"}

func init() {
    mutexMap = make(map[string]*filemutex.FileMutex)
    for _, lock := range(lockList) {
        lockName := "/tmp/"+lock+".lock"
        m, err := filemutex.New(lockName)
        if err != nil {
            cli.Println("e", "Failed to initialize lock:", lockName)
            continue
        }
        mutexMap[lock] = m
    }
    //cli.Println("d", mutexMap)

}

func Lock(mName string) (err int){
    mHdl, ok := mutexMap[mName]
    if ok == false {
        cli.Println("e", "Faied to lock device:", mName)
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


