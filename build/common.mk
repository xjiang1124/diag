SHELL := /bin/bash

BUILD_DIR = $(shell pwd)

GO_CMD=go
GO_BUILD=$(GO_CMD) build
GO_INSTALL=$(GO_CMD) install
GO_TEST=$(GO_CMD) test

CGO_LDFL = "-L$(GOPATH)/pkg/linux_amd64/clib/ -L$(GOPATH)/pkg/linux_arm64/clib/ -L$(GOPATH)/../lib/third-party/" 
GOBN = $(GOPATH)/bin/

# These will be provided to the target
VERSION := 1.0.0
BUILD := `git rev-parse HEAD`

# Use linker flags to provide version/build settings to the target
LDFLAGS=-ldflags "-X=main.Version=$(VERSION) -X=main.Build=$(BUILD)"

ARCH ?= amd64

CC_ARM_64_PATH=$(GOPATH)/../../tools/toolchain/arm64/bin
CC_ARM_64=$(CC_ARM_64_PATH)/aarch64-linux-gnu-gcc
CC_X86=gcc

ifeq (${ARCH}, amd64)
    CMPL=$(CC_X86)
else
    CMPL=$(CC_ARM_64)
endif
											
