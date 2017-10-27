TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

ARCH ?= amd64
ifeq (${ARCH}, amd64)
    CMPL=$(CC_X86)
else
    CMPL=$(CC_ARM_64)
endif

.PHONY: all

all: libi2csim

libi2csim:
	mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	@echo $(CMPL)
	$(CMPL) -static -c *.c
	ar rcs libi2csim.a *.o
	ar rcs ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2csim.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2csim.a *.o *.a

