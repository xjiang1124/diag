package dspInfra

import (
    "fmt"
    "os"
    "time"
    "runtime"
    "github.com/go-redis/redis"
)

//========================================================
// Constant definition
const (
    // Default timeout setting waiting for test to finish
    defaultTimeout = 5
    // Each DSP should know it own name
    sep = ":"
)

// Card info
type CardInfo struct {
    cardName string
    cardType string
    dspName string
}

// Define Test hander function type
type TestFn func(argList []string)uint32

//========================================================
// Global variables
var cardInfo CardInfo

//var FuncMap map[string]func(string)
var FuncMap map[string]TestFn

// Redis client
var r *redis.Client

//========================================================
func CardInfoInit(dspName string) {
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

func DspInfraInit() (err error) {
    r = redis.NewClient(&redis.Options{
        Addr:     "localhost:6379",
        Password: "", // no password set
        DB:       0,  // use default DB
    })  


    //========================================================
    // Define all redis key here

    // DSP key
    keyDsp := fmt.Sprintf("DSP:%s:%s", cardInfo.cardType, cardInfo.cardName)

    _, err = r.SAdd(keyDsp, cardInfo.dspName, defaultTimeout*2).Result()
    checkRedisErr(err)

    return err

}

func DspInfraMainLoop() (err error) {

    //========================================================
    // Define all redis key here

    // DSP queue to receive test/cmd requests. One per DSP
    keyQue := fmt.Sprintf("QUEUE:%s:%s:%s", cardInfo.cardType, cardInfo.cardName, cardInfo.dspName)


    iteCount := 0
    // Forever loop should be placed here
    for {

        // Wait for req from queue till timeout
        ticker := time.NewTicker(time.Second)
        i := 0
        var testID string
        for range ticker.C {
            testID, err = r.RPop(keyQue).Result()
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

        iteCount++
        fmt.Println(keyQue, iteCount)
        // Disable for now till main loop implemented
        // If no test received, move to the next round
        if testID == "" {
            //return err
            continue
        }

        // Match test handle table
        testHandler := FuncMap[testID]
        if testHandler != nil {
            testHandler([]string{"he"})
        }
        break;
    }
    fmt.Println("Done mainloop", iteCount)
    return err
}

func hdl1(argList []string) uint32 {
    fmt.Println("handle1", argList)
    return 0
}

func hdl2(argList []string) uint32 {
    fmt.Println("handle2", argList)
    return 0
}

