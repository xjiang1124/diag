TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld: ps48fpga.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/cbin/
	$(CMPL) ps48fpga.c -o ps48fpga
	mv ps48fpga $(GOPATH)/bin/linux_$(ARCH)/cbin/
clean:
	-rm -f *.o *.a; rm -f ps48fpga.o
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/ps48fpga

