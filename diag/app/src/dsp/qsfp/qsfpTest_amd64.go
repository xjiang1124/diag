//AMD64 BUILD.  DO NOT MESS WITH THE LINE BELOW


// +build amd64

//CODE AND COMMENTS BELOW THIS

package main

import (
    "flag"
    "common/dcli"
    "common/errType"
    "common/diagEngine"
    "platform/taormina"
)


func QsfpI2CHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
        diagEngine.FuncMsgChan <- errType.INVALID_PARAM
        return
    }

    ret := taormina.QsfpI2Ctest(argList)
    diagEngine.FuncMsgChan <- ret
    return
}

