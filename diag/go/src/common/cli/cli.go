/*
    Package cli provides output functionalities
 */

package cli

import (
    "encoding/json"
    "fmt"
    "io"
    "log"
    "os"
    "runtime"
    "time"
    "strings"

    "common/misc"
)

var (
    Debug   *log.Logger
    Info    *log.Logger
    Warning *log.Logger
    Error   *log.Logger
)

type OutputFmt struct {
    timeStamp int
    outStr int
}

var OutputMode int

func Init(fileName string, mode int) {
    OutputMode = mode

	multi := io.MultiWriter(os.Stdout)
    if fileName != "" {
        file, err := os.OpenFile(fileName, os.O_CREATE|os.O_WRONLY|os.O_TRUNC|os.O_SYNC|os.O_APPEND, 0666)
        if err != nil {
            log.Fatal("Open file failed!", fileName)
        }
        multi = io.MultiWriter(os.Stdout, file)
    }

	var debugHandle io.Writer = multi
	var infoHandle io.Writer = multi
	var warningHandle io.Writer = multi
	var errorHandle io.Writer = multi

	Debug = log.New(debugHandle,    "[DEBUG]:   ", 0)

    Info = log.New(infoHandle,      "[INFO]:    ", 0)

    Warning = log.New(warningHandle,"[WARNING]: ", 0)

    Error = log.New(errorHandle,    "[ERROR]:   ", 0)
}

func unixMilli(t time.Time) int64 {
        return t.Round(time.Millisecond).UnixNano() / (int64(time.Millisecond) / int64(time.Nanosecond))
}

func makeTimestampMilli() int64 {
        return unixMilli(time.Now())
}

func TStamp() string {
	m := makeTimestampMilli()
    timeStr := fmt.Sprintln(time.Unix(m/1e3, (m%1e3)*int64(time.Millisecond)/int64(time.Nanosecond)))
    timeStrs := strings.Split(timeStr, " ")

    return timeStrs[0]+"-"+timeStrs[1]
}

func FmtJsonOut(outStr string) string {
    //m := OutputFmt{TStamp(), outStr}
    //m := map[string]string{"timestamp": "12345", "outStr": "outStrO"}
    m := make(map[string]string)
    m["timestamp"] = TStamp()
    m["LOG"] = outStr
    b, _ := json.Marshal(m)

    jsonOut := fmt.Sprintln(string(b))
    //fmt.Println(jsonOut)
    return jsonOut
}

// Println outputs per desired log level
func Println(lvl string, a...interface{}) (err error) {

    outStr := fmt.Sprintln(a)
    // fmt.Sprintln add "[ ]\n" at begining and end of the string. 
    // Remove the extra stuff
    outStr = misc.TrimSuffix(outStr, "]\n")
    outStr = misc.TrimPrefix(outStr, "[")

    switch lvl {
    case "debug", "d":
        // Debug print, give file and line number
        _, fn, line, _ := runtime.Caller(1)
        fnArr := strings.Split(fn, "/")
        fnOnly := fnArr[len(fnArr)-1]
        if (fnOnly == "dcli.go") {
            _, fn, line, _ = runtime.Caller(2)
            fnArr = strings.Split(fn, "/")
            fnOnly = fnArr[len(fnArr)-1]
        }
        outStr = fmt.Sprintln(fnOnly, line, outStr)
    default:
    }

    timeStr := TStamp()

    // Control output for special format
    if (OutputMode == 1) {
        outStr = FmtJsonOut(outStr)
    } else {
        outStr = "["+timeStr+"]"+" "+outStr
    }

    switch lvl {
    case "debug", "d":
        Debug.Println(outStr)
    case "info", "i":
        Info.Println(outStr)
    case "warn", "w":
        Warning.Println(outStr)
    case "error", "e":
        Error.Println(outStr)
    default:
        Debug.Println(outStr)
    }

    return nil
}

