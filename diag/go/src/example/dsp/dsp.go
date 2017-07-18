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
    if err != nil {
        _, fileName, fileLine, _ := runtime.Caller(1)
        fmt.Println("err:", err, "fileName:", fileName, "fileLine", fileLine)
    }
}

func DspInfraInit(r *redis.Client) (err error) {

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



    return err
}

func DspInfraMain(r *redis.Client) (err error) {

    return nil
}

func main() {
    r := redis.NewClient(&redis.Options{
        Addr:     "localhost:6379",
        Password: "", // no password set
        DB:       0,  // use default DB
    })
    fmt.Printf("%T\n", r)


    CardInfoInit()
    DspInfraInit(r)

    DspInfraMain(r)
}

