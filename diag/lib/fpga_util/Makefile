DEPENDENCIES := -lpthread -lrt
#LINKER_OPTIONS := -Wl,-rpath /usr/local/lib -L/home/dwang/ws/110422/psdiag/diag/lib/temp
LINKER_OPTIONS := -Wl,-rpath /usr/local/lib
CFLAGS = -Wall -Wextra $(DEPENDENCIES) $(LINKER_OPTIONS) -L/usr/local/lib

all: libaccpcie.a fpga_uart jtag_accpcie

libaccpcie.a: accpcie.c
	$(CC) accpcie.c -I.. -fPIC $(CFLAGSl) -c
	ar rcs libaccpcie.a accpcie.o

fpga_uart: fpga_uart.c
	#$(CC) fpga_uart.c -I.. -L. -lncurses -o fpga_uart $(CFLAGS)
	$(CC) fpga_uart.c -I.. -L. -o fpga_uart $(CFLAGS)
	
jtag_accpcie: jtag_accpcie.c
	$(CC) jtag_accpcie.c -I.. -L. -laccpcie -o jtag_accpcie $(CFLAGS)

clean:
	-rm -f *.o *.a; rm fpga_uart jtag_accpcie
