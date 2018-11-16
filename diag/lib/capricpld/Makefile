TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libcpld

libcpld: cpld.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -c cpld.c -o cpld
	ar rs libcpld.a cpld
	mv libcpld.a ${GOPATH}/pkg/linux_$(ARCH)/clib/libcpld.a

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libcpld.a *.o *.a
