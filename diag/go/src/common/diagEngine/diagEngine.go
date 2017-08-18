package diagEngine

import (
    "fmt"
    "os"
    "time"
    "runtime"
    "flag"
    "strings"

    "config"
    "common/misc"
    "common/cli"

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
    CardName string
    CardType string
    dspName string
}

// Define Test hander function type
type TestFn func(argList []string)

//========================================================
// Global variables
var cardInfo CardInfo

//var FuncMap map[string]func(string)
var FuncMap map[string]TestFn

// Redis client
var RedisClient *redis.Client

// Function message channel
var FuncMsgChan chan int

// DShell I
var DshID int = -1

//========================================================
func GetCardInfo() CardInfo {
    return cardInfo
}

func CardInfoInit(dspName string) {
    // Card name and card type are from environment variable
    cardInfo.redisIP = os.Getenv("REDIS_IP")
    cardInfo.CardName = os.Getenv("CARD_NAME")
    cardInfo.CardType = os.Getenv("CARD_TYPE")
    cardInfo.dspName = dspName
}

func CheckRedisErr(err error) {
    if err == redis.Nil {
        // Key not exist
    } else if err == nil {
        // No error happened
    } else {
        _, fileName, fileLine, _ := runtime.Caller(1)
        fmt.Println("err:", err, "fileName:", fileName, "fileLine", fileLine)
    }
}

func sepArgList(argList []string, engList []string) (engArgList []string, dspArgList []string) {
    for i := 0; i < len(argList); i = i+1 {
        if misc.ContainStr(engList, argList[i]) {
            engArgList = append(engArgList, argList[i])
        } else {
            dspArgList = append(dspArgList, argList[i])
        }
    }
    return engArgList, dspArgList
}

func DspInfraInit() (err error) {
    RedisClient = redis.NewClient(&redis.Options{
        Addr:     cardInfo.redisIP+":6379",
        Password: "", // no password set
        DB:       0,  // use default DB
    })


    //========================================================
    // Define all redis key here

    //========================================================
    // Define all redis key here
    // DSP key: SADD DSP:CardType:CardName dspName
    keyDsp := fmt.Sprintf("DSP:%s:%s", cardInfo.CardType, cardInfo.CardName)

    _, err = RedisClient.SAdd(keyDsp, cardInfo.dspName).Result()
    CheckRedisErr(err)

    // Card dict
    _, err = RedisClient.HSet("CARD_DICT", cardInfo.CardType, cardInfo.CardName).Result()
    CheckRedisErr(err)

    // Init cli
    cli.Init("log_"+cardInfo.dspName+".txt", config.OutputMode)

    registerDSP()

    return err
}

func registerDSP () {
    keyDspFmt := "EXP:DSP:%s:%s:%s"
    keyCardFmt := "EXP:CARD:%s:%s"

    keyDsp := fmt.Sprintf(keyDspFmt, cardInfo.CardType, cardInfo.CardName, cardInfo.dspName)
    keyCard := fmt.Sprintf(keyCardFmt, cardInfo.CardType, cardInfo.CardName)

    // Create key entries
    _, err := RedisClient.Set(keyDsp, 1, 0).Result()
    CheckRedisErr(err)
    _, err = RedisClient.Set(keyCard, 1, 0).Result()
    CheckRedisErr(err)

    // Set expiration
    tout := time.Second *time.Duration(defaultTimeout*2)
    _, err = RedisClient.Expire(keyDsp, tout).Result()
    CheckRedisErr(err)
    _, err = RedisClient.Expire(keyCard, tout).Result()
    CheckRedisErr(err)

    // Set NON-EXPIRATION keys to support missing DSP/Card 
    keyDsp = fmt.Sprintf("NON"+keyDspFmt, cardInfo.CardType, cardInfo.CardName, cardInfo.dspName)
    keyCard = fmt.Sprintf("NON"+keyCardFmt, cardInfo.CardType, cardInfo.CardName)

    // Create key entries
    _, err = RedisClient.Set(keyDsp, 1, 0).Result()
    CheckRedisErr(err)
    _, err = RedisClient.Set(keyCard, 1, 0).Result()
    CheckRedisErr(err)

}

func renewDSP (timeout int) {
    keyDspFmt := "EXP:DSP:%s:%s:%s"
    keyCardFmt := "EXP:CARD:%s:%s"

    keyDsp := fmt.Sprintf(keyDspFmt, cardInfo.CardType, cardInfo.CardName, cardInfo.dspName)
    keyCard := fmt.Sprintf(keyCardFmt, cardInfo.CardType, cardInfo.CardName)

    // Set expiration
    tout := time.Second * time.Duration(timeout+defaultTimeout*2)
    _, err := RedisClient.Expire(keyDsp, tout).Result()
    CheckRedisErr(err)
    _, err = RedisClient.Expire(keyCard, tout).Result()
    CheckRedisErr(err)
}

func DspInfraMainLoop() (err error) {

    //========================================================
    // parameter needed for diag engine

    // Define all redis key here
    // DSP queue to receive test/cmd requests. One per DSP
    // RPOP QUEUE:CardType:CardName:dspName
    keyQueFmt := "QUEUE:%s:%s"
    keyQue := fmt.Sprintf(keyQueFmt, cardInfo.CardType, cardInfo.dspName)

    // TestID: GET TEST_ID:CardType:dspName:testID testName
    keyTestIDFmt := "TEST_ID:%s:%s:%s"
    // Test parameter: GET TEST_PARAM:CardType:dspName:testID paramStr
    keyTestParamFmt := "TEST_PARAM:%s:%s:%s"

    // Test history
    // Success: INCR HIST:CardType:dspName:testName:SUCCESS
    keyHistSuccFmt := "HIST:%s:%s:%s:SUCCESS"
    // Fail: INCR HIST:CardType:dspName:testName:FAILURE
    keyHistFailFmt := "HIST:%s:%s:%s:FAILURE"
    // Timeout: INCR HIST:CardType:dspName:testName:TIMEOUT
    keyHistTimeoutFmt := "HIST:%s:%s:%s:TIMEOUT"

    // Test result: SET TEST_RESULT:test_id err_code
    keyResultFmt := "TEST_RESULT:%s"

    // Parameter passing, needed for timeout and ite only
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    timeoutPtr := fs.Int("timeout", 30, "Timeout setting for the test")
    itePtr := fs.Int("ite", 1, "Iterations for the test")
    dshIDPtr := fs.Int("dshid", 1, "diag Shell ID")

    engList := []string {"-timeout", "-ite", "-dshid"}
    var argList []string

    var funcMsg int
    var histKey string

    iteCount := 0
    stopOnErrEn := 0
    stopOnErrFlag := 0
    i := 0
    var testID string
    // Forever loop should be placed here
    for {
        renewDSP(0)
        // Wait for req from queue till timeout
        ticker := time.NewTicker(time.Second)
        i = 0
        for range ticker.C {
            testID, err = RedisClient.RPop(keyQue).Result()
            CheckRedisErr(err)
            if testID != "" {
                cli.Println("info", "testID", testID, "err", err)
                break;
            }

            i++
            if i >= defaultTimeout {
                break;
            }
        }
        ticker.Stop()

        iteCount++
        cli.Println("d", keyQue, iteCount)

        // If no test received, move to the next round
        if testID == "" {
            //return err
            continue
        }

        // Get stop_on_error setting
        stopOnErrLvl, err := RedisClient.Get("STOP_ON_ERROR").Result()
        CheckRedisErr(err)
        if (stopOnErrLvl == "" || stopOnErrLvl == "0") {
            stopOnErrFlag = 0
            stopOnErrEn = 0
        } else {
            stopOnErrFlag = 1
        }

        // In case of stop_on_error, return a skip signature
        if (stopOnErrEn == 1) {
            keyResult := fmt.Sprintf(keyResultFmt, testID)
            RedisClient.Set(keyResult, 0xBEEF, 0)
            continue
        }

        // Get test name based on testID
        keyTestID := fmt.Sprintf(keyTestIDFmt, cardInfo.CardType, cardInfo.dspName, testID)
        testName, err := RedisClient.Get(keyTestID).Result()
        CheckRedisErr(err)

        // Get test parameter based on testID
        keyTestParam := fmt.Sprintf(keyTestParamFmt, cardInfo.CardType, cardInfo.dspName, testID)
        cli.Println("d", keyTestParam)
        testParam, err := RedisClient.Get(keyTestParam).Result()
        CheckRedisErr(err)

        // parameter timeout and ite are use by diag engine. Others are for dsp handlers
        // To avoid flag.Parse output error message: "flag provided but not defined"
        // Separate arguement to two part: one that diag engine needs and one for dsp handler
        argList = strings.Fields(testParam)
        engArgList, dspArgList := sepArgList(argList, engList)
        cli.Println("i", engArgList, dspArgList)

        err = fs.Parse(engArgList)
        if err != nil {
            cli.Println("e", "PARSE FAILED!", err)
        }
        DshID = *dshIDPtr
        cli.Println("i", *timeoutPtr, *itePtr, DshID)


        // Match test handle table
        testHandler := FuncMap[testName]
        if testHandler == nil {
            // Ignore non-valid test/cmd entry
            cli.Println("i", "No testHandler found", testID, testName)
            continue
        }

        //========================================================
        // Use go routine to execute test/cmd. Channel is used to communicate 
        // between go routine and diagEngine. If timeout happens, simply close
        // the channel and hold dsp from running

        // prepare message channel to function
        FuncMsgChan = make(chan int)

        // Support multiple iterations on test/cmd
        for ite := 0; ite < *itePtr; ite++ {
            // Renew DSP expiration based on timeout of the test
            renewDSP(*timeoutPtr)

            cli.Println("i", "=== TEST STARTED === testID:", testID, "testName:", testName)
            cli.Println("i", "Test run #", ite)
            // Dispatch to test handler
            go testHandler(dspArgList)

            // Wait for test handler gets back and check timeout as well
            select {
            case funcMsg = <-FuncMsgChan:
            case <-time.After(time.Second * time.Duration(*timeoutPtr)):
                // In case of timeout, set to infinite loop
                histKey = fmt.Sprintf(keyHistTimeoutFmt, cardInfo.CardType, cardInfo.dspName, testName)
                RedisClient.Incr(histKey)

                cli.Println("i", "Timeout happend!, testID:", testID, "testName:", testName, "param:", testParam)
                cli.Println("i", "DSP is in while(1) loop")
                for {
                }
            }
            // Process test return code
            if funcMsg == 0 {
                histKey = fmt.Sprintf(keyHistSuccFmt, cardInfo.CardType, cardInfo.dspName, testName)
            } else {
                histKey = fmt.Sprintf(keyHistFailFmt, cardInfo.CardType, cardInfo.dspName, testName)
            }
            RedisClient.Incr(histKey)

            keyResult := fmt.Sprintf(keyResultFmt, testID)
            RedisClient.Set(keyResult, funcMsg, 0)

            cli.Println("i", "=== TEST DONE === testID:", testID, "testName:", testName)

            // Check stop_on_error
            if (stopOnErrFlag > 0 && funcMsg != 0) {
                stopOnErrEn = 1
                break;
            }
        }

        // Close function message channel after it is done
        close(FuncMsgChan)
        //break;
    }
    cli.Println("i", "Done mainloop", iteCount)
    return err
}

