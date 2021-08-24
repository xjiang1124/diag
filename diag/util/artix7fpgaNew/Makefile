TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld: artix7fpgaNew.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/cbin/
	$(CMPL) artix7fpgaNew.c -o artix7fpgaNew
	mv artix7fpgaNew $(GOPATH)/bin/linux_$(ARCH)/cbin/artix7fpga
clean:
	-rm -f *.o *.a; rm -f artix7fpgaNew.o
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/artix7fpga

