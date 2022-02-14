TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

all: jtag_cpurd jtag_cpurd_v2

jtag_cpurd: jtag_cpurd.c
	$(CMPL) jtag_cpurd.c -I../../include -L$(GOPATH)/pkg/linux_amd64/clib -lacc -L$(GOPATH)/../lib/third-party -lftd2xx -lpthread -o jtag_cpurd
	mv jtag_cpurd $(GOPATH)/bin/linux_$(ARCH)/cbin/
	
jtag_cpurd_v2: jtag_cpurd_v2.c
	$(CMPL) jtag_cpurd_v2.c -I../../include -L$(GOPATH)/pkg/linux_amd64/clib -lacc_v2 -L$(GOPATH)/../lib/third-party -lftd2xx -lpthread -o jtag_cpurd_v2
	mv jtag_cpurd_v2 $(GOPATH)/bin/linux_$(ARCH)/cbin/
	
clean:
	-rm -f *.o *.a; rm -f jtag_cpurd jtag_cpurd_v2
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/jtag_cpurd
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/jtag_cpurd_v2
