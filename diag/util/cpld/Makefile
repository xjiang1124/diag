TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

cpld_program: cpld_program.c
	$(CMPL) cpld_program.c -I../../include -L$(GOPATH)/pkg/linux_amd64/clib -lacc -L$(GOPATH)/../lib/third-party -lftd2xx -lpthread -o cpld_program
	
clean:
	-rm -f *.o *.a; rm cpld_program
