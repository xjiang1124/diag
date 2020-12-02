TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libacc libacc_v2

libacc:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -L../third-party -lftd2xx -I../../include -c acc.c
	ar rs libacc.a acc.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc.a acc.o

libacc_v2:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -L../third-party -lftd2xx -I../../include -c acc_v2.c
	ar rs libacc_v2.a acc_v2.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc_v2.a acc_v2.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc.a libacc_v2.a *.o *.a

