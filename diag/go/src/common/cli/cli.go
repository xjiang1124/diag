/*
    Package cli provides output functionalities
 */

package cli

import (
    "fmt"
    "os"
    "io"
    "log"

    "common/misc"
)

var (
    Trace   *log.Logger
    Info    *log.Logger
    Warning *log.Logger
    Error   *log.Logger
)

func Init(fileName string) {
	multi := io.MultiWriter(os.Stdout)
    if fileName != "" {
        file, err := os.OpenFile(fileName, os.O_CREATE|os.O_WRONLY|os.O_TRUNC|os.O_SYNC|os.O_APPEND, 0666)
        if err != nil {
            log.Fatal("Open file failed!", fileName)
        }
        multi = io.MultiWriter(os.Stdout, file)
    }

	var traceHandle io.Writer = multi
	var infoHandle io.Writer = multi
	var warningHandle io.Writer = multi
	var errorHandle io.Writer = multi

	Trace = log.New(traceHandle, "TRACE: ", 0)

    Info = log.New(infoHandle, "INFO: ", 0)

    Warning = log.New(warningHandle, "WARNING: ", 0)

    Error = log.New(errorHandle, "ERROR: ", 0)
}

// Println outputs per desired log level
func Println(lvl string, a...interface{}) (err error) {

    outStr := fmt.Sprintln(a)
    // fmt.Sprintln add "[ ]\n" at begining and end of the string. 
    // Remove the extra stuff
    outStr = misc.TrimSuffix(outStr, "]\n")
    outStr = misc.TrimPrefix(outStr, "[")
    switch lvl {
    case "trace", "t":
        Trace.Println(outStr)
    case "info", "i":
        Info.Println(outStr)
    case "warn", "w":
        Warning.Println(outStr)
    case "error", "e":
        Error.Println(outStr)
    default:
        Trace.Println(outStr)
    }

    return nil
}

