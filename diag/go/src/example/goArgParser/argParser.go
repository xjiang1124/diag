package main

import (
    "fmt"
    "flag"
)

func TestParser(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    intArgPtr := fs.Int("intArg", 101, "Integer arguement")
    strArgPtr := fs.String("strArg", "str", "String arguement")

    fmt.Println("init val: ", *intArgPtr)
    err := fs.Parse(argList)
    if err != nil {
        fmt.Println("Parse failed", err)
    }
    fmt.Println("final intArg: ", *intArgPtr)
    fmt.Println("final strArg: ", *strArgPtr)
    fmt.Println("Parsed:", fs.Parsed())
    fmt.Println("//================================")
}

func main() {
    //================================
    TestParser([]string{"-intArg", "1"})
    TestParser([]string{"-intArg", "1", "-strArg", "str2"})
    TestParser([]string{"-intArg", "1", "-strArg"})
    TestParser([]string{})
}

