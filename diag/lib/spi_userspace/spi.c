#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#define CPLD_DEV_NAME	"/dev/spidev0.0"
#define FLASH_DEV_NAME	"/dev/spidev1.0"

#define CPLD_RD	0xB
#define CPLD_WR	0x2

#define CMD_ID 0x9F
#define ID_SIZE 0x6

#define CPLD_SPEED	25000000
#define DELAY_USECS 0
#define BITS		8

int ReadId(unsigned char* bp)
{
//	char name[] = "/dev/spidev1.0";
	int fd;
	struct spi_ioc_transfer xfer[2];
	unsigned char buf[32], *tmp;
	int len, status;

	fd = open(FLASH_DEV_NAME, O_RDWR);
	if (fd < 0) {
		perror("open");
		return 1;
	}

	memset(xfer, 0, sizeof xfer);
	memset(buf, 0, sizeof buf);
	len = ID_SIZE;

	// Send a GetID command
	buf[0] = CMD_ID;
	xfer[0].tx_buf = (unsigned long)buf;
	xfer[0].len = 1;
	xfer[0].delay_usecs = DELAY_USECS;
	//fixme
	xfer[0].speed_hz = CPLD_SPEED;
	xfer[0].bits_per_word = BITS;

	xfer[1].rx_buf = (unsigned long)bp;
	xfer[1].len = ID_SIZE;
	xfer[0].delay_usecs = DELAY_USECS;
	//fixme
	xfer[0].speed_hz = CPLD_SPEED;
	xfer[0].bits_per_word = BITS;

	status = ioctl(fd, SPI_IOC_MESSAGE(2), xfer);
	if (status < 0) {
		perror("SPI_IOC_MESSAGE");
		return -1;
	}

	printf("response(%d): ", status);
	for (tmp = bp; len; len--)
		printf("%02x ", *tmp++);
	printf("\n");

	close(fd);
	return 0;
}

int CpldRd(unsigned char addr, unsigned char* value)
{
	int fd;
	struct spi_ioc_transfer xfer;
	unsigned char buf[32], *tmp;
	int len, status;
	unsigned char rx[4];

	fd = open(CPLD_DEV_NAME, O_RDWR);
	if (fd < 0) {
		perror("open");
		return 1;
	}

	memset(&xfer, 0, sizeof xfer);
	memset(buf, 0, sizeof buf);

	buf[0] = CPLD_RD;
	buf[1] = addr;
	buf[2] = 0;
	buf[3] = 0;

	xfer.tx_buf = (unsigned long)buf;
	xfer.len = 4;
	xfer.delay_usecs = DELAY_USECS;
	xfer.speed_hz = CPLD_SPEED;
	xfer.bits_per_word = BITS;
	xfer.rx_buf = (unsigned long)rx;

	status = ioctl(fd, SPI_IOC_MESSAGE(1), xfer);
	if (status < 0) {
		perror("SPI_IOC_MESSAGE");
		return -1;
	}

	printf("response(%d): ", status);
	for (tmp = value, len = 0; len < 4; len++)
		printf("%02x ", *tmp++);
	printf("\n");

	close(fd);
	return 0;
}

int CpldWr(unsigned char addr, unsigned char value)
{
	int fd;
	struct spi_ioc_transfer xfer;
	unsigned char buf[32], *tmp;
	int len, status;

	fd = open(CPLD_DEV_NAME, O_RDWR);
	if (fd < 0) {
		perror("open");
		return 1;
	}

	memset(&xfer, 0, sizeof xfer);
	memset(buf, 0, sizeof buf);

	buf[0] = CPLD_WR;
	buf[1] = addr;
	buf[2] = value;

	xfer.tx_buf = (unsigned long)buf;
	xfer.len = 3;
	xfer.delay_usecs = DELAY_USECS;
	xfer.speed_hz = CPLD_SPEED;
	xfer.bits_per_word = BITS;

	status = ioctl(fd, SPI_IOC_MESSAGE(1), xfer);
	if (status < 0) {
		perror("SPI_IOC_MESSAGE");
		return -1;
	}

	close(fd);
	return 0;
}
