#include "accpcie.h"
#include <time.h>

int verbosity = 0;
ULONGLONG bar_addr = 0x40000000;
FT_HANDLE ftHandle = 0;

void set_verbosity(int level)
{
    verbosity = level;
    return;
}

void set_bar(ULONGLONG addr)
{
    bar_addr = addr;
    return;
}

ULONGLONG show_bar(void)
{
    if ( verbosity != 0 )
        printf("FPGA PCIe BAR address = %llx\n", bar_addr);
    return bar_addr;
}

int read_fpga_mem32(ULONGLONG ftHandle, DWORD reg, DWORD *data)
{
    ULONGLONG *addr;

    if ( verbosity )
        printf("read_fpag_mem32\n");
    /* int fd = open("/dev/mem", O_SYNC); */
    int fd = open("/sys/bus/pci/devices/0000:07:00.0/resource0", O_RDWR | O_SYNC);
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");

    }

    /* unsigned char *mem = mmap(NULL, page_offset + 256, PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, page_base); */
    unsigned char *mem = mmap((void *)ftHandle, 1024*1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd);
        return FT_ERROR_MAP_PCIE;
    }

    addr = (ULONGLONG *)(ftHandle + reg);
    *data = (DWORD)(*addr);

    close(fd);
    return FT_OK;
}

int write_fpga_mem32(ULONGLONG ftHandle, DWORD reg, ULONG value)
{
    ULONGLONG *addr;

    if ( verbosity )
        printf("write_fpag_mem32\n");
    /* int fd = open("/dev/mem", O_RDWR | O_SYNC); */
    int fd = open("/sys/bus/pci/devices/0000:07:00.0/resource0", O_RDWR | O_SYNC);
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }
    
    unsigned char *mem = mmap((void *)ftHandle, 1024 *1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd); 
        return FT_ERROR_MAP_PCIE;
    }

    addr = (ULONGLONG *)(mem + reg);
    if ( verbosity ) {
        printf("reg address %x\n", reg);
        printf("addr address %llx\n", (ULONGLONG)addr);
        printf("data %x\n", value);
    }
    *((DWORD *)addr) = value;

    close(fd); 
    return FT_OK;
}

void send_tx_input(int port)
{
    unsigned char ch;

    while ( (ch = getchar()) != EOF ) {
        write_fpga_mem32(bar_addr + UART_0_RXDATA_REG + port * 0x100, UART_0_TXDATA_REG, (DWORD)ch);
    };
}

void get_rx_buffer(int port)
{
    DWORD data;

    read_fpga_mem32(bar_addr + UART_0_RXDATA_REG + port * 0x100, UART_0_STAT_REG, &data);
    while ( data & 0x1 ) {
        read_fpga_mem32(bar_addr + UART_0_RXDATA_REG + port * 0x100, UART_0_RXDATA_REG, &data);
        printf("%c", (unsigned char)(data & 0xff));
        read_fpga_mem32(bar_addr + UART_0_RXDATA_REG + port * 0x100, UART_0_STAT_REG, &data);
    }
    return;
}

int main(int argc, char **argv)
{
    int cnt = 0;
    int port = atoi(argv[1]);

    printf("connecting to serial port %d\n", port);
    for ( ; ; ) { 
        /* printf("\ruart console %d>", (int)port); */
	get_rx_buffer(port);
	fflush(stdout);
	send_tx_input(port);
    }
    return 0;
}
    
