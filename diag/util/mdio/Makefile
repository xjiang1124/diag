TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

mdio_acc: mdio_acc.c
	$(CMPL) mdio_acc.c -I../../include -L$(GOPATH)/pkg/linux_amd64/clib -lacc -L$(GOPATH)/../lib/third-party -lftd2xx -lpthread -o mdio_acc
	mv mdio_acc $(GOPATH)/bin/linux_$(ARCH)/cbin/
	
clean:
	-rm -f *.o *.a; rm -f mdio_acc
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/mdio_acc
