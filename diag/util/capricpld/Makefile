TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld: cpld.c
	$(CMPL) cpld.c -o cpld
	mv cpld $(GOPATH)/bin/linux_$(ARCH)/cbin/

clean:
	-rm -f *.o *.a; rm -f cpld
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/cpld
