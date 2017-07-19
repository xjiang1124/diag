package main

import (
    "fmt"
    "os"
    "time"
    "runtime"
    "github.com/go-redis/redis"
)

// Constant definition
const (
    // Default timeout setting waiting for test to finish
    defaultTimeout = 30
    // Each DSP should know it own name
    dspName = "PMBUS"
    // Separator inside Redis key
    sep = ":"
)

type CardInfo struct {
    cardName string
    cardType string
    dspName string
}

var cardInfo CardInfo

func CardInfoInit() {
    // Card name and card type are from environment variable
    cardInfo.cardName = os.Getenv("CARD_NAME")
    cardInfo.cardType = os.Getenv("CARD_TYPE")
    cardInfo.dspName = dspName
}

func checkRedisErr(err error) {
    if err == redis.Nil {
        // Key not exist
    } else if err == nil {
        // No error happened
    } else {
        _, fileName, fileLine, _ := runtime.Caller(1)
        fmt.Println("err:", err, "fileName:", fileName, "fileLine", fileLine)
    }
}

func DspInfraInit(r *redis.Client) (err error) {
    //========================================================
    // Define all redis key here

    // DSP key
    keyDsp := fmt.Sprintf("DSP:%s:%s", cardInfo.cardType, cardInfo.cardName)

    _, err = r.SAdd(keyDsp, cardInfo.dspName, defaultTimeout*2).Result()
    checkRedisErr(err)

    return err

}

func DspInfraMainLoop(r *redis.Client) (err error) {

    //========================================================
    // Define all redis key here

    // DSP queue to receive test/cmd requests. One per DSP
    keyQue := fmt.Sprintf("QUEUE:%s:%s:%s", cardInfo.cardType, cardInfo.cardName, cardInfo.dspName)


    // Forever loop should be placed here

    // Wait for req from queue till timeout
    ticker := time.NewTicker(time.Second)
    i := 0
    for range ticker.C {
        testID, err := r.RPop(keyQue).Result()
        checkRedisErr(err)
        if testID != "" {
            fmt.Println("testID", testID, "err", err)
            break;
        }

        i++ 
        if i >= defaultTimeout {
            break;
        }

    }
    ticker.Stop()

    // Disable for now till main loop implemented
    // If no test received, move to the next round
    //if testID == "" {
    //    continue
    //}



    fmt.Println("Done mainloop")
    return err
}

func main() {
    r := redis.NewClient(&redis.Options{
        Addr:     "localhost:6379",
        Password: "", // no password set
        DB:       0,  // use default DB
    })

    CardInfoInit()
    DspInfraInit(r)
    DspInfraMainLoop(r)
}

