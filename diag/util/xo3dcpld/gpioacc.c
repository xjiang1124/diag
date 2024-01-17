
/*
 * Copyright (c) 2018, Pensando Systems Inc.
 */

#include <linux/gpio.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <stdint.h>
#include <unistd.h>

#define GPIOHANDLES_MAX 64

#define GPIOHANDLE_REQUEST_INPUT        (1UL << 0)
#define GPIOHANDLE_REQUEST_OUTPUT       (1UL << 1)
#define GPIOHANDLE_REQUEST_ACTIVE_LOW   (1UL << 2)
#define GPIOHANDLE_REQUEST_OPEN_DRAIN   (1UL << 3)
#define GPIOHANDLE_REQUEST_OPEN_SOURCE  (1UL << 4)

#define GPIOHANDLE_GET_LINE_VALUES_IOCTL _IOWR(0xB4, 0x08, struct gpiohandle_data)
#define GPIOHANDLE_SET_LINE_VALUES_IOCTL _IOWR(0xB4, 0x09, struct gpiohandle_data)
#define GPIO_GET_LINEHANDLE_IOCTL _IOWR(0xB4, 0x03, struct gpiohandle_request)
#define GPIO_GET_LINEEVENT_IOCTL _IOWR(0xB4, 0x04, struct gpioevent_request)

static int read_gpios(int gpio)
{
    struct gpiochip_info ci;
    struct gpiohandle_request hr;
    struct gpiohandle_data hd;
    char buf[32];
    int r, fd, n, i;

    memset(&hr, 0, sizeof(hr));
    if ( gpio > 7 ) {
        if ( (fd = open("/dev/gpiochip1", O_RDWR, 0)) < 0 ) {
            printf("GPIO gpiochip1 faile open failed\n");
            return -10;
        }
        hr.lineoffsets[0] = gpio - 7;
    } else {
    	if ( (fd = open("/dev/gpiochip0", O_RDWR, 0)) < 0 ) {
            printf("GPIO gpiochip0 file open failed\n");
            return -11;
        }
    	hr.lineoffsets[0] = gpio;
    }
    if ( ioctl(fd, GPIO_GET_CHIPINFO_IOCTL, &ci) < 0 ) {
        printf("GPIO get chipinfo ioctl failed\n");
        close(fd);
        return -12;
    }

    hr.lines = 1;
    if ( ioctl(fd, GPIO_GET_LINEHANDLE_IOCTL, &hr) < 0 ) {
        printf("GPIO Get Line-Hdl ioctl failed\n");
        close(fd);
        return -13;
    }
    close(fd);

    if ( ioctl(hr.fd, GPIOHANDLE_GET_LINE_VALUES_IOCTL, &hd.values[0]) < 0 ) {
        printf("GPIO Get Line value ioctl failed\n");
        close(hr.fd);
        return -14;
    }
    close(hr.fd);
    return hd.values[0];
}

int write_gpios(int gpio, uint32_t data)
{
    struct gpiochip_info ci;
    struct gpiohandle_request hr;
    struct gpiohandle_data hd;
    int fd;

    memset(&hr, 0, sizeof(hr));
    if ( gpio > 7 ) {
        if ( (fd = open("/dev/gpiochip1", O_RDWR, 0)) < 0 ) {
            printf("GPIO gpiochip1 faile open failed\n");
            return -10;
        }
        hr.lineoffsets[0] = gpio - 7;
    } else {
    	if ( (fd = open("/dev/gpiochip0", O_RDWR, 0)) < 0 ) {
            printf("GPIO gpiochip0 file open failed\n");
            return -11;
        }
    	hr.lineoffsets[0] = gpio;
    }
    if ( ioctl(fd, GPIO_GET_CHIPINFO_IOCTL, &ci) < 0 ) {
        printf("GPIO get chipinfo ioctl failed\n");
        close(fd);
        return -12;
    }

    hr.flags = GPIOHANDLE_REQUEST_OUTPUT;
    hr.lines = 1;
    hd.values[0] = data;
    if ( ioctl(fd, GPIO_GET_LINEHANDLE_IOCTL, &hr) < 0 ) {
        printf("GPIO Get Line-Hdl ioctl failed\n");
        close(fd);
        return -13;
    }
    close(fd);
    if ( ioctl(hr.fd, GPIOHANDLE_SET_LINE_VALUES_IOCTL, &hd) < 0 ) {
        printf("GPIO Set Line ioctl failed\n");
        close(hr.fd);
        return -14;
    }
    close(hr.fd);
    return 0;
}

static void usage(void)
{
    printf("gpioacc -r gpio_num\n");
    printf("gpioacc -w gpio_num value\n");
    exit(1);
}

int main(int argc, char *argv[])
{
    uint8_t gpio_num, gpio_value;
 
    if ( argc < 2 ) {
    	usage();
    }
    if ( strcmp(argv[1], "-r") == 0 ) {
        if ( argc < 3 )
            usage();
        gpio_num = (uint8_t)strtol(argv[2], NULL, 0);
        printf("reading gpio %d\n", gpio_num);
        gpio_value = read_gpios(gpio_num);
        printf("gpio %d value = %d\n", gpio_num, gpio_value);
    } else if ( strcmp(argv[1], "-w" ) == 0 ) {
        if ( argc < 4 )
            usage();
        gpio_num = (uint8_t)strtol(argv[2], NULL, 0);
        gpio_value = (uint8_t)strtol(argv[3], NULL, 0);
        if ( write_gpios(gpio_num, gpio_value) < 0 )
            printf("failed to write gpio %d\n", gpio_num);
        else
            printf("writing to gpio %d with value value = %d\n", gpio_num, gpio_value);
    } else
        usage();

    return 0;
}
