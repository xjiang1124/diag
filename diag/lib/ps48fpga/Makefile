TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libps48fpga

libps48fpga: ps48fpga.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -c ps48fpga.c -o ps48fpga
	ar rs libps48fpga.a ps48fpga
	mv libps48fpga.a ${GOPATH}/pkg/linux_$(ARCH)/clib/libps48fpga.a
	rm -rf ps48fpga

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libpa48fpga.a *.o *.a
