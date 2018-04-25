.PHONY: all

all: i2cCSW.go
	go install

i2cCSW.go:
	swig -go -cgo -c++ -intgosize 32 i2cCSW.i

clean:
	rm -f i2cCSW.go ${GOPATH}/pkg/linux_amd64/common/i2cCSW.a


