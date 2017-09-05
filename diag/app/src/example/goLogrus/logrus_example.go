package main

import (
	"os"
	log "logrus"
)

//var log = logrus.New()

func main() {

	file, err := os.OpenFile("log.txt", os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0666)
	if err != nil {
	    log.Fatal(err)
	}
	
	logger := log.New()
	
	logger.Out = file
	logger.Level = log.DebugLevel
	
    
    logger.Debug("test debug info")
    
    logger.Info("test info info")
    
    logger.Warn("test warn info")
    
    logger.Warning("test warning info")
    
    logger.Error("test error info")
    
    logger.Panic("test panic info")
    
	err = file.Close(); if err != nil {
	    log.Fatal(err)
	}
}
