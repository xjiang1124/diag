TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libspi

libspi:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -static -L../third-party -I../../include -c *.c
	ar rs libspi.a *.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libspi.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libspi.a *.o *.a

