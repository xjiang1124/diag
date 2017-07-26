/*
    Package misc provides miscellenance functions
*/
package misc 

import (
    "strings"
)

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

/*
    ContainStr checks whether src string contains any of element
    in target slice
 */
func ContainStr(target []string, src string) bool {
    for _, t := range target {
        if strings.Contains(src, t) {
            return true
        }
    }
    return false
}

/*
    ContainStr checks whether src string exactly match any element
    in the target slice
 */
func ContainStrExact(target []string, src string) bool {
    for _, t := range target {
        if t == src {
            return true
        }
    }
    return false
}

/*
	TrimSuffix trims the last charaters from the given string
 */
func TrimSuffix(s, suffix string) string {
    if strings.HasSuffix(s, suffix) {
        s = s[:len(s)-len(suffix)]
    }
    return s
}

/*
	TrimPrefix trims the first charaters from the given string
 */
func TrimPrefix(s, prefix string) string {
    if strings.HasPrefix(s, prefix) {
        s = s[len(prefix):]
    }
    return s
}

