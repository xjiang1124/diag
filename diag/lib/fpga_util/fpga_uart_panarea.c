#define _GNU_SOURCE

#include "accpcie.h"
#include <time.h>
#include <linux/input.h>
#include <termios.h>
#include <fcntl.h>
#include <sys/prctl.h>
#include <signal.h>
#include <unistd.h>
#include <pthread.h>


struct termios orig_termios;

int verbosity = 0;
ULONGLONG bar_addr = 0x10020300000;
FT_HANDLE ftHandle = 0;
int exit_all = 0;
int ctrlC_hit = 0;
unsigned char *uart_addr_tx;
unsigned char *uart_addr_rx;

#define BUF_SIZE 100 * 1024 * 1024

typedef struct __attribute__((packed)) _ring_buff
{
    char buffer[BUF_SIZE];
    int rptr;
    int wptr;
}RING_BUFF;

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
        usleep(20);
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
    return;
}

void set_bar(ULONGLONG addr)
{
    bar_addr = addr;
    return;
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
           if ( strcmp(ptr, "1dd8000b") == 0 ) {
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

unsigned char *map_fpga_mem32(ULONGLONG inst_offset)
{
    unsigned char *addr = NULL;

    off_t offset = bar_addr + inst_offset;
    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = (offset / pagesize) * pagesize;
    off_t page_offset = offset - page_base;

    if ( verbosity > 1 ) {
        printf("read_fpag_mem32 with inst_offset %llx\n", inst_offset);
        printf("page_size %lx; page_base %lx; offset %lx; page_offset %lx\n", pagesize, page_base, offset, page_offset);
    }
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return addr;
    }

    unsigned char *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page_base);
    close(fd);
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        return addr;
    }

    addr = mem + page_offset;
    if ( verbosity > 1 ) {
        printf("allocated mem %llx; addr %llx\n", (ULONGLONG)mem, (ULONGLONG)addr);
    }

    return addr;
}

int read_fpga_mem32(unsigned char *inst_offset, DWORD reg, DWORD *data)
{
    /*
    volatile unsigned char *addr;

    off_t offset = bar_addr + inst_offset + reg;
    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = (offset / pagesize) * pagesize;
    off_t page_offset = offset - page_base;

    if ( verbosity > 1 ) {
        printf("read_fpag_mem32 with inst_offset %llx\n", inst_offset);
        printf("page_size %lx; page_base %lx; offset %lx; page_offset %lx\n", pagesize, page_base, offset, page_offset);
    }
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    */
    /* int fd = open("/sys/bus/pci/devices/0000:02:00.0/resource0", O_RDWR | O_SYNC); */
    /*
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }

    unsigned char *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page_base);
    */
    /* unsigned char *mem = mmap((void *)bar_addr, 1024*1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); */
    /*
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd);
        return FT_ERROR_MAP_PCIE;
    }
    */
    /* addr = mem + inst_offset + reg; */
    /*
    addr = mem + page_offset;
    if ( verbosity > 1 ) {
        printf("allocated mem %llx; addr %llx\n", (ULONGLONG)mem, (ULONGLONG)addr);
    }
    */
    /* addr = (DWORD *)(mem | (unsigned char *)ftHandle | (unsigned char *)reg); */
    *data = *((DWORD *)(inst_offset + reg));

    /*
    munmap((void *)mem, 4096);
    close(fd);
    */
    return FT_OK;
}

int write_fpga_mem32(unsigned char *inst_offset, DWORD reg, ULONG value)
{
    /*
    unsigned char *addr;

    off_t offset = bar_addr + inst_offset + reg;
    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = (offset / pagesize) * pagesize;
    off_t page_offset = offset - page_base;

    if ( verbosity > 1 ) {
        printf("write_fpag_mem32 with inst_offset %llx\n", inst_offset);
        printf("page_size %lx; page_base %lx; offset %lx; page_offset %lx\n", pagesize, page_base, offset, page_offset);
    }
    int fd = open("/dev/mem", O_RDWR | O_SYNC); 
    */
    /* int fd = open("/sys/bus/pci/devices/0000:02:00.0/resource0", O_RDWR | O_SYNC); */
    /*
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }

    unsigned char *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page_base);
    */
    /* unsigned char *mem = mmap((void *)bar_addr, 1024*1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); */
    /*
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd);
        return FT_ERROR_MAP_PCIE;
    }
    */
    /* addr = mem + inst_offset + (ULONGLONG)reg; */
    /* addr = mem + page_offset; */
    /* 
    if ( verbosity > 1 ) {
        printf("allocated mem %llx; addr %llx\n", (ULONGLONG)mem, (ULONGLONG)addr);
    }
    */
    *((DWORD *)(inst_offset + reg)) = (DWORD)value;

    /*
    munmap((void *)mem, 4096);
    close(fd); 
    */
    return FT_OK;
}

void *send_tx_input(void *port)
{
    int ch;
    int inst = *(int *)port, dummy;
    int end_thread = 0;
    /* DWORD data; */
    /* ULONGLONG uart_addr; */

    dummy = inst;
    inst = dummy;

    set_conio_terminal_mode();
 
    /* initscr(); */
    /* uart_addr = UART_0_OFFSET + inst * UART_INST_OFFSET; */
    for ( ; ; ) {
        if ( !kbhit() ) {
            ch = getch_local();
            while ( ch != EOF ) {
                if ( ch == 1 ) {
                    end_thread = 1;
                } else if ( ch == 24 ) {
                    if ( end_thread == 1 ) {
                        end_thread = 2;
                        exit_all = 1;
                        ch = EOF;
                        break;
                    } else
                        end_thread = 0;
                } else
                    end_thread = 0;
                if ( verbosity )
                    printf("sending character %c\n", ch);
		if ( end_thread == 0 ) {
                    write_fpga_mem32(uart_addr_tx, UART_0_TXDATA_REG, (DWORD)ch);
                }
                usleep(40);
                ch = getch_local();
            }
            if ( verbosity > 1 )
                printf("input buffer is empty\n");
        }
        if ( end_thread == 2 )
            break;
        usleep(40);
    }
    /* endwin(); */
    reset_terminal_mode();
    pthread_exit(NULL);
}

void *get_rx_buffer(void *inst)
{
    DWORD data;
    int port = *(int *)inst;
    int fd;
    int shm_len = BUF_SIZE + 2 * sizeof(int);
    int buf_size = BUF_SIZE;
    int rptr;
    pthread_spinlock_t lock;
    /* ULONGLONG uart_addr; */
    cpu_set_t cpuset;
    pthread_t current_thread;
    char uart_path[8];
    RING_BUFF *pptr;

    /* uart_addr = UART_0_OFFSET + port * UART_INST_OFFSET; */
    // CPU_ZERO(&cpuset);
    // CPU_SET(port + 1, &cpuset);
    // current_thread = pthread_self();
    // pthread_setaffinity_np(current_thread, sizeof(cpuset), &cpuset);

    sprintf(uart_path, "/puart%d", port);
    fd = shm_open(uart_path, O_RDWR, 0644);
    if ( fd == -1 ) {
        printf("failed to open shared memory\n");
        return 0;
    }
/*
    if ( ftruncate(fd, shm_len) == -1 ) {
        printf("failed to attach shm size\n");
        shm_unlink(uart_path);
        return 0;
    }
*/
    pptr = (RING_BUFF *)mmap(NULL, shm_len, PROT_WRITE | PROT_READ, MAP_SHARED, fd, 0);
    if ( pptr == NULL ) {
        printf("failed to map shared memory for write\n");
	shm_unlink(uart_path);
	return 0;
    }
    close(fd);

    read_fpga_mem32(uart_addr_rx, UART_0_STAT_REG, &data);
    if ( data & 0xe0 ) {
        if ( verbosity )
            printf("UART ERROR1: uart status register = %x\n", data);
    }
    pthread_spin_init(&lock, PTHREAD_PROCESS_PRIVATE);
    while ( pthread_spin_lock(&lock));
    for ( ; ; ) {
        if ( data & 0x1 ) {
            if ( verbosity )  
                printf(" uart status register = %x\n", data);
            read_fpga_mem32(uart_addr_rx, UART_0_RXDATA_REG, &data);
            if ( verbosity )  
                printf(" uart received data = %c\n", data);
            /* printf("%c", (unsigned char)(data & 0xff)); */
	    /* fflush(stdout); */
	    rptr = pptr->rptr;
	    if ( (pptr->wptr + 1) == rptr ) {
                printf("ERROR: %s ring buffer overrun\n", uart_path);
            } else {
                pptr->buffer[pptr->wptr] = (char)(data & 0xff);
		pptr->wptr = (pptr->wptr + 1) % buf_size;
	    }
	}
        read_fpga_mem32(uart_addr_rx, UART_0_STAT_REG, &data);
        if ( data & 0xe0 )
            printf("UART ERROR2: uart status register = %x\n", data);
    }
    /* endwin(); should never be here */
    pthread_spin_unlock(&lock);
    pthread_spin_destroy(&lock);
    munmap(pptr, shm_len); 
    shm_unlink(uart_path);
    return 0;
}

int ring_buffer_init(RING_BUFF *ptr)
{
    memset(ptr, 0, sizeof(RING_BUFF));
    return 0;
}

void save_uart_to_file(char *uart_file, int append)
{
    FILE *dst_fd;
    int fd;
    int i, shm_len = sizeof(RING_BUFF);
    char filename[32];
    RING_BUFF *ptr;

    strcpy(filename, "/home/diag/diag");
    strcat(filename, uart_file);
    fd = shm_open(uart_file, O_RDWR, 0644);
    if ( fd == -1 ) {
        printf("failed to open shared memory\n");
        return;
    }
/*
    if ( ftruncate(fd, shm_len) == -1 ) {
        printf("failed to attach shm size\n");
        shm_unlink(uart_file);
        return;
    }
*/
    ptr = (RING_BUFF *)mmap(NULL, shm_len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if ( ptr == NULL ) {
        printf("failed to map shared memory for write\n");
	shm_unlink(uart_file);
	return;
    }

    if ( append == 1 )
        dst_fd = fopen(filename, "a");
    else
        dst_fd = fopen(filename, "w");
    if ( dst_fd == NULL ) {
        printf("failed to open uart log file\n");
        return;
    }

    for ( i = 0; i < BUF_SIZE; i++ ) {
        if ( ptr->wptr == i ) {
            printf("\n reached the end of ring buffer %x  %x\n", i, ptr->wptr);
            break;
        }
        /* printf("%c", ptr->buffer[i]); */
        fprintf(dst_fd, "%c", ptr->buffer[i]);
    }
    fprintf(dst_fd, "saved %d characters to file", i);
    printf("saved %d characters to file %s\n", i, filename);
    fclose(dst_fd);
    munmap(ptr, shm_len);
    shm_unlink(uart_file);
    return;
}

void sig_handler(int signo)
{
    if ( signo == SIGINT ) {
        printf("Ctrl-C key is hit, treat as with Ctrl-A Ctrl-X\n");
        ctrlC_hit = 1;
    }
    return;
}

int main(int argc, char **argv)
{
    int port = atoi(argv[1]);
    int fd;
    int wptr;
    int shm_len = BUF_SIZE + 2 * sizeof(int);
    int buf_size = BUF_SIZE;
    pid_t parent_id, child_id;
    pthread_t id_rx, id_tx;
    ULONGLONG pcie_bar;
    DWORD data;
    /* ULONGLONG uart_addr; */
    char uart_path[8];
    RING_BUFF *ptr;

    if ( argc < 2 ) { 
        printf("Invalid command syntax, please provide a port number (0 - based)\n");
        return 0;
    }

    pcie_bar = get_bar_from_proc();
    if ( pcie_bar != 0 ) {
        bar_addr = pcie_bar;
    }
    printf("connecting to serial port %d at bar address 0x%llx\n", port, bar_addr);
    /* uart_addr = UART_0_OFFSET + port * UART_INST_OFFSET; */
    uart_addr_tx = map_fpga_mem32(0x10B00 + port * UART_INST_OFFSET);
    uart_addr_rx = map_fpga_mem32(0x10B00 + port * UART_INST_OFFSET);
    data = UART_RESET_TXFIFO | UART_RESET_RXFIFO;
    write_fpga_mem32(uart_addr_tx, UART_0_CTRL_REG, data);
    read_fpga_mem32(uart_addr_tx, UART_0_STAT_REG, &data);
    printf("tx/rx buffer cleared\n");

    parent_id = getpid();
    child_id = fork();

    if ( child_id > 0 ) {
        if ( signal(SIGINT, sig_handler) == SIG_ERR )
            printf("can't catch SIGINT, please use ctrl-A, ctrl-X to exit\n");

        sprintf(uart_path, "/puart%d", port);
        fd = shm_open(uart_path, O_CREAT | O_RDWR, 0644 );
        if ( fd == -1 ) {
            printf("failed to create shared memory\n");
            return 0;
        }
        if ( ftruncate(fd, shm_len) == -1 ) {
            printf("failed to set shm size\n");
            shm_unlink(uart_path);
	    return 0;
        }
        ptr = (RING_BUFF *)mmap(NULL, shm_len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        close(fd);

        ring_buffer_init(ptr);
        pthread_create(&id_tx, NULL, send_tx_input, (void *)&port);
    } else { 
        pthread_create(&id_rx, NULL, get_rx_buffer, (void *)&port);
    }

    for ( ; ; ) { 
        /* printf("\ruart console %d>", (int)port); */
	/* get_rx_buffer(port); */
	/* fflush(stdout); */
	/* send_tx_input(port); */
	if ( child_id > 0 ) {
            if ( exit_all ) {
                printf("\n");
                fflush(stdout);
                kill(child_id, SIGKILL);
                if ( argc == 3 )
                    save_uart_to_file(uart_path, 1);
                else
                    save_uart_to_file(uart_path, 0);
	        break;
            } else {
                /* print from ring buffer one character per loop */
                wptr = ptr->wptr;
                if ( wptr != ptr->rptr ) {
                    printf("%c", ptr->buffer[ptr->rptr]);
                    ptr->rptr = (ptr->rptr + 1) % buf_size;
                    fflush(stdout);
                }
            }
        }
    }
    munmap((void *)uart_addr_tx, 4096);
    munmap((void *)uart_addr_rx, 4096);
    munmap(ptr, shm_len);
    shm_unlink(uart_path);
    return 0;
}
    
