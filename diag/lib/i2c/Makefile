ARCH ?= amd64

.PHONY: all

all: libi2c

libi2c:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	@echo $(CC)
	$(CC) -c *.c
	ar rs libi2c.a *.o
	ar rs ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2c.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/clib/libi2c.a *.o *.a

