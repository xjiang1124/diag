TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libi2c

libi2c:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -c *.c
	ar rs libi2c.a *.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2c.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2c.a *.o *.a

