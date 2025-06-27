DEPENDENCIES := -lpthread -lrt
#LINKER_OPTIONS := -Wl,-rpath /usr/local/lib -L/home/dwang/ws/110422/psdiag/diag/lib/temp
LINKER_OPTIONS := -Wl,-rpath /usr/local/lib
CFLAGS = -Wall -Wextra $(DEPENDENCIES) $(LINKER_OPTIONS) -L/usr/local/lib

all: fpga_uart


fpga_uart: fpga_uart.c
    $(CC) fpga_uart.c -I.. -L. -o fpga_uart $(CFLAGS)
    
clean:
    -rm -f *.o *.a; rm fpga_uart
