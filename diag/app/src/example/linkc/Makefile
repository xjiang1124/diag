SHELL := /bin/bash

BUILD_DIR = $(shell pwd)
TOP_DIR = "$(shell dirname $(BUILD_DIR))"

GO_CMD=go
GO_BUILD=$(GO_CMD) build
GO_INSTALL=$(GO_CMD) install
GO_TEST=$(GO_CMD) test
#GOPATH=$(TOP_DIR)/diag/go
#CGO_LDFLAGS=-L$(GOPATH)/pkg/linux_amd64/common

#C
CC_ARM_64=aarch64-linux-gnu-gcc
CC_ARM_32=arm-linux-gnueabi-gcc
CC_X86=gcc

# The name of the executable (default is current directory name)
TARGET := $(shell echo $${PWD\#\#*/})
.DEFAULT_GOAL: $(TARGET)

# These will be provided to the target
VERSION := 1.0.0
BUILD := `git rev-parse HEAD`

# Use linker flags to provide version/build settings to the target
LDFLAGS=-ldflags "-X=main.Version=$(VERSION) -X=main.Build=$(BUILD)"

.PHONY: all build clean install uninstall fmt simplify check run

all: check install

arm_64_go_build:
	env GOOS=linux GOARCH=arm64 CGO_ENABLED=1 CC=$(CC_ARM_64) $(GO_BUILD) -x --ldflags '-linkmode=external -extldflags "-no-pie"' -o linkc
