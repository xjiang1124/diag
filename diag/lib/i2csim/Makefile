TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libi2csim

libi2csim:
	mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -static -c *.c
	ar rcs libi2csim.a *.o
	ar rcs ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2csim.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2csim.a *.o *.a

