.PHONY: all

all: libi2csim

libi2csim:
	@echo $(CC)
	$(CC) -c *.c
	ar rs libi2csim.a *.o
	ar rs ${GOPATH}/pkg/linux_amd64/common/libi2csim.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_amd64/common/libi2csim.a *.o *.a

