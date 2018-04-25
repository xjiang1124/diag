.PHONY: all

all: i2c.go
	go install

i2c.go:
	swig -go -cgo -c++ -intgosize 64 i2c.i

clean:
	rm -f i2c.go i2c_wrap.cxx ${GOPATH}/pkg/linux_amd64/common/i2c.a


