TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libxo3dcpld

libxo3dcpld: xo3dcpld.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -c xo3dcpld.c -o xo3dcpld
	ar rs libxo3dcpld.a xo3dcpld
	mv libxo3dcpld.a ${GOPATH}/pkg/linux_$(ARCH)/clib/libxo3dcpld.a
	rm -rf xo3dcpld

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libxo3dcpld.a *.o *.a
