TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld: xo3dcpld.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/cbin/
	$(CMPL) xo3dcpld.c -o xo3dcpld
	mv xo3dcpld $(GOPATH)/bin/linux_$(ARCH)/cbin/
	$(CMPL) gpioacc.c -o gpioacc
	mv gpioacc $(GOPATH)/bin/linux_$(ARCH)/cbin/
clean:
	-rm -f *.o *.a; rm -f xo3dcpld.o gpioacc.o
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/xo3dcpld
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/gpioacc
