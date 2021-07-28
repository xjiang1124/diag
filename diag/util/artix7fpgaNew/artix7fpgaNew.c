
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

#define SPI_GLOBAL_INT_REG              0x1C
#define SPI_INT_STATUS_REG              0x20
#define SPI_INT_ENABLE_REG              0x28
#define SPI_SOFT_RESET_REG              0x40
#define SPI_CONTROL_REG                 0x60
#define SPI_STATUS_REG                  0x64
#define SPI_DATA_TRANSMIT_REG           0x68
#define SPI_DATA_RECEIVE_REG            0x6C
#define SPI_SLAVE_SEL_REG               0x70

#define FLASH_WRITE_STATUS_REG          0x01
#define FLASH_PAGE_PROG                 0x02
#define FLASH_READ_DATA_BYTES           0x03
#define FLASH_WRITE_DISABLE             0x04
#define FLASH_READ_STATUS_REG           0x05
#define FLASH_WRITE_ENABLE              0x06
#define FLASH_SOFT_RESET                0x0A
#define FLASH_READ_ADDR4B               0x13
#define FLASH_READ_CFG_REG              0x15
#define FLASH_SECTOR_ERASE              0x20
#define FLASH_BLOCK_ERASE_32K           0x52
#define FLASH_BLOCK_ERASE_64K           0xD8
#define FLASH_CHIP_ERASE                0x60
#define FLASH_READ_ID                   0x9F
#define FLASH_ENTER_4_BYTE_MODE         0xB7

#define FLASH_OFFSET_GOLD               0x0000000
#define FLASH_OFFSET_MAIN               0x1000000
#define FLASH_OFFSET_TEST               0x1FF0000

#define FLASH_IMG_TYPE_MAIN             0
#define FLASH_IMG_TYPE_GOLD             1
#define FLASH_IMG_TYPE_TEST             2

#define FLASH_AND_SWITCH_PAGE_CONFIG    0
#define NCSI_AND_BMC_PAGE_CONFIG        1
#define PC_AND_SERDES_PAGE_CONFIG       2

#define SWITCH_CORE_VERSION_REG         0x00
#define SWITCH_MAC_LOW_REG              0x04
#define SWITCH_MAC_HIGH_REG             0x08

#define QSFP_CTRL_FPGA_BASE_ADDR        0x2000000

#define PS48_FRAME_SIZE                 6
#define FLASH_PAGE_SIZE                 128
#define FLASH_TRANSFER_WIDTH_B          1
#define PS48_PIPELINE_SIZE              32

#define ENABLE                          1
#define DISABLE                         0

#define DEBUG                           DISABLE
//#define DEBUG                           ENABLE

// 5MHz
#define ELBA_SPI_CLK                    5000000

#define MIN(a,b)                        ((a>b)? b : a)

static int ps48_write_pipeline_test(uint32_t fd, uint32_t numByte);
static int flash_write_page_test(uint32_t fd, uint32_t addr);

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


void disp_buf(char *buf, uint32_t numByte) {
    for (int i = 0; i < numByte; i++) {
        printf("%02x ", *(buf+i));
        if (((i+1) % 16) == 0) {
            printf("\n");
        }
    }
    printf("\n");
}

// This function sends a sync command to PS-48 interface.

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
    msg[0].speed_hz = ELBA_SPI_CLK;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
 
    return 0;
}

// This function processes the response frame received from PS-48 interface.


// This function configure 4 pages in PS-48 interface.

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
    msg[0].speed_hz = ELBA_SPI_CLK;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);

    return 0;
}

static int ps48_init(uint32_t fd) {
    ps48_sync(fd);
    ps48_page_config(fd, FLASH_AND_SWITCH_PAGE_CONFIG);
    ps48_page_config(fd, NCSI_AND_BMC_PAGE_CONFIG);

    return 0;
}

static int ps48_resp(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t rxbuf[6];
    int ret;
    uint32_t val;
    int ite = 0;

    while(1) {
        memset(rxbuf, 0, 6);
        memset(msg, 0, sizeof (msg));

        msg[0].rx_buf = (intptr_t)rxbuf;
        msg[0].len = 6;
        msg[0].speed_hz = ELBA_SPI_CLK;

        ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);

        if (ret < 1) {
            return -1;
        }

        if ((rxbuf[0] & 0xC0) != 0) {
            break;
        }

        ite++;
        if (ite >= 10) {
            printf("PS48-RESP: Buffer empty\n");
            return -1;
        }
    }

#if (DEBUG == ENABLE)    
    printf("ps48-resp: rxbuf\n");
    disp_buf(rxbuf, PS48_FRAME_SIZE);
#endif

    val = (rxbuf[2] << 24) | (rxbuf[3] << 16) | (rxbuf[4] << 8) | rxbuf[5];
    //printf("val: 0x%x\n", val);
    return val;
}

static int ps48_clean_resp(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t rxbuf[6];
    int ret;
    uint32_t val;
    int max_try = 20;

    for (int i = 0; i < max_try; i++) {
        memset(rxbuf, 0, 6);
        memset(msg, 0, sizeof (msg));

        msg[0].rx_buf = (intptr_t)rxbuf;
        msg[0].len = 6;
        msg[0].speed_hz = ELBA_SPI_CLK;

        ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);

        if (ret < 1) {
            return -1;
        }
    }

    printf("PS48 FIFO cleared\n");
    return ret;
}

static int ps48_write(uint32_t fd, uint32_t addr, uint32_t data)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];    
    uint8_t *temp;
    int ret;

    temp = (uint8_t *)(&data);

    txbuf[0] = 0x40;
    txbuf[1] = addr;
    txbuf[5] = *temp++;
    txbuf[4] = *temp++;
    txbuf[3] = *temp++;
    txbuf[2] = *temp;  

#if (DEBUG == ENABLE)    
    printf("ps48-write: txbuf\n");
    disp_buf(txbuf, PS48_FRAME_SIZE);
#endif

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = ELBA_SPI_CLK;

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        return -1;
    } else {
        return 0;
    }
}

/*
 * Should only be used for Flash controller Data transmit register
 */
static int ps48_write_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte)
{
    struct spi_ioc_transfer msg[1];
    int ret = 1;
    int f_trans_w = FLASH_TRANSFER_WIDTH_B;
    uint8_t *txbuf;
    uint8_t *txbuf_1;
    uint8_t *rxbuf;
    uint8_t *rxbuf_1;
    uint32_t ovHead = 2;
    uint32_t revByte = 0;
    int val = 0;

    if (f_trans_w == FLASH_TRANSFER_WIDTH_B) {
        txbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
        rxbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
    }

    for (int i = 0; i < numByte; i++) {
        txbuf[i*6+0] = 0x40;
        txbuf[i*6+1] = addr;
        txbuf[i*6+2] = 0x00;
        txbuf[i*6+3] = 0x00;
        txbuf[i*6+4] = 0x00;
        txbuf[i*6+5] = buf[i];
    } 
    
#if (DEBUG == ENABLE)    
    printf("ps48-write_pipeline: txbuf\n");
    disp_buf(txbuf, numByte * 6);
#endif

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].rx_buf = (intptr_t)rxbuf;
    msg[0].len = (numByte+ovHead)*6;
    msg[0].speed_hz = ELBA_SPI_CLK;

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        ret = -1;
    } else {
        ret = 0;
    }
    
#if (DEBUG == ENABLE)    
    printf("ps48-write_pipeline: rxbuf\n");
    disp_buf(rxbuf, (numByte+ovHead) * 6);
#endif

    // Check write response
    for (int i = 0; i < numByte+ovHead; i++) {
        if ((rxbuf[i*6] & 0xC0) != 0) {
            revByte += rxbuf[i*6+5];
        }
    }

    // If not all responses received, keep checking
    if (revByte != numByte) {
        while(1) {
            val = ps48_resp(fd);
            if (val != -1) {
                revByte += val;
            }
            else {
                break;
            }
        }
    }

    if (revByte != numByte) {
        printf("ps48_write_pipeline failed: expect numbyte: %d; received numByte: %d\n", numByte, revByte);
        ret = -1;
    }

    free(txbuf);
    free(rxbuf);
    return ret;
}

static int ps48_read(uint32_t fd, uint32_t addr)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    uint8_t *temp;
    int ret;

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
    msg[0].speed_hz = ELBA_SPI_CLK;

#if (DEBUG == ENABLE)    
    printf("ps48-read: txbuf\n");
    disp_buf(txbuf, PS48_FRAME_SIZE);
#endif

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        return -1;
    } else {
        return 0;
    }

}

/*
 * Should only be used for Flash controller data receive register
 */
static int ps48_read_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte)
{
    struct spi_ioc_transfer msg[1];
    int ret = 1;
    int f_trans_w = FLASH_TRANSFER_WIDTH_B;
    uint8_t *txbuf;
    uint8_t *txbuf_1;
    uint8_t *rxbuf;
    uint8_t *rxbuf_1;
    uint32_t ovHead = 0;
    uint32_t revByte = 0;
    int val = 0;
    uint32_t bufIdx = 0;
    uint8_t *tmpPtr;
    uint32_t addr_f;
    addr_f = addr + QSFP_CTRL_FPGA_BASE_ADDR;

    tmpPtr = (uint8_t *)(&addr_f);

    if (f_trans_w == FLASH_TRANSFER_WIDTH_B) {
        txbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
        rxbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
    }

    for (int i = 0; i < numByte; i++) {
        txbuf[i*6+0] = 0x80;
        txbuf[i*6+1] = 0;
        txbuf[i*6+2] = tmpPtr[3];
        txbuf[i*6+3] = tmpPtr[2];
        txbuf[i*6+4] = tmpPtr[1];
        txbuf[i*6+5] = tmpPtr[0];
    } 
    
#if (DEBUG == ENABLE)    
    printf("ps48_rx_pipeline: txbuf\n");
    disp_buf(txbuf, (numByte+ovHead) * 6);
#endif

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].rx_buf = (intptr_t)rxbuf;
    msg[0].len = (numByte+ovHead)*6;
    msg[0].speed_hz = ELBA_SPI_CLK;

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        ret = -1;
    } else {
        ret = 0;
    }
    
#if (DEBUG == ENABLE)    
    printf("ps48_rx_pipeline: rxbuf\n");
    disp_buf(rxbuf, (numByte+ovHead) * 6);
#endif

    // Check write response
    for (int i = 0; i < numByte+ovHead; i++) {
        if ((rxbuf[i*6] & 0xC0) != 0) {
            buf[bufIdx] = rxbuf[i*6+5];
            bufIdx++;
        }
    }

    // If not all responses received, keep checking
    while(bufIdx < numByte) {
        val = ps48_resp(fd);
        if (val != -1) {
            buf[bufIdx] = val & 0xFF;
        }
        else {
            break;
        }
        bufIdx++;
    }

    if (bufIdx != numByte) {
        printf("ps48_read_pipeline failed: expect numbyte: %d; received numByte: %d\n", numByte, bufIdx);
        ret = -1;
    }

    free(txbuf);
    free(rxbuf);
    return ret;
}

static int ps48_noop(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    int ret;

    txbuf[0] = 0x00;
    txbuf[1] = 0x00;
    txbuf[2] = 0x00;
    txbuf[3] = 0x00;
    txbuf[4] = 0x00;
    txbuf[5] = 0x7F;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = ELBA_SPI_CLK;

#if (DEBUG == ENABLE)    
    printf("ps48-noop: txbuf\n");
    disp_buf(txbuf, PS48_FRAME_SIZE);
#endif

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        return -1;
    } else {
        return 0;
    }
}

static int ps48_qspi_ctrl_read(uint32_t fd, uint32_t addr)
{
    uint32_t addr_f;
    int ret;
    addr_f = addr + QSFP_CTRL_FPGA_BASE_ADDR;
    ret = ps48_read(fd, addr_f);
    if (ret == -1) {
        return ret;
    }

    return ps48_resp(fd);
}

static int ps48_qspi_ctrl_write(uint32_t fd, uint32_t addr, uint32_t data)
{
    uint32_t addr_f;
    int ret;
    ret = ps48_write(fd, addr, data);
    if (ret == -1) {
        return ret;
    }

    return ps48_resp(fd);
}

/*
 * flash_write uses 4B address. Make sure 4B mode is enabled
 */ 
static int flash_write(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    temp = (uint8_t *)(&addr);

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_PAGE_PROG);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    for (int i = 0; i < numByte; i++) {
        ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(buf+i));
    }

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    return ret;
}

/*
 * flash_write uses 4B address. Make sure 4B mode is enabled
 */ 
static int flash_write_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    temp = (uint8_t *)(&addr);
    uint32_t remainByte = numByte;
    uint32_t transByte;
    uint8_t *transBuf = buf;

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_PAGE_PROG);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    while(1) { 
        transByte = MIN(remainByte, PS48_PIPELINE_SIZE);
        ps48_write_pipeline(fd, SPI_DATA_TRANSMIT_REG, transBuf, transByte);
        if (remainByte <= PS48_PIPELINE_SIZE) {
            break;
        }
        transBuf += transByte;
        remainByte -= transByte;
    }

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    return ret;
}

static int flash_read(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    temp = (uint8_t *)(&addr);

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_READ_ADDR4B);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    for (int i = 0; i < numByte; i++) {
        ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, 0);
    }

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    for (int i = 0; i < (numByte+5); i++) {
        *(buf+i) = ps48_qspi_ctrl_read(fd, SPI_DATA_RECEIVE_REG);
    }

    return ret;
}

static int flash_read_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    uint8_t *transBufBase;
    uint8_t *transBuf;
    uint32_t transByte;
    uint32_t rdOvHead = 5;
    uint32_t remainByte = numByte;

    temp = (uint8_t *)(&addr);
    transBufBase = (uint8_t *) malloc(numByte);
    transBuf = transBufBase;

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    //printf("Writing flash read command\n");
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_READ_ADDR4B);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    //printf("Flushing 0s' to pop read data\n");
    while(1) { 
        transByte = MIN(remainByte, PS48_PIPELINE_SIZE);
        ps48_write_pipeline(fd, SPI_DATA_TRANSMIT_REG, transBuf, transByte);
        if (remainByte <= PS48_PIPELINE_SIZE) {
            break;
        }
        transBuf += transByte;
        remainByte -= transByte;
    }
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
    free(transBufBase);

    transBufBase = (uint8_t *) malloc(numByte + rdOvHead);
    transBuf = transBufBase;
    remainByte = numByte + rdOvHead;
    //printf("Reading flash data\n");
    while(1) { 
        transByte = MIN(remainByte, PS48_PIPELINE_SIZE);
        ps48_read_pipeline(fd, SPI_DATA_RECEIVE_REG, transBuf, transByte);
        if (remainByte <= PS48_PIPELINE_SIZE) {
            break;
        }
        transBuf += transByte;
        remainByte -= transByte;
    
        //ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
        //ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
    }

    memcpy(buf, transBufBase+rdOvHead, numByte); 

    return ret;
}

/*
 * This API is only to read one page. it will be slow to read actual image
 */
static int flash_read_page(uint32_t fd, uint32_t addr) {
    uint8_t ret = 0;
    uint8_t *buf = (uint8_t *)malloc(FLASH_PAGE_SIZE+5);

    ret = flash_read(fd, addr, buf, FLASH_PAGE_SIZE);
    disp_buf(buf+5, FLASH_PAGE_SIZE);

    free(buf);
    return ret;

}

static int flash_read_page_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf) {
    uint8_t ret = 0;

    ret = flash_read_pipeline(fd, addr, buf, FLASH_PAGE_SIZE);

    return ret;
}

/*
 * Read Status Register 
 */
static uint8_t flash_rdsr(uint32_t fd) {
    uint8_t val; 

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_READ_STATUS_REG);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, 0);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_read(fd, SPI_DATA_RECEIVE_REG);
    val = ps48_qspi_ctrl_read(fd, SPI_DATA_RECEIVE_REG);

    return val;
}

static int flash_wr_ena(uint32_t fd) {
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_WRITE_ENABLE);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
}

static int flash_wr_dis(uint32_t fd) {
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_WRITE_DISABLE);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
}

static int flash_ena_4B_addr(uint32_t fd) {
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_ENTER_4_BYTE_MODE);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
}

/*
 * Block erase uses 4B addressing. Make sure 4B addr is enabled
 */
static int flash_block_erase(uint32_t fd, uint32_t addr) {
    uint8_t *temp;
    temp = (uint8_t *)(&addr);

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_BLOCK_ERASE_64K);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

}

static int flash_block_erase_top(uint32_t fd, uint32_t addr) {
    uint8_t val;
    int retry = 0;
    flash_block_erase(fd, addr);

    // 2s max from spec
    while(retry < 20) {
        val = flash_rdsr(fd);
        if ( (val & 1) == 0 ) {
            break;
        }
        usleep(200*1000);
        retry++;
    }

    if (retry == 20) {
        printf("Block erase timeout!\n");
        return -1;
    }
    //printf("retry: %d\n", retry);
    return 0;
}

/*
 * flash_write_page
 * buf should have FLASH_PAGE_SIZE allocated
 */
static int flash_write_page(uint32_t fd, uint32_t addr, uint8_t *buf) {
    int retry;
    uint8_t val;

    flash_write(fd, addr, buf, FLASH_PAGE_SIZE);

    // 0.25-0.75 ms program time
    while(retry < 20) {
        val = flash_rdsr(fd);
        if ( (val & 1) == 0 ) {
            break;
        }
        usleep(100);
        retry++;
    }

    if (retry == 20) {
        printf("Write page timeout!\n");
        return -1;
    }
    //printf("retry: %d\n", retry);

    return 0;

}

static int flash_write_page_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf) {
    int retry;
    uint8_t val;

    flash_write_pipeline(fd, addr, buf, FLASH_PAGE_SIZE);

    // 0.25-0.75 ms program time
    while(retry < 20) {
        val = flash_rdsr(fd);
        if ( (val & 1) == 0 ) {
            break;
        }
        usleep(100);
        retry++;
    }

    if (retry == 20) {
        printf("Write page timeout!\n");
        return -1;
    }
    //printf("retry: %d\n", retry);

    return 0;

}

static int flash_erase(char* fn, char* imageType) {
    FILE* fp;
    int fileSize;

    uint32_t fd;

    uint32_t flash_base_addr;
    uint32_t blockSize = 0x10000;
    uint32_t cur_addr;
    uint32_t end_addr;

    int bufSize;
    uint8_t *buf;
    int buf_index;

    int ret;

    printf("fn: %s, imageType: %s\n", fn, imageType);

    if (strcmp(imageType, "main") == 0) {
        printf("main image; base: 0x%x\n", FLASH_OFFSET_MAIN);
        flash_base_addr = FLASH_OFFSET_MAIN;
    }
    else if (strcmp(imageType, "gold") == 0) {
        printf("gold image; base: 0x%x\n", FLASH_OFFSET_GOLD);
        flash_base_addr = FLASH_OFFSET_GOLD;
    }
    else if (strcmp(imageType, "test") == 0) {
        printf("test image; base: 0x%x\n", FLASH_OFFSET_TEST);
        flash_base_addr = FLASH_OFFSET_TEST;
    } 
    else {
        printf("Invalid image type: %s\n", imageType);
        return -1;
    }

    // Read image data to buffer
    fp = fopen(fn, "rb");
    if ( fp == NULL )
    {
        printf("Fail to open file %s\n", fn);
        return -1;
    }
    fseek(fp, 0L, SEEK_END);
    fileSize = ftell(fp);

    bufSize = ((fileSize + (FLASH_PAGE_SIZE -1)) / FLASH_PAGE_SIZE) * FLASH_PAGE_SIZE;
    fclose(fp);


    fd = e_open(spidev_path1, O_RDWR, 0);

    //ps48_init(fd);
    flash_ena_4B_addr(fd);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    close(fd);

    fd = e_open(spidev_path1, O_RDWR, 0);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    flash_ena_4B_addr(fd);

    // Block erase
    printf("Erasing blocks\n");
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Erasing 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Erasing 0x%x\n", cur_addr);
        }

        flash_wr_ena(fd);
        ret = flash_block_erase_top(fd, cur_addr);
        cur_addr += blockSize;
        if (cur_addr >= end_addr) {
            break;
        }
    }
    flash_wr_dis(fd);

    close(fd);
}


static int flash_prog(char* fn, char* imageType) {
    FILE* fp;
    int fileSize;

    uint32_t fd;

    uint32_t flash_base_addr;
    uint32_t blockSize = 0x10000;
    uint32_t cur_addr;
    uint32_t end_addr;

    int bufSize;
    uint8_t *buf;
    int buf_index;

    int ret;

    printf("fn: %s, imageType: %s\n", fn, imageType);

    if (strcmp(imageType, "main") == 0) {
        printf("main image; base: 0x%x\n", FLASH_OFFSET_MAIN);
        flash_base_addr = FLASH_OFFSET_MAIN;
    }
    else if (strcmp(imageType, "gold") == 0) {
        printf("gold image; base: 0x%x\n", FLASH_OFFSET_GOLD);
        flash_base_addr = FLASH_OFFSET_GOLD;
    }
    else if (strcmp(imageType, "test") == 0) {
        printf("test image; base: 0x%x\n", FLASH_OFFSET_TEST);
        flash_base_addr = FLASH_OFFSET_TEST;
    } 
    else {
        printf("Invalid image type: %s\n", imageType);
        return -1;
    }

    // Read image data to buffer
    fp = fopen(fn, "rb");
    if ( fp == NULL )
    {
        printf("Fail to open file %s\n", fn);
        return -1;
    }
    fseek(fp, 0L, SEEK_END);
    fileSize = ftell(fp);
    fseek(fp, 0L, SEEK_SET);

    bufSize = ((fileSize + (FLASH_PAGE_SIZE -1)) / FLASH_PAGE_SIZE) * FLASH_PAGE_SIZE;
    printf("fileSize = 0x%x, bufSize = 0x%x\n", fileSize, bufSize);
    buf = (uint8_t *) malloc(bufSize);
    memset(buf, 0xFF, bufSize);

    if (fread(buf, sizeof(*buf), fileSize, fp) != fileSize) {
        printf("Failed to read file\n");
        free(buf);
        fclose(fp);
        return -1;
    }
    fclose(fp);

    // Some wired WA. Otherwise first erase will not happen
    fd = e_open(spidev_path1, O_RDWR, 0);
    ps48_init(fd);
    flash_ena_4B_addr(fd);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    close(fd);

    fd = e_open(spidev_path1, O_RDWR, 0);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    flash_ena_4B_addr(fd);

    // Block erase
    printf("Erasing blocks\n");
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Erasing 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Erasing 0x%x\n", cur_addr);
        }

        flash_wr_ena(fd);
        ret = flash_block_erase_top(fd, cur_addr);
        cur_addr += blockSize;
        if (cur_addr >= end_addr) {
            break;
        }
    }

    // Write date to flash
    printf("Programming image\n");
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    buf_index = 0;

    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Writing 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Writing 0x%x\n", cur_addr);
        }

        flash_wr_ena(fd);
        ret = flash_write_page_pipeline(fd, cur_addr, (buf+buf_index));
        cur_addr += FLASH_PAGE_SIZE;
        buf_index += FLASH_PAGE_SIZE;
        if (cur_addr >= end_addr) {
            break;
        }
    }
    flash_wr_dis(fd);

    free(buf);
    close(fd);
}

static int flash_read_to_file(char* fn, char* imageType) {
    FILE* fp;
    int fileSize;

    uint32_t fd;

    uint32_t flash_base_addr;
    uint32_t cur_addr;
    uint32_t end_addr;

    int bufSize;
    uint8_t *buf;
    int buf_index;

    int ret;

    printf("fn: %s, imageType: %s\n", fn, imageType);

    if (strcmp(imageType, "main") == 0) {
        printf("main image; base: 0x%x\n", FLASH_OFFSET_MAIN);
        flash_base_addr = FLASH_OFFSET_MAIN;
        bufSize = 0x1000000;
        //bufSize = 0x3B0000;
    }
    else if (strcmp(imageType, "gold") == 0) {
        printf("gold image; base: 0x%x\n", FLASH_OFFSET_GOLD);
        flash_base_addr = FLASH_OFFSET_GOLD;
        bufSize = 0x1000000;
        //bufSize = 0x3B0000;
    }
    else if (strcmp(imageType, "test") == 0) {
        printf("test image; base: 0x%x\n", FLASH_OFFSET_TEST);
        flash_base_addr = FLASH_OFFSET_TEST;
        bufSize = 0x200;
    } 
    else {
        printf("Invalid image type: %s\n", imageType);
        return -1;
    }

    buf = (uint8_t *) malloc(bufSize);

    fd = e_open(spidev_path1, O_RDWR, 0);

    ps48_init(fd);
    flash_ena_4B_addr(fd);

    // Read data from flash
    printf("Reading flash data from offset 0x%x of 0x%x number of bytes\n", flash_base_addr, bufSize);
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    buf_index = 0;

    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Reading 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Reading 0x%x\n", cur_addr);
        }

        ret = flash_read_page_pipeline(fd, cur_addr, (buf+buf_index));
        cur_addr += FLASH_PAGE_SIZE;
        buf_index += FLASH_PAGE_SIZE;
        if (cur_addr >= end_addr) {
            break;
        }
    }

    //printf("flash_read buf: \n");
    //disp_buf(buf, bufSize);

    // Write to file
    FILE *write_ptr;
    fp = fopen(fn,"wb");
    fwrite(buf, bufSize, 1, fp);
    fclose(fp);

    free(buf);
    close(fd);
}

static int flash_write_page_test(uint32_t fd, uint32_t addr) {
    uint8_t * buf;
    uint8_t val_sr;

    buf = (uint8_t *)malloc(FLASH_PAGE_SIZE);

    for (int i = 0; i < FLASH_PAGE_SIZE; i++) {
        *(buf+i) = (uint8_t) i;
    }

    flash_ena_4B_addr(fd);
    flash_wr_ena(fd);

    val_sr = flash_rdsr(fd);
    printf("SR: 0x%x\n", val_sr);

    flash_write_page_pipeline(fd, addr, buf);
    flash_wr_dis(fd);

    printf("Write Bufer:\n");
    disp_buf(buf, FLASH_PAGE_SIZE);

    free(buf);
    return 0;
}

static int ps48_write_pipeline_test(uint32_t fd, uint32_t numByte) {
    uint8_t *buf;

    buf = (uint8_t *)malloc(numByte);
    for (int i = 0; i < numByte; i++) {
        *(buf+i) = (uint8_t) i;
    }
    disp_buf(buf, numByte);

    // Reset FIFO pointer    
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_write_pipeline(fd, SPI_DATA_TRANSMIT_REG, buf, numByte);

    free(buf);
    return 0;

}

static int flash_read_pipeline_test(uint32_t fd, uint32_t addr, uint32_t numByte) {
    uint8_t *buf;

    buf = (uint8_t *)malloc(numByte);

    flash_read_pipeline(fd, addr, buf, numByte);

    disp_buf(buf, numByte);

    free(buf);
    return 0;
}

static void usage(void)
{
    printf("artix7fpga -r addr\n");                      // Read PS-48 Register
    printf("artix7fpga -w addr data\n");                 // Write PS-48 Register
    printf("artix7fpga -prog file_name main/gold\n");
    printf("artix7fpga -file file_name main/gold\n");
    exit(1);
}

static void usage_full (void) {
    char *usage_ptr = 
        "============================================\n"
        "QSPI flash\n"
        "   -r addr\n"
        "       Read flash controller register\n"
        "   -w addr data\n"
        "       Write flash contorller register\n"
        "   -prog file_name main/gold\n"
        "       Program FPGA image to main or gold partition\n"
        "   -file file_name main/gold\n"
        "       Read flash partition (main/gold) to file. Entire 16MB of each partition will be read out\n"
        "------------------\n"
        "Debug commands\n"
        "   -init\n"
        "       PS48 initialization: sync and page confguration\n"
        "   -noop\n"
        "       Send noop command\n"
        "   -resp\n"
        "       Retrive resp packet\n"
        "   -frdsr\n"
        "       Read flash status register\n"
        "   -frpage addr\n"
        "       Read one page data from flash at specified address\n"
        "   -fberase addr\n"
        "       Erase one block at specified address\n"
        "   -fwpage addr\n"
        "       Complie one page binary data and write to specified address of flash\n"
        "   -wp numBytes\n"
        "       PS48 write pipeline test with specified number of bytes\n"
        "   -frp addr numBytes\n"
        "       Flash read pipeline test: read certain number of bytes at specified flash address\n"
        "";

    printf("%s", usage_ptr);
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
        ps48_init(fd); 
        close(fd);
    } 
    else if ( strcmp(argv[1], "-r") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        addr = strtoul(argv[2], NULL, 0);
        val = ps48_qspi_ctrl_read(fd, addr);

        close(fd);
    }  
    else if ( strcmp(argv[1], "-w" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        if ( argc < 4 ) usage();

        addr = strtoul(argv[2], NULL, 0);
        value = strtoul(argv[3], NULL, 0);
        val = ps48_qspi_ctrl_write(fd, addr, value);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-noop" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        val = ps48_noop(fd);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-resp" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        val = ps48_resp(fd);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-frdsr" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        val = flash_rdsr(fd);
        printf("SR: 0x%x\n", val);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-frpage" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 3 ) usage();

        addr = strtoul(argv[2], NULL, 0);
        flash_read_page(fd, addr);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-fberase" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        uint8_t val_sr;
        if ( argc < 3 ) usage();

        printf("Block Erase\n");

        addr = strtoul(argv[2], NULL, 0);
        flash_ena_4B_addr(fd);
        flash_wr_ena(fd);

        val_sr = flash_rdsr(fd);
        printf("SR: 0x%x\n", val_sr);

        flash_block_erase_top(fd, addr);
        flash_wr_dis(fd);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-fwpage" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 3 ) usage();

        printf("Write Page Test\n");

        addr = strtoul(argv[2], NULL, 0);

        flash_write_page_test(fd, addr);

        close(fd);
    } 
    else if ( (strcmp(argv[1], "-fprog") == 0)  || 
              (strcmp(argv[1], "-prog") == 0)
            ) 
    {
        if ( argc < 4 ) usage();
        printf("Program image\n");
        flash_prog(argv[2], argv[3]);
    } 
    else if ( (strcmp(argv[1], "-ffile" ) == 0) ||
              (strcmp(argv[1], "-file" ) == 0) ) 
    {
        if ( argc < 4 ) usage();
        printf("Reading flash data to file\n");
        flash_read_to_file(argv[2], argv[3]);
    } 
    else if ( strcmp(argv[1], "-erase" ) == 0 ) 
    {
        if ( argc < 4 ) usage();
        printf("Erasing flash data\n");
        flash_erase(argv[2], argv[3]);
    } 

    else if ( strcmp(argv[1], "-wp" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 3 ) usage();

        uint32_t numByte = strtoul(argv[2], NULL, 0);
        printf("Write Pipeline test\n");
        ps48_write_pipeline_test(fd, numByte);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-frp" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 4 ) usage();

        uint32_t addr = strtoul(argv[2], NULL, 0);
        uint32_t numByte = strtoul(argv[3], NULL, 0);
        printf("Read Pipeline test\n");
        flash_read_pipeline_test(fd, addr, numByte);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-frp" ) == 0 ) 
    {
        usage_full();
    }

    else usage();

    return 0;
}
