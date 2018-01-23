package dmutex

import (
    "os"
    "strings"

    "github.com/alexflint/go-filemutex"

    "common/cli"
    "common/errType"
    "hardware/hwinfo"
    //"config"
)

type mutexInfo struct {
    mHdl *filemutex.FileMutex
    mName string
}

/*
var pwrMutexTbl = []mutexInfo {
    mutexInfo {mName: "QSFP_0"},
    mutexInfo {mName: "TEMP_SENSOR"},
    mutexInfo {mName: "VRM_CAPRI"},
    mutexInfo {mName: "VRM_3V3"},
    mutexInfo {mName: "VRM_1V2"},
}

var mtpMutexTbl = []mutexInfo {
    mutexInfo {mName: "PSU_0"},
    mutexInfo {mName: "PSU_1"},
    mutexInfo {mName: "DC"},
    mutexInfo {mName: "OSC"},
    mutexInfo {mName: "FAN_CTLR"},
}
*/

var mutexTbl  []mutexInfo

func init() {
    var mInfo mutexInfo
    cardName := os.Getenv("CARD_NAME")

    i2cTbl, err := hwinfo.GetI2cTable(cardName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to get I2C table: ", err)
        return
    }

    for _, i2cInfo := range(i2cTbl) {
        mInfo.mName = i2cInfo.Name
        lockName := "/tmp/"+mInfo.mName+".lock"
        m, err := filemutex.New(lockName)
        if err != nil {
            cli.Println("e", "Failed to initialize lock:", lockName)
        }
        mInfo.mHdl = m
        mutexTbl = append(mutexTbl, mInfo)
    }

/*
    if cardName == "NIC_POWER" {
        mutexTbl = pwrMutexTbl
    } else if cardName == "MTP" {
        mutexTbl = mtpMutexTbl
    } else {
        cli.Println("e", "Invalid card name:", cardName)
        return;
    }

    for i, _ := range(mutexTbl) {
        //lockName := config.DiagNicBinPath+mutexTbl[i].mName+".lock"
        lockName := "/tmp/"+mutexTbl[i].mName+".lock"
        m, err := filemutex.New(lockName)
        if err != nil {
            cli.Println("e", "Failed to initialize lock:", lockName)
        }
        mutexTbl[i].mHdl = m
    }
*/
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


