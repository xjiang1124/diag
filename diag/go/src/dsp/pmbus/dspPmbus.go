package main
    
    import (
        "fmt"
        "flag"
        "common/diagEngine"
    )
    
    //========================================================
    // Constant definition
    const (
        // Each DSP should know it own name
        dspName = "PMBUS"
    )
    
    func PmbusPmbusHdl(argList []string) int {
        fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
        maskPtr := fs.Int("mask", 0xFF, "Devices bit mask")

    
        err := fs.Parse(argList)
        if err != nil {
            fmt.Println("Parse failed", err)
        }
    
        // To avoid compile error: variable not used
        fmt.Println("mask", *maskPtr)
    
        return 0
    }
    
    func PmbusIntrHdl(argList []string) int {
        fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
        maskPtr := fs.Int("mask", 0xFF, "Devices bit mask")

    
        err := fs.Parse(argList)
        if err != nil {
            fmt.Println("Parse failed", err)
        }
    
        // To avoid compile error: variable not used
        fmt.Println("mask", *maskPtr)
    
        return 0
    }
    
    func main() {
        diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
        diagEngine.FuncMap["PMBUS"] = PmbusPmbusHdl
    diagEngine.FuncMap["INTR"] = PmbusIntrHdl

        diagEngine.CardInfoInit(dspName)
        diagEngine.DspInfraInit()
        diagEngine.DspInfraMainLoop()
    }
    