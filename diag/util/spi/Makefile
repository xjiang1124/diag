TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

spi_acc: spi_acc.c
	$(CMPL) spi_acc.c -I../../include -L$(GOPATH)/pkg/linux_amd64/clib -lacc -L$(GOPATH)/../lib/third-party -lftd2xx -lpthread -o spi_acc
	
clean:
	-rm -f *.o *.a; rm spi_acc
