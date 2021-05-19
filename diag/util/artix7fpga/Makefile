TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld: artix7fpga.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/cbin/
	$(CMPL) artix7fpga.c -o artix7fpga
	mv artix7fpga $(GOPATH)/bin/linux_$(ARCH)/cbin/
clean:
	-rm -f *.o *.a; rm -f artix7fpga.o
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/artix7fpga

