TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld: str2asc6.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/cbin/
	$(CMPL) str2asc6.c -o str2asc6
	mv str2asc6 $(GOPATH)/bin/linux_$(ARCH)/cbin/

clean:
	-rm -f *.o *.a; rm -f str2asc6.o
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/str2asc6

