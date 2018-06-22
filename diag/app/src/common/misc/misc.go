/*
    Package misc provides miscellenance functions
*/
package misc

import (
    //"fmt"
    "reflect"
    "strings"
    "time"

    "common/errType"
)

//========================================================
// Constant definition
const (
    ONE_BYTE = 1
    TWO_BYTE = 2
    FOUR_BYTE = 4

    BITS_8 = 8
    BITS_16 = 16
    BITS_32 = 32

)

//========================================================
// Global variables

//========================================================

/*
    Integer verion of min
 */
func Min(a, b int) int {
    if a < b {
        return a
    }
    return b
}

/*
    Check whether  s has element of elem
 */
func HasElem(s interface{}, elem interface{}) bool {
    arrV := reflect.ValueOf(s)

    if arrV.Kind() == reflect.Slice {
        for i := 0; i < arrV.Len(); i++ {
            // XXX - panics if slice element points to an unexported struct field
            // see https://golang.org/pkg/reflect/#Value.Interface
            if arrV.Index(i).Interface() == elem {
                return true
            }
        }
    }

    return false
}

/*
    Read modify write    
*/
func Rmw32(origData uint32, newData uint32, startBit uint32, numBits uint32) (retVal uint32, err int) {
    var mask uint32

    mask = (1 << numBits - 1) << startBit
    retVal = (origData & mask) | ((newData << startBit) & mask)
    return
}
/*
    Twos complement with given number of bits
    Effective bits should be already shited to the right side
 */
func TwoCmplBits32(data uint32, numBits uint32) (retVal int, err int) {
    var msb uint32

    if numBits == 0 || numBits > 32 {
        return 0, errType.INVALID_PARAM
    }

    // Remove upper bits just in case
    data = data & (1 << numBits - 1)

    msb = 1 << (numBits - 1)
    sign := data & msb

    retVal = int(data)
    if sign == 0 {
        return retVal, errType.SUCCESS
    }

    // Negative number, make upper bits all one
    data = data | (^(1 << numBits - 1))
    retVal = int((^data + 1)) * (-1)

    return retVal, errType.SUCCESS
}
/*
    Twos complement with given number of bits
    Effective bits should be already shited to the right side
 */
func TwoCmplBits64(data uint64, numBits uint64) (retVal int64, err int) {
    var msb uint64

    if numBits == 0 || numBits > 64 {
        return 0, errType.INVALID_PARAM
    }

    // Remove upper bits just in case
    data = data & (1 << numBits - 1)

    msb = 1 << (numBits - 1)
    sign := data & msb

    retVal = int64(data)
    if sign == 0 {
        return retVal, errType.SUCCESS
    }

    // Negative number, make upper bits all one
    data = data | (^(1 << numBits - 1))
    retVal = int64((^data + 1)) * (-1)

    return retVal, errType.SUCCESS
}

/*
    Convert byte slice to uint32
 */
func BytesToU32(byteArr []byte, numBytes uint64) (dataU32 uint32) {
    dataU32 = 0
    var i uint64
    for i=0; i<numBytes; i++ {
        dataU32 = (dataU32 << 8) | uint32(byteArr[numBytes-i-1])
    }
    return

}
/*
    Convert byte slice to uint64
 */
func BytesToU64(byteArr []byte, numBytes uint64) (dataU64 uint64) {
    dataU64 = 0
    var i uint64
    for i=0; i<numBytes; i++ {
        dataU64 = (dataU64 << 8) | uint64(byteArr[numBytes-i-1])
    }
    return
}

/*
    Convert byte slice to uint16
 */
func BytesToU16(byteArr []byte, numBytes uint64) (dataU16 uint16) {
    dataU16 = 0
    var i uint64
    for i=0; i<numBytes; i++ {
        dataU16 = (dataU16 << 8) | uint16(byteArr[numBytes-i-1])
    }
    return dataU16
}

/*
    Convert byte slice to uint16
 */
func U64ToBytes(dataU64 uint64) (byteArr []byte) {
    byteArr = make([]byte, 8)
    for i:=0; i<8; i++ {
        byteArr[i] = byte(dataU64 & 0xFF)
        dataU64 = (dataU64 >> 8)
    }
    return
}

/*
    Convert byte slice to uint16
 */
func U32ToBytes(dataU32 uint32) (byteArr []byte) {
    byteArr = make([]byte, 4)
    for i:=0; i<4; i++ {
        byteArr[i] = byte(dataU32 & 0xFF)
        dataU32 = (dataU32 >> 8)
    }
    return
}

/*
    Convert byte slice to uint16
 */
func U16ToBytes(dataU16 uint16) (byteArr []byte) {
    byteArr = make([]byte, 2)
    for i:=0; i<2; i++ {
        byteArr[i] = byte(dataU16 & 0xFF)
        dataU16 = (dataU16 >> 8)
    }
    return
}

/*
    Sleep function in second
 */
func SleepInSec(numSec int) {
    time.Sleep(time.Duration(numSec) * time.Second)
}

/*
    Sleep function in micro-second
 */
func SleepInUSec(numUSec int) {
    time.Sleep(time.Duration(numUSec) * time.Microsecond)
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

/*
    Return keys of the given map
 */
func Keys(m map[string]interface{}) (keys []string) {
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}

func SetBits8(orig byte, val byte, startBit uint, numBits uint) (data byte, err int) {
    var mask byte
    if (startBit > 7) || (numBits > 8) {
        err = errType.INVALID_PARAM
    }

    if numBits == 8 {
        mask = 0xFF
    } else {
        mask = 1 << numBits
        mask = mask - 1
        mask = mask << startBit
    }

    data = orig & (^mask)
    data = data | (val << startBit)

    return
}

func ReverseSliceByte(data []byte) {
    dataLen := len(data)
    for i:=0; i < dataLen/2; i++ {
        temp := data[i]
        data[i] = data[dataLen - i - 1]
        data[dataLen - i - 1] = temp
    }
}

