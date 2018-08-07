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

#define CMD_ID 0x9F
#define ID_SIZE 0x6

int ReadId(unsigned char* bp)
{
	// hard code dev path for now
	char name[] = "/dev/spidev1.0";
	int fd;
	struct spi_ioc_transfer xfer[2];
	unsigned char buf[32], *tmp;
	int len, status;

	fd = open(name, O_RDWR);
	if (fd < 0) {
		perror("open");
		return 1;
	}

	memset(xfer, 0, sizeof xfer);
	memset(buf, 0, sizeof buf);
	len = sizeof buf;

	// Send a GetID command
	buf[0] = CMD_ID;
	len = ID_SIZE;
	xfer[0].tx_buf = (unsigned long)buf;
	xfer[0].len = 1;

	xfer[1].rx_buf = (unsigned long)bp;
	xfer[1].len = 6;

	status = ioctl(fd, SPI_IOC_MESSAGE(2), xfer);
	if (status < 0) {
		perror("SPI_IOC_MESSAGE");
		return -1;
	}

	printf("response(%d): ", status);
	for (tmp = bp; len; len--)
		printf("%02x ", *tmp++);
	printf("\n");

	return 0;
}
