/*
    Package misc provides miscellenance functions
*/
package misc

import (
    "fmt"
    "math/rand"
    "os"
    "reflect"
    "strings"
    "syscall"
    "time"
    "unsafe"

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

    ENABLE = 1
    DISABLE = 0

    STR_MAX_SIZE = 20 // 20 bytes
)

//========================================================
// Global variables

//========================================================


/* 
    Memory Mapped uint32 read from the address
*/
func ReadU32(addr uint64) (value uint32, err error) {
    pageSize := syscall.Getpagesize()
    pageSize64 := uint64(pageSize)
    pageAddr := addr / pageSize64 * pageSize64
    pageOffset := addr - pageAddr

    file, err := os.Open("/dev/mem")
    if err != nil {
        fmt.Printf("ERROR: os.Open /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err)
        return
    }

    /* defer file.Close() */
    mmap, err := syscall.Mmap(int(file.Fd()), int64(pageAddr), pageSize, syscall.PROT_READ, syscall.MAP_SHARED)
    file.Close()
    if err != nil {
        fmt.Printf("ERROR: syscall.Mmap /dev/mem failed.  Err !=nil:   ERR = '%s'\n", err)
        return
    }
    value = *(*uint32)(unsafe.Pointer(&mmap[pageOffset]))
    err = syscall.Munmap(mmap) 
    if err != nil {
        fmt.Printf("ERROR: syscall.Munmap failed.  Err !=nil:   ERR = '%s'\n", err)  
        return 
    }
    return
}


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

func GetOnes(data int) (ones int) {
    ones = data % 10
    return
}

func GetTens(data int) (tens int) {
    tens = (data/10) % 10
    return
}


func StringInSlice(a string, list []string) bool {
    for _, b := range list {
        if b == a {
            return true
        }
    }
    return false
}

/**
 * Concatenate two byte slice
 */
func ByteSliceAppend(slice1 []byte, slice2 []byte) (slice []byte) {
    len1 := len(slice1)
    len2 := len(slice2)
    slice = make([]byte, len1+len2)

    for i:=0; i<len1; i++ {
        slice[i] = slice1[i]
    }

    for i:=0; i<len2; i++ {
        slice[i+len1] = slice2[i]
    }
    return
}

/**
 * Generate byte slice with random value
 */
func GenRandByteSlice(numBytes int) (data []byte) {
    data = make([]byte, numBytes)
    for i:=0; i<numBytes; i++ {
        rand.Seed(time.Now().UnixNano())
        data[i] = byte(rand.Intn(0xFF))
    }
	return
}

/**
 * Swap bytes in a word
 */
func SwapUint16(a uint16) (b uint16) {
    b = ( uint16(a >> 8) | uint16(a << 8) )
    return
}

/*
    Converts a character to its 6-bit ASCII representation.
 */
func CharTo6BitAscii(c byte) (val int, err int) {
	if c >= 0x20 && c <= 0x5F {
		return int(c - 0x20), errType.SUCCESS
	} else {
        fmt.Printf("character '%c' is outside the printable ASCII range (0x20 to 0x5F) and does not have a valid 6-bit ASCII representation\n", c)
		return -1, errType.INVALID_PARAM
	}
}

/*
    Packs a string into a 6-bit ASCII representation.
 */
 
func StrToAsc6(input string) (output []byte, err int) {
	output = make([]byte, STR_MAX_SIZE)
	j := 0
	var bitCount uint32  = 0
	var currentByte byte

    if len(input) > STR_MAX_SIZE*8/6 {
        fmt.Printf("Error: Input string exceeds maximum length of 20 bytes.\n")
        return nil, errType.INVALID_PARAM
    }


	for i := 0; i < len(input); i++ {
		asciiVal, err := CharTo6BitAscii(input[i])
		if err != errType.SUCCESS {
			return nil, errType.FAIL
		}
		currentByte |= byte(asciiVal << bitCount)
		bitCount += 6

		// Update current byte if it is full (8 bits)
		if bitCount >= 8 {
			output[j] = currentByte
			j++
			bitCount -= 8
			currentByte = byte(asciiVal >> (6 - bitCount))
		}
	}

	// Flush the last byte if there are remaining bits
	if bitCount > 0 && j < STR_MAX_SIZE {
		output[j] = currentByte
	}

	return output, errType.SUCCESS
}


/*
    Converts a 6-bit ASCII value to its character representation
 */
func SixBitAsciiToChar(val int) (output int, err int) {
	if val >= 0 && val <= 0x3F {
		return val + 0x20, errType.SUCCESS
	} else {
        fmt.Printf("6-bit value %d is outside the valid range (0 to 0x3F)\n", val)
		return -1, errType.INVALID_PARAM
	}
}

/*
    Unpacks a byte array from a 6-bit ASCII representation back into a string.
 */
func Asc6ToStr(input []byte) (str string, err int) {
	output := make([]byte, 0, len(input)*8/6)
	var bitCount uint32 = 0
	var currentVal int

    if len(input) > STR_MAX_SIZE {        
        fmt.Printf("Error: Input byte array exceeds maximum length of 20 bytes.\n")
        return "", errType.INVALID_PARAM
    }

	for i := 0; i < len(input); i++ {
		currentVal |= int(input[i]) << bitCount
		bitCount += 8

		for bitCount >= 6 {
			charVal := currentVal & 0x3F
            
			char, err := SixBitAsciiToChar(charVal)
			if err != errType.SUCCESS {
                fmt.Printf("Error at byte %d\n", i)
				return "", errType.FAIL
			}
			output = append(output, byte(char))
			bitCount -= 6
			currentVal >>= 6
		}
	}
    
    if currentVal > 0 {
        fmt.Printf("Error: Input byte array contains extra digits 0x%X\n", currentVal)
        return "", errType.FAIL
    }

	return string(output), errType.SUCCESS
}
