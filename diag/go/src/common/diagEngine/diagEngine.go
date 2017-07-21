package diagEngine

import (
    "fmt"
    "os"
    "time"
    "runtime"
    "flag"
    "strings"
    "github.com/go-redis/redis"
)

//========================================================
// Constant definition
const (
    // Default timeout setting waiting for test to finish
    defaultTimeout = 30
    // Each DSP should know it own name
    sep = ":"
)

// Card info
type CardInfo struct {
    redisIP string
    cardName string
    cardType string
    dspName string
}

// Define Test hander function type
type TestFn func(argList []string) int

//========================================================
// Global variables
var cardInfo CardInfo

//var FuncMap map[string]func(string)
var FuncMap map[string]TestFn

// Redis client
var r *redis.Client

// Function message channel
var FuncMsgChan chan string

//========================================================
func CardInfoInit(dspName string) {
    // Card name and card type are from environment variable
    cardInfo.redisIP = os.Getenv("REDIS_IP")
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
    keyQueStr := "QUEUE:%s:%s:%s"
    keyQue := fmt.Sprintf(keyQueStr, cardInfo.cardType, cardInfo.cardName, cardInfo.dspName)

    // TestID: GET TEST_ID:cardType:dspName:testID testName
    keyTestIDStr := "TEST_ID:%s:%s:%s"
    // Test parameter: GET TEST_PARAM:cardType:dspName:testID paramStr
    keyTestParamStr := "TEST_PARAM:%s:%s:%s"


    // Parameter passing, needed for timeout and ite only
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    timeoutPtr := fs.Int("timeout", 30, "Timeout setting for the test")
    itePtr := fs.Int("ite", 1, "Iterations for the test")
    var argList []string

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

        // Get test name based on testID
        keyTestID := fmt.Sprintf(keyTestIDStr, cardInfo.cardType, cardInfo.dspName, testID)
        testName, err := r.Get(keyTestID).Result()
        checkRedisErr(err)

        // Get test parameter based on testID
        keyTestParam := fmt.Sprintf(keyTestParamStr, cardInfo.cardType, cardInfo.dspName, testID)
        testParam, err := r.Get(keyTestParam).Result()
        checkRedisErr(err)

        argList = strings.Split(testParam, " ")
        err = fs.Parse(argList)
        //if err != nil {
        //    fmt.Println("Parse failed", err)
        //}
        fmt.Println(*timeoutPtr, *itePtr)

        // Match test handle table
        testHandler := FuncMap[testName]
        if testHandler == nil {
            // Ignore non-valid test/cmd entry
            fmt.Println("No testHandler found", testID, testName)
            continue
        }
        argList = strings.Split(testParam, " ")

        //========================================================
        // Use go routine to execute test/cmd. Channel is used to communicate 
        // between go routine and diagEngine. If timeout happens, simply close
        // the channel and hold dsp from running

        // prepare message channel to function
        FuncMsgChan = make(chan string)

        // Dispatch to test handler
        go testHandler(argList)

		// Wait for test handler gets back and check timeout as well
		select {
		case funcMsg := <-FuncMsgChan:
            fmt.Println(funcMsg)
		case <-time.After(time.Second * time.Duration(*timeoutPtr)):
            fmt.Println("Timeout happend!, testID:", testID, "testName:", testName, "param:", testParam)
            fmt.Println("DSP is in while(1) loop")
            for {
			}
		}

        // Close function message channel after it is done
        close(FuncMsgChan)
        //break;
    }
    fmt.Println("Done mainloop", iteCount)
    return err
}

