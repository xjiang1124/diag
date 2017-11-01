TOP_DIR=../../../../../
include $(TOP_DIR)/build/common.mk

BUILD_DIR = $(shell pwd)
MODULE_NAME=$(shell basename $(BUILD_DIR))

.PHONY: all

all:
	env GOOS=linux GOARCH=${ARCH} CGO_ENABLED=1 CC=$(CMPL) $(GO_BUILD) -o arch_${ARCH}/$(MODULE_NAME)
	@mkdir -p $(GOBIN)/linux_${ARCH}/util/
	@cp arch_${ARCH}/$(MODULE_NAME) $(GOBIN)/linux_${ARCH}/util/

clean:
	rm -f arch_${ARCH}/$(MODULE_NAME)
	rm -f $(GOBIN)/${ARCH}/dsp/$(MODULE_NAME)

