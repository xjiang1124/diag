.PHONY: all

all: ../../common/i2c/i2c.go
	go install

../../common/i2c/i2c.go:
	swig -go -cgo -c++ -intgosize 64 ../../common/i2c/i2c.i

clean:
	rm -f ../../common/i2c/i2c.go ${GOPATH}/bin/pmbus 


