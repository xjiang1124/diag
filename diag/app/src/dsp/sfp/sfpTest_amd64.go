//AMD64 BUILD.  DO NOT MESS WITH THE LINE BELOW


// +build amd64

//CODE AND COMMENTS BELOW THIS


package main

import (
    "flag"
    "common/dcli"
    "common/diagEngine"
    "platform/taormina"
) 

func SfpI2CHdl(argList []string) {

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    ret := taormina.Sfp_i2c_test(argList)
    diagEngine.FuncMsgChan <- ret
    return
}

func SfpLaserHdl(argList []string) {
    
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    ret := taormina.Sfp_signal_test(argList)
    diagEngine.FuncMsgChan <- ret
    return
}
