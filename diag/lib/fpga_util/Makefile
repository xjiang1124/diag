DEPENDENCIES := -lpthread -lrt
#LINKER_OPTIONS := -Wl,-rpath /usr/local/lib -L/home/dwang/ws/110422/psdiag/diag/lib/temp
LINKER_OPTIONS := -Wl,-rpath /usr/local/lib
CFLAGS = -Wall -Wextra $(DEPENDENCIES) $(LINKER_OPTIONS) -L/usr/local/lib

.PHONY: all

all: libaccpcie.a libaccpcie_salina.a fpga_uart jtag_accpcie jtag_accpcie_salina

libaccpcie.a: accpcie.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CC) accpcie.c -I.. -fPIC $(CFLAGSl) -c
	ar rcs libaccpcie.a accpcie.o
	mv libaccpcie.a ${GOPATH}/pkg/linux_$(ARCH)/clib/libaccpcie.a

libaccpcie_salina.a: accpcie_salina.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CC) accpcie_salina.c -I.. -fPIC $(CFLAGSl) -c
	ar rcs libaccpcie_salina.a accpcie_salina.o
	mv libaccpcie_salina.a ${GOPATH}/pkg/linux_$(ARCH)/clib/libaccpcie_salina.a

fpga_uart: fpga_uart.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CC) fpga_uart.c -I.. -L. -o fpga_uart $(CFLAGS)
	mv fpga_uart ${GOPATH}/pkg/linux_$(ARCH)/clib/fpga_uart
	
jtag_accpcie: jtag_accpcie.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CC) jtag_accpcie.c accpcie.c -I.. -L. -o jtag_accpcie $(CFLAGS)
	mv jtag_accpcie ${GOPATH}/pkg/linux_$(ARCH)/clib/jtag_accpcie

jtag_accpcie_salina: jtag_accpcie.c
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/clib/
	$(CC) jtag_accpcie.c accpcie_salina.c  -I.. -L. -o jtag_accpcie_salina $(CFLAGS)
	mv jtag_accpcie_salina ${GOPATH}/pkg/linux_$(ARCH)/clib/jtag_accpcie_salina

clean:
	-rm -f *.o 
