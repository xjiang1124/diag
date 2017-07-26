/*
    Package cli provides output functionalities including
    log/terminal/diag-cli with desired format
 */

package cli

import (
    "fmt"
	"os"
    "strings"
    "io"
    "common/misc"
    logrus "github.com/Sirupsen/logrus"
)

//========================================================
// Constant definition


//========================================================
// Global variables

// diag shell ID. Used to direct output to dsh
var dShellID  int = 0
var logFile string = ""
var logLvl logrus.Level = logrus.DebugLevel
var logger *logrus.Logger
var file *os.File

//========================================================
func Init(fileName string) {
    logger = logrus.New()

    if fileName != "" {
        //file, err := os.OpenFile(fileName, os.O_CREATE|os.O_WRONLY|os.O_TRUNC|os.O_SYNC|os.O_APPEND, 0666)
        //if err != nil {
        //    logrus.Fatal(err)
        //}
        //logFile = fileName
        //logger.Out = file
        multi := io.MultiWriter(os.Stdout)
        //multi := io.MultiWriter(file)
        logger.Out = multi
    } else {
        // Default ouput option is stdout
        multi := io.MultiWriter(os.Stdout)
        logger.Out = multi
    }
    logger.Level = logLvl
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
        logger.Debug(outStr)
    case "info", "i":
        logger.Info(outStr)
    case "warn", "w":
        logger.Warn(outStr)
    case "error", "e":
        logger.Error(outStr)
    case "panic", "p":
        logger.Error(outStr)
    default:
        logger.Debug(outStr)
    }

    return nil
}

// SetLogLvl sets log output levels
func SetLogLvl(lvl string) (err error) {
    lvl = strings.ToLower(lvl)
    allLvls := []string{"debug", "d", "info", "i", "warn", "w", "warning", "wn", "error", "e", "panic", "p"}
    if misc.ContainStrExact(allLvls, lvl) == true {
        switch lvl {
        case "debug", "d":
            logLvl = logrus.DebugLevel
        case "info", "i":
            logLvl = logrus.InfoLevel
        case "warn", "w":
            logLvl = logrus.WarnLevel
        case "error", "e":
            logLvl = logrus.ErrorLevel
        case "panic", "p":
            logLvl = logrus.PanicLevel
        default:
            logLvl = logrus.DebugLevel
        }
        logger.Level = logLvl
        return nil
    } else {
        return nil
    }
}

// 
func setOutput(output string) (err error) {
    if output == "file" {
        if logFile != "" {
            file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_TRUNC|os.O_SYNC|os.O_APPEND, 0666)
            if err != nil {
                logrus.Fatal(err)
            }
            logger.Out = file
        }
    }
    if output == "stdout" {
        logger.Out = os.Stdout
    }
    return nil
}
