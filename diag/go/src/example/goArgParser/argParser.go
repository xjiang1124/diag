package main

import (
    "fmt"
    "flag"
)

func TestParser(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    intArgPtr := fs.Int("int", 101, "Integer arguement")

    fmt.Println("init val: ", *intArgPtr)
    err := fs.Parse(argList)
    if err != nil {
        fmt.Println("Parse failed")
    }
    fmt.Println("final val: ", *intArgPtr)
    fmt.Println("Parsed:", fs.Parsed())


}

func main() {
    //================================
    TestParser([]string{"-int", "1"})
    //TestParser([]string{"-int"})
    TestParser([]string{"int", "1"})
    TestParser([]string{"-int", "sa1"})
}

