TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libacc libacc_v2

libacc:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -L../third-party -lftd2xx -I../../include -c *.c
	ar rs libacc.a *.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc.a *.o

libacc_v2:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -L../third-party -lftd2xx -I../../include -c *.c
	ar rs libacc_v2.a *.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc_v2.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc.a libacc_v2.a *.o *.a

