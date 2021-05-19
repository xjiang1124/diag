TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libartix7fpga

libartix7fpga: artix7fpga.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -c artix7fpga.c -o artix7fpga
	ar rs libartix7fpga.a artix7fpga
	mv libartix7fpga.a ${GOPATH}/pkg/linux_$(ARCH)/clib/libartix7fpga.a
	rm -rf artix7fpga

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libartix7fpga.a *.o *.a
