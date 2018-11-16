TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld: cpld.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/cbin/
	$(CMPL) -c cpld.c -o cpld
	mv cpld $(GOPATH)/bin/linux_$(ARCH)/cbin/
clean:
	-rm -f *.o *.a; rm -f cpld.o
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/cpld
