.PHONY: all

all: libi2csim

libi2csim:
	@echo $(CC)
	$(CC) -static -c *.c
	ar rcs libi2csim.a *.o
	ar rcs ${GOPATH}/pkg/linux_$(ARCH)/common/libi2csim.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_$(ARCH)/common/libi2csim.a *.o *.a

