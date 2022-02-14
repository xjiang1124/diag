TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libutil

libutil:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -c *.c
	$(PREFIX)ar rs libutil.a *.o
	$(PREFIX)ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libutil.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libutil.a *.o *.a

