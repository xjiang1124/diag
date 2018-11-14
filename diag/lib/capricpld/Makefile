TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libcpld

libcpld:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -c *.c
	ar rs libcpld.a *.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libcpld.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libcpld.a *.o *.a
