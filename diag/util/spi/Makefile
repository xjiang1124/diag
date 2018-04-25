TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

spi_acc: spi_acc.c
	$(CMPL) spi_acc.c -I../../include -L$(GOPATH)/pkg/linux_amd64/clib -lacc -L$(GOPATH)/../lib/third-party -lftd2xx -lpthread -o spi_acc
	mv spi_acc $(GOPATH)/bin/linux_$(ARCH)/cbin/
	
clean:
	-rm -f *.o *.a; rm -f spi_acc
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/spi_acc
