/*
    Package misc provides miscellenance functions
*/
package misc

import (
    //"fmt"
    "strings"
    "time"

    "common/errType"
)

//========================================================
// Constant definition

//========================================================
// Global variables

//========================================================

/*
    Twos complement with given number of bits
    Effective bits should be already shited to the right side
 */
func TwoCmplBits(data uint32, numBits uint32) (retVal int, err int) {
    var msb uint32

    if numBits == 0 {
        return 0, errType.Invalidparam
    }

    // Remove upper bits just in case
    data = data & (1 << numBits - 1)

    msb = 1 << (numBits - 1)
    sign := data & msb

    retVal = int(data)
    if sign == 0 {
        return retVal, errType.Success
    }

    // Negative number, make upper bits all one
    data = data | (^(1 << numBits - 1))
    retVal = int((^data + 1)) * (-1)

    return retVal, errType.Success
}

/*
    Convert uint32 into 4 byte slice
 */
func U32ToBytes(dataU32 uint32, byteArr []byte) {
    for i:=0; i<4; i++ {
        byteArr[i] = byte(dataU32 & 0xFF)
        dataU32 = dataU32 >> 8
    }
}

/*
    Convert uint32 into 4 byte slice
 */
func BytesToU32(dataU32 *uint32, byteArr []byte) {
    *dataU32 = 0
    for i:=0; i<4; i++ {
        *dataU32 = (*dataU32 << 8) | uint32(byteArr[3-i])
    }
}

/*
    Sleep function in second
 */
func SleepInSec(numSec int) {
    time.Sleep(time.Duration(numSec) * time.Second)
}


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
    RmStrFromSlice removes string from given slice
*/
func RmStrFromSlice(target []string, src string) []string {
    for idx, t := range target {
        if t == src {
            return append(target[:idx], target[idx+1:]...)
        }
    }
    return target
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

