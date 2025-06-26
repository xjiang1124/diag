#include "accpcie.h"
#include <time.h>
/* #include <ncurses.h> */
#include <linux/input.h>
#include <termios.h>
#include <fcntl.h>


struct termios orig_termios;
int bytewrite=0;
int tx_full=0;
int readbyte;
int exit_send=0;
int exit_get=0;

int verbosity = 0;
ULONGLONG bar_addr = 0x183fffe00000;
FT_HANDLE ftHandle = 0;
int exit_all = 0;
volatile unsigned char *f0_uart_addr;
size_t buffSize=1048576;
int fd;
unsigned char *mem;


void reset_terminal_mode()
{
    tcsetattr(0, TCSANOW, &orig_termios);
}

void set_conio_terminal_mode()
{
    struct termios new_termios;
    int flags = fcntl(0, F_GETFL, 0);

    flags |= O_NONBLOCK;
    fcntl(0, F_SETFL, flags);

    /* take two copies - one for now, one for later */
    tcgetattr(0, &orig_termios);
    memcpy(&new_termios, &orig_termios, sizeof(new_termios));
/*
    printf("iflag %x %x %x %x %x %x %x %x %x\n", IGNBRK, BRKINT, IGNPAR, PARMRK, ISTRIP, INLCR, IGNCR, ICRNL, IXON);
    printf("oflag %x\n", OPOST);
    printf("cflag %x %x %x\n", CSIZE, PARENB, CS8);
    printf("lflag %x %x %x %x %x\n", ECHO, ECHONL, ICANON, ISIG, IEXTEN);
*/
    /* register cleanup handler, and set the new terminal mode */
    atexit(reset_terminal_mode);
/*
    printf("orig c_iflag is %x\n", orig_termios.c_iflag);
    printf("orig c_oflag is %x\n", orig_termios.c_oflag);
    printf("orig c_cflag is %x\n", orig_termios.c_cflag);
    printf("orig c_lflag is %x\n", orig_termios.c_lflag);
*/
    cfmakeraw(&new_termios);
/*
    printf("new c_iflag is %x\n", new_termios.c_iflag);
    printf("new c_oflag is %x\n", new_termios.c_oflag);
    printf("new c_cflag is %x\n", new_termios.c_cflag);
    printf("new c_lflag is %x\n", new_termios.c_lflag);
*/
    new_termios.c_oflag |= OPOST;
    /* new_termios.c_lflag |= ISIG | IEXTEN; */
    tcsetattr(0, TCSANOW, &new_termios);
}


int kbhit()
{
    struct timeval tv = { 0L, 0L };

    fd_set fds;
    FD_ZERO(&fds);
    FD_SET(0, &fds);
   
    if ( select(1, &fds, NULL, NULL, &tv) ) {

	fflush(stdout);
        return 0;
    }
    return -1;
}

int getch_local()
{
    int r;
    unsigned char c = 0xff;

    r = read(0, &c, sizeof(c));
    if ( r <= 0 ) {
        return EOF;
    } else {
        return c;
    }
}

void set_verbosity(int level)
{
    verbosity = level;
    return ;
}

void set_bar(ULONGLONG addr)
{
    bar_addr = addr;
    return ;
}

ULONGLONG get_bar_from_proc(void)
{
    FILE *fileptr = fopen("/proc/bus/pci/devices", "r");
    char line[512];
    char delim[] = "\t";
    char *ptr = NULL;
    int len;
    unsigned long long int address = 0;

    while ( fgets(line, sizeof(line), fileptr) ) {
        ptr = strtok(line, delim);
        while ( ptr != NULL ) {
           if ( strcmp(ptr, "1dd80003") == 0 ) {
               ptr = strtok(NULL, delim);
               ptr = strtok(NULL, delim);
               len = strlen(ptr);
               ptr[len - 1] = '0';
               address = strtoll(ptr, NULL, 16);
               break;
           } else
               ptr = strtok(NULL, delim);
        }
        if ( address != 0 ) {
            if ( verbosity )
                printf("PCIE BAR = 0x%llx\n", address);
            fclose(fileptr);
            return address;
        }
    }
    fclose(fileptr);
    return address;
}

ULONGLONG show_bar(void)
{
    if ( verbosity != 0 )
        printf("FPGA PCIe BAR address = %llx\n", bar_addr);
    return bar_addr;
}

int init_mmap(int port)
{    
	off_t offset = bar_addr + UART_0_OFFSET + port * UART_INST_OFFSET;
    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = (offset / pagesize) * pagesize;
    off_t page_offset = offset - page_base; //f0 uart with port offset
	if ( verbosity > 1 ) {
        printf("page_size %lx; page_base %lx; offset %lx; page_offset %lx\n", pagesize, page_base, offset, page_offset);
    }	
	
	fd = open("/dev/mem", O_RDWR | O_SYNC);
    if ( fd < 0 ) {
        printf("read function, Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }
	mem = mmap(NULL, buffSize, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page_base);
    if ( mem == NULL ) {
        printf("read function, failed to  map pcie memory\n");
        close(fd);
        return FT_ERROR_MAP_PCIE;
    }
	f0_uart_addr = mem + page_offset; //f0 uart address with port offset
	return 0;
}

int close_mmap()
{
	munmap((void *)mem, buffSize);
	close(fd);
	return 0;
}
	
unsigned int read_reg(off_t reg) 
{
    return *((uint32_t *) (f0_uart_addr+reg));
}

void write_reg(off_t reg, uint32_t data ) 
{

	*((uint32_t *) (f0_uart_addr+reg)) = data;
}


void *send_tx_input()
{
    int ch;
    int end_thread = 0;
    set_conio_terminal_mode();
	
    for ( ; ; ) {
        if ( !kbhit() ) {
            ch = getch_local();
            while ( ch != EOF ) {
                if ( ch == 1 ) {
                    end_thread = 1;
					ch = getch_local();	
					continue;
                } 
				else if ( ch == 24 ) {
                    if ( end_thread == 1 ) {
                        end_thread = 2;
                        exit_all = 1;
						ch = EOF;
						continue;
                    } else {
                        end_thread = 0;
                    }
                } else {
                    end_thread = 0;
                }
                if ( verbosity )
                    printf("sending character %c\n", ch);

				write_reg(UART_0_TXFIFO_REG, (uint32_t)ch);
                usleep(500);
				ch = getch_local();
			}
			if ( verbosity > 1 )
				printf("input buffer is empty\n");
		}
		if ( end_thread == 2 )
				break;
    }
    reset_terminal_mode();
    pthread_exit(NULL);
}

void get_rx_buffer()
{
    uint32_t data;
	data=read_reg(UART_0_STAT_REG);

	if ( (data & 0x00000001) == 0x00000000 )
		return ;

    while ( (data & 0x00000001) == 0x00000001) {
		if ( verbosity )  {
            printf(" uart status register = %x\n", data);
        }
		data=read_reg(UART_0_RXFIFO_REG) & 0xFF;
        if ( verbosity ) { 
            printf(" uart received data = %c\n", data); 
        }
		write (1, &data, 1);
		data=read_reg(UART_0_STAT_REG);
    }
	
    return ;
}

//New function for debug. Loopback the TX/RX FIFO on Taormina FPGA <> ECPLD
void *send_loopback_tx_debug()
{
   int ptr_in;
   uint32_t data;
   char buff;
	// Opening file in reading mode
    ptr_in = open("test_in",O_RDONLY); 
	readbyte=read(ptr_in, &buff,1);
	
	while (readbyte != 0)
    {	
		data=read_reg(UART_0_STAT_REG);
		while ((data & 0x00000008) == 0x00000008)
		{	
			if ((data & 0x00000020) == 0x00000020)
			{
				printf(" RX OVERRUN OCCURED, EXIT\n");	
				exit_get=1;
				break ;
			}	
			
			
			printf("TX FIFO FULL, WAIT\n");
			data=read_reg(UART_0_STAT_REG);
		}
		if ((data & 0x00000020) == 0x00000020)
			{
				printf(" RX OVERRUN OCCURED, EXIT\n");	
				exit_get=1;
				break ;
			}	
		//printf("input char is %x\n", buff);
		write_reg(UART_0_TXFIFO_REG, buff);
		readbyte=read(ptr_in, &buff,1);		
		//printf ("input char is %c\n", ch);
		//printf("input binary in hex is  %0x\n", ch);
    }

	close(ptr_in);
    //exit_send=1;
    pthread_exit(NULL);  	
}		

void get_loopback_rx_buffer_debug(int ptr_out)
{
	
    uint32_t data;
    data=read_reg(UART_0_STAT_REG);

	if (verbosity )  
           printf(" uart status register = %x\n", data);	

	if (bytewrite==33554431) {
	    exit_get=1;
		return ;
	}
	

	//if ((data & 0x00000020) == 0x00000020)
		//{
		//	printf(" RX OVERRUN OCCURED, EXIT");	
		//	exit_get=1;
		//	return ;
		//}
    while ( (data & 0x00000001) == 0x00000001) {
		if ( verbosity )  
            printf(" uart status register = %x\n", data);
        data=read_reg(UART_0_RXFIFO_REG);
        if ( verbosity )  
            printf(" uart received data = %x\n", data);
        write(ptr_out,&data,1);
		bytewrite=bytewrite+1;
        data=read_reg(UART_0_STAT_REG);	
		if ((data & 0x00000020) == 0x00000020)
		{
			printf(" RX OVERRUN OCCURED, EXIT\n");	
			exit_get=1;
			break ;
		}	
		//printf(" uart status register = %x\n", data);		
    }


	
    return ;
}		
		


int main(int argc, char **argv)
{
    int port = atoi(argv[1]);
    pthread_t id;
    ULONGLONG pcie_bar;
    uint32_t data;
	
    if ( argc < 2 ) { 
        printf("Invalid address, please provide a port number (0 - based)\n");
        return 0;
    }
    pcie_bar = get_bar_from_proc();
    if ( pcie_bar != 0 ) {
        bar_addr = pcie_bar;
    }

	init_mmap(0);
	data = UART_TXMUX_SET;
	write_reg(UART_0_TX_MUX_REG, data);
	data = UART_TXMUX_SET;
	write_reg(UART_1_TX_MUX_REG, data);	
	close_mmap();	

	init_mmap(port);
    
    printf("connecting to serial port %d at bar address 0x%llx\n", port, bar_addr);
	
	//uart 0 ctrl reg, clear rx/tx fifo
	//data = UART_RESET_TXRXFIFO;
	//write_reg(UART_0_CTRL_REG, data);
	

/*
//Uncomment for loopback test, comment out the main uart loop
	data = UART_TXMUX_SET;
	write_reg(UART_0_CTRL_REG, data);
	int ptr_out; 
	printf("tx/rx buffer cleared\n");
	printf("\ruart console Elba%d>", (int)port); 
	printf("\r\n");
	pthread_create(&id, NULL, send_loopback_tx_debug, (void *)&port);
	remove("test_out");
	ptr_out = open("test_out", O_WRONLY | O_CREAT);
	for ( ; ; ) { 
		get_loopback_rx_buffer_debug(ptr_out);
		
		if ( exit_get==1 ) {
			close(ptr_out);
		    printf ("loopback test is done\n");
			//data = UART_TXMUX_UNSET;
			//write_reg(UART_0_CTRL_REG, data);
			close_mmap();
			return 0;
		}

	//usleep(10);
	
	}
*/
//main uart loop	

	//For Taormina
	//set TX FIFO mux for new SW implementation

	printf("tx/rx buffer cleared\n");
	printf("\ruart console Elba%d>", (int)port); 
	printf("\r\n");
    pthread_create(&id, NULL, send_tx_input, (void *)&port);
	
    for ( ; ; ) { 
    
	get_rx_buffer();
        if ( exit_all ) {
			//unset the tx fifo mux
			//data = UART_TXMUX_UNSET;
			//write_reg(UART_0_TX_MUX_REG, data);
			//write_reg(UART_1_TX_MUX_REG, data);
			close_mmap();
            return 0;
        }
    //usleep(10);
    }
	
    return 0;
}
    
