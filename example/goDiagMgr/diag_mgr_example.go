package main

import (
	"os/exec"
	"os"
	"fmt"
	"log"
	"io/ioutil"
	"strings"
)

var dsp_map = make(map[string]int)

func process_start(processName string) {
		
	fmt.Println(processName)

    cmd := exec.Command(processName)
    
    err := cmd.Start(); if err != nil {
		fmt.Fprintln(os.Stderr, "Error starting Cmd", err)
		return
	}
    
	dsp_map[processName] = cmd.Process.Pid
	fmt.Printf("DSP %s is started\n", processName)
}

func process_stop(processName string) {
	
	pid, exist := dsp_map[processName]; if exist == false {
		fmt.Printf("No process named %s is under diag manager\n", processName)
		return
	}
	
	process, err := os.FindProcess(pid); if err != nil {
		fmt.Printf("No process named %s is running\n", processName)
		return
	}
	
	err = process.Kill(); if err != nil {
		fmt.Printf("Kill process %s, pid %d failed\n", processName, pid)
		return
	}
	
	delete(dsp_map, processName)
	fmt.Printf("DSP %s is stopped successfully!\n", processName)
}

func main() {
	
	bytes, err := ioutil.ReadFile("dsp.txt"); if err != nil {
		log.Fatal(err)
	}
	
	words := strings.Fields(string(bytes))
	
//	fmt.Println(words, len(words))
	
	for i := range words {
	
	    cmd := exec.Command(words[i])
	    
	    err = cmd.Start()
		if err != nil {
			fmt.Fprintln(os.Stderr, "Error starting Cmd", err)
			os.Exit(1)
		}
		
//		fmt.Printf("PID: %d\n", cmd.Process.Pid)
		dsp_map[words[i]] = cmd.Process.Pid
	}
	
/* test code
	process_start("countdown1")
	process_start("countdown2")
	
	time.Sleep(2 * time.Second)
	
	process_stop("countdown1")
*/
	for k,v := range dsp_map {
		fmt.Printf("DSP %s, PID %d\n", k, v)
	}
}
