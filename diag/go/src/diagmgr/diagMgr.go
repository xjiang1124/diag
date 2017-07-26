package main

import (
    "os/exec"
    "os"
    "fmt"
//    "log"
//    "io/ioutil"
    "strings"
    "github.com/go-redis/redis"
    "common/diagEngine"
)

// Constant definition
const (
    // Each DSP should know it own name
    dspName = "DIAGMGR"
)

var dsp_map = make(map[string]int)

func process_start(processName []string) int {

    for i := range processName {

        cmd := exec.Command(processName[i])
    
        err := cmd.Start(); if err != nil {
            fmt.Fprintln(os.Stderr, "Error starting Cmd", err)
            return 1
        }
    
        dsp_map[processName[i]] = cmd.Process.Pid
        fmt.Printf("DSP %s is started\n", processName[i])
    }
    return 0
}

func process_stop(processName []string) int {

    for i := range processName {
        pid, exist := dsp_map[processName[i]]; if exist == false {
            fmt.Printf("No process named %s is under diag manager\n", processName[i])
            return 1
        }
    
        process, err := os.FindProcess(pid); if err != nil {
            fmt.Printf("No process named %s is running\n", processName[i])
            return 1
        }
    
        err = process.Kill(); if err != nil {
            fmt.Printf("Kill process %s, pid %d failed\n", processName[i], pid)
            return 1
        }
    
        delete(dsp_map, processName[i])
        fmt.Printf("DSP %s is stopped successfully!\n", processName[i])
    }
    return 0
}

func main() {

    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["dsp_start"] = process_start
    diagEngine.FuncMap["dsp_stop"] = process_stop

//    bytes, err := ioutil.ReadFile("dsp.txt"); if err != nil {
//        log.Fatal(err)
//    }
//    

    redisClient:= redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "", // no password set
		DB:       0,  // use default DB
	})

    dspList, err := redisClient.SMembers("DSP:"+os.Getenv("CARD_NAME")).Result()

    fmt.Println(dspList, len(dspList))

    for i := range dspList {

        cmd := exec.Command(strings.ToLower(dspList[i]))

        err = cmd.Start()
	    if err != nil {
	    fmt.Fprintln(os.Stderr, "Error starting Cmd", err)
	    os.Exit(1)
        }

        dsp_map[dspList[i]] = cmd.Process.Pid
    }
    for k,v := range dsp_map {
        fmt.Printf("DSP %s, PID %d\n", k, v)
        
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
    }
}
