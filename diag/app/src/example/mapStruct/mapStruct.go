package main

import (
    "fmt"
)

type Info_t struct {
    write string
    numb int
}

var struct_map =  map[string]Info_t{}

func main() {

    struct_map = make(map[string]Info_t)
    struct_map["a"] = Info_t{"write", 2}

    fmt.Printf("Hello\n");
    fmt.Printf("map: %+v\n", struct_map)
    fmt.Print(struct_map)
}
