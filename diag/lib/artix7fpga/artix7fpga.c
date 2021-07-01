
/*
4 * Copyright (c) 2018, Pensando Systems Inc.
 */

#include <linux/gpio.h>
#include <linux/spi/spidev.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <stdint.h>
#include <unistd.h>

// Important instructions for Read and Write from Flash.
//
// Flash Write Enable must go first before Erase or Program of Chip.
// Program command should be given only when bit 0 (WIP) of Flash Status Register is 0.
// Every Program or Erase command results in Write Disable. So Enable it next time Program or Erase command is issued.


static const char spidev_path0[] = "/dev/spidev0.0";
static const char spidev_path1[] = "/dev/spidev0.3";

#define SPI_SOFT_RESET_REG	0x40
#define SPI_SLAVE_SEL_REG	0x70
#define SPI_CONTROL_REG		0x60
#define SPI_STATUS_REG		0x64
#define SPI_DATA_TRANSMIT_REG	0x68
#define SPI_DATA_RECEIVE_REG	0x6C
#define SPI_GLOBAL_INT_REG	0x1C
#define SPI_INT_STATUS_REG	0x20
#define SPI_INT_ENABLE_REG	0x28

#define FLASH_WRITE_ENABLE	0x06
#define FLASH_READ_ID		0x9F
#define FLASH_READ_STATUS_REG	0x05
#define FLASH_READ_CFG_REG	0x15
#define FLASH_ENTER_4_BYTE_MODE	0xB7
#define FLASH_WRITE_STATUS_REG	0x01
#define FLASH_READ_DATA_BYTES	0x03
#define FLASH_SECTOR_ERASE	0x20
#define FLASH_BLOCK_ERASE	0x52
#define FLASH_CHIP_ERASE	0x60
#define FLASH_PAGE_PROG		0x02
#define FLASH_SOFT_RESET	0x0A

#define FLASH_AND_SWITCH_PAGE_CONFIG 	0
#define NCSI_AND_BMC_PAGE_CONFIG	1
#define PC_AND_SERDES_PAGE_CONFIG	2

#define SWITCH_CORE_VERSION_REG		0x00
#define SWITCH_MAC_LOW_REG		0x04
#define SWITCH_MAC_HIGH_REG		0x08

int count1, count2;


static int _e_ioctl(int fd, const char *name, unsigned long req, void *arg)
{
    int r = ioctl(fd, req, arg);
    if (r < 0) {
        perror(name);
        exit(1);
    }
    return r;
}
#define e_ioctl(fd, req, arg)       _e_ioctl(fd, #req, req, arg)

static int e_open(const char *path, int flags, int mode)
{
    int fd = open(path, flags, mode);
    if (fd < 0) {
        perror(path);
        exit(1);
    }
    return fd;
}

static int ps48_sync(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];	
 
    txbuf[0] = 0x2a;
    txbuf[1] = 0x55;
    txbuf[2] = 0x95;
    txbuf[3] = 0xaa;
    txbuf[4] = 0x56;
    txbuf[5] = 0x94;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

        printf("In SYNC Command TX\n");
        printf("0x%x\n", txbuf[0]);
        printf("0x%x\n", txbuf[1]);
        printf("0x%x\n", txbuf[2]);
        printf("0x%x\n", txbuf[3]);
        printf("0x%x\n", txbuf[4]);
        printf("0x%x\n", txbuf[5]);

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    //close(fd);
    return 0;
}

static int ps48_process_resp(uint32_t fd)
{
    struct spi_ioc_transfer msg[2];
    uint8_t txbuf[6];
    uint8_t rxbuf[6];

    while(1)
    {
    	txbuf[0] = 0x00;
    	txbuf[1] = 0x00;
    	txbuf[2] = 0x00;
    	txbuf[3] = 0x00;
    	txbuf[4] = 0x00;
    	txbuf[5] = 0x00;

    	memset(msg, 0, sizeof (msg));
    	msg[0].tx_buf = (intptr_t)txbuf;
    	msg[0].len = 6;
    	msg[0].speed_hz = 5000000;

    	msg[1].rx_buf = (intptr_t)rxbuf;
    	msg[1].len = 6;

    	e_ioctl(fd, SPI_IOC_MESSAGE(2), msg);

        if(rxbuf[0] & 0xC0) break;
    }

    //close(fd);

    if(((rxbuf[0] >> 6) & 0x3) == 0x1)
    {
        //printf("In Write Response\n");
        //printf("0x%x\n", rxbuf[0]);
        //printf("0x%x\n", rxbuf[1]);
        //printf("0x%x\n", rxbuf[2]);
        //printf("0x%x\n", rxbuf[3]);
        //printf("0x%x\n", rxbuf[4]);
        //printf("0x%x\n", rxbuf[5]);

        if(rxbuf[5] && !(rxbuf[1] & 0x1F)) 
            return 1;
        else 
            return 0;
    }
    else if(((rxbuf[0] >> 6) & 0x3) == 0x2)
    {
        printf("In Read Response\n");
        printf("0x%x\n", rxbuf[0]);
        printf("0x%x\n", rxbuf[1]);
        printf("0x%x\n", rxbuf[2]);
        printf("0x%x\n", rxbuf[3]);
        printf("0x%x\n", rxbuf[4]);
        printf("0x%x\n", rxbuf[5]); // One data byte comes in rxbuf[5] for every read.

        //*buf = rxbuf[5];

           if(rxbuf[5] == 0x88) count1++;
            else if(rxbuf[5] == 0xff) count2++;


        if(!(rxbuf[1] & 0x1F))
        { 
            //buf = rxbuf;     
            return 0;
        } 
    }
    else 
    {
        printf("In Error Response\n");
        printf("0x%x\n", rxbuf[0]);
        printf("0x%x\n", rxbuf[1]);
        printf("0x%x\n", rxbuf[2]);
        printf("0x%x\n", rxbuf[3]);
        printf("0x%x\n", rxbuf[4]);
        printf("0x%x\n", rxbuf[5]);

        printf("\n Interrupt Errors = %d", (rxbuf[1] & 0x1F));
        return 1;
    }
}


static int ps48_page_config(uint32_t fd, uint8_t pageConfig)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6], val;

    if(pageConfig == FLASH_AND_SWITCH_PAGE_CONFIG)
    {
        txbuf[0] = 0xc4;
        txbuf[1] = 0x02;
        txbuf[2] = 0x00;
        txbuf[3] = 0x00;
        txbuf[4] = 0x10;
        txbuf[5] = 0x01;
    }
    else if(pageConfig == NCSI_AND_BMC_PAGE_CONFIG)
    {
        txbuf[0] = 0xf8;
        txbuf[1] = 0x00;
        txbuf[2] = 0x00;
        txbuf[3] = 0x00;
        txbuf[4] = 0x10;
        txbuf[5] = 0x05;
    }
    else 
    {
        txbuf[0] = 0xf8;
        txbuf[1] = 0x01;
        txbuf[2] = 0x00;
        txbuf[3] = 0x80;
        txbuf[4] = 0x10;
        txbuf[5] = 0x0c;
    }

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

        printf("In CONFIG Command TX\n");
        printf("0x%x\n", txbuf[0]);
        printf("0x%x\n", txbuf[1]);
        printf("0x%x\n", txbuf[2]);
        printf("0x%x\n", txbuf[3]);
        printf("0x%x\n", txbuf[4]);
        printf("0x%x\n", txbuf[5]);


    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);

    //val = ps48_process_resp(fd);

    return 0;
}


static int ps48_write(uint32_t fd, uint32_t addr, uint32_t data)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];	
    uint8_t *temp;
    int val = 0;

    temp = (uint8_t *)(&data);

    txbuf[0] = 0x40;
    txbuf[1] = addr;
    txbuf[5] = *temp++;
    txbuf[4] = *temp++;
    txbuf[3] = *temp++;
    txbuf[2] = *temp;  // 2 3 4 5

 


    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

        //printf("In WRITE Command TX\n");
        //printf("0x%x\n", txbuf[0]);
        //printf("0x%x\n", txbuf[1]);
        //printf("0x%x\n", txbuf[2]);
        //printf("0x%x\n", txbuf[3]);
        //printf("0x%x\n", txbuf[4]);
        //printf("0x%x\n", txbuf[5]);

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    val = ps48_process_resp(fd);

    return val;
}

static int ps48_read(uint32_t fd, uint32_t addr, char *buf)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    uint8_t *temp;
    int val;

    temp = (uint8_t *)(&addr);

    txbuf[0] = 0x80;
    txbuf[1] = 0x00;
    txbuf[5] = *temp++;
    txbuf[4] = *temp++;
    txbuf[3] = *temp++;
    txbuf[2] = *temp;



    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

        printf("In READ Command TX\n");
        printf("0x%x\n", txbuf[0]);
        printf("0x%x\n", txbuf[1]);
        printf("0x%x\n", txbuf[2]);
        printf("0x%x\n", txbuf[3]);
        printf("0x%x\n", txbuf[4]);
        printf("0x%x\n", txbuf[5]);


    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    val = ps48_process_resp(fd);

    return val;
}

static int ps48_write_switch(uint32_t fd, uint8_t addr, uint32_t data)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];	
    uint8_t *temp;
    int val;

    temp = (uint8_t *)(&data);

    txbuf[0] = 0x50;
    txbuf[1] = addr;
    txbuf[2] = *temp++;
    txbuf[3] = *temp++;
    txbuf[4] = *temp++;
    txbuf[5] = *temp;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    val = ps48_process_resp(fd);
    close(fd);
    return val;
}

static int ps48_read_switch(uint32_t fd, uint32_t addr, char *buf)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    uint8_t *temp;
    int val;

    temp = (uint8_t *)(&addr);

    txbuf[0] = 0x90;
    txbuf[1] = 0x00;
    txbuf[2] = *temp++;
    txbuf[3] = *temp++;
    txbuf[4] = *temp++;
    txbuf[5] = *temp;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    val = ps48_process_resp(fd);
    close(fd);
    return val;
}


static int flash_read(uint32_t fd)
{
    uint32_t status = 0;
    uint32_t val;
    uint32_t addr, index, size;
    uint8_t rxbuf[4], *temp;
    char *buf;

    FILE* fptr = fopen("amitav.bin", "wb");

    temp = (uint8_t *)(&addr);

    size = 32*1024*1024;

    addr = 0;

    buf = (char *)malloc(size);
    memset(buf, 0, sizeof(buf));


    while(size)
    {
        temp = (uint8_t *)(&addr);
        
        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);
        ps48_write(fd, 0x68, 0x3);
        ps48_write(fd, 0x68, *(temp+3));
        ps48_write(fd, 0x68, *(temp+2));
        ps48_write(fd, 0x68, *(temp+1));
        ps48_write(fd, 0x68, *temp);

        for(index=0;index<128;index++)
            ps48_write(fd, 0x68, 0x0);

        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);

        for(index=0;index<135;index++)  
            ps48_read(fd, 0x0200006c, buf++);
 

        addr += 128;
        size -= 128;
    }

    size = 32*1024*1024;

    fwrite(buf, size, 1, fptr);
    fclose(fptr);

printf("\n %d  %d  ", count1, count2);

    return status;
}

static int flash_program(uint32_t fd, unsigned char *data)
{
    uint32_t status = 0;
    uint32_t val;
    uint32_t addr, index, size;
    uint8_t rxbuf[4], *temp;
    char *buf;

    size = 32*1024*1024;

    addr = 0;

    while(size)
    {
        temp = (uint8_t *)(&addr);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);
        ps48_write(fd, 0x68, 0x6);
        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);


        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);
        ps48_write(fd, 0x68, 0x2);
        ps48_write(fd, 0x68, *(temp+3));
        ps48_write(fd, 0x68, *(temp+2));
        ps48_write(fd, 0x68, *(temp+1));
        ps48_write(fd, 0x68, *temp);


         for(index=0;index<128;index++)
            ps48_write(fd, 0x68, *data++);

        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);

        addr += 128;
        size -= 128;
    }

    return status;
}

// Flash ID read example
//
// 1. Issue -init command
// 2. Issue -id command


// Flash write example
//
// 1. Issue -init command
// 2. Issue -fwe command
// 3. Issue -fe command
// 4. Issue -fwe command
// 5. Issue -ff command
// 6. Issue -fw command




static void usage(void)
{
    printf("artix7fpga (-init) \n");                          // Initialize PS-48
    printf("artix7fpga (-r addr) \n");                        // Read from PS-48 Register
    printf("artix7fpga (-w addr data) \n");                   // Write to PS-48 Register
    printf("artix7fpga (-fsr) \n");                           // Read from Flash Status Register
    printf("artix7fpga (-fcr) \n");                           // Write to Flash Config Register
    printf("artix7fpga (-fwe) \n");                           // Send Flash Write Enable Command
    printf("artix7fpga (-fwd) \n");                           // Send Flash Write Disable Command
    printf("artix7fpga (-ff) \n");                            // Send 4 Byte Addressing Command
    printf("artix7fpga (-fw) \n");                            // Send Flash Write Command
    printf("artix7fpga (-fr)  \n");                           // Send Flash Read Command
    printf("artix7fpga (-fe) \n");                            // Send Flash Erase Command
    printf("artix7fpga (-id) \n");                            // Flash Read ID Command

    exit(1);
}
	
int main(int argc, char *argv[])
{
    uint8_t val, index;
    char *buf;
    uint32_t value, addr;

    if ( argc < 2 ) usage();

    if ( strcmp(argv[1], "-init") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
    
        ps48_sync(fd);
        val = ps48_page_config(fd, FLASH_AND_SWITCH_PAGE_CONFIG);
        val = ps48_page_config(fd, NCSI_AND_BMC_PAGE_CONFIG);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-r") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        addr = strtoul(argv[2], NULL, 0);
        val = ps48_read(fd, addr, buf);

        close(fd);
    }  
    else if ( strcmp(argv[1], "-w" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        if ( argc < 4 ) usage();

        addr = strtoul(argv[2], NULL, 0);
        value = strtoul(argv[3], NULL, 0);
        val = ps48_write(fd, addr, value);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-fsr") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);


        ps48_write(fd, 0x68, 0x5);
        ps48_write(fd, 0x68, 0x0);
        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);
        ps48_read(fd, 0x0200006c, buf);
        ps48_read(fd, 0x0200006c, buf);

        close(fd);
    }  
    else if ( strcmp(argv[1], "-fwe") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);


        ps48_write(fd, 0x68, 0x6);
        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);

        close(fd);
    }  
    else if ( strcmp(argv[1], "-fwd") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);


        ps48_write(fd, 0x68, 0x4);
        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);

        close(fd);
    }  
    else if ( strcmp(argv[1], "-ff") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);


        ps48_write(fd, 0x68, 0xb7);
        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);

        close(fd);
    }  
    else if ( strcmp(argv[1], "-fcr") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);


        ps48_write(fd, 0x68, 0x15);
        ps48_write(fd, 0x68, 0x0);
        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);
        ps48_read(fd, 0x0200006c, buf);
        ps48_read(fd, 0x0200006c, buf);

        close(fd);
    }  

    else if ( strcmp(argv[1], "-rSwitch") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        addr = strtoul(argv[2], NULL, 0);
        val = ps48_read_switch(fd, addr, buf);
    } 
    else if ( strcmp(argv[1], "-wSwitch") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        if ( argc < 4 ) usage();

        addr = strtoul(argv[2], NULL, 0);
        value = strtoul(argv[3], NULL, 0);
        val = ps48_write_switch(fd, addr, value);
    } 
    else if ( strcmp(argv[1], "-fw" ) == 0 ) 
    {
        int cfgSize = 32 * 1024 *1024;
	int read_byte = 0;
	int numBytes = 0;
	int i;
        unsigned char *buf;
        unsigned char *data;

        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        buf = (unsigned char *)malloc(cfgSize);
        memset(buf, 0, sizeof(buf));

	FILE* fptr = fopen("lac.bin", "rb");
        if ( fptr == NULL ) 
        {
            printf("Cannot open file %s\n", "lac.bin");
            free(buf);
	    return -1;
	}

	data = buf;
	for ( i = 0; i < cfgSize; i++ ) 
        {
	    read_byte = fread(data, 1, 1, fptr);
	    if ( read_byte != 1 )
	        break;
	    numBytes++;
	    data++;
	}
        fclose(fptr);
        if ( numBytes != cfgSize ) 
        {
            printf("wrong file size\n");
            printf("cpldSize %d\n", cfgSize);
            printf("File Size %d\n", numBytes);
	    return -1;
	}

	data = buf;
	flash_program(fd, data);
        close(fd);
        free(buf); 
    } 
    else if (strcmp(argv[1], "-fe") == 0) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);

        ps48_write(fd, 0x02000068, 0x60);
        ps48_write(fd, 0x02000060, 0x86);
        ps48_write(fd, 0x02000060, 0x186);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-fr") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        //FILE* fptr = fopen(argv[2], "wb");
    	//uint8_t *buf;
    	//uint8_t *fpga_data;

        //if ( fptr == NULL ) {
            //printf("Cannot create file %s\n", argv[2]);
            //return -1;
        //}

        //buf = (unsigned char *)malloc(16*1024*1024);

    	//flash_init(fd);
    	//memset(buf, 0, 16*1024*1024);
	//fpga_data = buf;

    	flash_read(fd);

    	//fwrite(buf, 16*1024*1024, 1, fptr);
	//free(buf);

        close(fd);

        //fclose(fptr);
    } 
    else if ( strcmp(argv[1], "-id" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        ps48_write(fd, 0x40, 0xa);
        ps48_write(fd, 0x70, 0x0);


        ps48_write(fd, 0x68, 0x9f);
        ps48_write(fd, 0x60, 0x86);
        ps48_write(fd, 0x60, 0x186);

        close(fd);
    } 
    else usage();

    return 0;
}