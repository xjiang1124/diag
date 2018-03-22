TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

jtag_cpurd: jtag_cpurd.c
	$(CMPL) jtag_cpurd.c -I../../include -L$(GOPATH)/pkg/linux_amd64/clib -lacc -L$(GOPATH)/../lib/third-party -lftd2xx -lpthread -o jtag_cpurd
	
clean:
	-rm -f *.o *.a; rm jtag_cpurd
