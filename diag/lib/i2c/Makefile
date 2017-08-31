.PHONY: all

all: libi2c

libi2c:
	@echo $(CC)
	$(CC) -c *.c
	ar rs libi2c.a *.o
	ar rs ${GOPATH}/pkg/linux_amd64/common/libi2c.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_amd64/common/libi2c.a *.o *.a

