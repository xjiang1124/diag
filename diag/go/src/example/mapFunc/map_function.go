package main

import (
	"fmt"
)

func handle1(str1 string, str2 string) {
	fmt.Printf("handle1 %s, %s\n", str1, str2)
}

func handle2(a int, b int) {
	fmt.Printf("handle2 %d, %d\n", a, b)
}

func main() {
	func_map := make(map[string]interface{})
	func_map["test1"] = handle1
	func_map["test2"] = handle2
	
	for k, _ := range func_map {
		switch k {
			case "test1":
				handle1("Hello", "world")
			case "test2":
				handle2(1, 2)
		}
	}
}
