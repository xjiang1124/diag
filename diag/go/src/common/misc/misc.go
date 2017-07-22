/*
    Package misc provides miscellenance functions
*/
package misc 

//import (
//    "fmt"
//)

//========================================================
// Constant definition

//========================================================
// Global variables

//========================================================

/* 
    GetElemIdx finds index of given element in the slice
    If element is not found, return nil
*/
func GetElemIdx(inList []string, elem string) (idx int) {
    for i, v := range inList {
        if v == elem {
            return i
        }
    }

    return -1
}

func ContainStr(s []string, e string) bool {
    for _, a := range s {
        if a == e {
            return true
        }
    }
    return false
}
