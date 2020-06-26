package main

import (
    "common/diagEngine"
    "common/dcli"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "LED"
)


func init() {
    dcli.Init("log_"+dspName+".txt", config.OutputMode)

}
func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["LED"] = LedLedHdl
    diagEngine.FuncMap["led_green"] = LedAllGreenHdl
    diagEngine.FuncMap["led_amber"] = LedAllAmberHdl
    diagEngine.FuncMap["led_off"] = LedAllOffHdl

    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
