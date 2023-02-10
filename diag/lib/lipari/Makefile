TOPDIR  := $(shell cd ..; pwd)
DEPENDENCIES := -lpthread
LINKER_OPTIONS := -Wl,-rpath /usr/local/lib
CFLAGS = -Wall -Wextra $(DEPENDENCIES) $(LINKER_OPTIONS) -L/usr/local/lib

all: libaccpcie.a fpga_uart 

libaccpcie.a: accpcie.c
	$(CC) accpcielib.c $(CFLAGS) -c
	ar rcs libpcieacc.a accpcielib.o

fpga_uart: fpga_uart.c
	$(CC) fpga_uart.c -I.. -L. -o fpga_uart $(CFLAGS)
	
clean:
	-rm -f *.o *.a; rm jtag_pcie_rw
