// dcli package wraps the function of cli and adds output to 
// redis

package dcli

import (
    "fmt"
    "os"
    "strconv"

    "common/cli"
    "common/misc"
    "common/diagEngine"

    "github.com/go-redis/redis"
)

// redis client
var r *redis.Client

func Init(fileName string) {
    cli.Init(fileName)

    redisIP := os.Getenv("REDIS_IP")
    r = redis.NewClient(&redis.Options{
        Addr:       redisIP+":6379",
        Password:   "",
        DB:         0,
    })
}

func Println(lvl string, a...interface{}) (err error) {
    cli.Println(lvl, a)

    outStr := fmt.Sprintln(a)
    // fmt.Sprintln add "[ ]\n" at begining and end of the string. 
    // Remove the extra stuff
    outStr = misc.TrimSuffix(outStr, "]\n")
    outStr = misc.TrimPrefix(outStr, "[")

    r.LPush("dshbuf:"+strconv.Itoa(diagEngine.DshID), outStr)

    return nil
}
