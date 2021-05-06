
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

static const char spidev_path0[] = "/dev/spidev0.0";
static const char spidev_path1[] = "/dev/spidev0.3";

#define SPI_CONTROL_REG		0x60
#define SPI_STATUS_REG		0x64
#define SPI_DATA_TRANSMIT_REG	0x68
#define SPI_DATA_RECEIVE_REG	0x6C
#define SPI_GLOBAL_INT_REG	0x1C
#define SPI_INT_STATUS_REG	0x20
#define SPI_INT_ENABLE_REG	0x28

#define FLASH_WRITE_ENABLE	0x06000000
#define FLASH_READ_ID		0x9F000000
#define FLASH_READ_STATUS_REG	0x05000000
#define FLASH_READ_CFG_REG	0x15000000
#define FLASH_ENTER_4_BYTE_MODE	0xB7000000
#define FLASH_WRITE_STATUS_REG	0x01000000
#define FLASH_READ_DATA_BYTES	0x03000000
#define FLASH_SECTOR_ERASE	0x20000000
#define FLASH_BLOCK_ERASE	0x52000000
#define FLASH_CHIP_ERASE	0x60000000
#define FLASH_PAGE_PROG		0x02000000
#define FLASH_SOFT_RESET	0x66000000

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

static int ps48_process_resp(uint32_t fd, char *buf)
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

        if(rxbuf[0]) break;
    }

    close(fd);

    if(((rxbuf[0] >> 6) & 0x3) == 0x1)
    {
        if(rxbuf[5] && !(rxbuf[1] & 0x1F)) 
            return 1;
        else 
            return 0;
    }
    else if(((rxbuf[0] >> 6) & 0x3) == 0x2)
    {
        if(!(rxbuf[1] & 0x1F))
        { 
            buf = &rxbuf[5];     
            return 1;
        } 
    }
    else 
    {
        printf("\n Interrupt Errors = %d", (rxbuf[1] & 0xe0));
        return 1;
    }
}

static int ps48_page_config(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    int val;

    txbuf[0] = 0xc4;
    txbuf[1] = 0x40;
    txbuf[2] = 0x00;
    txbuf[3] = 0x04;
    txbuf[4] = 0x00;
    txbuf[5] = 0x01;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    val = ps48_process_resp(fd, NULL);
    close(fd);
    return val;
}

static int ps48_write(uint32_t fd, uint8_t addr, uint32_t data)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];	
    uint8_t *temp;
    int val;

    temp = (uint8_t *)(&data);

    txbuf[0] = 0x40;
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
    val = ps48_process_resp(fd, NULL);
    close(fd);
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
    txbuf[2] = *temp++;
    txbuf[3] = *temp++;
    txbuf[4] = *temp++;
    txbuf[5] = *temp;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = 5000000;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    val = ps48_process_resp(fd, buf);
    close(fd);
    return val;
}

static int flash_erase(uint32_t fd)
{
    uint32_t status = 0;
    uint32_t val;

    val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_CHIP_ERASE);

    sleep(10);
    return status;
}

static int flash_program(uint32_t fd, uint8_t* buf, uint32_t size)
{
    uint32_t status = 0;
    uint32_t val;
    uint32_t data;
    uint32_t addr = 0;
    uint8_t temp[4];
    uint32_t page_prog_cmd = FLASH_PAGE_PROG;

    while(size > 256)
    {
        val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, page_prog_cmd++);
        data = *((uint32_t *)(buf));
        val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, data);
        buf += 256;
        size -= 256;
    }

    while(size)
    {
	if(size == 1) 
        {
	    temp[0] = *buf;
	    temp[1] = 0xFF;
	    temp[2] = 0xFF;
	    temp[3] = 0xFF;
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, page_prog_cmd++);
            data = *((uint32_t *)(buf));
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, data);
            size -= 1;
        }
        else if(size == 2)
        {
	    temp[0] = *buf++;
	    temp[1] = *buf;
	    temp[2] = 0xFF;
	    temp[3] = 0xFF;
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, page_prog_cmd++);
            data = *((uint32_t *)(buf));
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, data);
            size -= 2;
        }
        else if(size == 3)
        {
	    temp[0] = *buf++;
	    temp[1] = *buf++;
	    temp[2] = *buf;
	    temp[3] = 0xFF;
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, page_prog_cmd++);
            data = *((uint32_t *)(buf));
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, data);
            size -= 3;
        }
        else
        {
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, page_prog_cmd++);
            data = *((uint32_t *)(buf));
            val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, data);
            buf += 4;
            size -= 4;
        }
    }

    return status;
}

static int flash_read(uint32_t fd, uint8_t* buf, uint32_t size)
{
    uint32_t status = 0;
    uint32_t val;
    uint32_t addr = 0;
    uint8_t rxbuf[4];
    uint32_t read_cmd = FLASH_READ_DATA_BYTES;

    val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, read_cmd);

    while(size > 4)
    {
        val = ps48_read(fd, SPI_DATA_RECEIVE_REG, rxbuf);
        memcpy(buf, rxbuf, 4);
	buf = buf + 4;
	size = size - 4;
    }

    val = ps48_read(fd, SPI_DATA_RECEIVE_REG, rxbuf);
    memcpy(buf, rxbuf, size);

    return status;
}


static int flash_id(uint32_t fd, uint8_t *buf) 
{
    uint32_t val;

    val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_READ_ID);
    val = ps48_read(fd, SPI_DATA_RECEIVE_REG, buf);

    return 0;
}

void spi_init(uint32_t fd)
{
    uint32_t val;

    val = ps48_write(fd, SPI_CONTROL_REG, 0x6);
}

void flash_init(uint32_t fd)
{
    uint32_t val;

    val = ps48_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_WRITE_ENABLE);
}

static void usage(void)
{
    printf("ps48fpga (-r addr | -w addr data) \n");
    printf("ps48fpga (-prog input_file) \n"); 
    printf("ps48fpga (-file output_file)  \n");
    printf("ps48fpga (-file output_file)  \n");
    printf("ps48fpga (-erase) \n");
    exit(1);
}

int main(int argc, char *argv[])
{
    uint8_t addr, data;
 
    if ( argc < 2 ) usage();

    if ( strcmp(argv[1], "-spiInit") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        spi_init(fd);
    } 
    else if ( strcmp(argv[1], "-flashInit") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);   
        flash_init(fd);
    } 
    else if ( strcmp(argv[1], "-r") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        addr = strtoul(argv[2], NULL, 0);
        data = ps48_read(fd, addr, &data);
        printf("0x%x\n", data);
    } 
    else if ( strcmp(argv[1], "-w" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        if ( argc < 4 ) usage();

        addr = strtoul(argv[2], NULL, 0);
        data = strtoul(argv[3], NULL, 0);
        ps48_write(fd, addr, data);
    } 
    else if ( strcmp(argv[1], "-prog" ) == 0 ) 
    {
        int cfgSize = 16 * 1024 *1024;
	int read_byte = 0;
	int numBytes = 0;
	int i;
        unsigned char *buf;
        unsigned char *data;
        char fpgaFlashId[4];

        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

	flash_id(fd, fpgaFlashId);
	if ( memcmp(fpgaFlashId, flash_id, 4) ) 
        {
            printf("Invalid cpld id %8x\n", *(uint32_t *)fpgaFlashId);
            return -1;
	}

        buf = (unsigned char *)malloc(cfgSize);
        memset(buf, 0, sizeof(buf));

	FILE* fptr = fopen(argv[2], "rb");
        if ( fptr == NULL ) 
        {
            printf("Cannot open file %s\n", argv[2]);
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
     	flash_init(fd);
    	flash_erase(fd);
	flash_program(fd, data, numBytes);
        close(fd);
        free(buf); 
    } 
    else if (strcmp(argv[1], "-erase") == 0) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

    	flash_init(fd);
    	flash_erase(fd);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-file") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        FILE* fptr = fopen(argv[2], "wb");
    	uint8_t *buf;
    	uint8_t *fpga_data;

        if ( fptr == NULL ) {
            printf("Cannot create file %s\n", argv[2]);
            return -1;
        }

        buf = (unsigned char *)malloc(16*1024*1024);

    	flash_init(fd);
    	memset(buf, 0, 16*1024*1024);
	fpga_data = buf;
    	flash_read(fd, fpga_data, 16*1024*1024);
    	fwrite(buf, 16*1024*1024, 1, fptr);
	free(buf);
        close(fd);
        fclose(fptr);
    } 
    else if ( strcmp(argv[1], "-id" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
	char id[4];
	int rc = 0, i;

    	rc = flash_id(fd, id);
    	close(fd);
	if ( rc ) 
            printf("Error getting fpga flash id\n");
        else 
        {
            printf("Flash ID: ");
	    for ( i = 0; i < 4; i++ )
                printf("%2x ", id[i]);
	    printf("\n");
        }
    } 
    else usage();

    return 0;
}
