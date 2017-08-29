SHELL := /bin/bash

BUILD_DIR = $(shell pwd)
TOP_DIR = "$(shell dirname $(BUILD_DIR))"

GO_CMD=go
GO_BUILD=$(GO_CMD) build
GO_INSTALL=$(GO_CMD) install
#GOPATH=$(TOP_DIR)/diag/go
#CGO_LDFLAGS=-L$(GOPATH)/pkg/linux_amd64/common

# The name of the executable (default is current directory name)
TARGET := $(shell echo $${PWD\#\#*/})
.DEFAULT_GOAL: $(TARGET)

# These will be provided to the target
VERSION := 1.0.0
BUILD := `git rev-parse HEAD`

# Use linker flags to provide version/build settings to the target
LDFLAGS=-ldflags "-X=main.Version=$(VERSION) -X=main.Build=$(BUILD)"

# go source files, ignore unnecessary directories
#SRC = $(shell find $(TOP_DIR)/diag/go/src -type f -name '*.go' -not -path "$(TOP_DIR)/diag/go/src/github.com/*" -not -path "$(TOP_DIR)/diag/go/src/example/*")
#SRC_DIR = "$(shell dirname $(SRC))"
include path.mk

.PHONY: all build clean install uninstall fmt simplify check run

all: check install

c_build:
	@$(MAKE) -C $(TOP_DIR)/diag/go/src/common/$(C_SRC_DIR)

build:
	@for p in $(SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(GO_BUILD) $$p || exit 1; \
	done
#	@echo $(SRC);go build $(LDFLAGS) $(SRC)

clean:
	@rm -f $(GOPATH)/bin/*

install:
	@for p in $(SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(GO_INSTALL) $$p || exit 1; \
	done
#	@go install $(LDFLAGS)

uninstall: clean
	@rm -f $$(which ${TARGET})

fmt:
	@gofmt -l -w $(SRC)

simplify:
	@gofmt -s -l -w $(SRC)

check:
	@test -z $(shell gofmt -l main.go | tee /dev/stderr) || echo "[WARN] Fix formatting issues with 'make fmt'"
	@for d in $$(go list ./... | grep -v /vendor/); do golint $${d}; done
	@go tool vet ${SRC}

run: install
	@$(TARGET)
											
