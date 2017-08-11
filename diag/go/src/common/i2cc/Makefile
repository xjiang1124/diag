.PHONY: all

all: i2c

i2c:
	gcc -c *.c
	ar rs i2c.a *.o
	ar rs ${GOPATH}/pkg/linux_amd64/common/i2c.a *.o

clean:
	rm -rf ${GOPATH}/pkg/linux_amd64/common/i2c.a *.o *.a

