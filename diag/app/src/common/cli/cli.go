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
    "strconv"
    "strings"
    "time"

    "common/misc"
    "config"
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

const (
    INIT_NONE = 0
    INIT_DONE = 1
)

var initStatus int = INIT_NONE

var OutputMode int

func Init(fileName string, mode int) {
    OutputMode = mode

    cardName := os.Getenv("CARD_NAME")
    path := config.DiagNicLogPath
    if cardName == "HOST" {
        path = config.DiagHostLogPath
    }
    // Create log folder if not exists
    _ = os.Mkdir(path, os.ModePerm)

	multi := io.MultiWriter(os.Stdout)
    if fileName != "" {
        //file, err := os.OpenFile(path+fileName, os.O_CREATE|os.O_WRONLY|os.O_TRUNC|os.O_SYNC|os.O_APPEND, 0666)
        file, err := os.OpenFile(path+fileName, os.O_CREATE|os.O_APPEND|os.O_WRONLY|os.O_SYNC, 0666)
        if err != nil {
            log.Fatal("Open file failed!", fileName)
        }
        multi = io.MultiWriter(os.Stdout, file)
    }

	var debugHandle io.Writer = multi
	var infoHandle io.Writer = multi
	var warningHandle io.Writer = multi
	var errorHandle io.Writer = multi

	Debug = log.New(debugHandle,    "[DEBUG]  ", 0)

    Info = log.New(infoHandle,      "[INFO]   ", 0)

    Warning = log.New(warningHandle,"[WARNING]", 0)

    Error = log.New(errorHandle,    "[ERROR]  ", 0)

    initStatus = INIT_DONE
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

func formatOutput(lvl string, pOutStr string) string {
    var outStr string
    // fmt.Sprintln add "[ ]\n" at begining and end of the string. 
    // Remove the extra stuff
    outStr = misc.TrimSuffix(pOutStr, "]\n")
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
        outStr = fmt.Sprintln("("+fnOnly, strconv.Itoa(line)+")", outStr)
    default:
    }

    timeStr := TStamp()

    // Control output for special format
    if (OutputMode == 1) {
        outStr = FmtJsonOut(outStr)
    } else {
        outStr = "["+timeStr+"]"+" "+outStr
    }
    return outStr
}

// Println outputs per desired log level
func Println(lvl string, a...interface{}) (err error) {

    outStr := fmt.Sprintln(a)
    outStr = formatOutput(lvl, outStr)

    if initStatus == INIT_DONE {
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
    } else {
        switch lvl {
        case "debug", "d":
            fmt.Println("[DEBUG]  ", outStr)
        case "info", "i":
            fmt.Println("[INFO]   ", outStr)
        case "warn", "w":
            fmt.Println("[WARNING]", outStr)
        case "error", "e":
            fmt.Println("[ERROR]  ", outStr)
        default:
            fmt.Println("[DEBUG]  ", outStr)
        }
    }
    return nil
}

func formatOutput1(lvl string, pOutStr string) string {
    var outStr string
    // fmt.Sprintln add "[ ]\n" at begining and end of the string. 
    // Remove the extra stuff
    //outStr = misc.TrimSuffix(pOutStr, "]\n")
    //outStr = misc.TrimPrefix(outStr, "[")
    outStr = pOutStr

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
        outStr = fmt.Sprintln("("+fnOnly, strconv.Itoa(line)+")", outStr)
    default:
    }

    timeStr := TStamp()

    // Control output for special format
    if (OutputMode == 1) {
        outStr = FmtJsonOut(outStr)
    } else {
        outStr = "["+timeStr+"]"+" "+outStr
    }
    return outStr
}

func Printf(lvl string, format string, a ...interface{}) error {

    outStr := fmt.Sprintf(format, a)
    outStr = formatOutput1(lvl, outStr)

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
