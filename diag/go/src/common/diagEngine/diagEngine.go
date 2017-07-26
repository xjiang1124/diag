package diagEngine

import (
    "fmt"
    "os"
    "time"
    "runtime"
    "flag"
    "strings"
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
    r = redis.NewClient(&redis.Options{
        Addr:     cardInfo.redisIP+":6379",
        Password: "", // no password set
        DB:       0,  // use default DB
    })


    //========================================================
    // Define all redis key here

    // DSP key: SADD DSP:cardType:cardName dspName
    keyDsp := fmt.Sprintf("DSP:%s:%s", cardInfo.cardType, cardInfo.cardName)

    _, err = r.SAdd(keyDsp, cardInfo.dspName, defaultTimeout*2).Result()
    checkRedisErr(err)

    // Init cli
    cli.Init("log_"+cardInfo.dspName+".txt")

    return err
}

func DspInfraMainLoop() (err error) {

    //========================================================
    // parameter needed for diag engine
    engList := []string {"-timeout", "-ite"}

    // Define all redis key here
    // DSP queue to receive test/cmd requests. One per DSP
    // RPOP QUEUE:cardType:cardName:dspName
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

        // parameter timeout and ite are use by diag engine. Others are for dsp handlers
        // To avoid flag.Parse output error message: "flag provided but not defined"
        // Separate arguement to two part: one that diag engine needs and one for dsp handler
        argList = strings.Fields(testParam)
        engArgList, dspArgList := sepArgList(argList, engList)
        cli.Println("i", engArgList, dspArgList)

        err = fs.Parse(engArgList)
        if err != nil {
            cli.Println("e", "Parse failed", err)
        }
        cli.Println("i", *timeoutPtr, *itePtr)

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
        FuncMsgChan = make(chan string)

        // Support multiple iterations on test/cmd
        for ite := 0; ite < *itePtr; ite++ {
            cli.Println("i", "Test run #", ite)
            // Dispatch to test handler
            go testHandler(dspArgList)

            // Wait for test handler gets back and check timeout as well
            select {
            case funcMsg := <-FuncMsgChan:
                cli.Println("i", funcMsg)
            case <-time.After(time.Second * time.Duration(*timeoutPtr)):
                // In case of timeout, set to infinite loop
                cli.Println("i", "Timeout happend!, testID:", testID, "testName:", testName, "param:", testParam)
                cli.Println("i", "DSP is in while(1) loop")
                for {
                }
            }
        }

        // Close function message channel after it is done
        close(FuncMsgChan)
        //break;
    }
    cli.Println("i", "Done mainloop", iteCount)
    return err
}

