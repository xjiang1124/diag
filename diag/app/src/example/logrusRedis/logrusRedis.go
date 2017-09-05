package main

import (
	//"io/ioutil"

	"github.com/Sirupsen/logrus"
	"github.com/rogierlommers/logrus-redis-hook"
)

func init() {
	hookConfig := logredis.HookConfig{
		Host:   "localhost",
		Key:    "my_redis_key",
		Format: "v0",
		App:    "my_app_name",
		Port:   6379,
		DB:     0, // optional
	}

	hook, err := logredis.NewHook(hookConfig)
	if err == nil {
		logrus.AddHook(hook)
	} else {
		logrus.Errorf("logredis error: %q", err)
	}
}

func main() {
	// when hook is injected succesfully, logs will be sent to redis server
	logrus.Info("just some info logging...")

	// we also support log.WithFields()
	logrus.WithFields(logrus.Fields{
		"animal": "walrus",
		"foo":    "bar",
		"this":   "that"}).
		Info("additional fields are being logged as well")

	// If you want to disable writing to stdout, use setOutput
	//logrus.SetOutput(ioutil.Discard)
	logrus.Info("This will only be sent to Redis")
}
