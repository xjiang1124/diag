TOP_DIR=../../../../
include $(TOP_DIR)/build/common.mk

#BUILD_DIR = $(shell pwd)
MODULE_NAME=$(shell basename $(BUILD_DIR))

.PHONY: all

all:
	env GOOS=linux GOARCH=${ARCH} CC=$(CMPL) $(GO_BUILD) -o arch_${ARCH}/$(MODULE_NAME)
	@mkdir -p $(GOBN)/linux_${ARCH}/
	@cp arch_${ARCH}/$(MODULE_NAME) $(GOBN)/linux_${ARCH}/

clean:
	rm -f arch_${ARCH}/$(MODULE_NAME)
	rm -f $(GOBN)/${ARCH}/dsp/$(MODULE_NAME)

