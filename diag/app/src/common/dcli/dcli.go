// dcli package wraps the function of cli and adds output to 
// redis

package dcli

import (
    //"encoding/json"
    "fmt"
    "os"
    //"runtime"
    //"strings"
    "strconv"

    "common/cli"
    //"common/misc"
    "common/diagEngine"

    "github.com/go-redis/redis"
)

const (
    INIT_NONE = 0
    INIT_DONE = 1
)

var initStatus int = INIT_NONE

// redis client
var r *redis.Client

// Output mode
var outputMode int

var cardPre string

func TimeStampEnable (enaDis int) {
    cli.TimeStampEnable(enaDis)
}

func Init(fileName string, mode int) {
    cli.Init(fileName, mode)

    redisIP := os.Getenv("REDIS_IP")
    r = redis.NewClient(&redis.Options{
        Addr:       redisIP+":6379",
        Password:   "",
        DB:         0,
    })
    outputMode = mode
    initStatus = INIT_DONE

    cardInfo := diagEngine.GetCardInfo()
    cardPre = cardInfo.CardType+"#"+cardInfo.CardName

}

func Println(lvl string, a...interface{}) (err error) {
    cli.Println(lvl, a)

    if initStatus == INIT_NONE {
        return nil
    }

    outStr := fmt.Sprintln(a)
    outStr = cli.FormatOutput(lvl, outStr)

    switch lvl {
    case "debug", "d":
        outStr = fmt.Sprintf("[DEBUG]   %s", outStr)
    case "info", "i":
        outStr = fmt.Sprintf("[INFO]    %s", outStr)
    case "warn", "w":
        outStr = fmt.Sprintf("[WARNING] %s", outStr)
    case "error", "e", "f":
        outStr = fmt.Sprintf("[ERROR]   %s", outStr)
    //default:
        // Do nothing
	}
    outStr = "["+cardPre+"]" + outStr

    r.LPush("dshbuf:"+strconv.Itoa(diagEngine.DshID), outStr)

    return nil
}

func Printf(lvl string, format string, a ...interface{}) error {
    outStr := cli.FormatOutput1(lvl, format, a)

    switch lvl {
    case "debug", "d":
        outStr = fmt.Sprintf("[DEBUG]   %s", outStr)
    case "info", "i":
        outStr = fmt.Sprintf("[INFO]    %s", outStr)
    case "warn", "w":
        outStr = fmt.Sprintf("[WARNING] %s", outStr)
    case "error", "e", "f":
        outStr = fmt.Sprintf("[ERROR]   %s", outStr)
    default:
        outStr = fmt.Sprintf("[DEBUG]   %s", outStr)
	}

    if initStatus != INIT_NONE {
        outStr = "["+cardPre+"]" + outStr
    }

    fmt.Printf("%s", outStr)

    if initStatus == INIT_NONE {
        return nil
    }

    r.LPush("dshbuf:"+strconv.Itoa(diagEngine.DshID), outStr)

    return nil
}
