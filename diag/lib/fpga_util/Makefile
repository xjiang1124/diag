DEPENDENCIES := -lpthread -lrt -lftd2xx
TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk
#LINKER_OPTIONS := -Wl,-rpath /usr/local/lib -L/home/dwang/ws/110422/psdiag/diag/lib/temp
LINKER_OPTIONS := -Wl,-rpath /usr/local/lib -L./build
CFLAGS = -Wall -Wextra $(DEPENDENCIES) $(LINKER_OPTIONS) -L/usr/local/lib

.PHONY: all

all: libaccpcie.a libaccpcie_salina.a fpga_uart fpga_uart_panarea jtag_accpcie jtag_accpcie_salina

libaccpcie.a: accpcie.c
	@mkdir -p ${GOPATH}/bin/linux_$(ARCH)/clib/
	$(CC) accpcie.c -I.. -fPIC $(CFLAGSl) -c
	ar rcs libaccpcie.a accpcie.o
	#mv libaccpcie.a ${GOPATH}/bin/linux_$(ARCH)/clib/libaccpcie.a
	cp libaccpcie.a ${GOPATH}/bin/linux_$(ARCH)/clib/libaccpcie.a

libaccpcie_salina.a: accpcie_salina.c
	@mkdir -p ${GOPATH}/bin/linux_$(ARCH)/clib/
	$(CC) accpcie_salina.c -I.. -fPIC $(CFLAGSl) -c
	ar rcs libaccpcie_salina.a accpcie_salina.o
	#mv libaccpcie_salina.a ${GOPATH}/bin/linux_$(ARCH)/clib/libaccpcie_salina.a
	cp libaccpcie_salina.a ${GOPATH}/bin/linux_$(ARCH)/clib/libaccpcie_salina.a

fpga_uart: fpga_uart.c
	@mkdir -p ${GOPATH}/bin/linux_$(ARCH)/clib/
	$(CC) fpga_uart.c -I.. -L. -o fpga_uart $(CFLAGS)
	#mv fpga_uart ${GOPATH}/bin/linux_$(ARCH)/cbin/fpga_uart
	cp fpga_uart ${GOPATH}/bin/linux_$(ARCH)/cbin/fpga_uart
	
fpga_uart_panarea: fpga_uart_panarea.c
	@mkdir -p ${GOPATH}/bin/linux_$(ARCH)/clib/
	$(CC) fpga_uart_panarea.c -I.. -L. -o fpga_uart_panarea $(CFLAGS)
	#mv fpga_uart_panarea ${GOPATH}/bin/linux_$(ARCH)/cbin/fpga_uart_panarea
	cp fpga_uart_panarea ${GOPATH}/bin/linux_$(ARCH)/cbin/fpga_uart_panarea

jtag_accpcie: jtag_accpcie.c
	@mkdir -p ${GOPATH}/bin/linux_$(ARCH)/clib/
	$(CC) jtag_accpcie.c accpcie.c -I.. -L. -o jtag_accpcie $(CFLAGS)
	#mv jtag_accpcie ${GOPATH}/bin/linux_$(ARCH)/cbin/jtag_accpcie
	cp jtag_accpcie ${GOPATH}/bin/linux_$(ARCH)/cbin/jtag_accpcie

jtag_accpcie_salina: jtag_accpcie.c
	@mkdir -p ${GOPATH}/bin/linux_$(ARCH)/clib/
	$(CC) jtag_accpcie.c accpcie_salina.c  -I.. -L. -o jtag_accpcie_salina $(CFLAGS)
	#mv jtag_accpcie_salina ${GOPATH}/bin/linux_$(ARCH)/cbin/jtag_accpcie_salina
	cp jtag_accpcie_salina ${GOPATH}/bin/linux_$(ARCH)/cbin/jtag_accpcie_salina

clean:
	-rm -f *.o *.a fpga_uart jtag_accpcie jtag_accpcie_salina libaccpcie.a libaccpcie_salina.a
