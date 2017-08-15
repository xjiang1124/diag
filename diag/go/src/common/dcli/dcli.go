// dcli package wraps the function of cli and adds output to 
// redis

package dcli

import (
    "fmt"
    "os"
    "strconv"
    "encoding/json"

    "common/cli"
    "common/misc"
    "common/diagEngine"

    "github.com/go-redis/redis"
)

// redis client
var r *redis.Client

// Output mode
var outputMode int

func Init(fileName string, mode int) {
    cli.Init(fileName, mode)

    redisIP := os.Getenv("REDIS_IP")
    r = redis.NewClient(&redis.Options{
        Addr:       redisIP+":6379",
        Password:   "",
        DB:         0,
    })
    outputMode = mode
}

func Println(lvl string, a...interface{}) (err error) {
    cli.Println(lvl, a)

    outStr := fmt.Sprintln(a)
    // fmt.Sprintln add "[ ]\n" at begining and end of the string. 
    // Remove the extra stuff
    outStr = misc.TrimSuffix(outStr, "]\n")
    outStr = misc.TrimPrefix(outStr, "[")

    cardInfo := diagEngine.GetCardInfo()
    cardPre := cardInfo.CardType+"#"+cardInfo.CardName
    // Structural output
    if (outputMode == 1) {
        var dat map[string]interface{}
        outStr = cli.FmtJsonOut(outStr)
        outStrByte := []byte(outStr)
        json.Unmarshal(outStrByte, &dat)
        //dat["CARD"] = diagEngine.CardInfo.CardType+"#"+diagEngine.CardInfo.CardName
        dat["CARD"] = cardInfo.CardType+"#"+cardInfo.CardName
        b, _ := json.Marshal(dat)
        outStr = fmt.Sprintln(string(b))
    } else {
        outStr = "["+cardPre+"]"+" ["+cli.TStamp()+"] " + outStr
    }

    r.LPush("dshbuf:"+strconv.Itoa(diagEngine.DshID), outStr)

    return nil
}
