package XeonD

import (
    "fmt"
    //"os"
    "strconv"
    "strings"
    "os/exec"
    //"cardinfo"
    "common/cli"
    "common/errType"
)

/*
Timestamp: 2021-05-27 23:06:02root@elba4-ipmi:/fs/nos/eeupdate# rdmsr 412 --all | cut -b 3-4 | while read x; do echo $((105 - 0x$x)); done
54
54
54
54
54
54
54
54
54
54
54
54
*/


func ReadTemp(devName string) (temps []int, err int) {
    var data64 int64
    var i int

    var args string = "rdmsr 412 --all | cut -b 3-4 | while read x; do echo $((105 - 0x$x)); done"
    output, errGo := exec.Command("bash", "-c", args).Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
        return
    }
    temperatures := strings.Split(string(output), "\n")
    temperatures = temperatures[:len(temperatures)-1]   //remove extra space which makes an entry
    for _, temp := range temperatures {
        data64, _ = strconv.ParseInt(temp, 16, 32)
        temps = append(temps, int(data64))
        i++
    }
    return
}


func GetTemperature(devName string) (temperatures []float64, err int) {
    temps := []int{}
    temps, err = ReadTemp(devName)
    for _, temp := range temps {
        out := fmt.Sprintf("%x", temp)
        dec, _ := strconv.ParseUint(out, 0, 32)
        temperatures = append(temperatures, float64(dec))
    }
    return
}




func DispStatus(devName string) (err int) {
    err = errType.SUCCESS

    degSym := fmt.Sprintf("(%cC)",0xB0)
    
    tmpStr := fmt.Sprintf("%-15s", devName+degSym)

    temps, err := ReadTemp(devName)
    if err != errType.SUCCESS {
        return err
    }

    for _, temp := range temps {
        tmpStr = fmt.Sprintf("%s %x", tmpStr, temp)
    }
    cli.Println("i", tmpStr)
    return
}


