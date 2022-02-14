TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

.PHONY: all

all: libacc libacc_v2 libacc_turbo libacc_mtp

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

libacc_turbo:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -L../third-party -lftd2xx -I../../include -c -fPIC acc_turbo.c -o acc_turbo.o
	$(CMPL) -shared -o libacc_turbo.so acc_turbo.o libftd2xx.a
	cp libacc_turbo.so ${GOPATH}/pkg/linux_$(ARCH)/clib/.

libacc_mtp:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CMPL) -L../third-party -lftd2xx -I../../include -c -fPIC acc.c -o acc_mtp.o
	$(CMPL) -shared -o libacc_mtp.so acc_mtp.o libftd2xx.a
	cp libacc_mtp.so ${GOPATH}/pkg/linux_$(ARCH)/clib/.

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libacc.a libacc_v2.a libacc_mtp.so libacc_turbo.so *.o *.a *.so

