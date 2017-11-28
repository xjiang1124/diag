package dmutex

import (
    "strings"

    "github.com/alexflint/go-filemutex"

    "common/cli"
    "common/errType"
    //"config"
)

type mutexInfo struct {
    mHdl *filemutex.FileMutex
    mName string
}

var mutexTbl = []mutexInfo {
    mutexInfo {mName: "QSFP_0"},
    mutexInfo {mName: "TEMP_SENSOR"},
    mutexInfo {mName: "VRM_CAPRI"},
    mutexInfo {mName: "VRM_3V3"},
    mutexInfo {mName: "VRM_1V2"},
}

func init() {
    for i, _ := range(mutexTbl) {
        //lockName := config.DiagNicBinPath+mutexTbl[i].mName+".lock"
        lockName := "/tmp/"+mutexTbl[i].mName+".lock"
        m, err := filemutex.New(lockName)
        if err != nil {
            cli.Println("e", "Failed to initialize lock:", lockName)
        }
        mutexTbl[i].mHdl = m
    }
}

func Lock(mName string) (err int){
    for i, _ := range(mutexTbl) {
        if strings.Contains(mName, mutexTbl[i].mName) == true {
            mutexTbl[i].mHdl.Lock()
            return
        }
    }
    return errType.INVALID_LOCK
}

func Unlock(mName string) {
    for _, m := range(mutexTbl) {
        if strings.Contains(mName, m.mName) == true {
            m.mHdl.Unlock()
        }
    }
}

func TestLock() {
    //lockName := config.DiagNicBinPath+"temp"
    //lockName := "/tmp/foo.lock"
    lockName := "/home/xguo2/workspace/psdiag/diag/app/src/common/dmutex/foo.lock"
    m, err := filemutex.New(lockName)
    if err != nil {
        cli.Println("Directory did not exist or file could not created")
    }
    m.Lock()
    m.Unlock()
}


