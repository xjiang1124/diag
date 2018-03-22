TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libacc

libacc:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -L../third-party -lftd2xx -I../../include -c *.c
	ar rs libacc.a *.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2c.a *.o *.a

